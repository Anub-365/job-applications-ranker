import asyncio
import httpx
import time
import os
import sys

# We assume uvicorn is running on http://127.0.0.1:8000
BASE_URL = "http://127.0.0.1:8000/api"

async def register_user(client, name, email, role):
    res = await client.post(f"{BASE_URL}/auth/register", json={
        "name": name,
        "email": email,
        "password": "password123",
        "role": role
    })
    if res.status_code == 400: # Already registered
        res = await client.post(f"{BASE_URL}/auth/login", json={
            "email": email,
            "password": "password123"
        })
    return res.json()["access_token"]

async def upload_resume(client, token, name):
    print(f"[{name}] Starting resume upload...")
    start = time.time()
    
    # Create a dummy PDF file content (just minimal valid PDF header so validation passes)
    dummy_pdf = b"%PDF-1.4\n%Dummy PDF for testing\n"
    files = {"file": ("resume.pdf", dummy_pdf, "application/pdf")}
    
    # Actually wait, the backend will pass this to the LLM. If it's a dummy PDF, PyMuPDF might fail or extract nothing.
    # If it extracts nothing, LLM returns empty, it takes 2 seconds.
    # To truly simulate CPU load, we need real text, but since we're just testing Event Loop blocking,
    # the LLM network call + basic embedding of empty string is enough to see if it blocks.
    
    res = await client.post(
        f"{BASE_URL}/students/upload-resume",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
        timeout=60.0
    )
    elapsed = time.time() - start
    print(f"[{name}] Upload finished in {elapsed:.2f}s | Status: {res.status_code}")
    return elapsed

async def create_job(client, token):
    print("[Recruiter] Starting job creation...")
    start = time.time()
    res = await client.post(
        f"{BASE_URL}/recruiters/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Software Engineer",
            "company": "Test Inc",
            "description": "A very long description for a software engineer. " * 20,
            "required_skills": ["Python", "FastAPI", "React"]
        },
        timeout=30.0
    )
    elapsed = time.time() - start
    print(f"[Recruiter] Job created in {elapsed:.2f}s | Status: {res.status_code}")
    return elapsed

async def event_loop_monitor(client, token, duration=10):
    """Pings the server every 0.5s to see if the event loop is blocked."""
    print("[Monitor] Starting event loop monitor...")
    max_latency = 0
    start = time.time()
    while time.time() - start < duration:
        t0 = time.time()
        try:
            # ping profile endpoint as a health check
            res = await client.get(
                f"{BASE_URL}/students/profile",
                headers={"Authorization": f"Bearer {token}"},
                timeout=2.0
            )
            latency = time.time() - t0
            max_latency = max(max_latency, latency)
        except Exception as e:
            max_latency = 999
        await asyncio.sleep(0.5)
    print(f"[Monitor] Max observed latency: {max_latency:.3f}s")
    return max_latency

async def run_stress_test():
    async with httpx.AsyncClient() as client:
        # Prepare tokens
        try:
            token_s1 = await register_user(client, "Student1", "s1@test.com", "student")
            token_s2 = await register_user(client, "Student2", "s2@test.com", "student")
            token_r1 = await register_user(client, "Recruiter1", "r1@test.com", "recruiter")
        except Exception as e:
            print(f"Failed to setup users. Is the server running? {e}")
            return

        print("\n--- Test 1: Single Upload ---")
        await asyncio.gather(
            upload_resume(client, token_s1, "Student1"),
            event_loop_monitor(client, token_s1, duration=5)
        )

        print("\n--- Test 2: Two Simultaneous Uploads ---")
        await asyncio.gather(
            upload_resume(client, token_s1, "Student1"),
            upload_resume(client, token_s2, "Student2"),
            event_loop_monitor(client, token_s1, duration=5)
        )

        print("\n--- Test 3: Upload while creating job ---")
        await asyncio.gather(
            upload_resume(client, token_s1, "Student1"),
            create_job(client, token_r1),
            event_loop_monitor(client, token_s1, duration=5)
        )

        print("\n--- Test 4: Upload while login ---")
        async def login_test():
            start = time.time()
            res = await client.post(f"{BASE_URL}/auth/login", json={"email": "s2@test.com", "password": "password123"})
            print(f"[LoginTest] Login took {time.time()-start:.2f}s")
            
        await asyncio.gather(
            upload_resume(client, token_s1, "Student1"),
            login_test(),
            event_loop_monitor(client, token_s1, duration=5)
        )

if __name__ == "__main__":
    asyncio.run(run_stress_test())
