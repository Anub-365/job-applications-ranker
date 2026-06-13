import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete

from backend.models.models import (
    User, StudentProfile, Skill, GithubMetrics, Project, Match, JobDescription
)

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"statement_cache_size": 0},
    echo=False,
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def main():
    async with AsyncSessionLocal() as db:
        if not os.path.exists("to_delete.txt"):
            print("No to_delete.txt found.")
            return

        with open("to_delete.txt", "r") as f:
            ids = [line.strip() for line in f if line.strip()]

        if not ids:
            print("No IDs to delete.")
            return

        print(f"Executing deletion for {len(ids)} duplicate users...")

        # Find associated student profiles first to clean up children manually just in case
        stmt = select(StudentProfile.id).where(StudentProfile.user_id.in_(ids))
        result = await db.execute(stmt)
        profile_ids = result.scalars().all()

        if profile_ids:
            # Delete matches
            res = await db.execute(delete(Match).where(Match.student_id.in_(profile_ids)))
            print(f"Deleted {res.rowcount} matches.")

            # Delete skills
            res = await db.execute(delete(Skill).where(Skill.student_id.in_(profile_ids)))
            print(f"Deleted {res.rowcount} skills.")

            # Delete projects
            res = await db.execute(delete(Project).where(Project.student_id.in_(profile_ids)))
            print(f"Deleted {res.rowcount} projects.")

            # Delete github metrics
            res = await db.execute(delete(GithubMetrics).where(GithubMetrics.student_id.in_(profile_ids)))
            print(f"Deleted {res.rowcount} github metrics.")

            # Delete profiles
            res = await db.execute(delete(StudentProfile).where(StudentProfile.id.in_(profile_ids)))
            print(f"Deleted {res.rowcount} profiles.")

        # Finally delete users
        res = await db.execute(delete(User).where(User.id.in_(ids)))
        print(f"Deleted {res.rowcount} users.")

        await db.commit()
        print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(main())
