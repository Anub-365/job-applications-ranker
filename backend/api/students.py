"""Student API — profile, resume upload, GitHub connect, matches."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.db.database import get_db
from backend.models.models import User, UserRole, StudentProfile, Project, Skill, GithubMetrics, Match
from backend.schemas.schemas import StudentProfileOut, StudentProfileUpdate, MatchOut
from backend.core.security import get_current_user
from backend.services import resume_service, github_service, embedding_service, skill_service

router = APIRouter()


async def _get_student_profile(user: User, db: AsyncSession) -> StudentProfile:
    """Helper to fetch or create student profile."""
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can access this")
    stmt = (
        select(StudentProfile)
        .where(StudentProfile.user_id == user.id)
        .options(
            selectinload(StudentProfile.projects),
            selectinload(StudentProfile.skills),
            selectinload(StudentProfile.github_metrics),
        )
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        profile = StudentProfile(user_id=user.id)
        db.add(profile)
        await db.flush()
    return profile


@router.get("/profile", response_model=StudentProfileOut)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_student_profile(user, db)
    return profile


@router.put("/profile", response_model=StudentProfileOut)
async def update_profile(
    data: StudentProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_student_profile(user, db)
    if data.github_username is not None:
        profile.github_username = data.github_username
    if data.cgpa is not None:
        profile.cgpa = data.cgpa
    if data.branch is not None:
        profile.branch = data.branch
    await db.flush()
    return profile


@router.post("/upload-resume")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    profile = await _get_student_profile(user, db)
    pdf_bytes = await file.read()

    # Process synchronously for now (can be moved to background)
    profile.processing_status = "processing"
    await db.flush()

    result = await resume_service.process_resume(pdf_bytes)

    if result.get("error"):
        profile.processing_status = "error"
        await db.flush()
        raise HTTPException(status_code=422, detail=result["error"])

    profile.resume_text = result["raw_text"]
    profile.resume_structured = result["structured"]

    # Create projects from structured data
    # Clear old projects first
    for old_proj in profile.projects:
        await db.delete(old_proj)
    await db.flush()

    structured = result["structured"]
    github_summary = ""
    if profile.github_metrics:
        github_summary = profile.github_metrics.summary or ""

    for proj_data in structured.get("projects", []):
        student_text = embedding_service.construct_student_text(
            {"skills": structured.get("skills", []), "projects": [proj_data], "experience": []},
            github_summary=github_summary,
        )
        embedding = embedding_service.generate_embedding(student_text)
        project = Project(
            student_id=profile.id,
            title=proj_data.get("title", "Untitled"),
            description=proj_data.get("description", ""),
            tech_stack=proj_data.get("tech_stack", []),
            embedding=embedding,
        )
        db.add(project)

    # Process skills
    raw_skills = structured.get("skills", [])
    github_data = None
    if profile.github_metrics and profile.github_metrics.raw_data:
        github_data = profile.github_metrics.raw_data

    skill_results = await skill_service.process_skills(
        raw_skills,
        github_data=github_data,
        projects=structured.get("projects", []),
    )

    # Clear and re-create skills
    for old_skill in profile.skills:
        await db.delete(old_skill)
    await db.flush()

    for sk in skill_results:
        skill = Skill(
            student_id=profile.id,
            skill_name=sk["skill_name"],
            confidence_score=sk["confidence_score"],
            level=sk["level"],
        )
        db.add(skill)

    profile.processing_status = "done"
    await db.flush()

    return {"message": "Resume processed successfully", "skills_found": len(skill_results), "projects_found": len(structured.get("projects", []))}


@router.post("/connect-github")
async def connect_github(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_student_profile(user, db)

    if not profile.github_username:
        raise HTTPException(status_code=400, detail="Set GitHub username in profile first")

    # Fetch GitHub data
    github_data = await github_service.fetch_github_data(profile.github_username)
    if not github_data:
        raise HTTPException(status_code=404, detail=f"GitHub user '{profile.github_username}' not found")

    # Compute scores
    scores = github_service.compute_github_scores(github_data)

    # Summarize
    summary = await github_service.summarize_github(github_data)

    # Store / update
    if profile.github_metrics:
        metrics = profile.github_metrics
    else:
        metrics = GithubMetrics(student_id=profile.id)
        db.add(metrics)

    metrics.commit_score = scores["commit_score"]
    metrics.repo_score = scores["repo_score"]
    metrics.oss_score = scores["oss_score"]
    metrics.diversity_score = scores["diversity_score"]
    metrics.activity_score = scores["activity_score"]
    metrics.total_score = scores["total_score"]
    metrics.summary = summary
    metrics.raw_data = github_data

    await db.flush()

    # Re-embed projects with updated GitHub summary if projects exist
    if profile.projects and profile.resume_structured:
        for proj in profile.projects:
            proj_data = {"title": proj.title, "description": proj.description, "tech_stack": proj.tech_stack}
            student_text = embedding_service.construct_student_text(
                {"skills": profile.resume_structured.get("skills", []), "projects": [proj_data], "experience": []},
                github_summary=summary,
            )
            proj.embedding = embedding_service.generate_embedding(student_text)
        await db.flush()

    return {
        "message": "GitHub connected successfully",
        "scores": scores,
        "summary": summary,
    }


@router.get("/matches", response_model=list[MatchOut])
async def get_matches(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_student_profile(user, db)
    stmt = (
        select(Match)
        .where(Match.student_id == profile.id)
        .order_by(Match.final_score.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
