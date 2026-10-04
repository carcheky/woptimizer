"""Configura los metadatos del repo en GitHub via API. NO imprime el token.

Uso: python .taskmaster/_gh_configure.py apply   (escribe)
     python .taskmaster/_gh_configure.py show    (solo lectura)
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


def req(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Authorization", f"Bearer {TOK}")
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("X-GitHub-Api-Version", "2022-11-28")
    r.add_header("User-Agent", "woptimizer-config")
    if data:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:400]


DESCRIPTION = (
    "Cierra en masa las apps que sobran al jugar y reabre tu setup al volver. "
    "Process manager para Windows con perfiles (Packs), semaforo de seguridad "
    "protegido y .exe standalone."
)

TOPICS = [
    "windows",
    "python",
    "process-manager",
    "gaming",
    "gui",
    "customtkinter",
    "psutil",
    "performance",
    "system-utility",
    "pyinstaller",
    "semantic-release",
]

# has_wiki False, has_projects False: el wiki y los projects estan vacios y un
# boton muerto en la barra lateral es ruido en un repo publico.
REPO_PATCH = {
    "description": DESCRIPTION,
    "has_wiki": False,
    "has_projects": False,
    "has_discussions": True,
    "delete_branch_on_merge": True,
}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "show"
    print("== ESTADO ACTUAL ==")
    st, cur = req("GET", BASE)
    if st != 200:
        print(f"GET fallo {st}: {cur}")
        return 1
    for k in ("description", "has_wiki", "has_projects", "has_discussions",
              "delete_branch_on_merge", "default_branch", "topics"):
        print(f"  {k:24} {cur.get(k)}")

    if mode == "show":
        return 0

    print("\n== APLICANDO ==")
    st, res = req("PATCH", BASE, REPO_PATCH)
    print(f"  PATCH repo -> {st}")
    if st != 200:
        print(f"  {res}")
        return 1
    print(f"  description    = {res.get('description')}")
    print(f"  has_discussions= {res.get('has_discussions')}")
    print(f"  has_wiki       = {res.get('has_wiki')}")
    print(f"  has_projects   = {res.get('has_projects')}")

    st, res = req("PUT", f"{BASE}/topics", {"names": TOPICS})
    print(f"  PUT topics -> {st}")
    if st not in (200, 204):
        print(f"  {res}")
        return 1
    st, res = req("GET", f"{BASE}/topics")
    print(f"  topics ahora  = {res.get('names')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
