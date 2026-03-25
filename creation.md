# Internship Connect Platform — FINAL Production Engineering Blueprint (v2)

## 📌 Objective

Build a **reliable, production-grade AI system** that:

* Matches students to internships using semantic understanding (NOT keywords)
* Evaluates real skills using GitHub activity + project intelligence
* Produces **explainable and recruiter-trustworthy rankings**
* Handles real-world constraints (rate limits, cold start, noisy data)

---

# 🚨 CORE ENGINEERING PRINCIPLES

* ✅ Modular Monolith (NO microservices)
* ✅ Deterministic scoring (NOT black-box AI)
* ✅ Minimal LLM usage (only for reasoning tasks)
* ✅ Cost-efficient + deployable
* ✅ Strong preprocessing (NO raw PDF embedding)
* ✅ Explainability first (every score justified)

---

# 🧱 SYSTEM ARCHITECTURE

```text
backend/
 ├── api/
 ├── core/
 ├── models/
 ├── schemas/
 ├── services/
 │    ├── resume_service.py
 │    ├── github_service.py
 │    ├── embedding_service.py
 │    ├── skill_service.py
 │    ├── matching_service.py
 ├── db/
 ├── utils/
 ├── main.py
```

---

# ⚙️ FINAL TECH STACK (LOCKED)

## Backend

* FastAPI
* SQLAlchemy
* Pydantic

## Database

* PostgreSQL
* pgvector

## Frontend

* React (Vite)
* Tailwind CSS

## AI

### Embeddings (CORE ENGINE)

```text
BAAI/bge-small-en-v1.5 (local)
```

### LLM (LIMITED + CONTROLLED USAGE)

```text
OpenAI GPT-4o-mini
```

Used ONLY for:

* Skill extraction + normalization
* GitHub summarization

---

## External APIs

* GitHub REST API v3

## Background Processing

* FastAPI BackgroundTasks

## Deployment

* Docker + Render/Railway

---

# 🗂 DATABASE DESIGN

## Enable pgvector

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Tables

### users

* id (UUID)
* name
* email
* role
* created_at

---

### student_profiles

* id
* user_id
* resume_text
* github_username
* cgpa
* branch
* created_at

---

### projects

* id
* student_id
* title
* description
* tech_stack (JSONB)
* embedding (VECTOR(384))
* embedding_model_version (TEXT)

---

### skills

* id
* student_id
* skill_name
* confidence_score
* level

---

### github_metrics

* id
* student_id
* commit_score
* repo_score
* oss_score
* activity_score
* diversity_score

---

### job_descriptions

* id
* recruiter_id
* title
* description
* embedding (VECTOR(384))
* created_at

---

### matches

* id
* student_id
* job_id
* semantic_score
* github_score
* skill_score
* final_score

---

# 🔍 CORE FEATURE 1: SEMANTIC SEARCH ENGINE

## ❗ RULE

NEVER embed raw PDF

---

## Pipeline

### Step 1: PDF Parsing (PyMuPDF)

```python
import fitz

def extract_text_from_pdf(pdf_bytes):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text("text")
        return text.strip()
    except Exception:
        return ""
```

If empty → mark profile for manual input

---

### Step 2: LLM Structured Parsing

Convert raw text → structured JSON:

```json
{
  "skills": [],
  "projects": [],
  "experience": []
}
```

---

### Step 3: Construct Embedding Text

```python
student_text = f"""
Skills: {skills}
Projects: {projects}
Experience: {experience}
GitHub: {github_summary}
"""
```

---

### Step 4: Generate Embedding

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")
embedding = model.encode(student_text)
```

---

### Step 5: Store (IMPORTANT)

* Store embeddings per project
* Store model version

---

### Step 6: Job Matching Query

```sql
SELECT *, 1 - (embedding <=> :job_embedding) AS score
FROM projects
ORDER BY embedding <=> :job_embedding
LIMIT 20;
```

---

# 🧠 CORE FEATURE 2: GITHUB INTELLIGENCE ENGINE

## API Rate Limit Problem

* GitHub limit: 5000 requests/hour

---

## REQUIRED SOLUTION

### 1. HTTP Client + Cache

```text
httpx + hishel caching (24h TTL)
```

---

### 2. Fetch Strategy

* Fetch only top 10–15 repos
* Avoid full repo traversal

---

### 3. Service Flow

```text
Request → Cache check → Hit? return
                     ↓
                  Miss → GitHub API → Store → Return
