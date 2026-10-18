#!/usr/bin/env python3
"""
git_safe_commit.py - Wrapper de commit blindado para woptimizer (Windows + Nextcloud/VFS).

En entornos con Virtual Files (Nextcloud/OneDrive) el `.git` que vive dentro del
arbol de trabajo queda corrupto (`fatal: bad object HEAD`), asi que el historial
real vive en un repo desacoplado en `%LOCALAPPDATA%\\woptimizer_git\\.git`. Este
wrapper redirige GIT_DIR ahi ANTES de tocar nada y VALIDA que ese repo sea
utilizable. Nunca hace fallback al `.git` del arbol de trabajo: si el repo
desacoplado no valida, se sale con codigo 3.

CONTRATO DE CODIGOS DE SALIDA (normativo, documentado en docs/ai/sandbox-rules.md):
    0  WOPT_COMMIT_OK <hash-short> <mensaje>   commit creado de verdad
    0  WOPT_NOOP <motivo>                      no hay nada que comitear (benigno)
    1  WOPT_FAIL <operacion> <detalle>         fallo de una operacion de git
    2  WOPT_USAGE <detalle>                    uso incorrecto
    2  WOPT_USAGE ancla-mensaje <detalle>      el mensaje no lleva identificador
    2  WOPT_USAGE paridad-git <detalle>        llega una sola de las dos variables
    2  WOPT_USAGE cabecera-larga <que> <med>   la cabecera pasa de 120 caracteres
    2  WOPT_USAGE cabecera-regla <regla> <mot> la cabecera incumple otra regla
    2  WOPT_USAGE cwd-fuera-de-raiz <detalle>  el cwd no esta en la raiz del proyecto
    3  WOPT_REPO_INVALIDO <detalle>            repositorio no verificable

LAS DOS ALARMAS DE UBICACION (TASK-072, ronda 3). Este fichero ES la puerta que
existe para que nadie versione sin ancla, y medido tres veces en la historia de
este repo ha sido tambien la VIA por la que un subagente ha contaminado el
historial real (ciclo 56/TASK-069, y dos veces el 2026-10-08). La causa esta en
sus propias lineas: `REPO_ROOT` se deriva de `__file__`, pero `LOCAL_GIT_DIR` es
una CONSTANTE ABSOLUTA y no admite hermeticidad ninguna; luego una copia en
`%TEMP%` commitea en el repo real con el arbol de la camara, y su propio
`--verify` lo certifica con `WOPT_REPO_OK`.

Las dos alarmas cierran los dos lados de ese defecto, y son independientes:

    1. `cwd` FUERA de `REPO_ROOT` -> 2 (`cwd-fuera-de-raiz`). El bucle commitea
       desde la raiz, luego el camino bueno no se entera. Se puede saltar con
       `--allow-cwd-externo`, que suena en el log.
    2. Repositorio y arbol QUE NO SE CORRESPONDEN -> 3. El repositorio declara
       cual es su arbol (`core.worktree`, o un remoto que sea una ruta local
       existente) y lo que se va a versionar tiene que ser ese. **La 1 sola no
       cierra el caso medido**: en `a5de331` el cwd estaba DENTRO del arbol de la
       camara, luego la 2 es la que lo detiene. No se puede saltar: no es una
       costumbre, es una incoherencia entre el repositorio y el arbol.

LIMITES DECLARADOS de la segunda, porque un limite que no se escribe se lee
como cobertura: (a) si el repositorio no declara ningun arbol, la alarma no
tiene nada que comparar y **acepta** (sale un `INFO ancla-arbol:` que lo dice);
(b) solo mira `run_tests`-style argv, no el estado del indice. El `INFO` del
camino sin declaracion lo nombra en voz alta en cada invocacion.

PUERTA DE LA CABECERA (TASK-066): el mensaje tiene que parsear como
conventional commit y su cabecera no pasar de 120, con el criterio COPIADO del
codigo de commitlint y no inventado (ver `clasificar_cabecera`). Sin ella un
commit de 135 caracteres si puede existir, y el dia que puede volver a existir
vuelve el rojo: el job `commits` tumba la corrida entera y nada despues corre.
Va en el mismo sitio que la puerta de ancla, por la misma razon y con el mismo
codigo 2: la puerta no ejecuta ninguna operacion de git, luego un `WOPT_FAIL`
seria indistinguible de un fallo de git para el unico consumidor que ramifica
por el codigo.

LA RAMA ES AVISO, NO RECHAZO (proposal.md seccion 3.2). Estar en `main` imprime
un bloque `AVISO` que nombra la regla de TASK-066 y **se sigue con codigo 0**.
El motivo es evidencia ya pagada por este repo (`STATUS.md:95(b)`): una puerta
que solo existe en el wrapper no puede cerrar un `git commit` escrito a mano, y
un rechazo duro sobre `main` solo guardaria el camino guardado --el wrapper-- y
**bloquearia el commit legitimo del dueno en la rama de release**, que es el
caso para el que `main` existe. Lo que se rechaza es la cabecera, no la rama.

PUERTA DEL MENSAJE (TASK-059): un mensaje pasa si lleva `TASK-NNN` que exista en
`.taskmaster/tasks.json`, o `CYCLE-NNN`, o un marcador de ciclo (`ciclo N`). Sin
identificador el commit no tiene tercer testigo, asi que se rechaza con el codigo
2 (uso incorrecto), NO con el 1: la puerta no ejecuta ninguna operacion de git y
meterla en `WOPT_FAIL` haria falsa la tabla de docs/ai/sandbox-rules.md. Se
coloca despues de `validar_repo` y del NOOP y ANTES de `add -A`, luego un arbol
limpio sigue diciendo WOPT_NOOP + 0 y un rechazo no muta el arbol.

PARIDAD `GIT_DIR` / `GIT_WORK_TREE` (TASK-061): las dos variables del entorno se
honran CON LA MISMA precedencia, pero no se admiten sueltas. `get_env()` devuelve
ademas si llegaron juntas o solo una, y una sola se RECHAZA con el codigo 2
(`WOPT_USAGE paridad-git`) sin escribir nada, en `main()` y DESPUES de
`validar_repo` (y por tanto tambien en `--verify`). Motivo medido: con un
`GIT_DIR` desechable y sin `GIT_WORK_TREE`, el hook hermetizaba el REPOSITORIO y
seguia haciendo `add -A` y `commit` sobre el ARBOL DE TRABAJO REAL, que es como
una sonda llego a stagear y commitear el arbol del dueno dentro de un repo de
temporal. La paridad no es un extra: es el precio de honar `GIT_WORK_TREE` del
entorno, porque sin ella bastaria un `GIT_DIR` real + un arbol ajeno para
versionar un arbol extranjero en el historial real.

`--verify` es un modo diagnostico de solo lectura: reutiliza EXACTAMENTE la misma
validacion, imprime `WOPT_REPO_OK <git_dir>` + 0 si el repo esta sano, o
`WOPT_REPO_INVALIDO <detalle>` + 3 si no. Nunca comitea y NO pasa por la puerta
(es un diagnostico del repo y no lleva mensaje).

Uso:
    python .taskmaster/git_safe_commit.py "tipo(scope): descripcion (TASK-NNN)"
    python .taskmaster/git_safe_commit.py --verify

Desde la raiz del proyecto. Fuera de ella se sale con 2
(`WOPT_USAGE cwd-fuera-de-raiz`); `--allow-cwd-externo` lo salta, suena.
"""

import sys
import os
import re
import json
import subprocess
import io

# La consola de este host es cp1252 y `git` emite acentos, codigos de color ANSI
# y saltos de linea: sin esto, un `print()` revienta con UnicodeEncodeError
# justo en el mensaje de error. MEDIDO el 2026-10-04 (TASK-059): esto solo se
# hace CUANDO EL WRAPPER ES EL PROGRAMA, nunca al importarlo. La razon es
# medida: `run_tests.py` importa este modulo para probar `ancla_del_mensaje` sin
# escribir nada, y envolver `sys.stdout`/`sys.stderr` a nivel de modulo
# reenvuelve los streams del PROCESO QUE IMPORTA: al terminar, el doble
# envoltorio se libera y la salida del validador de tests muere con
# `ValueError: I/O operation on closed file` y `lost sys.stderr`. Importar un
# modulo no puede cambiarle la consola a quien lo importa.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_GIT_DIR = os.path.expandvars(r"%LOCALAPPDATA%\woptimizer_git\.git")

