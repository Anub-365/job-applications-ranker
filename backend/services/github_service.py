"""GitHub Intelligence Engine — API fetching, caching, scoring, summarization."""
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
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

# Simple in-memory cache (24h TTL)
_cache: dict[str, tuple[float, any]] = {}
CACHE_TTL = 86400  # 24 hours


def _get_cached(key: str):
    if key in _cache:
        ts, val = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return val
        del _cache[key]
    return None


def _set_cached(key: str, val):
    _cache[key] = (time.time(), val)


http_client = httpx.AsyncClient(
    headers={
        "Accept": "application/vnd.github.v3+json",
        **({"Authorization": f"token {settings.GITHUB_TOKEN}"} if settings.GITHUB_TOKEN else {}),
    },
    timeout=30.0,
)

llm_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

GITHUB_API = "https://api.github.com"


async def fetch_github_data(username: str) -> Optional[dict]:
    """Fetch repos, languages, commits, PRs for a GitHub user."""
    # Handle full URLs if provided
    if "github.com/" in username:
        username = username.rstrip("/").split("/")[-1]
    cached = _get_cached(f"github:{username}")
    if cached is not None:
        logger.info(f"GitHub cache hit for {username}")
        return cached
    try:
        # User info
        user_resp = await http_client.get(f"{GITHUB_API}/users/{username}")
        if user_resp.status_code in (403, 429):
            from fastapi import HTTPException
            raise HTTPException(status_code=429, detail="GitHub rate limit reached. Please try again later.")
        if user_resp.status_code != 200:
            logger.warning(f"GitHub user not found: {username}")
            return None
        user_data = user_resp.json()

        # Top repos (sorted by updated, limit 100)
        repos_resp = await http_client.get(
            f"{GITHUB_API}/users/{username}/repos",
            params={"sort": "updated", "per_page": 100, "type": "owner"},
        )
        repos = repos_resp.json() if repos_resp.status_code == 200 else []

        # Events (recent activity)
        events_resp = await http_client.get(
            f"{GITHUB_API}/users/{username}/events/public",
            params={"per_page": 100},
        )
        events = events_resp.json() if events_resp.status_code == 200 else []

        # Aggregate data
        languages = set()
        total_stars = 0
        total_forks = 0
        has_readme_count = 0
        repo_details = []

        for repo in repos:
            if isinstance(repo, dict) and not repo.get("fork", False):
                lang = repo.get("language")
                if lang:
                    languages.add(lang)
                total_stars += repo.get("stargazers_count", 0)
                total_forks += repo.get("forks_count", 0)
                if repo.get("description"):
                    has_readme_count += 1
                repo_details.append({
                    "name": repo.get("name", ""),
                    "description": repo.get("description", "") or "",
                    "language": lang or "Unknown",
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "updated_at": repo.get("updated_at", ""),
                })

        # Count push events as proxy for commits
        push_events = [e for e in events if isinstance(e, dict) and e.get("type") == "PushEvent"]
        total_commits = sum(len(e.get("payload", {}).get("commits", [])) for e in push_events)

        # Count PRs
        pr_events = [e for e in events if isinstance(e, dict) and e.get("type") == "PullRequestEvent"]

        # Last activity
        last_activity = user_data.get("updated_at", "")

        result = {
            "username": username,
            "public_repos": user_data.get("public_repos", 0),
            "followers": user_data.get("followers", 0),
            "repos": repo_details,
            "languages": list(languages),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "has_readme_count": has_readme_count,
            "total_commits_recent": total_commits,
            "total_prs_recent": len(pr_events),
            "last_activity": last_activity,
        }
        _set_cached(f"github:{username}", result)
        return result
    except Exception as e:
        # Check if it's already our HTTPException
        if type(e).__name__ == "HTTPException":
            raise
        logger.error(f"GitHub fetch failed for {username}: {e}")
        return None


