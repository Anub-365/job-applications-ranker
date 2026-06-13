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
from fastapi.concurrency import run_in_threadpool

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
        # Return 429 for quota errors, 422 for others
        status_code = 429 if result.get("is_quota") else 422
        raise HTTPException(status_code=status_code, detail=result["error"])

    profile.resume_text = result["raw_text"]
    profile.resume_structured = result["structured"]

    # Extract CGPA and map to database column
    extracted_cgpa = result["structured"].get("education", {}).get("cgpa")
    if extracted_cgpa is not None:
        import re
        try:
            if isinstance(extracted_cgpa, (int, float)):
                profile.cgpa = float(extracted_cgpa)
            else:
                # Find the first floating point number in the string (e.g. "9.8/10" -> "9.8")
                match = re.search(r'(\d+\.\d+|\d+)', str(extracted_cgpa))
                if match:
                    val = float(match.group(1))
                    if val <= 10.0:  # Validating scale
                        profile.cgpa = val
        except Exception:
            pass

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
        embedding = await run_in_threadpool(embedding_service.generate_embedding, student_text)
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
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"[DEBUG] raw_skills from resume: {raw_skills}")
    
    github_data = None
    if profile.github_metrics and profile.github_metrics.raw_data:
        github_data = profile.github_metrics.raw_data

    skill_results = await skill_service.process_skills(
        raw_skills,
        github_data=github_data,
        projects=structured.get("projects", []),
    )
    
    logger.warning(f"[DEBUG] skill_results type: {type(skill_results)}, len: {len(skill_results) if isinstance(skill_results, list) else 'N/A'}")
    if isinstance(skill_results, list) and skill_results:
        logger.warning(f"[DEBUG] first skill_result: {skill_results[0]}")
    else:
        logger.warning(f"[DEBUG] skill_results value: {skill_results}")

    # Clear and re-create skills
    for old_skill in profile.skills:
        await db.delete(old_skill)
    await db.flush()

    saved_count = 0
    for sk in skill_results:
        # GUARDRAIL: Only save if the AI is fairly certain AND not a generic blacklist word
        # (30.0 was the exact score for a 100% Base match with 0 Project/GitHub evidence = Self-Reported, 
        # lowering to 20.0 allows partial matches to render correctly on the frontend)
        if sk["confidence_score"] >= 20.0 and not sk.get("is_blacklisted", False):
            skill = Skill(
                student_id=profile.id,
                skill_name=sk["skill_name"],
                confidence_score=sk["confidence_score"],
                level=sk["level"],
            )
            db.add(skill)
            saved_count += 1
            logger.warning(f"[DEBUG] SAVED skill: {sk['skill_name']} ({sk['confidence_score']}%)")
        else:
            logger.warning(f"[DEBUG] SKIPPED skill: {sk['skill_name']} ({sk['confidence_score']}%) blacklisted={sk.get('is_blacklisted')}")
    
    logger.warning(f"[DEBUG] Total saved to DB: {saved_count}")

    profile.processing_status = "done"
    await db.flush()

    return {
        "message": "Resume processed successfully", 
        "skills_found": len([s for s in skill_results if s["confidence_score"] >= 20.0 and not s.get("is_blacklisted")]),
        "all_skills": skill_results,
        "projects_found": len(structured.get("projects", [])),
        "llm_used": result.get("llm", "Unknown")
    }


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
    summary_res = await github_service.summarize_github(github_data)
    summary = summary_res["summary"]
    if not summary_res.get("success") and summary_res.get("is_quota"):
        # We still save the data with basic summary, but we might want to inform the user
        # For now, let's just proceed but maybe add a flag if we want the frontend to know.
        pass

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
            proj.embedding = await run_in_threadpool(embedding_service.generate_embedding, student_text)
        await db.flush()

    return {
        "message": "GitHub connected successfully",
        "scores": scores,
        "summary": summary,
        "llm_used": summary_res.get("llm", "Unknown")
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
