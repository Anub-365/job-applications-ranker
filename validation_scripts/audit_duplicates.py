import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

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
        users = await db.execute(select(User).order_by(User.created_at.asc()))
        users = users.scalars().all()
        
        name_groups = {}
        for u in users:
            if u.role == "student":
                name_groups.setdefault(u.name, []).append(u)
                
        print("DUPLICATE USERS AUDIT\n")
        
        to_delete_user_ids = []
        canonical_user_ids = []
        
        for name, group in name_groups.items():
            if len(group) > 1:
                print(f"Name: {name} ({len(group)} accounts)")
                # Keep the MOST RECENT fully processed one, or the LAST one created
                # Wait, the user said "Arjun Karpathy (one account)". Let's keep the last created one 
                # because the last one has the fixed CGPA logic!
                canonical = group[-1]
                canonical_user_ids.append(canonical.id)
                for u in group[:-1]:
                    print(f"  [DELETE] ID: {u.id} | Email: {u.email} | Created: {u.created_at}")
                    to_delete_user_ids.append(u.id)
                print(f"  [KEEP]   ID: {canonical.id} | Email: {canonical.email} | Created: {canonical.created_at}\n")
            else:
                canonical_user_ids.append(group[0].id)
                
        print(f"Total Users to Delete: {len(to_delete_user_ids)}")
        
        with open("to_delete.txt", "w") as f:
            for uid in to_delete_user_ids:
                f.write(f"{uid}\n")

if __name__ == "__main__":
    asyncio.run(main())
