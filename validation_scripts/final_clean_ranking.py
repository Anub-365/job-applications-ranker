import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, ".")

import httpx

BASE = "http://localhost:8000/api"

async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        # Register/Login a fresh recruiter
        import uuid
        email = f"rec.{uuid.uuid4().hex[:6]}@example.com"
        await client.post(f"{BASE}/auth/register", json={"name": "Final Recruiter", "email": email, "password": "password123", "role": "recruiter"})
        r = await client.post(f"{BASE}/auth/login", json={"email": email, "password": "password123"})
        token = r.json()["access_token"]
        
        # Create Job
        job_desc = "We are hiring an AI/ML Engineering Intern. Required: strong Python, PyTorch or TensorFlow, NLP, Machine Learning, and MLOps tooling (Docker, FastAPI)."
        skills = ["Python", "PyTorch", "TensorFlow", "BERT", "Machine Learning", "NLP", "FastAPI", "Docker", "Deep Learning"]
        
        r = await client.post(f"{BASE}/recruiters/jobs", json={
            "title": "AI/ML Intern", "description": job_desc, "required_skills": skills
        }, headers={"Authorization": f"Bearer {token}"})
        
        job_id = r.json()["id"]
        
        # Get Candidates
        r = await client.get(f"{BASE}/recruiters/jobs/{job_id}/candidates", headers={"Authorization": f"Bearer {token}"})
        candidates = r.json()
        
        print("\n" + "="*50)
        print("RECRUITER DASHBOARD RANKING")
        print("="*50)
        for rank, c in enumerate(candidates, 1):
            match = c["match"]
            print(f"#{rank} {c['student_name']:<20} | Final Score: {match['final_score']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