# Codigos de salida del contrato (no inventar otros).
CODE_OK = 0
CODE_FAIL = 1
CODE_USAGE = 2
CODE_REPO = 3

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# --- La puerta del mensaje (TASK-059) ---------------------------------------
#
# El marcador de ciclo es el MISMO patron, caracter por caracter, que el del
# validador (`validate_docs.py` -> `_RE_MARCADOR_DE_CICLO`, decision D1 de
# `docs/ai/sandbox-rules.md`). No se importa de ahi: el wrapper no puede depender
# del validador (es la unica puerta de versionado y tiene que valer con el
# validador caido). Lo que impide que diverjan es `run_tests.py`, que compara las
# dos cadenas: dos copias que nadie contrasta son dos puertas.
_RE_MARCADOR_ANCLA = re.compile(
    r"\b(?:ciclo|cycle)(s?)\b[\s:#-]*#?(\d{1,4})(?:\s*-\s*(\d{1,4}))?",
    re.IGNORECASE,
)
# `TASK-` con 1 a 4 digitos y el `\b` de salida. Sin el `\b` final, "TASK-12345"
# casaria con "TASK-1234" y resolveria un id que no existe. `T-\d+` NO se acepta:
# `T-1`..`T-9` son ids de tarea DENTRO de un change
# (`openspec/changes/*/tasks.md`), no existen en `tasks.json` y nadie puede
# resolverlos: seria un ancla de mentira.
_RE_TASK_ANCLA = re.compile(r"\bTASK-(\d{1,4})\b")
_RE_CYCLE_ANCLA = re.compile(r"\bCYCLE-\d{3}\b")

# Motivo del rechazo. ASCII PURO (trampa #16, consola cp1252) y con las TRES
# formas aceptadas nombradas, que es lo que permite corregir el mensaje sin
# abrir el contrato. La linea `WOPT_*` lo imprime la ULTIMA (regla 4).
MOTIVO_SIN_ANCLA = (
    "este mensaje no lleva identificador de ciclo ni de tarea; se espera "
    "'TASK-NNN' existente en .taskmaster/tasks.json, 'CYCLE-NNN' o 'ciclo N'. "
    "POR QUE importa: sin identificador este commit no tiene tercer testigo --ni "
    "rd_journal.json ni el historial podran anclarlo despues-- y esa es la ceguera "
    "que TASK-059 cierra. Ancla tu mensaje y repite el commit."
)

# Motivo del rechazo de PARIDAD. ASCII PURO, mismo motivo que el de la puerta del
# mensaje: es el texto que mas urge y el que menos puede fallar al imprimirse.
# Nombra las DOS formas que valen y el POR QUE, que es lo que permite corregir la
# invocacion sin abrir el contrato.
MOTIVO_PARIDAD_ROTA = (
    "llega solo una de las dos: si el entorno trae GIT_DIR y no GIT_WORK_TREE (o al "
    "reves), el par no es utilizable. Pon las dos al valor que quieras usar, o ninguna "
    "y el wrapper usa su par por defecto ("
    "'%LOCALAPPDATA%\\woptimizer_git\\.git' + el arbol del proyecto). POR QUE importa: "
    "con un GIT_DIR desechable y el arbol del proyecto, el hook hermetizaba el "
    "REPOSITORIO y seguia haciendo add -A y commit sobre el ARBOL REAL, que es como "
    "una sonda llego a stagear y commitear el arbol del dueno dentro de un repo "
    "temporal. Medido, y la hermeticidad de repo y arbol es lo que queda cerrado"
)

# --- Las dos alarmas de ubicacion (TASK-072, ronda 3) ------------------------
#
# MEDIDO: tres veces en la historia de este repo un subagente ha escrito un
# commit en el HISTORIAL REAL con un arbol que no era el suyo (ciclo 56/TASK-069,
# y dos veces el 2026-10-08 en la ronda 1 y la ronda 2 de este ciclo). No lo
# causo el agente: lo causo ESTE fichero, que es la puerta que existe para que
# nadie versione sin ancla.
#
# La causa medida, en cuatro lineas:
#     REPO_ROOT     = os.path.dirname(...(os.path.abspath(__file__)))
#     LOCAL_GIT_DIR = os.path.expandvars(r"%LOCALAPPDATA%\woptimizer_git\.git")
#     env["GIT_DIR"]        = env.get("GIT_DIR") or LOCAL_GIT_DIR
#     env["GIT_WORK_TREE"]  = env.get("GIT_WORK_TREE") or REPO_ROOT
#
# El arbol SE DERIVA de donde vive el script, pero el repositorio es una
# CONSTANTE ABSOLUTA, luego no admite hermeticidad ninguna. Invocado desde una
# copia en `%TEMP%`, el wrapper escribe en el repo real con el arbol de la
# camara, y su propio `--verify` responde `WOPT_REPO_OK` desde la camara. Dos
# alarmas distintas cierran los dos lados de ese mismo defecto:
#
#   1. `cwd` FUERA del arbol del proyecto -> 2, porque quien esta ahi no esta
#      versionando lo que cree.
#   2. repositorio y arbol QUE NO SE CORRESPONDEN -> 3, porque es el caso
#      medido (`a5de331`): el cwd SI estaba dentro del arbol de la copia, luego
#      la alarma 1 sola NO lo habria cerrado. Aqui el repo DECLARA cual es su
#      arbol (`core.worktree`, o un remoto que es una ruta local existente) y lo
#      que se le quiere versionar tiene que ser ese.
#
# La 1 se puede saltar con `--allow-cwd-externo`, que suena en el log. La 2 NO
# se puede saltar: no es una costumbre, es una incoherencia entre el repositorio
# y el arbol, y por eso es codigo 3 y no codigo 2.
#
# POR QUE CODIGO 3 y no 2 en la segunda: 3 es "no pude ni comprobar / no es
# utilizable", que es exactamente lo que ocurre --este repositorio no es el
# repositorio de este arbol--, y 2 es "tu invocacion esta mal", que aqui seria
# verdad y a la vez insuficiente: la invocacion seria la misma con el arbol
# correcto. Ademas la linea `WOPT_REPO_INVALIDO` es la que `--verify` ya sabe
# leer, luego el diagnostico no gana un caso nuevo.
MOTIVO_CWD_FUERA = (
    "estas fuera del proyecto: el directorio de trabajo es '<cwd>' y el arbol de "
    "este wrapper es '<raiz>'. El arbol es lo que versionan 'git add -A' y 'git "
    "commit', luego commitear desde aqui versiona un ARBOL AJENO. POR QUE importa: "
    "con el arbol derivado de '__file__' y el repositorio en una constante "
    "absoluta, una COPIA del proyecto en %TEMP% commitea en el historial real, y "
    "eso ya ha pasado tres veces en este repo. Lanza el wrapper desde la raiz del "
    "proyecto, o pon '--allow-cwd-externo' si sabes lo que haces: con el flag se "
    "sigue y queda el AVISO en el log"
)

MOTIVO_ARBOL_AJENO = (
    "este repositorio declara que su arbol es '<declarado>' y la invocacion "
    "pretende versionar '<arbol>'. Versionarlos juntos mete un arbol en el "
    "historial de otro. POR QUE importa: es el modo de fallo MEDIDO de este "
    "wrapper --el repositorio es una constante y el arbol se deriva de '__file__'--, "
    "y produce justo los 'arboles sucios que no sabes de donde vienen'. Si de verdad "
    "has movido el proyecto, cambia el arbol que declara el repo ('git config "
    "core.worktree <ruta>') en vez de forzar aqui el versionado"
)

# INFO (no rechazo) cuando el repo no declara su arbol. ASCII PURO.
AVISO_SIN_DECLARACION = (
    "el repositorio no declara que arbol es (ni 'core.worktree' ni un remoto que "
    "sea una ruta local existente), luego la alarma de correspondencia no puede "
    "comparar nada y la versionada. ES UN LIMITE DECLARADO, no una comprobacion: si "
    "este repo se usa con un arbol ajeno, la puerta no lo nota"
)

