"""INCERT-1: mide la proteccion de `main` por API. Solo lectura. NO imprime el token."""
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
    req.add_header("User-Agent", "woptimizer-incert1")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


print("=== INCERT-1: proteccion de la rama main ===")
try:
    prot = get(f"{BASE}/branches/main/protection")
except urllib.error.HTTPError as exc:
    prot = {"HTTP_ERROR": exc.code, "cuerpo": exc.read().decode("utf-8")[:400]}

print(json.dumps(prot, indent=2, ensure_ascii=True)[:3000])

if "required_status_checks" in prot:
    rsc = prot.get("required_status_checks")
    print("\n--- LECTURA ---")
    if rsc is None:
        print("required_status_checks = None (NO HAY checks requeridos)")
    else:
        print("required_status_checks =", json.dumps(rsc, ensure_ascii=True))
else:
    print("\n--- LECTURA ---")
    print("sin campo required_status_checks: proteccion no impuesta o no legible")

print("\n=== ramas remotas ===")
for b in get(f"{BASE}/branches?per_page=100"):
    print(f"  {b['name']:10s} {b['commit']['sha']}")

print("\n=== releases ===")
for rel in get(f"{BASE}/releases?per_page=20"):
    print(f"  {rel['tag_name']:22s} prerelease={rel['prerelease']!s:5s} "
          f"published={rel['published_at']} assets={len(rel.get('assets') or [])} "
          f"names={[a['name'] for a in (rel.get('assets') or [])]}")

print("\n=== workflows runs (10 ultimos) ===")
try:
    _d = get(f"{BASE}/actions/runs?per_page=10")
    for run in _d.get("workflow_runs", []):
        print(f"  {run['id']} {run['name']:28s} {run['head_branch']:6s} "
              f"{run['status']:11s} {str(run['conclusion']):11s} {run['created_at']}")
except urllib.error.HTTPError as exc:
    print("  runs:", exc.code, exc.read().decode("utf-8")[:200])

print("\n=== jobs del ultimo run de beta ===")
try:
    _d = get(f"{BASE}/actions/runs?per_page=1&branch=beta")
    _runs = _d.get("workflow_runs", [])
    if _runs:
        rid = _runs[0]["id"]
        print(f"  run id={rid} {dict((k, _runs[0].get(k)) for k in ('head_branch', 'head_sha', 'status', 'conclusion'))}")
        for j in get(f"{BASE}/actions/runs/{rid}/jobs?per_page=100").get("jobs", []):
            print(f"    job {j['name']:30s} {j['status']:11s} {str(j['conclusion']):11s}")
except urllib.error.HTTPError as exc:
    print("  jobs:", exc.code, exc.read().decode("utf-8")[:200])

print("\n=== comparación de ancestros (API compare) ===")
try:
    cmp_ = get(f"{BASE}/compare/main...beta")
    print("  main...beta status:", cmp_.get("status"),
          "ahead_by:", cmp_.get("ahead_by"),
          "behind_by:", cmp_.get("behind_by"),
          "total_commits:", cmp_.get("total_commits"))
    for c in cmp_.get("commits", []):
        primera = c["commit"]["message"].splitlines()[0]
        print(f"    {c['sha'][:7]} ({len(primera)}) {primera}")
except urllib.error.HTTPError as exc:
    print("  compare:", exc.code, exc.read().decode("utf-8")[:200])
