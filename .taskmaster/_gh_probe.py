"""Sonda de solo lectura del repo en GitHub. NO imprime el token."""
import json
import subprocess
import sys
import urllib.request


def token() -> str:
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True,
        text=True,
    )
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    sys.exit("NO_TOKEN")


TOK = token()
OWNER = "carcheky"
REPO = "woptimizer"
BASE = f"https://api.github.com/repos/{OWNER}/{REPO}"


def get(url):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {TOK}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "woptimizer-probe")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


out = {}

r = get(BASE)
out["repo"] = {
    "name": r.get("full_name"),
    "description": r.get("description"),
    "homepage": r.get("homepage"),
    "private": r.get("private"),
    "fork": r.get("fork"),
    "archived": r.get("archived"),
    "default_branch": r.get("default_branch"),
    "topics": r.get("topics"),
    "language": r.get("language"),
    "license": (r.get("license") or {}).get("spdx_id"),
    "created_at": r.get("created_at"),
    "pushed_at": r.get("pushed_at"),
    "size_kb": r.get("size"),
    "open_issues": r.get("open_issues_count"),
    "has_issues": r.get("has_issues"),
    "has_wiki": r.get("has_wiki"),
    "has_projects": r.get("has_projects"),
    "has_discussions": r.get("has_discussions"),
    "has_pages": r.get("has_pages"),
    "subscribers": r.get("subscribers_count"),
    "stargazers": r.get("stargazers_count"),
    "forks": r.get("forks_count"),
    "watchers": r.get("watchers_count"),
    "allow_forking": r.get("allow_forking"),
    "is_template": r.get("is_template"),
    "web_commit_signoff": r.get("web_commit_signoff_required"),
    "security_and_analysis": r.get("security_and_analysis"),
    "visibility": r.get("visibility"),
}

out["branches"] = [
    {
        "name": b["name"],
        "protected": b["protected"],
        "sha": b["commit"]["sha"][:8],
    }
    for b in get(f"{BASE}/branches?per_page=100")
]

out["branch_main_protection"] = None
try:
    bp = get(f"{BASE}/branches/main/protection")
    out["branch_main_protection"] = {
        "enabled": bp.get("enabled"),
        "checks": (bp.get("required_status_checks") or {}).get("contexts"),
        "enforce_admins": (bp.get("enforce_admins") or {}).get("enabled"),
        "required_reviews": (bp.get("required_pull_request_reviews") or {}).get(
            "required_approving_review_count"
        ),
        "require_signed": (bp.get("required_signatures") or {}).get("enabled"),
        "allow_force": (bp.get("allow_force_pushes") or {}).get("enabled"),
        "allow_deletion": (bp.get("allow_deletions") or {}).get("enabled"),
    }
except Exception as e:
    out["branch_main_protection"] = f"ERR {e}"

out["tags"] = [t["name"] for t in get(f"{BASE}/tags?per_page=100")]

out["releases"] = [
    {
        "tag": rel["tag_name"],
        "name": rel["name"],
        "draft": rel["draft"],
        "prerelease": rel["prerelease"],
        "published_at": rel["published_at"],
        "assets": [a["name"] for a in rel["assets"]],
    }
    for rel in get(f"{BASE}/releases?per_page=20")
]

out["workflows"] = [
    {"name": w["name"], "path": w["path"], "state": w["state"]}
    for w in get(f"{BASE}/actions/workflows?per_page=100").get("workflows", [])
]

out["runs"] = [
    {
        "name": r["name"],
        "head_branch": r["head_branch"],
        "event": r["event"],
        "status": r["status"],
        "conclusion": r["conclusion"],
        "created_at": r["created_at"],
        "head_sha": r["head_sha"][:8],
    }
    for r in get(f"{BASE}/actions/runs?per_page=15").get("workflow_runs", [])
]

out["contents_root"] = sorted(
    c["name"] for c in get(f"{BASE}/contents?ref=main")
)

print(json.dumps(out, indent=2, ensure_ascii=False))