# `git config --get-regexp` devuelve `remote.<nombre>.url <valor>` por linea.
# Se filtra lo que parece una RUTA LOCAL: `C:/...`, `C:\...`, `/...` y el prefijo
# `file://`. Una URL de red (`https://github.com/...`) no declara un arbol de este
# host y se descarta, que es lo que evita tomar `origin` por el arbol.
_RE_REMOTO_LOCAL = re.compile(r"^(?:[A-Za-z]:[\\/]|[/\\]|file://)")



def detalle(texto, max_len=240):
    """Normaliza cualquier texto a una unica linea ASCII imprimible.

    La consola es cp1252 (trampa #16) y git puede emitir acentos, codigos de
    color ANSI o saltos de linea. Sin esta normalizacion, un `print()` revienta
    con UnicodeEncodeError justo en el mensaje de error, que es el que mas urge.
    """
    if not texto:
        return "sin detalle"
    limpio = _ANSI_RE.sub("", str(texto))
    limpio = limpio.replace("\r", " ").replace("\n", " ")
    limpio = limpio.encode("ascii", "replace").decode("ascii")
    limpio = " ".join(limpio.split())
    if len(limpio) > max_len:
        limpio = limpio[:max_len].rstrip() + "..."
    return limpio


def get_env():
    """`(env, paridad_rota)`: el entorno de git de todos los subprocesos.

    Precedencia, la MISMA para las dos variables: si el entorno ya trae
    `GIT_DIR` se respeta tal cual (es la via documentada en AGENTS.md y ademas el
    hook que permite tests hermeticos), y si no se fuerza el repo desacoplado de
    LOCALAPPDATA **aunque no exista**: asi la validacion falla con codigo 3 en vez
    de que git descubra en silencio el `.git` corrupto del arbol de trabajo
    (fallback prohibido por el contrato). Lo MISMO vale para `GIT_WORK_TREE`, que
    antes se imponia a `REPO_ROOT` sin condiciones.

    **La hermeticidad del hook es de REPO y de ARBOL, no solo de repo (TASK-061).**
    MEDIDO: con la imposicion incondicional, una sonda con `GIT_DIR` temporal
    stageaba y commiteaba el ARBOL DE TRABAJO REAL dentro del repo temporal, que es
    exactamente el mecanismo que produjo la contaminacion de `STATUS.md:23`. Honrar
    `GIT_WORK_TREE` sin mas seria un arma de doble filo (basta un `GIT_DIR` real +
    un arbol ajeno para versionar un arbol extranjero en el historial real), asi que
    la paridad es **el precio** de la decision, no un extra.

    Por eso `get_env()` **no puede callarse** de la asimetria: devuelve
    `paridad_rota` y `main()` la rechaza con el codigo 2 (`WOPT_USAGE paridad-git`),
    sin escribir nada. Una bandera interna en el propio `env` se perderia en
    cualquier reescritura futura de esta funcion; un valor de retorno se rompe en
    la firma, que es visible.
    """
    env = os.environ.copy()
    paridad_rota = bool(env.get("GIT_DIR")) != bool(env.get("GIT_WORK_TREE"))
    env["GIT_DIR"] = env.get("GIT_DIR") or LOCAL_GIT_DIR
    env["GIT_WORK_TREE"] = env.get("GIT_WORK_TREE") or REPO_ROOT
    return env, paridad_rota


def _canonica(ruta):
    r"""La ruta tal y como hay que COMPARARLAS: absoluta y normalizada.

    `normcase` en Windows pasa a minusculas y unifica separadores, luego
    `C:/Users/X` y `c:\users\x` son la misma. `realpath` NO se usa a proposito:
    resolver enlaces symbolically antes de comparar haria que dos rutas que
    git escribe de una manera y Python de otra dejaran de coincidir, y el fallo
    seria un falso 3.
    """
    return os.path.normcase(os.path.abspath(ruta))


def cwd_dentro_del_arbol(repo_root):
    """`(ok, cwd, raiz)`: quien llama esta dentro del arbol del proyecto.

    El caso normal del bucle es `cwd == raiz`: el orquestador commitea desde la
    raiz siempre, luego el coste de esta puerta es cero para el camino bueno y
    solo muerde a quien llama desde otro sitio. El criterio es de CONTENIDO
    (`cwd` dentro de `raiz`, no necesariamente igual), porque working en un
    subdirectorio del proyecto --`.agents/`, `docs/`-- es una invocacion
    legitima y no debe salir con 2.

    `os.getcwd()` puede fallar si el directorio actual se borro por debajo (un
    temporal de una sonda, tipico). No se inventa un valor: se devuelve `False`
    y el motivo, y `main()` lo tradujo al mismo rechazo que un cwd ajeno.
    """
    try:
        cwd = os.getcwd()
    except OSError as exc:
        return False, "", f"no se pudo leer el directorio de trabajo: {exc}"
    raiz = _canonica(repo_root)
    aqui = _canonica(cwd)
    return (aqui == raiz or aqui.startswith(raiz + os.sep)), cwd, raiz


def arboles_declarados_por_el_repo(env):
    """`[str]` de los arboles que el REPOSITORIO dice que son suyos.

    MEDIDO el 2026-10-08 sobre el repo real de este proyecto: `core.worktree`
    **no esta puesto** (`git config --get core.worktree` sale con 1) y lo que si
    hay es `remote.mirror-local.url=C:/Users/carch/Nextcloud/Scripts/woptimizer/`,
    que es la declaracion de que este repositorio y este arbol son el mismo
    par. Sin una fuente asi el par repo/arbol no tiene nada que contrastar y la
    alarma se queda muda, que es un limite DECLARADO (`AVISO_SIN_DECLARACION`),
    no una comprobacion que se pueda creer.

    Son DOS fuentes y en este orden: `core.worktree` (la de git) y los remotos
    que sean una ruta local existente. Se aceptan varias porque un repo puede
    tener mas de un clon local: basta con que el arbol de la invocacion sea UNO
    de los declarados. Una URL de red no cuenta, luego `origin` =
    `https://github.com/...` no puede pasar por arbol de este host.
    """
    declarados = []
    rc, out, err, exc = run_git(["config", "--get", "core.worktree"], env)
    if exc is None and rc == 0 and out.strip():
        declarados.append(out.strip().splitlines()[0].strip())

    rc, out, err, exc = run_git(
        ["config", "--get-regexp", r"^remote\..*\.url$"], env)
    if exc is None and rc == 0 and out.strip():
        for linea in out.splitlines():
            if " " not in linea:
                continue
            valor = linea.split(" ", 1)[1].strip().strip('"')
            if not _RE_REMOTO_LOCAL.match(valor):
                continue
            ruta = valor[len("file://"):] if valor.startswith("file://") else valor
            if os.path.isdir(ruta):
                declarados.append(ruta)
    return declarados


def ancla_del_arbol(env, git_dir):
    """`(ok, detalle)`: el repositorio y el arbol de la invocacion son el par.

    Devuelve `True` con un detalle informativo cuando no hay nada que oponer
    (el repo no declara arbol, limite declarado y escrito). Devuelve `False` con
    el motivo cuando el repo declara un arbol y este NO es el que se va a
    versionar, que es el caso medido de `a5de331`.

    **Solo lectura**: pregunta al repo con `git config` y no escribe ni un
    fichero, ni un ancla, ni un config. La version con escritura (un fichero de
    ancla DENTRO del `GIT_DIR`) se descarto a proposito: en un repo recien
    clonado el ancla no existe todavia, luego la crearia la PRIMERA invocacion,
    y si esa primera invocacion es la de una camara en `%TEMP%` deja el repo real
    anclado al arbol de la camara y a partir de ahi rechaza al arbol bueno. Un
    ancla que se escribe a si misma es un ancla que envenena.
    """
    arbol = _canonica(env.get("GIT_WORK_TREE") or REPO_ROOT)
    declarados = arboles_declarados_por_el_repo(env)
    if not declarados:
        return True, ("sin declaracion: el repositorio no dice que arbol es, "
                      "luego no hay nada que comparar")
    for declarado in declarados:
        if _canonica(declarado) == arbol:
            return True, f"declarado: {declarado}"
    return False, (
        f"el repositorio '{git_dir}' declara como suyo el arbol "
        f"'{declarados[0]}' y la invocacion pretende versionar '{arbol}'"
    )


