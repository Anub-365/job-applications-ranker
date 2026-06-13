"""Resume parsing service — PDF extraction + LLM structuring + fallback skill mining."""
import re
import fitz  # PyMuPDF
import json
import logging
import google.generativeai as genai
from openai import AsyncOpenAI

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# OpenAI Client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

# Groq Clients (OpenAI-compatible)
groq_keys = [settings.GROQ_API_KEY_1, settings.GROQ_API_KEY_2, settings.GROQ_API_KEY_3]
groq_clients = [
    AsyncOpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
    for key in groq_keys if key
]

# Gemini Config
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

# ---------------------------------------------------------------------------
# Synonym Normalization Map
# ---------------------------------------------------------------------------
SYNONYM_MAP = {
    "js": "JavaScript", "javascript": "JavaScript", "node.js": "Node.js",
    "nodejs": "Node.js", "ts": "TypeScript", "typescript": "TypeScript",
    "py": "Python", "python3": "Python", "python 3": "Python",
    "c++": "C++", "cpp": "C++", "c#": "C#", "csharp": "C#",
    "reactjs": "React", "react.js": "React", "react js": "React",
    "nextjs": "Next.js", "next.js": "Next.js",
    "vuejs": "Vue.js", "vue.js": "Vue.js",
    "angularjs": "Angular", "angular.js": "Angular",
    "expressjs": "Express.js", "express.js": "Express.js",
    "ml": "Machine Learning", "dl": "Deep Learning",
    "ai": "Artificial Intelligence",
    "nlp": "Natural Language Processing",
    "cv": "Computer Vision",
    "sql": "SQL", "nosql": "NoSQL",
    "mongo": "MongoDB", "mongodb": "MongoDB",
    "postgres": "PostgreSQL", "postgresql": "PostgreSQL", "psql": "PostgreSQL",
    "mysql": "MySQL",
    "aws": "AWS", "gcp": "Google Cloud", "azure": "Azure",
    "k8s": "Kubernetes", "kubernetes": "Kubernetes",
    "docker": "Docker", "tf": "TensorFlow", "tensorflow": "TensorFlow",
    "pytorch": "PyTorch", "torch": "PyTorch",
    "sklearn": "Scikit-Learn", "scikit-learn": "Scikit-Learn",
    "flask": "Flask", "fastapi": "FastAPI", "django": "Django",
    "html5": "HTML", "css3": "CSS",
    "tailwind": "Tailwind CSS", "tailwindcss": "Tailwind CSS",
    "bootstrap": "Bootstrap",
    "git": "Git", "github": "GitHub",
    "ci/cd": "CI/CD", "cicd": "CI/CD",
    "rest": "REST API", "restful": "REST API", "graphql": "GraphQL",
    "redis": "Redis", "kafka": "Kafka",
    "figma": "Figma", "jira": "Jira",
    "webrtc": "WebRTC", "websocket": "WebSocket",
    "pandas": "Pandas", "numpy": "NumPy", "matplotlib": "Matplotlib",
    "opencv": "OpenCV",
    "linux": "Linux", "bash": "Bash",
    "swift": "Swift", "kotlin": "Kotlin", "flutter": "Flutter", "dart": "Dart",
    "r": "R", "matlab": "MATLAB", "scala": "Scala", "rust": "Rust", "go": "Go",
    "golang": "Go", "java": "Java", "ruby": "Ruby",
}

# ---------------------------------------------------------------------------
# Fallback Skill Miner — regex-based tech keyword extraction
# ---------------------------------------------------------------------------
TECH_KEYWORDS = {
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
    "Ruby", "Swift", "Kotlin", "Dart", "Scala", "R", "MATLAB", "PHP", "Perl",
    "React", "Angular", "Vue.js", "Next.js", "Node.js", "Express.js",
    "Django", "Flask", "FastAPI", "Spring Boot", "Rails",
    "HTML", "CSS", "Tailwind CSS", "Bootstrap", "SASS",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kafka", "Elasticsearch",
    "Docker", "Kubernetes", "AWS", "Azure", "Google Cloud", "Terraform",
    "Git", "CI/CD", "Jenkins", "GitHub Actions",
    "TensorFlow", "PyTorch", "Scikit-Learn", "Pandas", "NumPy", "OpenCV",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "REST API", "GraphQL", "WebSocket", "WebRTC",
    "Linux", "Bash", "Nginx", "Apache",
    "Flutter", "React Native", "Figma", "Jira",
    "Selenium", "Cypress", "Jest", "Pytest",
    "Firebase", "Supabase", "Netlify", "Vercel",
    "Solidity", "Blockchain", "Ethereum",
    "Power BI", "Tableau", "Excel",
}


