"""
Live database query: Pull all students, their skills, GitHub scores,
and any existing matches from Supabase to validate the ranking engine.
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"statement_cache_size": 0},
    echo=False,
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def main():
    from backend.models.models import (
        User, StudentProfile, Skill, GithubMetrics, Project, JobDescription, Match
    )

    async with AsyncSessionLocal() as db:
        print("=" * 70)
        print("STUDENT PROFILES & SKILLS")
        print("=" * 70)

        stmt = (
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.user),
                selectinload(StudentProfile.skills),
                selectinload(StudentProfile.github_metrics),
                selectinload(StudentProfile.projects),
            )
        )
        result = await db.execute(stmt)
        profiles = result.scalars().all()

        for p in profiles:
            name = p.user.name if p.user else "Unknown"
            email = p.user.email if p.user else "Unknown"
            print(f"\n--- {name} ({email}) ---")
            print(f"  GitHub: {p.github_username or 'Not connected'}")
            print(f"  CGPA: {p.cgpa}")
            print(f"  Status: {p.processing_status}")
            print(f"  Projects: {len(p.projects)}")
            print(f"  Skills ({len(p.skills)}):")
            for sk in sorted(p.skills, key=lambda x: x.confidence_score, reverse=True):
                print(f"    • {sk.skill_name}: {sk.confidence_score:.1f}% [{sk.level}]")
            if p.github_metrics:
                gm = p.github_metrics
                print(f"  GitHub Scores:")
                print(f"    Commit Score:    {gm.commit_score}")
                print(f"    Repo Score:      {gm.repo_score}")
                print(f"    OSS Score:       {gm.oss_score}")
                print(f"    Diversity Score: {gm.diversity_score}")
                print(f"    Total Score:     {gm.total_score}")
            else:
                print(f"  GitHub Scores: None")

        print("\n" + "=" * 70)
        print("JOB DESCRIPTIONS")
        print("=" * 70)
        jobs = await db.execute(select(JobDescription).order_by(JobDescription.created_at.desc()))
        jobs = jobs.scalars().all()
        for j in jobs:
            print(f"\n  Job: {j.title} (ID: {j.id})")
            print(f"  Required Skills: {j.required_skills}")

        print("\n" + "=" * 70)
        print("MATCH RESULTS")
        print("=" * 70)
        matches = await db.execute(
            select(Match)
            .options(selectinload(Match.student))
            .order_by(Match.final_score.desc())
        )
        matches = matches.scalars().all()

        if not matches:
            print("  No matches found in database.")
        else:
            for i, m in enumerate(matches, 1):
                name = "Unknown"
                if hasattr(m, 'student') and m.student and m.student.user:
                    pass  # will resolve separately
                # Fetch student name
                sp = await db.execute(
                    select(StudentProfile)
                    .where(StudentProfile.id == m.student_id)
                    .options(selectinload(StudentProfile.user))
                )
                sp = sp.scalar_one_or_none()
                name = sp.user.name if sp and sp.user else "Unknown"

                print(f"\n  RANK #{i}: {name}")
                print(f"    Final Score:    {m.final_score:.2f}")
                print(f"    Semantic Score: {m.semantic_score:.4f} ({m.semantic_score*100:.1f}%)")
                print(f"    GitHub Score:   {m.github_score:.2f}")
                print(f"    Skill Score:    {m.skill_score:.2f}")
                print(f"    CGPA Score:     {m.cgpa_score:.2f}")
                print(f"    Explanation:")
                for line in (m.explanation or "").split("\n"):
                    print(f"      {line}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
