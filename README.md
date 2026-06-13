<div align="center">

# 🎯 Internship Connect Platform

**AI-Powered Student–Internship Matching using Semantic Search, GitHub Intelligence & Skill Triangulation**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![pgvector](https://img.shields.io/badge/pgvector-Vector_Search-blue)](https://github.com/pgvector/pgvector)

</div>

---

## 📋 Table of Contents

- [What Is This?](#-what-is-this)
- [How It Works](#-how-it-works)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Setup Guide](#-setup-guide)
  - [1. Clone the Repo](#1-clone-the-repo)
  - [2. PostgreSQL + pgvector](#2-postgresql--pgvector-setup)
  - [3. Backend Setup](#3-backend-setup)
  - [4. Frontend Setup](#4-frontend-setup)
  - [5. API Keys](#5-api-key-setup)
  - [6. Run the App](#6-run-the-app)
- [API Reference](#-api-reference)
- [Architecture Deep Dive](#-architecture-deep-dive)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🧠 What Is This?

Internship Connect is a full-stack platform that **semantically matches students to internship postings** using AI. Instead of keyword-based filtering, it uses **384-dimensional vector embeddings** to understand what a student's projects *actually do* and how they relate to a job's requirements.

**For Students:**
- Upload your resume (PDF) → AI extracts skills, projects, and experience
- Connect your GitHub → platform analyzes your code quality and activity
- Get automatically ranked for relevant internships

**For Recruiters:**
- Post a job description → AI instantly ranks all students
- See verified vs. self-reported skills (anti-resume-padding)
- Filter candidates by score, branch, or specific skills

---

## ⚙️ How It Works

```
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   Student    │────▶│   Resume Pipeline    │────▶│   Vector Embeddings │
│  Uploads PDF │     │  (PyMuPDF + LLM)     │     │  (BAAI/bge-small)   │
└─────────────┘     └──────────────────────┘     └─────────┬───────────┘
                                                           │
┌─────────────┐     ┌──────────────────────┐               │
│   Student    │────▶│  GitHub Intelligence │               │
│ Connects GH  │     │  (API + Scoring)     │               │
└─────────────┘     └──────────────────────┘               │
                                                           ▼
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  Recruiter   │────▶│  Job Embedding       │────▶│  pgvector Cosine    │
│  Posts Job   │     │  (BAAI/bge-small)    │     │  Similarity Search  │
└─────────────┘     └──────────────────────┘     └─────────┬───────────┘
                                                           │
                                                           ▼
                                                 ┌─────────────────────┐
                                                 │  Final Ranking      │
                                                 │  Semantic (50%)     │
                                                 │  GitHub   (25%)     │
                                                 │  Skills   (20%)     │
                                                 │  CGPA     (5%)      │
                                                 └─────────────────────┘
```

### Ranking Formula

| Mode | Formula |
|------|---------|
| **Standard** | `0.50 × Semantic + 0.25 × GitHub + 0.20 × Skills + 0.05 × CGPA` |
| **Cold Start** (no GitHub) | `0.70 × Semantic + 0.25 × Skills + 0.05 × CGPA` |

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | FastAPI + Python 3.10+ | Async REST API |
| **Database** | PostgreSQL 15+ + pgvector | Relational + vector similarity search |
| **ORM** | SQLAlchemy (async) | Database operations |
| **Embeddings** | `BAAI/bge-small-en-v1.5` (sentence-transformers) | 384-dim local embeddings |
| **LLM (Primary)** | OpenAI `gpt-4o-mini` | Resume parsing & skill extraction |
| **LLM (Fallback 1)** | Groq `llama-3.3-70b-versatile` | Fast fallback when OpenAI quota hits |
| **LLM (Fallback 2)** | Google Gemini `gemini-1.5-flash` | Secondary fallback |
| **Frontend** | React 18 + Vite | SPA with Tailwind CSS |
| **Auth** | JWT + bcrypt | Stateless authentication |

---

## 📁 Project Structure

```
.
├── .env.example                 # ← Copy to .env and fill in your keys
├── .gitignore
├── README.md
│
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── requirements.txt         # Python dependencies
│   │
│   ├── api/                     # Route handlers
│   │   ├── auth.py              #   POST /register, /login
│   │   ├── students.py          #   GET/PUT /profile, POST /upload-resume, /connect-github
│   │   └── recruiters.py        #   CRUD /jobs, GET /candidates, POST /rematch
│   │
│   ├── core/                    # App configuration
│   │   ├── config.py            #   Pydantic settings (reads .env)
│   │   └── security.py          #   JWT + bcrypt utilities
│   │
│   ├── db/                      # Database layer
│   │   └── database.py          #   SQLAlchemy async engine + session
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   └── models.py            #   User, StudentProfile, Project, Skill, Match, etc.
│   │
│   ├── schemas/                 # Pydantic request/response schemas
│   │   └── schemas.py           #   All API schemas
│   │
│   ├── services/                # Business logic
│   │   ├── embedding_service.py #   Local BAAI/bge-small model
│   │   ├── github_service.py    #   GitHub API + scoring engine
│   │   ├── matching_service.py  #   Semantic search + final ranking
│   │   ├── resume_service.py    #   PDF extraction + LLM structuring
│   │   └── skill_service.py     #   Triangulation scoring model
│   │
│   ├── tests/                   # Test suite
│   │   └── test_semantic_audit.py
│   │
│   └── utils/                   # Shared utilities
│       └── __init__.py
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js            # Vite + API proxy config
    ├── tailwind.config.js
    └── src/
        ├── main.jsx              # React entry point
        ├── App.jsx               # Router + protected routes
        ├── AuthContext.jsx        # Auth state management
        ├── api.js                # Axios client + interceptors
        ├── index.css             # Global styles
        ├── components/
        │   └── Navbar.jsx
        └── pages/
            ├── Landing.jsx
            ├── Login.jsx
            ├── Register.jsx
            ├── StudentDashboard.jsx
            └── RecruiterDashboard.jsx
```

---

## 📦 Prerequisites

Before you start, make sure you have these installed:

| Tool | Version | Download |
|------|---------|----------|
| **Python** | 3.10 or higher | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18 or higher | [nodejs.org](https://nodejs.org/) |
| **PostgreSQL** | 15 or higher | [postgresql.org](https://www.postgresql.org/download/) |
| **Git** | Any recent version | [git-scm.com](https://git-scm.com/) |

---

## 🚀 Setup Guide

### 1. Clone the Repo

```bash
git clone https://github.com/Thunder07-blip/job-applications-ranker.git
cd job-applications-ranker
```

### 2. PostgreSQL + pgvector Setup

You need PostgreSQL running with the **pgvector** extension installed.

#### Option A: Install pgvector on existing PostgreSQL (Windows)

1. Download the pgvector installer for your PostgreSQL version from [pgvector releases](https://github.com/pgvector/pgvector/releases)
2. Or build from source:
   ```bash
   # In a Visual Studio Developer Command Prompt:
   git clone https://github.com/pgvector/pgvector.git
   cd pgvector
   nmake /F Makefile.win install
   ```

#### Option B: Install pgvector on Linux/macOS

```bash
# Ubuntu/Debian
sudo apt install postgresql-15-pgvector

# macOS (Homebrew)
brew install pgvector
```

#### Create the Database

Open a PostgreSQL shell (`psql`) and run:

```sql
-- Create the database
CREATE DATABASE internship_connect;

-- Connect to it
\c internship_connect

-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

> **Note:** The app will also run `CREATE EXTENSION IF NOT EXISTS vector` on startup, but it's good to verify it works manually first.

### 3. Backend Setup

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies (includes PyTorch CPU for embeddings)
pip install -r backend/requirements.txt
```

> **⏱ First install will take a few minutes** — it downloads PyTorch (CPU) and sentence-transformers.

### 4. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### 5. API Key Setup

Copy the example environment file and fill in your keys:

```bash
# Windows:
copy .env.example .env

# macOS/Linux:
cp .env.example .env
```

Now open `.env` and configure each key:

#### 🔑 Database URL

```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/internship_connect
```

Replace `YOUR_PASSWORD` with your PostgreSQL password.

#### 🔑 Secret Key

Generate a secure random key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Paste the output as your `SECRET_KEY`.

#### 🔑 OpenAI API Key (Primary LLM)

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click **"Create new secret key"**
3. Copy the key (starts with `sk-`)
4. Add credits to your account if needed ($5 minimum)

```env
OPENAI_API_KEY=sk-proj-...
```

#### 🔑 GitHub Personal Access Token

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Select scope: **`public_repo`** (read-only access to public repos)
4. Click **Generate token** and copy it

```env
GITHUB_TOKEN=ghp_...
```

#### 🔑 Groq API Keys (Fallback LLM — Free Tier Available)

1. Go to [console.groq.com/keys](https://console.groq.com/keys)
2. Sign up (free) and create API keys
3. Create up to 3 keys for automatic rotation on rate limits

```env
GROQ_API_KEY_1=gsk_...
GROQ_API_KEY_2=gsk_...
GROQ_API_KEY_3=gsk_...
```

#### 🔑 Google Gemini API Key (Secondary Fallback — Free Tier Available)

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **"Create API Key"**
3. Copy the key

```env
GEMINI_API_KEY=AIza...
```

> **💡 Tip:** At minimum, you need **one** LLM key (Groq is free and fastest). The system auto-falls back: OpenAI → Groq → Gemini.

### 6. Run the App

You need **two terminals** — one for the backend, one for the frontend.

**Terminal 1 — Backend:**

```bash
# Make sure your venv is activated
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

> On first run, the embedding model (`BAAI/bge-small-en-v1.5`, ~130MB) will be downloaded automatically.

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

**Open your browser:**

| Service | URL |
|---------|-----|
| Frontend | [http://localhost:3000](http://localhost:3000) |
| Backend API | [http://localhost:8000](http://localhost:8000) |
| API Docs (Swagger) | [http://localhost:8000/docs](http://localhost:8000/docs) |

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Register a new student or recruiter |
| `POST` | `/api/auth/login` | Login and receive JWT token |

### Student Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/students/profile` | Get your profile with skills, projects, GitHub metrics |
| `PUT` | `/api/students/profile` | Update profile (GitHub username, CGPA, branch) |
| `POST` | `/api/students/upload-resume` | Upload PDF resume → AI parses and creates embeddings |
| `POST` | `/api/students/connect-github` | Analyze GitHub profile and compute scores |
| `GET` | `/api/students/matches` | View your match scores across all jobs |

### Recruiter Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/recruiters/jobs` | Post a new job → auto-runs semantic matching |
| `GET` | `/api/recruiters/jobs` | List all your posted jobs |
| `GET` | `/api/recruiters/jobs/{id}` | Get a specific job |
| `GET` | `/api/recruiters/jobs/{id}/candidates` | Get ranked candidates (filterable by score, branch, skill) |
| `POST` | `/api/recruiters/jobs/{id}/rematch` | Re-run matching (e.g., after new students register) |

> All endpoints except `/register` and `/login` require a Bearer token in the `Authorization` header.

---

## 🔬 Architecture Deep Dive

<details>
<summary><b>📄 Resume Pipeline (Click to expand)</b></summary>

The pipeline uses **PyMuPDF** to extract text from uploaded PDFs and feeds it into a multi-provider LLM tiering strategy.

**High-Density Entity Recognition Prompt:** Instead of just looking for a "Skills" section, the LLM scans the *entire* document — including Projects, Work Experience, and Achievements — to extract every named technology, framework, language, and tool.

**Safeguards:**
1. **Multi-Provider Fallback:** OpenAI → Groq (`llama-3.3-70b`) → Gemini (`gemini-1.5-flash`)
2. **Synonym Normalization:** A dictionary normalizes extracted names (`"ReactJS"` → `"React"`, `"js"` → `"JavaScript"`)
3. **Regex Fallback Miner:** If the LLM extracts 0 skills, a secondary miner scans against 100+ proven engineering keywords

</details>

<details>
<summary><b>🐙 GitHub Intelligence Engine (Click to expand)</b></summary>

When a student connects their GitHub, the backend pulls up to **100 repositories** and computes a weighted score:

| Sub-Score | Weight | What It Measures |
|-----------|--------|------------------|
| Commit Consistency | 35% | Developer velocity (log-scaled) |
| Repo Quality | 30% | Stars, forks, documentation |
| OSS Contributions | 15% | Pull requests and issue activity |
| Tech Diversity | 15% | Unique languages across repos |
| Activity Status | 5% | Recent activity check |

</details>

<details>
<summary><b>🎯 Skill Triangulation Model (Click to expand)</b></summary>

This is the platform's defense against **resume padding**. Each skill is scored on three axes:

| Source | Weight | Evidence |
|--------|--------|----------|
| **Base** | 30% | Skill appears on the resume |
| **Project** | 40% | Skill found in project tech_stack or descriptions |
| **Execution** | 30% | GitHub shows commits in the corresponding language |

**Self-Reported Guardrail:** Skills with 0% project evidence and 0% GitHub evidence cap at 40% confidence and are tagged as `"Self-Reported"`. On the recruiter dashboard, these appear with a ⚠️ yellow badge, while verified skills get a ✅ green badge.

</details>

<details>
<summary><b>🔍 Semantic Search Engine (Click to expand)</b></summary>

1. **Embedding:** Job descriptions and student projects are converted to **384-dimensional vectors** using `BAAI/bge-small-en-v1.5`
2. **Cosine Similarity:** PostgreSQL `pgvector` computes geometric distance between job vectors and every project vector
3. **Top-50 Filter:** Only the closest 50 projects proceed to full scoring
4. **Final Ranking:** Semantic score is combined with GitHub, skills, and CGPA scores

</details>

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">

**Built with ❤️ using FastAPI, React, pgvector, and sentence-transformers**

</div>