def run_git(args, env):
    """Ejecuta `git` y devuelve (rc, out, err, exc).

    `rc` es None cuando git NO llego a ejecutarse (excepcion de Python: no
    instalado, OSError, sandbox...). Esa distincion importa: "git fallo" es
    codigo 1, pero "no pude ni comprobar" es codigo 3. Colapsar los dos casos en
    el mismo 1 era el agujero que el contrato 3.4 corrige.

    El `cwd` de cada subproceso **se deriva del propio `env`** (`GIT_WORK_TREE`),
    no de `REPO_ROOT` fijo (TASK-061). Es lo que hace que honar `GIT_WORK_TREE`
    sea verdad de verdad y no a medias: MEDIDO, con `cwd=REPO_ROOT` y un work tree
    temporal, `rev-parse --is-inside-work-tree` responde `false` —el directorio de
    trabajo no esta dentro del work tree efectivo— y `validar_repo` rechazaba con
    el codigo 3 la propia invocacion que se le acababa de pedir. Correr git desde
    el work tree efectivo es ademas lo coherente con que `add -A` y `commit`
    operen sobre el. En el camino normal (`GIT_WORK_TREE = REPO_ROOT`) el valor es
    el mismo de siempre, byte a byte. `validar_repo` comprueba que ese directorio
    EXISTE antes de llegar aqui, luego el `cwd` de aqui siempre existe.
    """
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=env.get("GIT_WORK_TREE") or REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip(), None
    except Exception as e:
        return None, "", "", str(e)


def validar_repo(env):
    """Valida el repo efectivo. Devuelve (ok, detalle_error, git_dir_real).

    Es la UNICA validacion del wrapper: la usan igual el camino principal y
    `--verify`, de modo que el diagnostico nunca puede divergir del comportamiento
    real. Es de solo lectura (solo `rev-parse`) y no acepta una excepcion como
    "repo valido": `os.path.isdir` no basta, hay que preguntar a git.

    Valida **el par entero** (TASK-061): el repositorio Y el arbol de trabajo
    efectivo. Sin la comprobacion del arbol, un `GIT_WORK_TREE` a una ruta
    inexistente caeria en un `rc` de git que nadie ha medido, y el codigo 3 tiene
    que ser "no pude ni comprobar" de forma **determinista**, no "git dijo algo
    raro".
    """
    git_dir = env.get("GIT_DIR") or LOCAL_GIT_DIR
    if not os.path.isdir(git_dir):
        return False, f"GIT_DIR no existe o no es un directorio: {git_dir}", git_dir

    work_tree = env.get("GIT_WORK_TREE") or REPO_ROOT
    if not os.path.isdir(work_tree):
        return False, (
            f"GIT_WORK_TREE no existe o no es un directorio: {work_tree}"
        ), git_dir

    rc, out, err, exc = run_git(["rev-parse", "--git-dir"], env)
    if exc is not None:
        return False, f"git no ejecutable: {detalle(exc)}", git_dir
    if rc != 0 or not out:
        return False, f"rev-parse --git-dir fallo (rc={rc}): {detalle(err or out)}", git_dir
    git_dir_real = out

    rc, out, err, exc = run_git(["rev-parse", "--is-inside-work-tree"], env)
    if exc is not None:
        return False, f"git no ejecutable: {detalle(exc)}", git_dir
    if rc != 0 or out.strip().lower() != "true":
        return False, (
            f"is-inside-work-tree no es true (rc={rc}, out='{detalle(out)}'): {detalle(err)}"
        ), git_dir_real

    rc, out, err, exc = run_git(["rev-parse", "--verify", "HEAD"], env)
    if exc is not None:
        return False, f"git no ejecutable: {detalle(exc)}", git_dir
    if rc != 0 or not out:
        return False, f"HEAD no resuelve (rc={rc}): {detalle(err or out)}", git_dir_real

    return True, "", os.path.abspath(git_dir_real)


def parse_args(argv):
    """Devuelve (verify, allow_cwd_externo, mensaje, error_de_uso)."""
    verify = False
    allow_cwd_externo = False
    posicionales = []
    for arg in argv:
        if arg == "--verify":
            verify = True
        elif arg == "--allow-cwd-externo":
            allow_cwd_externo = True
        elif arg.startswith("-"):
            return False, False, None, f"flag desconocido: {arg}"
        else:
            posicionales.append(arg)

    if verify and posicionales:
        return False, allow_cwd_externo, None, "--verify no admite un mensaje de commit"
    if len(posicionales) > 1:
        return False, allow_cwd_externo, None, "se esperaba un unico mensaje entrecomillado"
    mensaje = posicionales[0].strip() if posicionales else ""
    if not verify and not mensaje:
        return False, allow_cwd_externo, None, "falta el mensaje de commit (o esta vacio)"
    return verify, allow_cwd_externo, mensaje, None


def ancla_del_mensaje(mensaje, ids):
    """`(ok, motivo)`: el mensaje lleva identificador de ciclo o de tarea.

    PURA por construccion: recibe el mensaje y el CONJUNTO de ids y no lee
    ficheros ni llama a `subprocess`. Por eso se puede probar entera sin
    escribir nada (limite 1 de la propuesta: el arbol de trabajo no es
    controlable desde fuera del wrapper, luego lo unico hermetico es la funcion
    extraida y la posicion de su llamada, que se afirma con `ast`).

    `ids` es el conjunto de identificadores RESUELTOS de `.taskmaster/tasks.json`
    (`ids_de_tareas`). La resolubilidad se exige porque es lo que convierte el
    identificador en un ancla y no en una decoracion: `"chore: TASK-999"` tiene
    la forma correcta y no apunta a nada, asi que NO pasa.

    Tres convenciones de mensaje, dos RESOLUBLES: primero `TASK-`, que es la unica
    que se puede resolver, luego `CYCLE-NNN` y el marcador de ciclo. Se recorre
    TODAS las menciones de `TASK-` en vez de quedarse con la primera, porque un
    mensaje que dice "arrastra TASK-999 de TASK-059" tiene un ancla real al final
    y negarsela seria un falso rojo.

    `ids` VACIO ES FAIL-CLOSED, y lo que hace esta MEDIDO (2026-10-04, corrigiendo
    la auditoria del ciclo 52 que lo dio por fail-open): con `ids=set()`,
    `"chore: TASK-059"` -> `False` y `"chore: TASK-999"` -> `False`. NO degrada a
    la forma: **deja de aceptar `TASK-` por completo**, porque el `in` sobre un
    conjunto vacio no encuentra nada. Solo las dos convenciones de ciclo siguen
    pasando, y no dependen de ficheros. Es decir: con `tasks.json` roto la puerta
    **para al bucle** (un mensaje con `TASK-NNN` sale con 2) y **deja pasar** los
    mensajes que llevan ciclo.

    Y es la decision correcta, aunque pese: la alternativa (aceptar `TASK-NNN` por
    su forma cuando el fichero no se puede leer) es **exactamente el punto ciego
    que esta tarea cierra**: un identificador que nadie puede resolver no es un
    ancla, es una decoracion, y aceptarla por su forma devuelve el proyecto al
    estado previo. Un `except` que devolviera "todo valido" seria peor todavia.
    El precio es que un `tasks.json` roto **detiene el bucle**, y eso es visible al
    instante: el `INFO` lo dice con el motivo literal y el siguiente mensaje con
    `ciclo N` pasa igual, luego el bucle nunca queda sin salida. Fijado por test en
    `run_tests.py` -> `test_la_puerta_del_mensaje_exige_un_ancla_resoluble` y
    `test_los_ids_del_bolsillo_se_leen_y_la_puerta_no_se_degrada_a_forma`.
    """
    texto = mensaje or ""
    for encontrado in _RE_TASK_ANCLA.finditer(texto):
        if "TASK-" + encontrado.group(1) in ids:
            return True, ""
    if _RE_CYCLE_ANCLA.search(texto):
        return True, ""
    if _RE_MARCADOR_ANCLA.search(texto):
        return True, ""
    return False, MOTIVO_SIN_ANCLA