def compute_github_scores(data: dict) -> dict:
    """Compute 5 sub-scores + total GitHub score."""

    # 1. Commit Consistency (0-100): based on recent commits
    commits = data.get("total_commits_recent", 0)
    commit_score = min(100, commits * 2)  # ~50 commits = 100

    # 2. Repo Quality (0-100): stars + forks + READMEs
    stars = data.get("total_stars", 0)
    forks = data.get("total_forks", 0)
    readmes = data.get("has_readme_count", 0)
    repo_count = max(len(data.get("repos", [])), 1)
    repo_score = min(100, (stars * 10 + forks * 5 + (readmes / repo_count) * 30))

    # 3. OSS Contribution (0-100): based on PRs
    prs = data.get("total_prs_recent", 0)
    oss_score = min(100, prs * 20)

    # 4. Tech Diversity (0-100): unique languages
    langs = len(data.get("languages", []))
    diversity_score = min(100, langs * 20)

    # 5. Activity Status (0-100): Binary — any activity = 100
    activity_score = 0.0
    last_activity = data.get("last_activity", "")
    if last_activity:
        activity_score = 100.0  # Any tracked activity = full score

    # Weighted total (35/30/15/15/5)
    total = (
        0.35 * commit_score
        + 0.30 * repo_score
        + 0.15 * oss_score
        + 0.15 * diversity_score
        + 0.05 * activity_score
    )

    return {
        "commit_score": round(commit_score, 2),
        "repo_score": round(repo_score, 2),
        "oss_score": round(oss_score, 2),
        "diversity_score": round(diversity_score, 2),
        "activity_score": round(activity_score, 2),
        "total_score": round(total, 2),
    }


async def summarize_github(data: dict) -> str:
    """Use LLM to produce a clean summary of GitHub activity."""
    if not llm_client or not data:
        return _basic_summary(data)

    repos_text = "\n".join(
        f"- {r['name']}: {r['description']} ({r['language']}, ⭐{r['stars']})"
        for r in data.get("repos", [])[:10]
    )
    prompt = f"""Summarize this developer's GitHub profile in 2-3 sentences for a recruiter.
Focus on their technical strengths, primary technologies, and project quality.

Username: {data.get('username')}
Languages: {', '.join(data.get('languages', []))}
Repos: {data.get('public_repos', 0)}
Stars: {data.get('total_stars', 0)}
Recent commits: {data.get('total_commits_recent', 0)}

Top repos:
{repos_text}"""

    # Try OpenAI first
    if openai_client:
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
            )
            return {"success": True, "summary": response.choices[0].message.content.strip(), "llm": "OpenAI"}
        except Exception as e:
            error_msg = str(e)
            is_quota = "insufficient_quota" in error_msg or "quota_exceeded" in error_msg
            if not is_quota:
                logger.error(f"GitHub summarization OpenAI error: {error_msg}")
            else:
                logger.info("GitHub summarization OpenAI quota reached, attempting Groq fallback...")

    # Groq Fallback (Primary Fallback)
    for i, g_client in enumerate(groq_clients):
        try:
            response = await g_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
            )
            return {"success": True, "summary": response.choices[0].message.content.strip(), "llm": f"Groq (Key {i+1})"}
        except Exception as e:
            logger.warning(f"GitHub summarization Groq fallback failed with Key {i+1}: {e}")
            if i == len(groq_clients) - 1:
                logger.info("All Groq keys exhausted, attempting Gemini fallback...")

    # Gemini Fallback (Secondary Fallback)
    if settings.GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.3, max_output_tokens=200)
            )
            return {"success": True, "summary": response.text.strip(), "llm": "Gemini"}
        except Exception as e:
            logger.error(f"GitHub summarization Gemini fallback failed: {e}")

    return {
        "success": False, 
        "summary": _basic_summary(data),
        "error": "All AI services exhausted",
        "llm": "None (Fallback)"
    }


def _basic_summary(data: dict) -> str:
    if not data:
        return "No GitHub data available."
    langs = ", ".join(data.get("languages", [])[:5]) or "Unknown"
    return f"Developer with {data.get('public_repos', 0)} repos using {langs}. {data.get('total_stars', 0)} total stars."
