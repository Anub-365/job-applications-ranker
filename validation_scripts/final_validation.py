# -*- coding: utf-8 -*-
import os, sys
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import asyncio
import httpx
import time
import uuid

BASE = "http://localhost:8000/api"
TIMEOUT = 120

def ok(msg):    print(f"  [OK]  {msg}")
def err(msg):   print(f"  [ERR] {msg}")
def info(msg):  print(f"  [..] {msg}")
def hdr(msg):   print(f"\n{'='*65}\n  {msg}\n{'='*65}")

async def process_candidate(client, name, email, password, pdf_path, github):
    hdr(f"CANDIDATE: {name}")
    
    # Reg
    r = await client.post(f"{BASE}/auth/register", json={"name": name, "email": email, "password": password, "role": "student"})
    if r.status_code not in (200, 201):
        err(f"Reg failed: {r.text}")
        return None
    ok("Registered")
    
    # Login
    r = await client.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    token = r.json()["access_token"]
    ok("Logged in")
    
    # Upload
    info(f"Uploading {pdf_path} ...")
    t0 = time.time()
    with open(pdf_path, "rb") as f:
        r = await client.post(
            f"{BASE}/students/upload-resume",
            files={"file": (pdf_path.split("\\")[-1], f, "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT
        )
    if r.status_code == 200:
        data = r.json()
        ok(f"Resume processed in {time.time()-t0:.1f}s")
        ok(f"Skills Found: {data.get('skills_found', 0)}")
    else:
        err(f"Upload failed: {r.status_code} {r.text[:300]}")
        return None
        
    # GitHub
    info(f"Connecting GitHub: {github} ...")
    await client.put(f"{BASE}/students/profile", json={"github_username": github}, headers={"Authorization": f"Bearer {token}"})
    r = await client.post(f"{BASE}/students/connect-github", headers={"Authorization": f"Bearer {token}"}, timeout=60)
    if r.status_code == 200:
        gdata = r.json()
        ok(f"GitHub connected. Total Score: {gdata.get('scores', {}).get('total_score', 0):.1f}/100")
    else:
        err(f"GitHub connect failed: {r.status_code} {r.text[:200]}")
        
    return token

async def main():
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # 1. Process Candidates
        suffix = uuid.uuid4().hex[:6]
        c_strong = await process_candidate(client, "Arjun Karpathy", f"arjun.{suffix}@example.com", "password123", "resume_strong.pdf", "karpathy")
        c_avg = await process_candidate(client, "Octo Cat", f"octo.{suffix}@example.com", "password123", "resume_avg.pdf", "octocat")
        c_pad = await process_candidate(client, "Rahul Fake", f"rahul.{suffix}@example.com", "password123", "resume_pad.pdf", "rahulverma-web")
        
        # 2. Recruiter creates job
        hdr("RECRUITER — Create Job")
        r = await client.post(f"{BASE}/auth/register", json={"name": "Recruiter", "email": f"rec.{suffix}@example.com", "password": "password123", "role": "recruiter"})
        r = await client.post(f"{BASE}/auth/login", json={"email": f"rec.{suffix}@example.com", "password": "password123"})
        token_r = r.json()["access_token"]
        ok("Recruiter logged in")
        
        info("Creating AI/ML Intern Job...")
        job_desc = "Looking for an AI/ML Intern with experience in deep learning, Python, PyTorch or TensorFlow, and NLP/LLMs. Bonus: MLOps."
        skills = ["Python", "PyTorch", "TensorFlow", "Deep Learning", "NLP", "LLM", "MLOps"]
        r = await client.post(f"{BASE}/recruiters/jobs", json={"title": "AI/ML Intern", "description": job_desc, "required_skills": skills}, headers={"Authorization": f"Bearer {token_r}"})
        job_id = r.json()["id"]
        ok("Job created")
        
        # 3. Fetch Rankings
        hdr("FINAL RANKINGS")
        r = await client.get(f"{BASE}/recruiters/jobs/{job_id}/candidates", headers={"Authorization": f"Bearer {token_r}"})
        candidates = r.json()
        
        for rank, c in enumerate(candidates, 1):
            if c["student_name"] not in ["Arjun Karpathy", "Octo Cat", "Rahul Fake"]:
                continue
            match = c["match"]
            print(f"\n  RANK #{rank}: {c['student_name']}")
            print(f"  Final Score:    {match['final_score']:.2f} / 100")
            print(f"  Semantic Score: {match['semantic_score']:.4f}")
            print(f"  GitHub Score:   {match['github_score']:.2f}")
            print(f"  Skill Score:    {match['skill_score']:.2f}")
            print(f"  CGPA Score:     {match['cgpa_score']:.2f}")
            print(f"\n  Explanation:")
            for line in (match.get("explanation") or "").split("\n"):
                print(f"    {line}")

if __name__ == "__main__":
    asyncio.run(main())
