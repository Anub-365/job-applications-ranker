"""Recruiter API — job posting, candidate ranking, match retrieval."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional
from fastapi.concurrency import run_in_threadpool

from backend.db.database import get_db
from backend.models.models import User, UserRole, JobDescription, Match, StudentProfile
from backend.schemas.schemas import JobCreate, JobOut, CandidateOut, MatchOut, SkillOut, ProjectOut
from backend.core.security import get_current_user
from backend.services import embedding_service, matching_service

router = APIRouter()


def _check_recruiter(user: User):
    if user.role != UserRole.RECRUITER:
        raise HTTPException(status_code=403, detail="Only recruiters can access this")


@router.post("/jobs", response_model=JobOut)
async def create_job(
    data: JobCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _check_recruiter(user)

    # Generate embedding for job description
    job_text = embedding_service.construct_job_text(
        title=data.title,
        description=data.description,
        required_skills=data.required_skills,
    )
    job_embedding = await run_in_threadpool(embedding_service.generate_embedding, job_text)

    job = JobDescription(
        recruiter_id=user.id,
        title=data.title,
        company=data.company,
        description=data.description,
        required_skills=data.required_skills,
        embedding=job_embedding,
    )
    db.add(job)
    await db.flush()

    # Run matching INLINE (not background) to guarantee DB persistence
    import logging
    logger = logging.getLogger(__name__)
    try:
        results = await matching_service.run_matching_for_job(
            db, str(job.id), job_embedding, data.required_skills or []
        )
        logger.warning(f"[MATCH] Produced {len(results)} candidates for job {job.id}")
        for r in results:
            match = Match(
                student_id=r["student_id"],
                job_id=r["job_id"],
                semantic_score=r["semantic_score"],
                github_score=r["github_score"],
                skill_score=r["skill_score"],
                cgpa_score=r["cgpa_score"],
                final_score=r["final_score"],
                explanation=r["explanation"],
                top_project_title=r["top_project_title"],
            )
            db.add(match)
        await db.flush()
        logger.warning(f"[MATCH] Saved {len(results)} matches to DB for job {job.id}")
    except Exception as e:
        logger.error(f"[MATCH] Matching failed for job {job.id}: {e}")
        import traceback
        traceback.print_exc()

    return job


async def _run_matching(job_id: str, job_embedding: list, required_skills: list):
    """Background task to run matching for a new job."""
    from backend.db.database import async_session
    async with async_session() as db:
        try:
            results = await matching_service.run_matching_for_job(
                db, job_id, job_embedding, required_skills
            )

            # Store matches
            for r in results:
                match = Match(
                    student_id=r["student_id"],
                    job_id=r["job_id"],
                    semantic_score=r["semantic_score"],
                    github_score=r["github_score"],
                    skill_score=r["skill_score"],
                    cgpa_score=r["cgpa_score"],
                    final_score=r["final_score"],
                    explanation=r["explanation"],
                    top_project_title=r["top_project_title"],
                )
                db.add(match)

            await db.commit()
        except Exception as e:
            import logging
            print(f"CRITICAL ERROR in _run_matching: {e}")
            import traceback
            traceback.print_exc()
            logging.getLogger(__name__).error(f"Matching failed for job {job_id}: {e}")
            await db.rollback()


@router.get("/jobs", response_model=list[JobOut])
async def list_jobs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _check_recruiter(user)
    stmt = (
        select(JobDescription)
        .where(JobDescription.recruiter_id == user.id)
        .order_by(JobDescription.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _check_recruiter(user)
    stmt = select(JobDescription).where(
        JobDescription.id == job_id,
        JobDescription.recruiter_id == user.id,
    )
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs/{job_id}/candidates", response_model=list[CandidateOut])
async def get_candidates(
    job_id: str,
    min_score: Optional[float] = Query(None, ge=0, le=100),
    branch: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _check_recruiter(user)

    # Verify job belongs to this recruiter
    job_stmt = select(JobDescription).where(
        JobDescription.id == job_id,
        JobDescription.recruiter_id == user.id,
    )
    job_result = await db.execute(job_stmt)
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch matches
    stmt = (
        select(Match)
        .where(Match.job_id == job_id)
        .order_by(Match.final_score.desc())
    )
    result = await db.execute(stmt)
    matches = result.scalars().all()

    candidates = []
    for match in matches:
        if min_score and match.final_score < min_score:
            continue

        # Fetch student profile
        profile_stmt = (
            select(StudentProfile)
            .where(StudentProfile.id == match.student_id)
            .options(
                selectinload(StudentProfile.user),
                selectinload(StudentProfile.skills),
                selectinload(StudentProfile.projects),
            )
        )
        profile_result = await db.execute(profile_stmt)
        profile = profile_result.scalar_one_or_none()
        if not profile:
            continue

        # Apply filters
        if branch and profile.branch and branch.lower() not in profile.branch.lower():
            continue
        if skill:
            student_skills = [s.skill_name.lower() for s in profile.skills]
            if skill.lower() not in student_skills:
                continue

        candidates.append(CandidateOut(
            match=MatchOut.model_validate(match),
            student_name=profile.user.name if profile.user else "Unknown",
            student_email=profile.user.email if profile.user else "",
            github_username=profile.github_username or "",
            branch=profile.branch or "",
            cgpa=profile.cgpa or 0.0,
            skills=[SkillOut.model_validate(s) for s in sorted(profile.skills, key=lambda x: x.confidence_score, reverse=True)[:10]],
            top_projects=[ProjectOut.model_validate(p) for p in profile.projects[:3]],
        ))

    return candidates


@router.post("/jobs/{job_id}/rematch")
async def rematch_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-run matching for a job (e.g., after new students register)."""
    _check_recruiter(user)

    stmt = select(JobDescription).where(
        JobDescription.id == job_id,
        JobDescription.recruiter_id == user.id,
    )
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete old matches
    old_matches = await db.execute(select(Match).where(Match.job_id == job_id))
    for m in old_matches.scalars().all():
        await db.delete(m)
    await db.flush()

    # Run matching inline
    import logging
    logger = logging.getLogger(__name__)
    try:
        results = await matching_service.run_matching_for_job(
            db, str(job.id), list(job.embedding), job.required_skills or []
        )
        for r in results:
            match = Match(
                student_id=r["student_id"],
                job_id=r["job_id"],
                semantic_score=r["semantic_score"],
                github_score=r["github_score"],
                skill_score=r["skill_score"],
                cgpa_score=r["cgpa_score"],
                final_score=r["final_score"],
                explanation=r["explanation"],
                top_project_title=r["top_project_title"],
            )
            db.add(match)
        await db.flush()
        logger.warning(f"[REMATCH] Saved {len(results)} matches for job {job.id}")
    except Exception as e:
        logger.error(f"[REMATCH] Failed for job {job.id}: {e}")
        import traceback
        traceback.print_exc()

    return {"message": f"Rematching complete. Found {len(results)} candidates."}

