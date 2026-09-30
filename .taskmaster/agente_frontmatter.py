"""Anade al frontmatter de los agentes las claves que exigen otros runtimes.

POR QUE: los cuatro agentes se declaran con `name` + `description`, que es lo
que MiniMax Code lee y lo unico que ambos runtimes exigen. Pero el resto de
runtimes anaden claves propias para que un agente pueda delegarse:

    OpenCode     -> `mode: subagent`   (sin ella, el agente no se puede lanzar)
    Antigravity  -> `subagent: true`   (por defecto true, pero explicito se ve)
    Claude Code  -> no lo soporta: ignora claves desconocidas

La interseccion de esos requisitos cabe en un unico fichero, asi que se anaden
las dos. Si un runtime futuro se queja de una clave, se quita esa linea: estan
en un bloque propio, al principio, para poder editar sin tocar el prompt.

Idempotente: se puede volver a ejecutar, no duplica claves.
"""

from __future__ import annotations

import io
import os
import re
import sys

AGENTES = ("architect-review", "mutation-auditor", "openspec-dev", "process-db-updater")

# Claves que se anaden si no existen. Se comprueban una a una para no
# duplicarlas en una segunda ejecucion.
CLAVES = (
    "mode: subagent",
    "subagent: true",
    "mainAgent: false",
)


def repo_raiz() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def anadir(ruta: str) -> str:
    """Devuelve 'ok', 'ya-estaba' o 'error'."""
    with io.open(ruta, encoding="utf-8") as fh:
        texto = fh.read()

    if not texto.startswith("---"):
        return "error: sin frontmatter"

    fin = texto.find("\n---", 3)
    if fin == -1:
        return "error: frontmatter sin cerrar"

    cabecera = texto[3:fin]
    cuerpo = texto[fin:]

    faltan = [c for c in CLAVES if not re.search(
        r"^" + re.escape(c.split(":")[0]) + r"\s*:", cabecera, re.M)]

    if not faltan:
        return "ya-estaba"

    if cabecera and not cabecera.endswith("\n"):
        cabecera += "\n"
    cabecera += "\n".join(faltan) + "\n"

    with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
        fh.write("---" + cabecera + cuerpo)
    return "ok: " + ", ".join(c.split(":")[0] for c in faltan)


def main() -> int:
    base = os.path.join(repo_raiz(), ".agents", "agents")
    if not os.path.isdir(base):
        print("WOPT_FALTA_FUENTE: no existe .agents/agents/")
        return 3
    for nombre in AGENTES:
        ruta = os.path.join(base, nombre, "agent.md")
        if not os.path.isfile(ruta):
            print("FALTA   " + nombre)
            continue
        print("{:8s} {}".format(anadir(ruta), nombre))
    return 0


if __name__ == "__main__":
    sys.exit(main())