```

---

## Data Extracted

* Repos
* Languages
* Stars / forks
* Commits
* PRs
* Last activity

---

## Derived Metrics

### Commit Consistency

* commits/week

### Repo Quality

* stars + forks + README

### Tech Diversity

* unique tech stack

### OSS Score

* PRs merged

### Recency

* last activity

---

## Final GitHub Score

```text
GitHub Score =
0.30 × Commit Consistency
+ 0.25 × Repo Quality
+ 0.20 × OSS Contribution
+ 0.15 × Tech Diversity
+ 0.10 × Recency
```

---

## GitHub Summarization (LLM)

Convert repos → clean summary:

```text
"This student has built and deployed ML models using FastAPI and Docker..."
```

---

# 🧠 CORE FEATURE 3: SKILL CONFIDENCE SYSTEM

## LLM Role

* Normalize skill names
* Extract context-aware skills

---

## Example

```text
"ReactJS", "React.js" → React
"Learning Python" ≠ "Production Python"
```

---

## Confidence Formula

```text
Skill Confidence =
0.40 × GitHub Evidence
+ 0.30 × Project Relevance
+ 0.20 × Optional Test
+ 0.10 × Recency
```

---

## Output

```text
Python: 90% (Advanced)
React: 75% (Intermediate)
Docker: 65% (Working)
```

---

# 🧮 MATCHING & RANKING ENGINE

## Inputs

* Semantic score
* GitHub score
* Skill score
* CGPA

---

## Default Formula

```text
Final Score =
0.50 × Semantic
+ 0.25 × GitHub
+ 0.20 × Skill
+ 0.05 × CGPA
```

---

## Cold Start Handling (MANDATORY)

If no GitHub:

```text
Final Score =
0.70 × Semantic
+ 0.25 × Skill
+ 0.05 × CGPA
```

---

## Flow

1. Retrieve top semantic matches
2. Compute scores
3. Rank candidates
4. Store results

---

# 📊 EXPLAINABILITY (CRITICAL FEATURE)

Every match must include:

```text
Matched because:
- Built REST APIs using FastAPI
- Experience with Docker
- Active GitHub contributions
```

---

## Also Return:

* semantic_score
* github_score
* skill_score

---

## Highlight Best Project

Show:

```text
"Top Matching Project: AI Resume Analyzer"
```

---

# 👨‍🎓 STUDENT DASHBOARD

* Upload resume
* Connect GitHub
* View:

  * Skill confidence
  * Match results
  * Weak areas

---

# 🏢 RECRUITER DASHBOARD

* Post job
* View ranked candidates
* Filters:

  * Skills
  * CGPA
  * Branch

---

# 🔄 FINAL DATA PIPELINE

```text
PDF Upload
→ PyMuPDF Extraction
→ LLM Structuring
→ GitHub Fetch (cached)
→ GitHub Summary (LLM)
→ Skill Scoring
→ Embedding Generation
→ Store in pgvector
→ Matching Engine
```

---

# 🔐 RELIABILITY REQUIREMENTS

* ❌ No raw PDF embeddings
* ✅ GitHub caching mandatory
* ✅ Background processing for heavy tasks
* ✅ Async APIs
* ✅ Logging + error handling

---

# 🚀 MVP SCOPE (STRICT)

Build ONLY:

* Resume parsing (PyMuPDF + LLM)
* GitHub integration (with caching)
* Skill confidence scoring
* pgvector semantic search
* Matching engine
* Recruiter dashboard

---

# ❌ DO NOT BUILD

* Microservices
* Kafka / Redis clusters
* Complex infra
* Overuse of LLM

---

# 🏁 SUCCESS CRITERIA

* Recruiter can shortlist candidates in < 2 minutes
* Matching works beyond keywords
* GitHub scoring is meaningful
* System handles missing GitHub gracefully
* Results are explainable

---

# 🎯 FINAL INSTRUCTION TO AI AGENT

Focus on:

* Clean modular backend
* Strong preprocessing pipeline
* Efficient vector queries
* Deterministic scoring
* Minimal AI usage

Avoid:

* Black-box logic
* Overengineering
* External dependency overload

---

# 🚀 FINAL OUTCOME

A system that:

* Evaluates real developer ability
* Reduces recruiter workload drastically
* Provides transparent and intelligent matching
* Is deployable, scalable, and trustworthy

---
