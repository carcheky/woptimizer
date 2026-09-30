"""Espejo de los agentes del repo hacia el runtime que los delega.

POR QUE EXISTE: los cuatro roles viven en DOS sitios a proposito, porque los
consumen dos runtimes que no comparten configuracion:

  - `.agents/agents/<n>/agent.md`  -> lo descubre Antigravity (workspace).
  - `~/.minimax/agents/<n>/`       -> lo descubre MiniMax Code (global).

El repo es la FUENTE DE VERDAD: esta versionado y viaja. El global es un
ESPEJO: si editas el global, el cambio se pierde en el siguiente `sync` de
otro equipo, y en el tuyo no se ve hasta que alguien lo ejecuta.

`--check` informa de la divergencia SIN escribir nada: util antes de commitear,
y es el que debe correr un validador. Escribir sin mirar antes es como
sobreescribir la configuracion de otro.

Uso:
    python .taskmaster/sync_agents.py           # espejo repo -> global
    python .taskmaster/sync_agents.py --check   # solo informa, exit 1 si diverge

Códigos de salida (contrato, igual que git_safe_commit.py):
    0  espejo hecho, o ya estaba sincronizado
    1  fallo de E/S al leer o escribir
    2  uso incorrecto
    3  falta la fuente (repo sin `.agents/agents/`)
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys

AGENTES = ("architect-review", "mutation-auditor", "openspec-dev", "process-db-updater")

REPO_AGENTS = os.path.join(".agents", "agents")


def _raiz_repo() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _destino_global() -> str:
    base = os.environ.get("MINIMAX_HOME")
    if base:
        return os.path.join(base, "agents")
    return os.path.join(os.path.expanduser("~"), ".minimax", "agents")


def _sha(ruta: str) -> str:
    with open(ruta, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:12]


def main(argv: list[str]) -> int:
    check = "--check" in argv[1:]
    desconocidas = [a for a in argv[1:] if a not in ("--check",)]
    if desconocidas:
        print("WOPT_USO: solo se admite --check")
        return 2

    raiz = _raiz_repo()
    origen_dir = os.path.join(raiz, REPO_AGENTS)
    destino_dir = _destino_global()

    if not os.path.isdir(origen_dir):
        print("WOPT_FALTA_FUENTE: no existe " + REPO_AGENTS + " en el repo")
        return 3

    print("repo   : " + origen_dir)
    print("espejo : " + destino_dir)
    print("")

    exit_code = 0
    for nombre in AGENTES:
        origen = os.path.join(origen_dir, nombre, "agent.md")
        destino = os.path.join(destino_dir, nombre, "agent.md")

        if not os.path.isfile(origen):
            print("WOPT_FALTA_AGENTE: " + nombre + " no esta en el repo")
            exit_code = 3
            continue

        if os.path.isfile(destino) and _sha(origen) == _sha(destino):
            print("OK        " + nombre + "  identico")
            continue

        if check:
            print("DIVERGE   " + nombre + "  el espejo global no coincide")
            exit_code = 1
            continue

        try:
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            shutil.copy2(origen, destino)
        except OSError as exc:
            print("WOPT_ESCRITURA: " + nombre + " -> " + str(exc))
            exit_code = 1
            continue

        print("ESPEJADO  " + nombre + "  " + _sha(origen))

    if check and exit_code == 1:
        print("")
        print("Hay divergencia. Ejecuta sin --check para corregirla.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
