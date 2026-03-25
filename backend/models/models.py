import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import enum

from backend.db.database import Base


class UserRole(str, enum.Enum):
    STUDENT = "student"
    RECRUITER = "recruiter"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    job_descriptions = relationship("JobDescription", back_populates="recruiter")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    resume_text = Column(Text, default="")
    resume_structured = Column(JSONB, default=dict)
    github_username = Column(String(255), default="")
    cgpa = Column(Float, default=0.0)
    branch = Column(String(255), default="")
    processing_status = Column(String(50), default="idle")  # idle | processing | done | error
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="student_profile")
    projects = relationship("Project", back_populates="student", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="student", cascade="all, delete-orphan")
    github_metrics = relationship("GithubMetrics", back_populates="student", uselist=False, cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="student", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    tech_stack = Column(JSONB, default=list)
    embedding = Column(Vector(384))
    embedding_model_version = Column(String(100), default="BAAI/bge-small-en-v1.5")

    # Relationships
    student = relationship("StudentProfile", back_populates="projects")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id"), nullable=False)
    skill_name = Column(String(255), nullable=False)
    confidence_score = Column(Float, default=0.0)
    level = Column(String(50), default="Beginner")  # Beginner | Working | Intermediate | Advanced | Expert

    # Relationships
    student = relationship("StudentProfile", back_populates="skills")


class GithubMetrics(Base):
    __tablename__ = "github_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id"), unique=True, nullable=False)
    commit_score = Column(Float, default=0.0)
    repo_score = Column(Float, default=0.0)
    oss_score = Column(Float, default=0.0)
    activity_score = Column(Float, default=0.0)
    diversity_score = Column(Float, default=0.0)
    total_score = Column(Float, default=0.0)
    summary = Column(Text, default="")
    raw_data = Column(JSONB, default=dict)

    # Relationships
    student = relationship("StudentProfile", back_populates="github_metrics")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    company = Column(String(255), default="")
    description = Column(Text, nullable=False)
    required_skills = Column(JSONB, default=list)
    embedding = Column(Vector(384))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recruiter = relationship("User", back_populates="job_descriptions")
    matches = relationship("Match", back_populates="job", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False)
    semantic_score = Column(Float, default=0.0)
    github_score = Column(Float, default=0.0)
    skill_score = Column(Float, default=0.0)
    cgpa_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0)
    explanation = Column(Text, default="")
    top_project_title = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("StudentProfile", back_populates="matches")
    job = relationship("JobDescription", back_populates="matches")
