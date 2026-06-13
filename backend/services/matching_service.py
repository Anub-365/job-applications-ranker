"""Matching & Ranking Engine — semantic + GitHub + skill + CGPA scoring."""
import logging
from typing import List, Dict, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.embedding_service import generate_embedding

logger = logging.getLogger(__name__)


async def find_semantic_matches(
    db: AsyncSession,
    job_embedding: list,
    limit: int = 50,
) -> List[Dict]:
    """Find top student projects by cosine similarity using pgvector."""
    from sqlalchemy import select
    from backend.models.models import Project
    
    # Ensure it's a list or numpy array that pgvector can serialize
    emb_vector = list(job_embedding)
    
    stmt = (
        select(
            Project.id,
            Project.student_id,
            Project.title,
            Project.description,
            (1 - Project.embedding.cosine_distance(emb_vector)).label("semantic_score")
        )
        .where(Project.embedding.is_not(None))
        .order_by(Project.embedding.cosine_distance(emb_vector))
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    rows = result.all()

    # Group by student — keep best project per student
    student_matches = {}
    for row in rows:
        sid = str(row.student_id)
        if sid not in student_matches or row.semantic_score > student_matches[sid]["semantic_score"]:
            student_matches[sid] = {
                "student_id": sid,
                "semantic_score": round(float(row.semantic_score), 4),
                "top_project_title": row.title,
                "top_project_description": row.description,
                "project_id": str(row.id),
            }

    return list(student_matches.values())


def compute_final_score(
    semantic_score: float,
    github_score: float,
    skill_score: float,
    cgpa: float,
    has_github: bool = True,
) -> Dict:
    """
    Compute final weighted score.
    Normal:     0.50×Semantic + 0.25×GitHub + 0.20×Skill + 0.05×CGPA
    Cold start: 0.70×Semantic + 0.25×Skill + 0.05×CGPA
    """
    # Normalize CGPA to 0-100 scale (assuming max 10.0)
    cgpa_normalized = min(100, (cgpa / 10.0) * 100) if cgpa > 0 else 0

    if has_github and github_score > 0:
        final = (
            0.50 * (semantic_score * 100)
            + 0.25 * github_score
            + 0.20 * skill_score
            + 0.05 * cgpa_normalized
        )
        formula_used = "standard"
    else:
        # Cold start — no GitHub data
        final = (
            0.70 * (semantic_score * 100)
            + 0.25 * skill_score
            + 0.05 * cgpa_normalized
        )
        formula_used = "cold_start"

    return {
        "final_score": round(min(100, max(0, final)), 2),
        "formula_used": formula_used,
    }


def generate_explanation(
    semantic_score: float,
    github_score: float,
    skill_score: float,
    top_project: str,
    matched_skills: list = None,
    github_summary: str = "",
    verified_skills: list = None,
    self_reported_skills: list = None,
) -> str:
    """Generate human-readable explanation for a match."""
    reasons = []

    if semantic_score > 0.7:
        reasons.append(f"Strong semantic alignment (score: {semantic_score:.0%})")
    elif semantic_score > 0.5:
        reasons.append(f"Good semantic alignment (score: {semantic_score:.0%})")
    else:
        reasons.append(f"Partial semantic alignment (score: {semantic_score:.0%})")

    if github_score > 60:
        reasons.append(f"Strong GitHub profile (score: {github_score:.0f}/100)")
    elif github_score > 30:
        reasons.append(f"Active GitHub profile (score: {github_score:.0f}/100)")

    if matched_skills:
        reasons.append(f"Matching skills: {', '.join(matched_skills[:5])}")

    # Add verified skill details if available
    if verified_skills:
        reasons.append(f"Verified code found: {', '.join(verified_skills[:3])}")
    if self_reported_skills:
        reasons.append(f"Self-reported (no code evidence): {', '.join(self_reported_skills[:3])}")

    if top_project:
        reasons.append(f"Top matching project: {top_project}")

    if github_summary and github_score > 0:
        reasons.append(f"GitHub: {github_summary[:150]}")

    return "\n".join(f"• {r}" for r in reasons) if reasons else "Match based on profile analysis."


async def run_matching_for_job(
    db: AsyncSession,
    job_id: str,
    job_embedding: list,
    job_required_skills: list = None,
) -> List[Dict]:
    """
    Full matching pipeline for a job posting.
    1. Semantic search → top candidates
    2. Enrich with GitHub + skill scores
    3. Compute final scores
    4. Return ranked list
    """
    from backend.models.models import StudentProfile, Skill, GithubMetrics, Match
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    # Step 1: Semantic matches (Top 50 filter)
    semantic_matches = await find_semantic_matches(db, job_embedding, limit=50)

    if not semantic_matches:
        return []

    results = []
    job_required_skills = job_required_skills or []

    for match in semantic_matches:
        student_id = match["student_id"]

        # Fetch student profile with related data
        stmt = (
            select(StudentProfile)
            .where(StudentProfile.id == student_id)
            .options(
                selectinload(StudentProfile.skills),
                selectinload(StudentProfile.github_metrics),
                selectinload(StudentProfile.user),
            )
        )
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            continue

        # GitHub score
        github_score = 0.0
        github_summary = ""
        has_github = False
        if profile.github_metrics:
            github_score = profile.github_metrics.total_score
            github_summary = profile.github_metrics.summary or ""
            has_github = True

        # Skill score: average confidence of matching skills
        skill_score = 0.0
        matched_skills = []
        if profile.skills:
            if job_required_skills:
                req_lower = [s.lower() for s in job_required_skills]
                for sk in profile.skills:
                    if sk.skill_name.lower() in req_lower:
                        matched_skills.append(sk.skill_name)
                        skill_score += sk.confidence_score
                skill_score = (skill_score / len(job_required_skills)) if job_required_skills else 0
            else:
                # No required skills specified — use average of top skills
                top = sorted(profile.skills, key=lambda s: s.confidence_score, reverse=True)[:5]
                skill_score = sum(s.confidence_score for s in top) / max(len(top), 1)
                matched_skills = [s.skill_name for s in top]

        # Categorize skills by verification status
        verified_skills = []
        self_reported_skills = []
        if profile.skills:
            for sk in profile.skills:
                if hasattr(sk, 'level') and sk.level == 'Self-Reported':
                    self_reported_skills.append(sk.skill_name)
                else:
                    verified_skills.append(sk.skill_name)

        # Compute final
        final = compute_final_score(
            semantic_score=match["semantic_score"],
            github_score=github_score,
            skill_score=skill_score,
            cgpa=profile.cgpa or 0,
            has_github=has_github,
        )

        explanation = generate_explanation(
            semantic_score=match["semantic_score"],
            github_score=github_score,
            skill_score=skill_score,
            top_project=match["top_project_title"],
            matched_skills=matched_skills,
            github_summary=github_summary,
            verified_skills=verified_skills,
            self_reported_skills=self_reported_skills,
        )

        results.append({
            "student_id": student_id,
            "job_id": job_id,
            "semantic_score": match["semantic_score"],
            "github_score": round(github_score, 2),
            "skill_score": round(skill_score, 2),
            "cgpa_score": round((profile.cgpa or 0) / 10.0 * 100, 2),
            "final_score": final["final_score"],
            "explanation": explanation,
            "top_project_title": match["top_project_title"],
            "formula_used": final["formula_used"],
        })

    # Sort by final score descending
    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results