def _fallback_skill_mine(text: str) -> list:
    """Regex-based secondary scan against TECH_KEYWORDS when LLM returns empty skills."""
    text_lower = text.lower()
    found = []
    for kw in TECH_KEYWORDS:
        # Use word boundary match for short keywords to avoid false positives
        pattern = r'\b' + re.escape(kw.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.append(kw)
    return sorted(set(found))


def _normalize_synonyms(skills: list) -> list:
    """Apply synonym map to normalize skill names."""
    normalized = []
    seen = set()
    for skill in skills:
        mapped = SYNONYM_MAP.get(skill.lower().strip(), skill.strip())
        if mapped.lower() not in seen:
            seen.add(mapped.lower())
            normalized.append(mapped)
    return normalized


# ---------------------------------------------------------------------------
# High-Density Entity Recognition Prompt
# ---------------------------------------------------------------------------
STRUCTURING_PROMPT = """
You are an expert technical recruiter performing High-Density Entity Recognition on a resume.

MANDATORY RULES:
1. SCAN THE ENTIRE TEXT — do NOT stop after the first section.
2. SKILL EXTRACTION — Extract EVERY technical tool, programming language, framework,
   library, platform, and methodology mentioned ANYWHERE:
   - From explicit "Skills" sections
   - From project titles and descriptions (e.g., "Built a React dashboard" → React)
   - From technology tags and bullet points
   - From "Competitive Programming" or "Achievements" sections (e.g., "C++ on Codeforces" → C++)
   - From work experience descriptions
3. PROJECT EXTRACTION — For EACH project, extract the title, a 1-2 sentence description,
   and the specific tech_stack used.
4. NORMALIZATION — Convert abbreviations: "JS" → "JavaScript", "py" → "Python",
   "ML" → "Machine Learning", "k8s" → "Kubernetes".
5. If you find NO skills, return skills: [] — a secondary system will handle it.

Return ONLY valid JSON:
{
  "skills": ["Python", "FastAPI", "React", "Docker", ...],
  "projects": [{"title": "...", "description": "...", "tech_stack": ["...", "..."]}],
  "experience": [{"role": "...", "company": "...", "description": "..."}],
  "education": {"degree": "...", "branch": "...", "cgpa": 0.0}
}
"""


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text("text")
        doc.close()
        return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""


async def structure_resume_text(raw_text: str) -> dict:
    """Use LLM to convert raw resume text into structured JSON."""
    # Try OpenAI first
    if openai_client:
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": STRUCTURING_PROMPT},
                    {"role": "user", "content": raw_text[:8000]},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
            return {"success": True, "data": result, "llm": "OpenAI"}
        except Exception as e:
            error_msg = str(e)
            is_quota = "insufficient_quota" in error_msg or "quota_exceeded" in error_msg
            if not is_quota:
                logger.error(f"OpenAI error (not quota): {error_msg}")
            else:
                logger.info("OpenAI quota reached, attempting Groq fallback...")

    # Groq Fallback (Primary Fallback)
    for i, g_client in enumerate(groq_clients):
        try:
            response = await g_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": STRUCTURING_PROMPT},
                    {"role": "user", "content": raw_text[:8000]},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
            return {"success": True, "data": result, "llm": f"Groq (Key {i+1})"}
        except Exception as e:
            logger.warning(f"Groq fallback failed with Key {i+1}: {e}")
            if i == len(groq_clients) - 1:
                logger.info("All Groq keys exhausted, attempting Gemini fallback...")

    # Gemini Fallback (Secondary Fallback)
    if settings.GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            full_prompt = f"{STRUCTURING_PROMPT}\n\nResume Text:\n{raw_text[:8000]}"
            response = await model.generate_content_async(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )
            result = json.loads(response.text)
            return {"success": True, "data": result, "llm": "Gemini"}
        except Exception as e:
            logger.error(f"Gemini fallback failed: {e}")
            return {"success": False, "error": "All AI services (OpenAI, Groq, Gemini) exhausted", "is_quota": True}

    return {"success": False, "error": "All AI services (OpenAI, Groq) exhausted", "is_quota": True}


def _basic_structure(raw_text: str) -> dict:
    """Fallback: return raw text wrapped in minimal structure."""
    return {
        "skills": [],
        "projects": [{"title": "Resume Content", "description": raw_text[:2000], "tech_stack": []}],
        "experience": [],
        "education": {},
    }


async def process_resume(pdf_bytes: bytes) -> dict:
    """Full pipeline: PDF → text → structured JSON → synonym normalization → fallback mining."""
    raw_text = extract_text_from_pdf(pdf_bytes)
    if not raw_text:
        return {"raw_text": "", "structured": _basic_structure(""), "error": "Could not extract text from PDF"}

    structured_res = await structure_resume_text(raw_text)
    if not structured_res.get("success"):
        return {
            "raw_text": raw_text, 
            "structured": _basic_structure(raw_text), 
            "error": structured_res.get("error"),
            "is_quota": structured_res.get("is_quota", False),
            "llm": "None (Fallback)"
        }

    data = structured_res["data"]

    # Step 1: Normalize synonyms in extracted skills
    raw_skills = data.get("skills", [])
    data["skills"] = _normalize_synonyms(raw_skills)

    # Step 2: Also normalize tech_stack in each project
    for proj in data.get("projects", []):
        proj["tech_stack"] = _normalize_synonyms(proj.get("tech_stack", []))

    # Step 3: Fallback Skill Miner — if LLM returned empty skills, mine from raw text
    if not data["skills"]:
        logger.info("LLM returned empty skills — triggering Fallback Skill Miner...")
        mined = _fallback_skill_mine(raw_text)
        data["skills"] = mined
        logger.info(f"Fallback Skill Miner found {len(mined)} skills: {mined}")

    return {
        "raw_text": raw_text, 
        "structured": data, 
        "error": None,
        "llm": structured_res["llm"]
    }
