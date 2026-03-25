from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


# ── Auth ──────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)
    role: str = Field(..., pattern="^(student|recruiter)$")


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    name: str


class UserOut(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Student ───────────────────────────────────────────

class StudentProfileUpdate(BaseModel):
    github_username: Optional[str] = None
    cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    branch: Optional[str] = None


class ProjectOut(BaseModel):
    id: UUID
    title: str
    description: str
    tech_stack: list

    model_config = {"from_attributes": True}


class SkillOut(BaseModel):
    id: UUID
    skill_name: str
    confidence_score: float
    level: str

    model_config = {"from_attributes": True}


class GithubMetricsOut(BaseModel):
    commit_score: float
    repo_score: float
    oss_score: float
    activity_score: float
    diversity_score: float
    total_score: float
    summary: str

    model_config = {"from_attributes": True}


class StudentProfileOut(BaseModel):
    id: UUID
    user_id: UUID
    resume_text: str
    github_username: str
    cgpa: float
    branch: str
    processing_status: str
    projects: List[ProjectOut] = []
    skills: List[SkillOut] = []
    github_metrics: Optional[GithubMetricsOut] = None

    model_config = {"from_attributes": True}


# ── Recruiter / Jobs ─────────────────────────────────

class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    company: str = Field("", max_length=255)
    description: str = Field(..., min_length=10)
    required_skills: List[str] = []


class JobOut(BaseModel):
    id: UUID
    recruiter_id: UUID
    title: str
    company: str
    description: str
    required_skills: list
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Matches ───────────────────────────────────────────

class MatchOut(BaseModel):
    id: UUID
    student_id: UUID
    job_id: UUID
    semantic_score: float
    github_score: float
    skill_score: float
    cgpa_score: float
    final_score: float
    explanation: str
    top_project_title: str

    model_config = {"from_attributes": True}


class CandidateOut(BaseModel):
    """Enriched match result shown to recruiters."""
    match: MatchOut
    student_name: str
    student_email: str
    github_username: str
    branch: str
    cgpa: float
    skills: List[SkillOut] = []
    top_projects: List[ProjectOut] = []
