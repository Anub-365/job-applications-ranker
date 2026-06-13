"""
Simulate a padded resume vs a generic web dev GitHub profile.
"""
from fpdf import FPDF
import asyncio
import httpx
import time

BASE = "http://localhost:8000/api"

def clean(s):
    return (s.replace('\u2014', '--').replace('\u2013', '-')
             .replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
             .replace('&', 'and'))

def make_padded_resume(filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Fake AI Expert', ln=1, align='C')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, 'Email: fakeai@example.com  |  GitHub: github.com/rahulverma-web', ln=1, align='C')
    pdf.ln(4)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Professional Summary', ln=1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, 'Expert AI Engineer with 5 years experience building LLMs and scalable ML infrastructure.')
    pdf.ln(3)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Technical Skills', ln=1)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 6, 'ML/Cloud:', ln=0)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, 'AWS, Kubernetes, PyTorch, TensorFlow, LLM Engineering, MLOps, OpenAI API')
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Key Projects', ln=1)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, 'Enterprise LLM Chatbot', ln=1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, 'Built a custom GPT-4 chatbot using LangChain and PyTorch. Deployed on AWS EKS (Kubernetes).')
    pdf.set_font('Arial', 'I', 9)
    pdf.cell(0, 6, 'Technologies: Python, PyTorch, AWS, Kubernetes, LLM', ln=1)
    pdf.output(filename)

async def main():
    make_padded_resume("padded_resume.pdf")
    
    async with httpx.AsyncClient(timeout=120) as client:
        # Register Student
        import uuid
        email = f"fake.ai.{uuid.uuid4().hex[:6]}@example.com"
        r = await client.post(f"{BASE}/auth/register", json={
            "name": "Fake AI Expert", "email": email, "password": "password123", "role": "student"
        })
        print("Reg:", r.text)
        
        # Login
        r = await client.post(f"{BASE}/auth/login", json={"email": email, "password": "password123"})
        if "access_token" not in r.json():
            print(f"Login failed: {r.text}")
            return
        token = r.json()["access_token"]
        
        # Upload
        print("Uploading padded resume...")
        with open("padded_resume.pdf", "rb") as f:
            r = await client.post(
                f"{BASE}/students/upload-resume",
                files={"file": ("padded_resume.pdf", f, "application/pdf")},
                headers={"Authorization": f"Bearer {token}"}
            )
        data = r.json()
        print(f"Skills Found: {data.get('skills_found')}")
        for sk in data.get("all_skills", []):
            if sk["confidence_score"] >= 20:
                print(f"  • {sk['skill_name']} ({sk['level']}): {sk['confidence_score']}%")
        
        # GitHub Connect (Web dev profile)
        print("\nConnecting Web Dev GitHub (rahulverma-web)...")
        await client.put(f"{BASE}/students/profile", json={"github_username": "rahulverma-web"}, headers={"Authorization": f"Bearer {token}"})
        r = await client.post(f"{BASE}/students/connect-github", headers={"Authorization": f"Bearer {token}"})
        gdata = r.json()
        print(f"GitHub Total Score: {gdata['scores']['total_score']}/100")
        print(f"GitHub Summary: {gdata['summary']}")
        
        # Recruiter
        email_r = f"rec.{uuid.uuid4().hex[:6]}@example.com"
        r = await client.post(f"{BASE}/auth/register", json={"name": "Rec", "email": email_r, "password": "password123", "role": "recruiter"})
        r = await client.post(f"{BASE}/auth/login", json={"email": email_r, "password": "password123"})
        token_r = r.json()["access_token"]
        
        print("\nCreating Job...")
        r = await client.post(f"{BASE}/recruiters/jobs", json={
            "title": "MLOps Engineer", "description": "Need AWS, Kubernetes, PyTorch.", "required_skills": ["AWS", "Kubernetes", "PyTorch", "MLOps", "LLM Engineering"]
        }, headers={"Authorization": f"Bearer {token_r}"})
        job_id = r.json()["id"]
        
        print("\nFetching Matches...")
        r = await client.get(f"{BASE}/recruiters/jobs/{job_id}/candidates", headers={"Authorization": f"Bearer {token_r}"})
        candidates = r.json()
        for c in candidates:
            if c["student_name"] == "Fake AI Expert":
                match = c["match"]
                print(f"\nRANKING RESULT:")
                print(f"Final Score: {match['final_score']}")
                print(f"Skill Score: {match['skill_score']}")
                print(f"GitHub Score: {match['github_score']}")
                print(f"Explanation:\n{match['explanation']}")

if __name__ == "__main__":
    asyncio.run(main())
