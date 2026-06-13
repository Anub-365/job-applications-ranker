"""Skill service — extraction, normalization, and triangulated confidence scoring."""
import json
import logging
from typing import List, Dict

import google.generativeai as genai
from openai import AsyncOpenAI

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# OpenAI Client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

# Groq Clients (OpenAI-compatible)
groq_keys = [settings.GROQ_API_KEY_1, settings.GROQ_API_KEY_2, settings.GROQ_API_KEY_3]
groq_clients = [
    AsyncOpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
    for key in groq_keys if key
]

# Gemini Config
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

# Skill Blacklist to prevent generic/garbage entries
BLACKLIST = {
    "success", "skills", "skill", "experience", "qualified", "candidate",
    "teamwork", "communication", "leadership", "management",
    "problem solving", "time management", "learning", "training",
    "professional", "expert", "beginner", "intermediate", "advanced",
    "knowledge", "understanding", "ability", "proficient", "familiar",
    "good", "excellent", "strong", "basic", "working", "fast learner",
}

NORMALIZATION_PROMPT = """You are an expert technical skill extractor. Given a raw list of skills, normalize them and filter out non-technical fluff:
- Map to standard technical skills (e.g., "ReactJS", "React.js" → "React")
- Fix casing ("python" → "Python", "sql" → "SQL")
- STRICTLY EXCLUDE soft skills, buzzwords, generic words, and adjectives (e.g., "Teamwork", "Success", "Skills", "Experience", "Communication")
- Only keep concrete technical tools, programming languages, libraries, frameworks, and core IT methodologies.

Input skills: {skills}

Return ONLY a JSON object with a "skills" key containing an array of clean, normalized technical skill strings. Example: {{"skills": ["Python", "React", "Docker", "PostgreSQL"]}}"""


async def normalize_skills(raw_skills: list) -> dict:
    """Normalize skill names using LLM."""
    if not raw_skills:
        return {"success": True, "skills": [], "llm": "None"}

    # Try OpenAI first
    if openai_client:
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": NORMALIZATION_PROMPT.format(skills=json.dumps(raw_skills))},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            skills = _extract_skills_from_result(result)
            return {"success": True, "skills": skills, "llm": "OpenAI"}
        except Exception as e:
            error_msg = str(e)
            is_quota = "insufficient_quota" in error_msg or "quota_exceeded" in error_msg
            if not is_quota:
                logger.error(f"Skill normalization OpenAI error: {error_msg}")
            else:
                logger.info("Skill normalization OpenAI quota reached, attempting Groq fallback...")

    # Groq Fallback (Primary Fallback)
    for i, g_client in enumerate(groq_clients):
        try:
            response = await g_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "user", "content": NORMALIZATION_PROMPT.format(skills=json.dumps(raw_skills))},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            skills = _extract_skills_from_result(result)
            return {"success": True, "skills": skills, "llm": f"Groq (Key {i+1})"}
        except Exception as e:
            logger.warning(f"Skill normalization Groq fallback failed with Key {i+1}: {e}")
            if i == len(groq_clients) - 1:
                logger.info("All Groq keys exhausted, attempting Gemini fallback...")

    # Gemini Fallback (Secondary Fallback)
    if settings.GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = NORMALIZATION_PROMPT.format(skills=json.dumps(raw_skills))
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.0,
                )
            )
            result = json.loads(response.text)
            skills = _extract_skills_from_result(result)
            return {"success": True, "skills": skills, "llm": "Gemini"}
        except Exception as e:
            logger.error(f"Skill normalization Gemini fallback failed: {e}")

    # Fallback to basic dedup
    seen = set()
    normalized = []
    for s in raw_skills:
        clean = s.strip().title()
        if clean.lower() not in seen:
            seen.add(clean.lower())
            normalized.append(clean)
    return {"success": False, "skills": normalized, "llm": "None (Fallback)"}


def _extract_skills_from_result(result) -> list:
    """Safely extract skills list from various LLM JSON shapes."""
    if isinstance(result, dict):
        return result.get("skills", result.get("normalized", list(result.values())[0] if result else []))
    elif isinstance(result, list):
        return result
    return []


# ---------------------------------------------------------------------------
# Triangulation Scoring Model
# ---------------------------------------------------------------------------

