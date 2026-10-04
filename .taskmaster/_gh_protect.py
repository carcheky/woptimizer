"""Aplica proteccion BLANDA en main: sin force-push, sin borrado, sin required
checks y sin PR obligatorio. Ver seccion 2 y O-2 de docs/GITHUB-SETUP-CHECKLIST.md.

Por que NO required status checks: el job `release` de .github/workflows/release.yml
empuja los TAGS con GITHUB_TOKEN (contents: write). Con required checks activos,
GitHub rechaza ese push con 403 y NO se publica ninguna release. El propio
release-pipeline.md:67 lo documenta. Proteccion fuerte + token publicando tags
= releases rotas.

Uso: python .taskmaster/_gh_protect.py apply | show
"""
import json
import subprocess
import sys
import urllib.error
import urllib.request

OWNER = "carcheky"
REPO = "woptimizer"
BASE = f"https://api.github.com/repos/{OWNER}/{REPO}"


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

# allow_force_pushes: false  -> bloquea force-push
# allow_deletions:    false  -> bloquea borrar la rama
# required_status_checks: null      -> NO exige checks (compat con el push de tags)
# required_pull_request_reviews: null -> NO exige PR
# enforce_admins: false -> ni los admins se saltan las dos reglas de arriba
PROTECTION = {
    "required_status_checks": None,
    "enforce_admins": False,
    "required_pull_request_reviews": None,
    "restrictions": None,
    "required_linear_history": False,
    "allow_force_pushes": False,
    "allow_deletions": False,
    "required_conversation_resolution": False,
    "lock_branch": False,
    "allow_fork_syncing": True,
}


def req(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Authorization", f"Bearer {TOK}")
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("X-GitHub-Api-Version", "2022-11-28")
    r.add_header("User-Agent", "woptimizer-protect")
    if data:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:500]


def show():
    st, res = req("GET", f"{BASE}/branches/main/protection")
    print(f"GET protection/main -> {st}")
    if st != 200:
        print(f"  {res}")
        return 1
    print(json.dumps({
        "enabled": res.get("enabled"),
        "allow_force_pushes": (res.get("allow_force_pushes") or {}).get("enabled"),
        "allow_deletions": (res.get("allow_deletions") or {}).get("enabled"),
        "enforce_admins": (res.get("enforce_admins") or {}).get("enabled"),
        "required_status_checks": res.get("required_status_checks"),
        "required_pull_request_reviews": res.get("required_pull_request_reviews"),
        "required_linear_history": (res.get("required_linear_history") or {}).get("enabled"),
    }, indent=2, ensure_ascii=False))
    return 0


def apply():
    st, res = req("PUT", f"{BASE}/branches/main/protection", PROTECTION)
    print(f"PUT protection/main -> {st}")
    if st not in (200, 201):
        print(f"  {res}")
        return 1
    print(json.dumps({
        "enabled": res.get("enabled"),
        "allow_force_pushes": (res.get("allow_force_pushes") or {}).get("enabled"),
        "allow_deletions": (res.get("allow_deletions") or {}).get("enabled"),
        "enforce_admins": (res.get("enforce_admins") or {}).get("enabled"),
        "required_status_checks": res.get("required_status_checks"),
    }, indent=2, ensure_ascii=False))
    print("\nVerificacion independiente:")
    return show()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "show"
    sys.exit(apply() if mode == "apply" else show())