def ids_de_tareas():
    """`(ids, aviso)` leidos de `.taskmaster/tasks.json`. -> `set[str]`.

    `aviso` es `None` cuando todo fue bien y un texto de UNA linea cuando no: el
    llamante lo imprime como `INFO` ANTES de la linea `WOPT_*`, que tiene que
    quedar la ultima (regla 4 del contrato). El aviso existe porque degradar en
    silencio es INVISIBLE: con `ids` vacio la puerta deja de aceptar `TASK-`
    (fail-closed, ver `ancla_del_mensaje`), asi que el bucle se para, y si eso no
    se dice en voz alta el agente lee un codigo 2 sin entender por que.

    El aviso NO dice "exige la forma pero no la resolubilidad": eso afirmaba antes
    y es FALSO (medido el 2026-10-04: con `ids` vacio, `TASK-059` NO pasa). Dice
    lo que ocurre de verdad: `TASK-` no se acepta y las convenciones de ciclo
    siguen valiendo. Un aviso que describe un comportamiento que el codigo no
    tiene es peor que no dar aviso: manda a leer el codigo y a no fiarse de el.
    """
    ruta = os.path.join(REPO_ROOT, ".taskmaster", "tasks.json")
    try:
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError) as exc:
        return set(), (
            f".taskmaster/tasks.json ilegible ({type(exc).__name__}: {exc}); con el "
            "bolsillo ilegible la puerta es FAIL-CLOSED: 'TASK-NNN' deja de pasar "
            "por completo porque no se puede resolver. Los mensajes con 'ciclo N' o "
            "'CYCLE-NNN' siguen valiendo, que no dependen de este fichero"
        )

    tareas = datos.get("tasks") if isinstance(datos, dict) else datos
    ids = set()
    if isinstance(tareas, list):
        for tarea in tareas:
            if isinstance(tarea, dict) and isinstance(tarea.get("id"), str):
                ids.add(tarea["id"].strip().upper())
    if isinstance(datos, dict) and isinstance(datos.get("active_task_id"), str):
        # `active_task_id` es tambien un id que EXISTE en el fichero, y el
        # orquestador lo escribe a mano en sus mensajes.
        ids.add(datos["active_task_id"].strip().upper())

    if not ids:
        return set(), (
            ".taskmaster/tasks.json no aporta ningun id utilizable; la puerta exige "
            "solo la FORMA del identificador"
        )
    return ids, None


# --- La puerta de la cabecera (TASK-066) ------------------------------------
#
# Copia del criterio de commitlint, LEIDO de su codigo y no supuesto. Las
# cuatro fuentes, para que un cambio de criterio sea rastreable en vez de
#opinionado:
#
#   - parse:  `@commitlint/parse` usa `conventional-changelog-angular`, cuyo
#             `headerPattern` es `/^(\w*)(?:\((.*)\))?!?: (.*)$/` con
#             `headerCorrespondence` [type, scope, subject]. Si el patron NO
#             casa, `type` y `subject` quedan a **null**.
#   - case:   `@commitlint/ensure/src/case.ts` borra `x` / "x" / 'x', hace
#             `trim`, y compara `toCase(entrada, objetivo) === entrada`, con DOS
#             excepciones: si el resultado es "" o **empieza por digito**
#             devuelve True (indeterminado, y por eso pasa).
#   - toCase: `@commitlint/ensure/src/to-case.ts`: `upper-case` es
#             `toUpperCase()` de **TODA** la cadena; `pascal-case` es
#             `upperFirst(camelCase(entrada))`.
#   - regla:  `@commitlint/rules/src/subject-case.ts`: si el subject NO empieza
#             por una letra CON CASO (`\p{Ll}\p{Lu}\p{Lt}`) la regla PASA sin
#             mirar; si empieza, `never` falla en cuanto `ensureCase` dice que
#             ES uno de los cases.
#
# MEDIDO (2026-10-05) y escrito porque es contraintuitivo: `subject-case` **no**
# es "no empezar por mayuscula". Rechaza el subject **entero** en mayusculas y
# el subject en PascalCase; uno que solo empieza en mayuscula y lleva espacios
# ("T-9 afirma el invariante") PASA. La premisa de que el primer caracter es lo
# que se mira era FALSA, y con ella la cuenta de commits rojos del rango
#historico: son 7, no 8.
LIMITE_CABECERA = 120
# Ramas por las que sale una version ESTABLE. Estar en una de ellas es AVISO,
# no rechazo (proposal.md seccion 3.2). La razon esta en el docstring del
# contrato: un `sys.exit` aqui solo guardaria el wrapper y bloquearia el commit
# legitimo del dueno en la rama de release.
RAMAS_DE_PUBLICACION = ("main",)
TIPOS_ADMITIDOS = (
    "feat", "fix", "docs", "style", "refactor", "perf",
    "test", "build", "ci", "chore", "revert",
)
# `\w` NO incluye `/`, asi que `feat/fix: ...` NO casa con el patron y el `type`
# queda a null: eso es lo que hace que el job `commits` lo rechace.
_RE_CABECERA = re.compile(r"^(\w*)(?:\((.*)\))?!?: (.*)$")
# Lo que `case.ts` borra antes de comparar cualquier cosa.
_RE_COTILLAS = re.compile(r"`.*?`|\".*?\"|'.*?'", re.DOTALL)
# Palabras de `camelCase`: mayusculas en serie, o mayuscula+minusculas, o
# minusculas/digitos. Es la aproximacion de `es-toolkit` para los casos que
# aparecen en este repo.
_RE_PALABRAS = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+")

# El rechazo de longitud, en la FORMA que pide el contrato: que se espera y
# medicion. ASCII PURO (trampa #16, consola cp1252). Nombra la regla de
# `.commitlintrc.json` de la que sale, para que corregir el mensaje no obligue a
# abrir el codigo.
MOTIVO_CABECERA_LARGA = (
    "la cabecera pasa de 120 caracteres y el job 'commits' de "
    ".github/workflows/release.yml tumba la corrida entera con eso. Se espera "
    "una cabecera de 120 caracteres o menos, con el tipo pegado al subject por "
    "': ' y el ancla al final. POR QUE importa: sin esta puerta un mensaje de "
    "135 caracteres si puede existir, y el dia que puede volver a existir vuelve "
    "el rojo --'commits' tumba la corrida, y 'verify', 'release' y 'build' no "
    "llegan a correr, asi que tampoco sale el .exe. Ancla tu mensaje y acortalo"
)

# El rechazo de las otras cinco reglas. El nombre de la regla va DENTRO del
# mensaje porque es lo que hay que arreglar, y el texto dice que hacer con ella.
MOTIVO_CABECERA_REGLA = {
    "type-empty": (
        "la cabecera no tiene tipo. El job 'commits' espera un conventional "
        "commit que empiece por 'tipo: ' o 'tipo(scope): '. Revisa que el tipo "
        "esté pegado al subject con ': ' y con un solo espacio"
    ),
    "type-enum": (
        "el tipo no es uno de los que admite la regla 'type-enum' de "
        ".commitlintrc.json. Ojo con los tipos compuestos: 'feat/fix: ...' NO "
        "parsea, porque '/' no es un caracter de tipo para el parser de CI, y "
        "el tipo tiene que ser UNO de los de la lista. Pon el tipo que "
        "corresponda al cambio y ya"
    ),
    "type-case": (
        "el tipo no va en minusculas, y la regla 'type-case' lo exige. "
        "Escribe 'fix', no 'Fix' ni 'FIX'"
    ),
    "subject-empty": (
        "la cabecera no tiene subject: sobra el ': ' o falta el texto detras. "
        "El job 'commits' espera 'tipo(scope): texto' con texto no vacio"
    ),
    "subject-case": (
        "el subject va enteramente en mayusculas o en PascalCase, y la regla "
        "'subject-case' lo prohibe. Ponlo en minusculas, con solo la primera "
        "palabra en mayuscula si hace falta. Ojo: lo que se prohibe aqui es el "
        "subject ENTERO en mayusculas, no empezar por mayuscula, asi que "
        "'T-9 afirma el invariante' es valido y 'T-9 AFIRMA EL INVARIANTE' no"
    ),
}