def compute_skill_confidence(
    skill: str,
    resume_skills: list = None,
    github_languages: list = None,
    github_repos: list = None,
    projects: list = None,
) -> Dict:
    """
    Triangulation Scoring Model for skill confidence.

    Formula:
      Base Score   (30%) — Skill explicitly mentioned in resume
      Project Bonus(40%) — Skill found in project tech_stack or description
      Execution    (30%) — Skill's language found in GitHub languages + repos

    If a skill has ZERO GitHub + Project evidence → cap at 40%, label "Self-Reported".
    """
    resume_skills = resume_skills or []
    github_languages = github_languages or []
    github_repos = github_repos or []
    projects = projects or []

    skill_lower = skill.lower()

    # ---- Base Score (0-100): Is the skill on the resume? ----
    base_score = 0
    if any(skill_lower == rs.lower() for rs in resume_skills):
        base_score = 100  # Explicitly listed
    elif any(skill_lower in rs.lower() for rs in resume_skills):
        base_score = 70   # Partial match (e.g., "React Native" contains "React")

    # ---- Project Bonus (0-100): Is the skill in project tech_stacks? ----
    project_score = 0
    for proj in projects:
        tech = [t.lower() for t in proj.get("tech_stack", [])]
        desc = (proj.get("description", "") or "").lower()
        title = (proj.get("title", "") or "").lower()
        if skill_lower in tech:
            project_score = min(100, project_score + 50)  # Direct tech_stack match
        elif skill_lower in desc or skill_lower in title:
            project_score = min(100, project_score + 30)  # Mentioned in description

    # ---- Execution Proof (0-100): Is there GitHub evidence? ----
    execution_score = 0
    # Check if in GitHub languages
    if any(skill_lower == lang.lower() for lang in github_languages):
        execution_score = 80
    elif any(skill_lower in lang.lower() for lang in github_languages):
        execution_score = 50

    # Also check repo names/descriptions
    for repo in github_repos:
        name = (repo.get("name", "") or "").lower()
        desc = (repo.get("description", "") or "").lower()
        if skill_lower in name or skill_lower in desc:
            execution_score = min(100, execution_score + 20)
            break

    # ---- Triangulated Confidence ----
    confidence = (
        0.30 * base_score
        + 0.40 * project_score
        + 0.30 * execution_score
    )
    confidence = round(min(100, max(0, confidence)), 1)

    # ---- Self-Reported Check ----
    has_project_evidence = project_score > 0
    has_github_evidence = execution_score > 0
    is_self_reported = not has_project_evidence and not has_github_evidence

    if is_self_reported and confidence > 40:
        confidence = 40.0  # Cap at 40% if no external verification

    # ---- Map to level ----
    if confidence >= 85:
        level = "Advanced"
    elif confidence >= 65:
        level = "Intermediate"
    elif confidence >= 40:
        level = "Working"
    else:
        level = "Beginner"

    # Override level label for self-reported
    if is_self_reported:
        level = "Self-Reported"

    return {
        "skill_name": skill,
        "confidence_score": confidence,
        "level": level,
        "is_blacklisted": skill_lower in BLACKLIST,
        "is_self_reported": is_self_reported,
        "evidence": {
            "base": base_score,
            "project": project_score,
            "execution": execution_score,
        },
    }


async def process_skills(
    raw_skills: list,
    github_data: dict = None,
    projects: list = None,
) -> List[Dict]:
    """Full pipeline: normalize skills → compute triangulated confidence for each."""
    norm_result = await normalize_skills(raw_skills)

    # Extract the skills list from the normalization result
    if isinstance(norm_result, dict):
        normalized = norm_result.get("skills", [])
    else:
        normalized = norm_result

    github_languages = (github_data or {}).get("languages", [])
    github_repos = (github_data or {}).get("repos", [])
    projects = projects or []

    results = []
    for skill in normalized:
        conf = compute_skill_confidence(
            skill,
            resume_skills=raw_skills,  # Pass raw resume skills for base score
            github_languages=github_languages,
            github_repos=github_repos,
            projects=projects,
        )
        results.append(conf)

    # Sort by confidence descending
    results.sort(key=lambda x: x["confidence_score"], reverse=True)
    return results
