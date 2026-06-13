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
        print("Starting comprehensive cleanup...")
        
        # 1. Fetch all students
        users = await db.execute(select(User).where(User.role == "student").order_by(User.created_at.desc()))
        users = users.scalars().all()
        
        target_names = [
            "Arjun Karpathy", "Octo Cat", "Rahul Fake", 
            "Priyansh Verma", "Priya Sharma", "John Doe"
        ]
        
        canonical_ids = []
        to_delete_ids = []
        
        # Group by name
        seen_names = set()
        
        for u in users:
            # We want to keep exactly one for the target names
            if u.name in target_names and u.name not in seen_names:
                canonical_ids.append(u.id)
                seen_names.add(u.name)
            elif u.name in target_names:
                to_delete_ids.append(u.id)
            else:
                # If they are not in target names (e.g. "Fake AI Expert"), just delete them
                to_delete_ids.append(u.id)
                
        print(f"Canonical Users to keep ({len(canonical_ids)}):")
        for u in users:
            if u.id in canonical_ids:
                print(f"  - {u.name} ({u.email})")
                
        print(f"\nUsers to delete ({len(to_delete_ids)}):")
        
        if not to_delete_ids:
            print("No duplicates to delete.")
            return
            
        # 2. Find associated profiles
        stmt = select(StudentProfile.id).where(StudentProfile.user_id.in_(to_delete_ids))
        result = await db.execute(stmt)
        profile_ids = result.scalars().all()

        if profile_ids:
            # Cascading deletes
            res = await db.execute(delete(Match).where(Match.student_id.in_(profile_ids)))
            print(f"Deleted {res.rowcount} matches.")

            res = await db.execute(delete(Skill).where(Skill.student_id.in_(profile_ids)))
            print(f"Deleted {res.rowcount} skills.")

            res = await db.execute(delete(Project).where(Project.student_id.in_(profile_ids)))
            print(f"Deleted {res.rowcount} projects.")

            res = await db.execute(delete(GithubMetrics).where(GithubMetrics.student_id.in_(profile_ids)))
            print(f"Deleted {res.rowcount} github metrics.")

            res = await db.execute(delete(StudentProfile).where(StudentProfile.id.in_(profile_ids)))
            print(f"Deleted {res.rowcount} profiles.")

        # Delete users
        res = await db.execute(delete(User).where(User.id.in_(to_delete_ids)))
        print(f"Deleted {res.rowcount} users.")

        await db.commit()
        print("\nCleanup successfully completed.")

if __name__ == "__main__":
    asyncio.run(main())