def _empieza_con_letra_con_caso(texto):
    r"""El `\p{Ll}\p{Lu}\p{Lt}` de `subject-case.ts`, sin `regex` de terceros.

    Lo que importa es distinguir una letra **con caso** de una que no lo tiene:
    `str.isupper()` y `str.islower()` de Python son las dos False en una letra
    `Lo` (otras letras, p. ej. las de los alfabetos sin caja), y para `subject-case`
    esas NO cuentan. El modulo `re` de la biblioteca estandar no entiende `\p{}`.
    """
    if not texto:
        return False
    primero = texto[0]
    if not primero.isalpha():
        return False
    return primero.isupper() != primero.islower()


def _camel_case(texto):
    partes = _RE_PALABRAS.findall(texto)
    if not partes:
        return texto
    return partes[0].lower() + "".join(
        p[:1].upper() + p[1:] for p in partes[1:]
    )


def _ensure_case(texto, objetivo):
    """`(bool)` de `ensureCase` de commitlint. Copia, no aproximacion.

    Incluye las DOS excepciones de `case.ts`, que son las que hacen que un
    subject que empieza por digito pase siempre.
    """
    entrada = _RE_COTILLAS.sub("", texto or "").strip()
    if objetivo == "upper-case":
        transformado = entrada.upper()
    elif objetivo == "pascal-case":
        camel = _camel_case(entrada)
        transformado = camel[:1].upper() + camel[1:]
    else:
        transformado = entrada.lower()
    if transformado == "" or transformado[0].isdigit():
        return True
    return transformado == entrada


def clasificar_cabecera(mensaje):
    """`(ok, codigo_regla, texto)`: el PRIMER fallo de las 6 reglas de nivel 2.

    PURA por construccion: sin `subprocess`, sin ficheros y sin leer
    `.commitlintrc.json` en caliente. Por eso se prueba entera sin escribir
    nada. Que NO lea la config es deliberado: leerla en caliente haria que en un
    repo sin `.commitlintrc.json` la puerta se quedaria muda y verde, que es
    la misma clase de fallo que la puerta de ancla sufrio con un
    `tasks.json` ilegible. Para que los numeros no se separen de la config,
    `run_tests.py` -> `test_la_puerta_de_cabecera_usa_las_cuentas_de_la_config`
    compara estas constantes con `.commitlintrc.json`: si alguien cambia el
    limite ahi, este test se pone rojo en el acto.

    `codigo_regla` es el nombre EXACTO de la regla de `.commitlintrc.json` que
    incumple, y va en el mensaje del rechazo, porque es lo que hay que
    arreglar. Se devuelve el PRIMER fallo en el ORDEN del fichero de config,
    no en el orden en que las mira CI: el orden de la config es el unico
    criterio estable y escribible, y el motivo de rechazo no depende de el.
    """
    texto = mensaje or ""
    cabecera = texto.split("\n", 1)[0]

    tipo = _scope = _subject = None
    encontrada = _RE_CABECERA.match(cabecera)
    if encontrada:
        tipo, _scope, _subject = encontrada.group(1), encontrada.group(2), encontrada.group(3)

    # 1. type-empty
    if not tipo:
        return False, "type-empty", MOTIVO_CABECERA_REGLA["type-empty"]
    # 2. type-enum
    if tipo not in TIPOS_ADMITIDOS:
        return False, "type-enum", MOTIVO_CABECERA_REGLA["type-enum"]
    # 3. type-case (lower-case)
    if not _ensure_case(tipo, "lower-case"):
        return False, "type-case", MOTIVO_CABECERA_REGLA["type-case"]
    # 4. subject-empty
    if not _subject:
        return False, "subject-empty", MOTIVO_CABECERA_REGLA["subject-empty"]
    # 5. subject-case: [2, never, [upper-case, pascal-case]]
    if _empieza_con_letra_con_caso(_subject):
        for caso in ("upper-case", "pascal-case"):
            if _ensure_case(_subject, caso):
                return False, "subject-case", MOTIVO_CABECERA_REGLA["subject-case"]
    # 6. header-max-length: mide la PRIMERA LINEA, no el mensaje entero.
    if len(cabecera) > LIMITE_CABECERA:
        return False, "header-max-length", MOTIVO_CABECERA_LARGA
    return True, "", ""


def rama_actual(env):
    """`(ok, rama)`: la rama en la que se va a escribir.

    MEDIDO: `git_safe_commit.py` no tenia ni una coincidencia de `branch`, asi
    que la pregunta "en que rama estoy escribiendo" no tenia respuesta en la
    salida. `INFO rama:` la hace respondible y es la precondicion legible del
    AVISO de TASK-066. Se lee UNA vez, y si no resuelve se dice `desconocida`
    en vez de inventar un valor: un `INFO` que dice una rama que no es la suya
    es peor que un `INFO` que no sale.
    """
    rc, out, err, exc = run_git(["rev-parse", "--abbrev-ref", "HEAD"], env)
    if exc is not None or rc != 0 or not out:
        return False, "desconocida"
    return True, out.splitlines()[0].strip()


def imprimir_uso():
    print('Uso: python .taskmaster/git_safe_commit.py "tipo(scope): descripcion (TASK-NNN)"')
    print("     python .taskmaster/git_safe_commit.py --verify")
    print()
    print("EL WRAPPER TIENE QUE LLAMARSE DESDE LA RAIZ DEL PROYECTO (TASK-072):")
    print("  el arbol de trabajo es lo que versionan 'git add -A' y 'git commit', y")
    print("  con el arbol derivado de '__file__' y el repositorio en una constante")
    print("  absoluta, commitear desde una COPIA del proyecto en %TEMP% escribe en el")
    print("  historial real. Desde fuera de la raiz se sale con 2; con")
    print("  '--allow-cwd-externo' se sigue y queda el AVISO en el log.")
    print()
    print("El mensaje LLEVA IDENTIFICADOR, y el wrapper lo exige (TASK-059):")
    print("  'TASK-NNN'  existente en .taskmaster/tasks.json   (p. ej. '(TASK-059)')")
    print("  'CYCLE-NNN'                                       (p. ej. 'CYCLE-059')")
    print("  'ciclo N'                                         (p. ej. 'ciclo 59')")
    print("Sin identificador el commit no tiene tercer testigo y se rechaza con 2.")
    print()
    print("El mensaje TAMBIEN tiene que ser un conventional commit valido, y lo exige")
    print("el mismo criterio que el job 'commits' de .github/workflows/release.yml")
    print("(TASK-066). Se rechaza con 2, y las reglas son las de .commitlintrc.json:")
    print("  header-max-length  la cabecera (primera linea) no pasa de 120 caracteres")
    print("  type-enum          el tipo es uno de: " + ", ".join(TIPOS_ADMITIDOS))
    print("  type-case          el tipo va en minusculas")
    print("  type-empty         hay tipo")
    print("  subject-empty      hay subject")
    print("  subject-case       el subject NO va en mayusculas ni en PascalCase")
    print("El tipo va pegado al subject con ': ', y el scope opcional entre parentesis:")
    print('  "fix(tooling): cerrar la puerta de versionado (TASK-061)"')
    print("Un tipo con barra NO parsea -- 'feat/fix: ...' no es conventional commit y")
    print("se rechaza, porque el '/' no es un caracter de tipo para el parser de CI.")
    print()
    print("La RAMA no se rechaza: estar en 'main' imprime un AVISO y se sigue con 0.")
    print("El bucle trabaja en 'beta'; 'main' solo recibe 'beta' por fast-forward.")


