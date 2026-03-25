"""Embedding service — local BAAI/bge-small-en-v1.5 model."""
import logging
from typing import List
from sentence_transformers import SentenceTransformer

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Load model once at module level
_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully")
    return _model


def generate_embedding(text: str) -> List[float]:
    """Generate a 384-dim embedding vector from text."""
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def construct_student_text(structured: dict, github_summary: str = "") -> str:
    """Build the embedding input text from structured resume + GitHub data."""
    parts = []

    # Skills
    skills = structured.get("skills", [])
    if skills:
        parts.append(f"Skills: {', '.join(skills)}")

    # Projects
    projects = structured.get("projects", [])
    for proj in projects[:5]:  # Limit to top 5
        title = proj.get("title", "")
        desc = proj.get("description", "")
        tech = ", ".join(proj.get("tech_stack", []))
        parts.append(f"Project: {title}. {desc}. Technologies: {tech}")

    # Experience
    experience = structured.get("experience", [])
    for exp in experience[:3]:  # Limit to top 3
        role = exp.get("role", "")
        company = exp.get("company", "")
        desc = exp.get("description", "")
        parts.append(f"Experience: {role} at {company}. {desc}")

    # GitHub summary
    if github_summary:
        parts.append(f"GitHub: {github_summary}")

    return "\n".join(parts) if parts else "No profile data available"


def construct_job_text(title: str, description: str, required_skills: list = None) -> str:
    """Build the embedding input text from job description."""
    parts = [f"Job: {title}", f"Description: {description}"]
    if required_skills:
        parts.append(f"Required Skills: {', '.join(required_skills)}")
    return "\n".join(parts)
