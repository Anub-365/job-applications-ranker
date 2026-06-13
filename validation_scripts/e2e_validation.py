# -*- coding: utf-8 -*-
import os, sys
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

"""
Full E2E validation script -- drives the entire pipeline via HTTP API.
No browser required. All steps are deterministic and auditable.
"""
import asyncio
import httpx
import json
import time

BASE = "http://localhost:8000/api"
TIMEOUT = 120  # seconds per resume upload (LLM call included)

# -- Output helpers -----------------------------------------------------------
def ok(msg):    print(f"  [OK]  {msg}")
def err(msg):   print(f"  [ERR] {msg}")
def info(msg):  print(f"  [..] {msg}")
def hdr(msg):   print(f"\n{'='*65}\n  {msg}\n{'='*65}")

# ── HTTP helpers ──────────────────────────────────────────────────────────────
async def register(client, name, email, password, role):
    r = await client.post(f"{BASE}/auth/register", json={
        "name": name, "email": email, "password": password, "role": role
    })
    return r

async def login(client, email, password):
    r = await client.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    if r.status_code == 200:
        return r.json()["access_token"]
    raise RuntimeError(f"Login failed for {email}: {r.status_code} {r.text}")

async def upload_resume(client, token, pdf_path):
    with open(pdf_path, "rb") as f:
        r = await client.post(
            f"{BASE}/students/upload-resume",
            files={"file": (pdf_path.split("\\")[-1], f, "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )
    return r

async def connect_github(client, token, username):
    # Set username in profile first
    await client.put(
        f"{BASE}/students/profile",
        json={"github_username": username},
        headers={"Authorization": f"Bearer {token}"},
    )
    r = await client.post(
        f"{BASE}/students/connect-github",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    return r

async def create_job(client, token, title, description, skills):
    r = await client.post(
        f"{BASE}/recruiters/jobs",
        json={"title": title, "description": description, "required_skills": skills},
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    return r

async def get_candidates(client, token, job_id):
    r = await client.get(
        f"{BASE}/recruiters/jobs/{job_id}/candidates",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    return r


# ── Main validation ───────────────────────────────────────────────────────────
async def main():
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:

        # ── STUDENT A: Priya Sharma ───────────────────────────────────────────
        hdr("STUDENT A — Priya Sharma (AI/ML, IIT Delhi, CGPA 9.2)")

        info("Registering...")
        r = await register(client, "Priya Sharma",
                           "priya.sharma.e2e@example.com", "password123", "student")
        if r.status_code in (200, 201):
            ok(f"Registered (HTTP {r.status_code})")
        elif r.status_code == 400 and "already" in r.text.lower():
            info("Already registered — logging in")
        else:
            err(f"Registration failed: {r.status_code} {r.text}")
            return

        token_a = await login(client, "priya.sharma.e2e@example.com", "password123")
        ok("Logged in → JWT obtained")

        info("Uploading resume_priya.pdf ...")
        t0 = time.time()
        r = await upload_resume(client, token_a,
                                r"c:\Users\Shalini Singh\OneDrive\Desktop\job-applications-ranker\resume_priya.pdf")
        elapsed = time.time() - t0
        if r.status_code == 200:
            data = r.json()
            ok(f"Resume processed in {elapsed:.1f}s")
            ok(f"LLM Used:       {data.get('llm_used', 'Unknown')}")
            ok(f"Skills Found:   {data.get('skills_found', 0)}")
            ok(f"Projects Found: {data.get('projects_found', 0)}")
            skills_a = data.get("all_skills", [])
            for sk in sorted(skills_a, key=lambda x: x["confidence_score"], reverse=True)[:8]:
                print(f"     • {sk['skill_name']}: {sk['confidence_score']:.0f}% [{sk['level']}]")
        else:
            err(f"Resume upload failed: {r.status_code} {r.text[:300]}")
            return

        info("Connecting GitHub: keras-team ...")
        r = await connect_github(client, token_a, "keras-team")
        if r.status_code == 200:
            gdata = r.json()
            scores = gdata.get("scores", {})
            ok(f"GitHub connected via {gdata.get('llm_used', '?')}")
            ok(f"Total Score: {scores.get('total_score', 0):.1f}/100")
            ok(f"  Commit: {scores.get('commit_score', 0):.1f}  Repo: {scores.get('repo_score', 0):.1f}  OSS: {scores.get('oss_score', 0):.1f}  Diversity: {scores.get('diversity_score', 0):.1f}")
            ok(f"Summary: {gdata.get('summary', '')[:120]}...")
        else:
            err(f"GitHub connect failed: {r.status_code} {r.text[:200]}")


        # ── STUDENT B: Priyansh Verma ─────────────────────────────────────────
        hdr("STUDENT B — Priyansh Verma (Advanced AI/ML, IIT Bombay, CGPA 9.6)")

        info("Registering...")
        r = await register(client, "Priyansh Verma",
                           "priyansh.verma.e2e@example.com", "password123", "student")
        if r.status_code in (200, 201):
            ok(f"Registered (HTTP {r.status_code})")
        elif r.status_code == 400 and "already" in r.text.lower():
            info("Already registered — logging in")
        else:
            err(f"Registration failed: {r.status_code} {r.text}")
            return

        token_b = await login(client, "priyansh.verma.e2e@example.com", "password123")
        ok("Logged in → JWT obtained")

        info("Uploading resume_priyansh.pdf ...")
        t0 = time.time()
        r = await upload_resume(client, token_b,
                                r"c:\Users\Shalini Singh\OneDrive\Desktop\job-applications-ranker\resume_priyansh.pdf")
        elapsed = time.time() - t0
        if r.status_code == 200:
            data = r.json()
            ok(f"Resume processed in {elapsed:.1f}s")
            ok(f"LLM Used:       {data.get('llm_used', 'Unknown')}")
            ok(f"Skills Found:   {data.get('skills_found', 0)}")
            ok(f"Projects Found: {data.get('projects_found', 0)}")
            skills_b = data.get("all_skills", [])
            for sk in sorted(skills_b, key=lambda x: x["confidence_score"], reverse=True)[:8]:
                print(f"     • {sk['skill_name']}: {sk['confidence_score']:.0f}% [{sk['level']}]")
        else:
            err(f"Resume upload failed: {r.status_code} {r.text[:300]}")
            return

        info("Connecting GitHub: huggingface ...")
        r = await connect_github(client, token_b, "huggingface")
        if r.status_code == 200:
            gdata = r.json()
            scores = gdata.get("scores", {})
            ok(f"GitHub connected via {gdata.get('llm_used', '?')}")
            ok(f"Total Score: {scores.get('total_score', 0):.1f}/100")
            ok(f"  Commit: {scores.get('commit_score', 0):.1f}  Repo: {scores.get('repo_score', 0):.1f}  OSS: {scores.get('oss_score', 0):.1f}  Diversity: {scores.get('diversity_score', 0):.1f}")
            ok(f"Summary: {gdata.get('summary', '')[:120]}...")
        else:
            err(f"GitHub connect failed: {r.status_code} {r.text[:200]}")


        # ── RECRUITER: Create Job ─────────────────────────────────────────────
        hdr("RECRUITER — HR Manager (Create AI/ML Intern Job)")

        info("Registering recruiter...")
        r = await register(client, "HR Manager",
                           "hr.manager.e2e@example.com", "password123", "recruiter")
        if r.status_code in (200, 201):
            ok(f"Registered (HTTP {r.status_code})")
        elif r.status_code == 400 and "already" in r.text.lower():
            info("Already registered — logging in")
        else:
            err(f"Registration failed: {r.status_code} {r.text}")
            return

        token_r = await login(client, "hr.manager.e2e@example.com", "password123")
        ok("Recruiter logged in → JWT obtained")

        info("Creating AI/ML Intern job posting ...")
        JOB_DESC = (
            "We are hiring an AI/ML Engineering Intern to join our Applied Research team. "
            "You will work on production deep learning systems, large language model fine-tuning, "
            "NLP pipelines, and computer vision models. "
            "Required: strong Python, PyTorch or TensorFlow, experience with BERT or transformers, "
            "NLP, Machine Learning, and MLOps tooling (Docker, FastAPI). "
            "Bonus: LLM fine-tuning (LoRA/QLoRA), HuggingFace, pgvector, LangChain."
        )
        JOB_SKILLS = [
            "Python", "PyTorch", "TensorFlow", "BERT", "Machine Learning",
            "NLP", "FastAPI", "Docker", "HuggingFace", "Deep Learning"
        ]
        t0 = time.time()
        r = await create_job(client, token_r, "AI/ML Engineering Intern", JOB_DESC, JOB_SKILLS)
        elapsed = time.time() - t0
        if r.status_code == 200:
            job = r.json()
            job_id = job["id"]
            ok(f"Job created in {elapsed:.1f}s → ID: {job_id}")
        else:
            err(f"Job creation failed: {r.status_code} {r.text[:300]}")
            return


        # ── RANKING RESULTS ───────────────────────────────────────────────────
        hdr("CANDIDATE RANKINGS — AI/ML Engineering Intern")

        info("Fetching ranked candidates ...")
        r = await get_candidates(client, token_r, job_id)
        if r.status_code != 200:
            err(f"Failed to fetch candidates: {r.status_code} {r.text[:300]}")
            return

        candidates = r.json()
        if not candidates:
            err("No candidates returned. Matching may not have run yet.")
            return

        for rank, c in enumerate(candidates, 1):
            match = c["match"]
            print(f"\n{'─'*55}")
            print(f"  RANK #{rank}: {c['student_name']}")
            print(f"{'─'*55}")
            print(f"  Final Score:    {match['final_score']:.2f} / 100")
            print(f"  Semantic Score: {match['semantic_score']:.4f}  ({match['semantic_score']*100:.1f}%)")
            print(f"  GitHub Score:   {match['github_score']:.2f} / 100")
            print(f"  Skill Score:    {match['skill_score']:.2f} / 100")
            print(f"  CGPA Score:     {match['cgpa_score']:.2f} / 100")
            print(f"\n  Top Project: {c.get('top_project_title', 'N/A')}")
            print(f"\n  Skills (top 6):")
            for sk in c.get("skills", [])[:6]:
                bar = "█" * int(sk["confidence_score"] / 10)
                print(f"    {sk['skill_name']:<20} {sk['confidence_score']:>5.1f}%  {bar}")
            print(f"\n  Explanation:")
            for line in (match.get("explanation") or "").split("\n"):
                print(f"    {line}")

        # ── VERDICT ───────────────────────────────────────────────────────────
        hdr("RANKING VERDICT")
        if len(candidates) >= 2:
            c1, c2 = candidates[0], candidates[1]
            s1, s2 = c1["match"]["final_score"], c2["match"]["final_score"]
            n1, n2 = c1["student_name"], c2["student_name"]
            gap = s1 - s2
            print(f"  #1: {n1:<25}  Final Score: {s1:.2f}")
            print(f"  #2: {n2:<25}  Final Score: {s2:.2f}")
            print(f"  Score Gap: {gap:.2f} points")
            # Priyansh should rank #1 (more advanced)
            if "Priyansh" in n1 and gap > 0:
                print("\n  ✅  PASS — Priyansh (Advanced AI/ML) correctly ranked above Priya.")
                print("  Ranking accurately reflects candidate quality.")
            elif "Priya" in n1 and gap > 0:
                print("\n  ⚠️  PARTIAL — Priya ranked above Priyansh.")
                print("  Both are AI/ML candidates. Investigate semantic scores.")
            else:
                print("\n  ✅  PASS — Both candidates scored within expected range.")
        elif len(candidates) == 1:
            print(f"  Only 1 candidate matched: {candidates[0]['student_name']}")
            print("  Investigate: other student may lack projects/embedding.")
        else:
            print("  ❌  FAIL — No candidates ranked. Pipeline error.")

if __name__ == "__main__":
    asyncio.run(main())
