"""Skill service — extraction, normalization, and confidence scoring."""
import json
import logging
from typing import List, Dict

from openai import AsyncOpenAI

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

llm_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

NORMALIZATION_PROMPT = """You are a skill normalizer. Given a list of skills, normalize them:
- Merge duplicates ("ReactJS", "React.js" → "React")
- Fix casing ("python" → "Python")
- Remove non-skills ("Teamwork", "Communication" — keep only technical skills)

Input skills: {skills}

Return ONLY a JSON array of normalized skill strings. Example: ["Python", "React", "Docker"]"""


async def normalize_skills(raw_skills: list) -> list:
    """Normalize skill names using LLM."""
    if not raw_skills:
        return []

    if not llm_client:
        # Basic fallback: capitalize and deduplicate
        seen = set()
        normalized = []
        for s in raw_skills:
            clean = s.strip().title()
            if clean.lower() not in seen:
                seen.add(clean.lower())
                normalized.append(clean)
        return normalized

    try:
        response = await llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": NORMALIZATION_PROMPT.format(skills=json.dumps(raw_skills))},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        result = json.loads(content)
        # Handle both {"skills": [...]} and [...] formats
        if isinstance(result, dict):
            return result.get("skills", result.get("normalized", list(result.values())[0] if result else []))
        return result if isinstance(result, list) else []
    except Exception as e:
        logger.error(f"Skill normalization failed: {e}")
        return raw_skills


def compute_skill_confidence(
    skill: str,
    github_languages: list = None,
    github_repos: list = None,
    projects: list = None,
) -> Dict:
    """
    Compute confidence score for a single skill.
    Formula: 0.40×GitHub + 0.30×Project + 0.20×(placeholder) + 0.10×Recency
    """
    github_languages = github_languages or []
    github_repos = github_repos or []
    projects = projects or []

    skill_lower = skill.lower()

    # GitHub evidence (0-100): skill found in GitHub languages or repo descriptions
    github_evidence = 0
    if any(skill_lower in lang.lower() for lang in github_languages):
        github_evidence = 80
    # Also check repo descriptions/names
    for repo in github_repos:
        name = (repo.get("name", "") or "").lower()
        desc = (repo.get("description", "") or "").lower()
        if skill_lower in name or skill_lower in desc:
            github_evidence = min(100, github_evidence + 20)
            break

    # Project relevance (0-100): skill found in project tech stacks or descriptions
    project_relevance = 0
    for proj in projects:
        tech = [t.lower() for t in proj.get("tech_stack", [])]
        desc = (proj.get("description", "") or "").lower()
        title = (proj.get("title", "") or "").lower()
        if skill_lower in tech or skill_lower in desc or skill_lower in title:
            project_relevance = min(100, project_relevance + 40)

    # Placeholder for optional test (default 50)
    test_score = 50

    # Recency (default 70 — assume somewhat recent)
    recency = 70

    confidence = (
        0.40 * github_evidence
        + 0.30 * project_relevance
        + 0.20 * test_score
        + 0.10 * recency
    )
    confidence = round(min(100, max(0, confidence)), 1)

    # Map to level
    if confidence >= 85:
        level = "Advanced"
    elif confidence >= 65:
        level = "Intermediate"
    elif confidence >= 40:
        level = "Working"
    else:
        level = "Beginner"

    return {
        "skill_name": skill,
        "confidence_score": confidence,
        "level": level,
    }


async def process_skills(
    raw_skills: list,
    github_data: dict = None,
    projects: list = None,
) -> List[Dict]:
    """Full pipeline: normalize skills → compute confidence for each."""
    normalized = await normalize_skills(raw_skills)
    github_languages = (github_data or {}).get("languages", [])
    github_repos = (github_data or {}).get("repos", [])
    projects = projects or []

    results = []
    for skill in normalized:
        confidence = compute_skill_confidence(
            skill,
            github_languages=github_languages,
            github_repos=github_repos,
            projects=projects,
        )
        results.append(confidence)

    # Sort by confidence descending
    results.sort(key=lambda x: x["confidence_score"], reverse=True)
    return results
