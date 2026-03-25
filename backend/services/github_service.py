"""GitHub Intelligence Engine — API fetching, caching, scoring, summarization."""
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
from openai import AsyncOpenAI

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

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
        if user_resp.status_code != 200:
            logger.warning(f"GitHub user not found: {username}")
            return None
        user_data = user_resp.json()

        # Top repos (sorted by updated, limit 15)
        repos_resp = await http_client.get(
            f"{GITHUB_API}/users/{username}/repos",
            params={"sort": "updated", "per_page": 15, "type": "owner"},
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

    # 5. Recency (0-100): last activity
    activity_score = 50.0  # default
    last_activity = data.get("last_activity", "")
    if last_activity:
        try:
            last_dt = datetime.fromisoformat(last_activity.replace("Z", "+00:00"))
            days_ago = (datetime.now(timezone.utc) - last_dt).days
            activity_score = max(0, 100 - days_ago * 2)  # Decays ~2 pts/day
        except Exception:
            pass

    # Weighted total
    total = (
        0.30 * commit_score
        + 0.25 * repo_score
        + 0.20 * oss_score
        + 0.15 * diversity_score
        + 0.10 * activity_score
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

    try:
        response = await llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"GitHub summarization failed: {e}")
        return _basic_summary(data)


def _basic_summary(data: dict) -> str:
    if not data:
        return "No GitHub data available."
    langs = ", ".join(data.get("languages", [])[:5]) or "Unknown"
    return f"Developer with {data.get('public_repos', 0)} repos using {langs}. {data.get('total_stars', 0)} total stars."