def main():
    verify, allow_cwd_externo, mensaje, error_uso = parse_args(sys.argv[1:])
    if error_uso:
        imprimir_uso()
        print(f"WOPT_USAGE {detalle(error_uso)}")
        sys.exit(CODE_USAGE)

    env, paridad_rota = get_env()
    ok, fallo_repo, git_dir = validar_repo(env)

    # 0. PUERTA DE PARIDAD (TASK-061), y desde TASK-074 la PRIMERA puerta que
    #    puede rechazar. Va DESPUES de `validar_repo` (que no imprime: ver el
    #    test AST `...va_despues_de_validar_repo_por_estructura`) y ANTES de todo
    #    lo demas: del NOOP, de `add -A`, del `WOPT_REPO_OK` de `--verify` y del
    #    `3` del repo. Los cuatro sitios importan y estan medidos:
    #    - despues de `validar_repo`: MEDIDO, es la UNICA diferencia de este
    #      bucle que ninguna sonda de comportamiento puede ver, porque
    #      `validar_repo` no imprime ni escribe: el mutante M5 es EQUIVALENTE
    #      y por eso la posicion se ata con `ast` y no con un codigo de salida;
    #    - ANTES del `if verify and not ok` (TASK-074): con par asimetrico y repo
    #      no verificable el 3 describiria un problema del repo que nadie ha
    #      mirado de verdad, porque `validar_repo` miraria un par IMPUESTO
    #      (`work_tree = env.get("GIT_WORK_TREE") or REPO_ROOT`), no el del
    #      llamante, que es justamente la situacion que la alarma de ancla
    #      (`ancla_del_arbol`, TASK-072) declara rota. MEDIDO el 2026-10-18 en
    #      las ocho celdas (commit | `--verify`) x (paridad rota | entera) x
    #      (repo verificable | no): este orden cambia UNA sola celda, la de
    #      `--verify` + par roto + repo roto, que pasa de 3 a 2, y 2 es el
    #      remedio correcto ("pon las dos variables") porque el par es la causa
    #      primaria. Ademas el 2 no depende de git: `paridad_rota` se calcula
    #      leyendo `os.environ` (`get_env()`), luego una precondicion que se
    #      comprueba sin salir del proceso no puede ir detras de una que
    #      necesita salir;
    #    - antes del NOOP: es de SOLO LECTURA, luego un arbol limpio con el par
    #      asimetrico sale con 2 sin haber stageado nada (rechazar despues de
    #      `add -A` seria mutar el arbol para luego decir que no);
    #    - antes de `WOPT_REPO_OK`: `--verify` que dice "el repo y su arbol son
    #      usables" no puede contar una asimetria de ese par, que es justo la
    #      mentira que un diagnostico no debe decir.
    if paridad_rota:
        print(f"WOPT_USAGE paridad-git {detalle(MOTIVO_PARIDAD_ROTA)}")
        sys.exit(CODE_USAGE)

    # El repo no verificable se juzga DESPUES de la invocacion (TASK-074), con
    # la precedencia que fijo D2 de TASK-059 y ahora CON UNA CONDICION que el
    # propio D2 no tenia: el 3 ("no pude ni comprobar") gana al 2 ("tu
    # invocacion esta mal") solo CUANDO EL PAR ES ENTERO. Con media pareja ya
    # ha salido el 2 de la puerta de paridad, y sin esa condicion el 3
    # describiria un problema del repo que en realidad nunca llego a mirarse:
    # `validar_repo` habria mirado el par IMPUESTO por `get_env()` (repo y
    # arbol por defecto), no el que pidio el llamante, luego su veredicto
    # hablaria de un repositorio que nadie eligio. MEDIDO el 2026-10-18: con el
    # par entero las cuatro celdas de repo no verificable siguen dando 3, que
    # es lo que prometen `run_tests.py:1600` y este mismo docstring.
    if verify and not ok:
        print(f"WOPT_REPO_INVALIDO {detalle(fallo_repo)}")
        sys.exit(CODE_REPO)

    # 0bis. ALARMA DE UBICACION, LA DEL CWD (TASK-072 ronda 3). Va al lado de
    #      la de paridad y por el mismo motivo: es de SOLO LECTURA, ocurre antes
    #      del NOOP y antes de `add -A`, y en `--verify` tambien, porque un
    #      "`WOPT_REPO_OK`" no puede ser el diagnostico de alguien que esta
    #      versionando desde un directorio que no es el proyecto.
    #
    #      El caso normal del bucle es `cwd == REPO_ROOT` (el orquestador
    #      commitea desde la raiz), luego el coste es cero para el camino bueno.
    dentro, cwd, raiz = cwd_dentro_del_arbol(REPO_ROOT)
    if not dentro:
        if not allow_cwd_externo:
            motivo = MOTIVO_CWD_FUERA
            if cwd:
                motivo = motivo.replace("<cwd>", detalle(cwd)).replace(
                    "<raiz>", detalle(raiz))
            else:
                # `os.getcwd()` no se pudo leer: mismo rechazo, con el motivo
                # real en lugar de dos marcadores de plantilla.
                motivo = ("no se pudo resolver el directorio de trabajo: "
                          + detalle(raiz) + "; " + MOTIVO_CWD_FUERA)
            print(f"WOPT_USAGE cwd-fuera-de-raiz {detalle(motivo)}")
            sys.exit(CODE_USAGE)
        print(f"AVISO cwd: '{detalle(cwd)}' esta FUERA del arbol del proyecto "
              f"'{detalle(raiz)}' y se sigue porque se paso "
              "'--allow-cwd-externo'.")
        print("AVISO POR QUE esto NO se rechaza: la alarma existe porque con el "
              "arbol derivado de '__file__' y el repositorio en una constante "
              "absoluta, commitear desde una copia del proyecto en %TEMP% escribe "
              "en el historial real. Si has llegado aqui sin saber por que, quita "
              "el flag y lanza el wrapper desde la raiz del proyecto.")

    # 0ter. ALARMA DE UBICACION, LA DEL PAR REPO/ARBOL (TASK-072 ronda 3). La
    #       que cierra el caso MEDIDO (`a5de331`): el cwd SI estaba dentro del
    #       arbol de la camara, luego la alarma de arriba, sola, no lo habria
    #       cerrado. Aqui lo que se comprueba es que el repositorio y el arbol
    #       sean EL MISMO par, y sale con 3 (`WOPT_REPO_INVALIDO`) porque no es
    #       un problema de la invocacion: es que este repositorio no es el
    #       repositorio de este arbol.
    #
    #       Va DESPUES de las alarmas de uso (codigo 2) y ANTES del NOOP y de
    #       `add -A`, como las demas: es de SOLO LECTURA y un rechazo no muta el
    #       arbol ni el indice.
    ok_ancla, detalle_ancla = ancla_del_arbol(env, git_dir)
    if not ok_ancla:
        print(f"WOPT_REPO_INVALIDO {detalle(detalle_ancla)}. {detalle(MOTIVO_ARBOL_AJENO)}")
        sys.exit(CODE_REPO)
    if detalle_ancla.startswith("sin declaracion"):
        print(f"INFO ancla-arbol: {detalle(detalle_ancla)}. "
              f"{detalle(AVISO_SIN_DECLARACION)}")
    else:
        print(f"INFO ancla-arbol: {detalle(detalle_ancla)}")

    if verify:
        # Modo diagnostico: misma validacion, cero escrituras.
        print(f"WOPT_REPO_OK {git_dir}")
        sys.exit(CODE_OK)

    if not ok:
        # Sin fallback: el .git del arbol de trabajo esta corrupto en VFS.
        print(f"WOPT_REPO_INVALIDO {detalle(fallo_repo)}")
        print("INFO no se intenta el .git del arbol de trabajo: fallback prohibido.")
        sys.exit(CODE_REPO)

    print(f"INFO git_dir en uso: {git_dir}")

    # La rama, leida UNA vez y temprano, para que `INFO rama:` sea la
    # precondicion legible del AVISO de TASK-066. MEDIDO: hasta TASK-066 el
    # wrapper era ciego a la rama (cero coincidencias de `branch`), y el bucle
    # llevaba 52 ciclos comiteando en `main` sin que ninguna salida lo dijera.
    # Se imprime ANTES del NOOP y de las puertas para que tambien salga cuando
    # el commit se rechaza: un rechazo con la rama a la vista es diagnosticable,
    # y uno sin ella obliga a abrir otra terminal para averiguar donde estas.
    ok_rama, rama = rama_actual(env)
    print(f"INFO rama: {detalle(rama)}")
    if rama in RAMAS_DE_PUBLICACION:
        # AVISO, y se sigue con 0. Ver el docstring del contrato de codigos.
        print(f"AVISO rama: '{detalle(rama)}' es una rama de PUBLICACION y aqui "
              f"se va a escribir un commit del bucle.")
        print("AVISO la regla de TASK-066 dice que el bucle comitea y empuja a "
              "'beta', y que 'main' es la rama de publicacion y solo recibe "
              "'beta' por fast-forward.")
        print("AVISO POR QUE esto NO se rechaza: un rechazo aqui solo guardaria "
              "el wrapper y bloquearia el commit legitimo del dueno en la rama "
              "de release, que es justo el caso para el que 'main' existe. El "
              "que se rechaza es el mensaje, no la rama. La regla esta escrita "
              "en .agents/skills/id-pipeline/SKILL.md (0-bis), .agents/agents/"
              "openspec-dev/agent.md, AGENTS.md y docs/ai/release-pipeline.md "
              "(2.1).")
        if not ok_rama:
            print("AVISO no se pudo resolver la rama con git, asi que este "
                  "AVISO sale del nombre que el wrapper cree, no de una "
                  "medida: creelo con la prudencia de un aviso.")

    # 1. status --porcelain como fast path. Un status FALLIDO es un error, no
    #    "hay cambios": la version anterior hacia justo eso y segua hacia add.
    rc, out, err, exc = run_git(["status", "--porcelain"], env)
    if exc is not None or rc != 0:
        print(f"WOPT_FAIL status {detalle(exc or err or out)}")
        sys.exit(CODE_FAIL)
    if not out:
        print("WOPT_NOOP arbol limpio (status --porcelain vacio)")
        sys.exit(CODE_OK)

    # 2. PUERTA DEL MENSAJE (TASK-059). Va DESPUES de `validar_repo` y del NOOP
    #    y ANTES de `add -A`, y el orden se mide contra el codigo real:
    #    antes de `validar_repo` rompia el contrato (un `GIT_DIR` invalido con
    #    cualquier mensaje salia con 3 y pasaria a 2: "no pude ni comprobar" y
    #    "tu invocacion esta mal" son dos diagnosticos distintos, y confundirlos
    #    entrena al orquestador a mirar el repo cuando el problema es su cadena);
    #    despues de `add -A` rechazaria con el arbol ya stageado, es decir, mutaria
    #    el arbol para luego decir que no. Aqui es de SOLO LECTURA y cae antes de
    #    la primera escritura. Un arbol limpio sigue diciendo WOPT_NOOP + 0: un
    #    no-op no tiene commit que anclar, y rechazarlo seria ruido que el
    #    orquestador leeria como "el commit fallo".
    ids, aviso_ids = ids_de_tareas()
    if aviso_ids:
        print(f"INFO ancla-mensaje: {detalle(aviso_ids)}")
    ok_ancla, motivo_ancla = ancla_del_mensaje(mensaje, ids)
    if not ok_ancla:
        # Codigo 2 y NO 1 (D3): la puerta no ejecuta ninguna operacion de git, y
        # un `WOPT_FAIL ancla-mensaje` seria indistinguible de un fallo de git
        # para el unico consumidor real del codigo, que ramifica por el codigo.
        print(f"WOPT_USAGE ancla-mensaje {detalle(motivo_ancla)}")
        sys.exit(CODE_USAGE)

    # 2bis. PUERTA DE LA CABECERA (TASK-066). Mismo sitio y mismo codigo que la
    #      de ancla, y por el mismo motivo: DESPUES de `validar_repo` y del
    #      NOOP, y ANTES de `add -A`. Aqui es de SOLO LECTURA y cae antes de la
    #      primera escritura, luego un rechazo no muta el arbol. Ponerla
    #      despues de `add -A` rechazaria con el indice ya modificado, que es el
    #      error que ya se cometio una vez con la puerta de ancla y que por eso
    #      el sitio esta dicho con su porque.
    #
    #      `--verify` NO pasa por aqui: es un diagnostico del repo y no lleva
    #      mensaje, asi que no hay cabecera que clasificar.
    ok_cabecera, regla_cabecera, motivo_cabecera = clasificar_cabecera(mensaje)
    if not ok_cabecera:
        # Codigo 2 y NO 1, por el mismo motivo que la puerta de ancla: la puerta
        # no ejecuta ninguna operacion de git, y un `WOPT_FAIL` seria
        # indistinguible de un fallo de git para el unico consumidor que ramifica
        # por el codigo.
        #
        # El `sys.exit` va DENTRO de cada rama y no despues del `if/else`: el
        # contrato dice que una linea `WOPT_*` cierra una salida EN SU BLOQUE, y
        # `run_tests.py` -> `test_toda_linea_wopt_de_main_esta_en_la_tabla_y_cierra_
        # una_salida` lo verifica con `ast` sobre el arbol de `main()`. Un
        # `sys.exit` compartido por las dos ramas deja las dos lineas `WOPT_*`
        # huerfanas, que es el mutante M10. La linea `WOPT_*` va SIEMPRE la
        # ULTIMA (regla 4 del contrato).
        if regla_cabecera == "header-max-length":
            largo = len((mensaje or "").split("\n", 1)[0])
            print(f"WOPT_USAGE cabecera-larga se espera 120 caracteres o menos, "
                  f"y la cabecera mide {largo}: {detalle(motivo_cabecera)}")
            sys.exit(CODE_USAGE)
        print(f"WOPT_USAGE cabecera-regla {regla_cabecera} "
              f"{detalle(motivo_cabecera)}")
        sys.exit(CODE_USAGE)

    # 3. add -A. Si falla, ABORTAR: comitear despues seria staging parcial
    #    silencioso (solo se versionaria una parte de los cambios).
    rc, out, err, exc = run_git(["add", "-A"], env)
    if exc is not None or rc != 0:
        print(f"WOPT_FAIL add {detalle(exc or err or out)}")
        sys.exit(CODE_FAIL)

    # 4. Hay algo staged? Se decide con `diff --cached --quiet`, NO parseando el
    #    texto de git: "nothing to commit" se traduce segun LANG/LC_ALL y en un
    #    Windows en espanol no aparece nunca, lo que convertiria un arbol limpio
    #    en un fallo. rc 0 = nada staged, rc 1 = hay staged, rc > 1 = error.
    rc, out, err, exc = run_git(["diff", "--cached", "--quiet"], env)
    if exc is not None:
        print(f"WOPT_FAIL diff {detalle(exc)}")
        sys.exit(CODE_FAIL)
    if rc == 0:
        print("WOPT_NOOP nada staged tras add -A")
        sys.exit(CODE_OK)
    if rc != 1:
        print(f"WOPT_FAIL diff (rc={rc}) {detalle(err or out)}")
        sys.exit(CODE_FAIL)

    # 5. commit. Cualquier fallo real es codigo 1, nunca 0.
    rc, out, err, exc = run_git(["commit", "-m", mensaje], env)
    if exc is not None or rc != 0:
        print(f"WOPT_FAIL commit {detalle(exc or err or out)}")
        sys.exit(CODE_FAIL)

    # 6. Hash real y solo si resuelve: sin hash no se inventa nada en el CHANGELOG.
    rc, out, err, exc = run_git(["rev-parse", "--short", "HEAD"], env)
    if exc is not None or rc != 0 or not out:
        print(f"WOPT_FAIL hash-no-resoluble {detalle(exc or err or out)}")
        sys.exit(CODE_FAIL)

    primera_linea = out.splitlines()[0].strip() if out else ""
    if primera_linea:
        print(f"INFO commit: {detalle(primera_linea)}")
    # La linea canonica va SIEMPRE la ultima: es la unica que lee el pipeline.
    print(f"WOPT_COMMIT_OK {out.splitlines()[0].strip()} {detalle(mensaje, 120)}")
    sys.exit(CODE_OK)


if __name__ == "__main__":
    main()
