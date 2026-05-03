# tools/github_tools.py — GitHub API Agentic Workflow (Production-Grade)
import os
import requests
from typing import Optional
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")
BASE_URL = "https://api.github.com"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def _api(method: str, endpoint: str, data: dict = None) -> dict:
    """Make a GitHub API call."""
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = requests.request(
            method, url,
            headers=_headers(),
            json=data,
            timeout=15
        )
        if resp.status_code in (200, 201, 204):
            return {"ok": True, "data": resp.json() if resp.text else {}, "status": resp.status_code}
        else:
            msg = resp.json().get("message", resp.text[:200]) if resp.text else "Unknown error"
            return {"ok": False, "error": f"GitHub API {resp.status_code}: {msg}", "status": resp.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ─── REPO TOOLS ──────────────────────────────────────────

@tool
def github_create_repo(name: str, description: str = "", private: bool = False) -> str:
    """
    Create a new GitHub repository.
    Args:
        name: Repository name (e.g., my-awesome-project)
        description: Short description of the repo
        private: True for private, False for public
    """
    if not GITHUB_TOKEN or GITHUB_TOKEN == "your_github_token_here":
        return "❌ GITHUB_TOKEN not set in .env"

    result = _api("POST", "/user/repos", {
        "name": name,
        "description": description,
        "private": private,
        "auto_init": True,
        "has_issues": True,
        "has_projects": True,
        "has_wiki": True
    })

    if result["ok"]:
        repo = result["data"]
        return (
            f"✅ Repo created!\n"
            f"   Name: {repo['full_name']}\n"
            f"   URL: {repo['html_url']}\n"
            f"   Private: {repo['private']}\n"
            f"   Description: {repo.get('description', 'None')}"
        )
    return f"❌ Failed to create repo: {result['error']}"


@tool
def github_get_repo(repo: str) -> str:
    """
    Get information about a GitHub repository.
    Args:
        repo: Repo in format owner/repo-name (e.g., Nithin-genAI/Boss-agent)
    """
    result = _api("GET", f"/repos/{repo}")
    if result["ok"]:
        r = result["data"]
        return (
            f"📦 {r['full_name']}\n"
            f"   Description: {r.get('description', 'None')}\n"
            f"   Stars: {r['stargazers_count']} | Forks: {r['forks_count']}\n"
            f"   Language: {r.get('language', 'Unknown')}\n"
            f"   Private: {r['private']}\n"
            f"   Open Issues: {r['open_issues_count']}\n"
            f"   URL: {r['html_url']}"
        )
    return f"❌ Repo not found: {result['error']}"


@tool
def github_read_readme(repo: str) -> str:
    """
    Read the README of a GitHub repository.
    Args:
        repo: Repo in format owner/repo-name
    """
    import base64
    result = _api("GET", f"/repos/{repo}/readme")
    if result["ok"]:
        content = result["data"].get("content", "")
        try:
            decoded = base64.b64decode(content).decode("utf-8")
            if len(decoded) > 2000:
                decoded = decoded[:2000] + "\n\n... [truncated]"
            return f"📄 README for {repo}:\n\n{decoded}"
        except:
            return f"📄 README exists but could not decode for {repo}"
    return f"❌ No README found: {result['error']}"


@tool
def github_update_repo(repo: str, description: str = None, homepage: str = None,
                        private: bool = None, has_issues: bool = None) -> str:
    """
    Update repository settings.
    Args:
        repo: Repo in format owner/repo-name
        description: New description
        homepage: Homepage URL
        private: True/False to change visibility
        has_issues: Enable/disable issues
    """
    data = {}
    if description is not None:
        data["description"] = description
    if homepage is not None:
        data["homepage"] = homepage
    if private is not None:
        data["private"] = private
    if has_issues is not None:
        data["has_issues"] = has_issues

    if not data:
        return "❌ Nothing to update — provide at least one field"

    result = _api("PATCH", f"/repos/{repo}", data)
    if result["ok"]:
        r = result["data"]
        return f"✅ Repo updated: {r['full_name']} | {r['html_url']}"
    return f"❌ Update failed: {result['error']}"


@tool
def github_list_repos(username: str = "") -> str:
    """
    List GitHub repositories for a user.
    Args:
        username: GitHub username (leave blank to list yours)
    """
    user = username or GITHUB_USERNAME
    result = _api("GET", f"/users/{user}/repos?sort=updated&per_page=10")
    if result["ok"]:
        repos = result["data"]
        if not repos:
            return f"No repositories found for {user}"
        lines = [f"📦 Repos for {user}:"]
        for r in repos:
            lines.append(f"  • {r['name']} ({'🔒' if r['private'] else '🌐'}) — {r.get('description', 'No description')}")
        return "\n".join(lines)
    return f"❌ Failed: {result['error']}"


# ─── ISSUE TOOLS ─────────────────────────────────────────

@tool
def github_create_issue(repo: str, title: str, body: str = "", labels: str = "") -> str:
    """
    Create a new issue in a GitHub repository.
    Args:
        repo: Repo in format owner/repo-name
        title: Issue title
        body: Issue description (supports Markdown)
        labels: Comma-separated labels (e.g., bug,enhancement)
    """
    data = {"title": title, "body": body}
    if labels:
        data["labels"] = [l.strip() for l in labels.split(",")]

    result = _api("POST", f"/repos/{repo}/issues", data)
    if result["ok"]:
        issue = result["data"]
        return (
            f"✅ Issue created!\n"
            f"   #{issue['number']}: {issue['title']}\n"
            f"   URL: {issue['html_url']}"
        )
    return f"❌ Failed to create issue: {result['error']}"


@tool
def github_list_issues(repo: str, state: str = "open") -> str:
    """
    List issues in a GitHub repository.
    Args:
        repo: Repo in format owner/repo-name
        state: open, closed, or all
    """
    result = _api("GET", f"/repos/{repo}/issues?state={state}&per_page=10")
    if result["ok"]:
        issues = result["data"]
        if not issues:
            return f"No {state} issues in {repo}"
        lines = [f"🐛 {state.capitalize()} issues in {repo}:"]
        for i in issues:
            labels = ", ".join(l["name"] for l in i.get("labels", []))
            lines.append(f"  #{i['number']}: {i['title']} [{labels}]")
        return "\n".join(lines)
    return f"❌ Failed: {result['error']}"


@tool
def github_comment_on_issue(repo: str, issue_number: int, comment: str) -> str:
    """
    Add a comment to a GitHub issue.
    Args:
        repo: Repo in format owner/repo-name
        issue_number: The issue number
        comment: Comment text (supports Markdown)
    """
    result = _api("POST", f"/repos/{repo}/issues/{issue_number}/comments", {"body": comment})
    if result["ok"]:
        c = result["data"]
        return (
            f"✅ Comment added!\n"
            f"   Issue #{issue_number} in {repo}\n"
            f"   URL: {c['html_url']}"
        )
    return f"❌ Failed to comment: {result['error']}"


@tool
def github_close_issue(repo: str, issue_number: int) -> str:
    """
    Close a GitHub issue.
    Args:
        repo: Repo in format owner/repo-name
        issue_number: The issue number to close
    """
    result = _api("PATCH", f"/repos/{repo}/issues/{issue_number}", {"state": "closed"})
    if result["ok"]:
        return f"✅ Issue #{issue_number} closed in {repo}"
    return f"❌ Failed: {result['error']}"


# ─── FILE TOOLS ──────────────────────────────────────────

@tool
def github_create_file(repo: str, path: str, content: str, message: str = "Add file via Boss Agent") -> str:
    """
    Create or update a file in a GitHub repository.
    Args:
        repo: Repo in format owner/repo-name
        path: File path like README.md or src/main.py
        content: File content (plain text)
        message: Commit message
    """
    import base64

    # Check if file exists (to get sha for update)
    existing = _api("GET", f"/repos/{repo}/contents/{path}")
    data = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode()
    }
    if existing["ok"]:
        data["sha"] = existing["data"]["sha"]  # Required for update

    result = _api("PUT", f"/repos/{repo}/contents/{path}", data)
    if result["ok"]:
        action = "Updated" if existing["ok"] else "Created"
        return f"✅ {action} {path} in {repo} | Commit: {message}"
    return f"❌ Failed to create file: {result['error']}"


@tool
def github_search_code(query: str, repo: str = "") -> str:
    """
    Search for code on GitHub.
    Args:
        query: Search query (e.g., 'def train_model')
        repo: Optional repo to search within (owner/repo-name)
    """
    q = f"{query} repo:{repo}" if repo else query
    result = _api("GET", f"/search/code?q={requests.utils.quote(q)}&per_page=5")
    if result["ok"]:
        items = result["data"].get("items", [])
        if not items:
            return f"No code found for '{query}'"
        lines = [f"🔍 Code search: '{query}'"]
        for item in items:
            lines.append(f"  • {item['repository']['full_name']}/{item['path']}")
        return "\n".join(lines)
    return f"❌ Search failed: {result['error']}"
