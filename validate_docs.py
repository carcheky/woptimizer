"""
validate_docs.py — valida que llms.txt cumple el formato Answer.AI v2
y que la estructura openspec/ esta completa. Sin dependencias externas.
"""
import os
import re
import ast
import json
import sys
import subprocess


def _recuento_de_tests(ruta_run_tests):
    """`(defined, invoked, solo_definidos, solo_invocados)` de `run_tests.py`.

    DERIVADO con `ast`, nunca escrito a mano: una constante en el validador
    seria la misma mentira que corrige, un nivel mas arriba. `defined` son las
    funciones `test_*` de modulo; `invoked`, las llamadas que hace el bloque
    `if __name__ == "__main__":`. Se exigen las dos cifras porque basta con lo
    de siempre para que un test exista en el fichero y no se ejecute nunca.

    Devuelve `None` cuando el recuento NO se puede derivar (fichero ausente,
    sin permisos, o fuente que no compila). Ese `None` es el estado que su
    consumidor `if n_tests is None:` declara desde el ciclo 12 y que este
    productor no sabia emitir: propagaba `FileNotFoundError` e
    `IndentationError`, asi que la rama era codigo MUERTO y sus dos rutas
    salian con traceback en vez de con informe. Arreglar el PRODUCTOR y no la
    rama es lo unico que no deja la expectativa escrita a mano.
    """
    try:
        with open(ruta_run_tests, encoding="utf-8") as f:
            fuente = f.read()
    except OSError:
        return None
    try:
        arbol = ast.parse(fuente, filename=ruta_run_tests)
    except SyntaxError:
        # `SyntaxError` y NO `IndentationError`. Medido, no es una cuestion de
        # gusto: la sangria inesperada lanza `IndentationError` y el tabulador
        # contra espacios `TabError`, las DOS subclases, y estrechar aqui
        # deja `TabError` fuera. Pero lo que de verdad se pierde al estrechar es
        # el `SyntaxError` PLANO -- un dos puntos borrado o un parentesis
        # descuadrado en `run_tests.py`, que es como se rompe un fichero de
        # verdad; los tabuladores son un caso limite. Las TRES fixtures estan
        # en `test_el_validador_avisa_en_vez_de_tirar_la_excepcion`, y el test
        # comprueba la clase que lanza CADA una antes de escribirla en disco,
        # para que un cambio de comportamiento de `ast.parse` se note en el
        # sitio donde se le puede atribuir en vez de dejar un mutante vivo.
        return None
    defined = {
        nodo.name for nodo in arbol.body
        if isinstance(nodo, ast.FunctionDef) and nodo.name.startswith("test_")
    }
    cuerpo_main = None
    for nodo in arbol.body:
        if not isinstance(nodo, ast.If):
            continue
        comparacion = nodo.test
        if (isinstance(comparacion, ast.Compare)
                and isinstance(comparacion.left, ast.Name)
                and comparacion.left.id == "__name__"):
            cuerpo_main = nodo.body
            break
    invocados = set()
    for stmt in (cuerpo_main or []):
        for nodo in ast.walk(stmt):
            if (isinstance(nodo, ast.Call)
                    and isinstance(nodo.func, ast.Name)
                    and nodo.func.id.startswith("test_")):
                invocados.add(nodo.func.id)
    return (len(defined), len(invocados),
            sorted(defined - invocados), sorted(invocados - defined))


def _comprobar_recuento_de_tests(root, errors, ok):
    """Cuerpo del check 7, extraido a funcion CON RAIZ (TASK-037, ciclo 27).

    Sin este refactor la rama `if n_tests is None:` solo se podia despertar
    lanzando el validador entero contra el repo entero, es decir, nunca en un
    test. Una rama que existe y nadie ejecuta es exactamente el defecto que
    este ciclo arregla, un nivel mas abajo: por eso el productor se arregla Y
    la rama se hace alcanzable en la misma pasada.
    """
    # El numero exigido se DERIVA del codigo con `ast` (los `def test_*` de
    # modulo y las llamadas del `__main__`), no de una constante escrita a mano:
    # una constante seria el mismo bug un nivel mas arriba. Ademas se exige que
    # `defined == invoked`, que es lo que hacia que un test nuevo "existiera"
    # sin ejecutarse nunca.
    n_tests = _recuento_de_tests(os.path.join(root, "run_tests.py"))
    if n_tests is None:
        errors.append(
            "run_tests.py: NO SE PUEDE DERIVAR el numero de tests. Sin el ancla no "
            "hay forma de saber si los ficheros que lo declaran estan caducados"
        )
    else:
        defined, invoked, solo_definidos, solo_invocados = n_tests
        if solo_definidos or solo_invocados:
            # Cada segmento se concatena SOLO si su lista tiene algo. Antes el
            # segundo se concatenaba igual y un test definido y no invocado --
            # el caso normal -- salia como `... | invocado y NO definido: .`,
            # con un punto huerfano que decia "esta lista vacia es un huerfano".
            huerfanos = []
            if solo_definidos:
                huerfanos.append("definido y NO invocado: " + ", ".join(solo_definidos))
            if solo_invocados:
                huerfanos.append("invocado y NO definido: " + ", ".join(solo_invocados))
            errors.append(
                f"run_tests.py: {defined} test(s) definidos y {invoked} invocado(s) en el "
                f"`__main__`. {' | '.join(huerfanos)}. Un test definido y no invocado "
                "pasa en verde porque no corre nunca"
            )
        else:
            ok.append(f"run_tests.py: {defined} tests definidos = {invoked} invocados (derivado con ast)")

        for relativo, patron in (
            ("STATUS.md", r"run_tests\.py`?,?\s*\*\*(?P<num>\d+)\s+tests"),
            ("AGENTS.md", r"run_tests\.py\s+#\s*(?P<num>\d+)\s+tests"),
            ("README.md", r"run_tests\.py\s*#\s*(?P<num>\d+)\s+tests"),
        ):
            ruta_doc = os.path.join(root, relativo)
            if not os.path.exists(ruta_doc):
                errors.append(f"{relativo}: NO EXISTE, no se puede comprobar el recuento de tests")
                continue
            with open(ruta_doc, encoding="utf-8") as f:
                cuerpo = f.read()
            encontrados = [int(m.group("num")) for m in re.finditer(patron, cuerpo)]
            if not encontrados:
                errors.append(
                    f"{relativo}: no declara el numero de tests de `run_tests.py` con la "
                    f"forma que este check lee ({patron}). Si el texto cambio, cambia el "
                    "patron aqui tambien: un validador que no encuentra lo que valida "
                    "no es un validador"
                )
            elif any(n != defined for n in encontrados):
                errors.append(
                    f"{relativo}: declara {encontrados} tests y la verdad son {defined} "
                    "(derivado de run_tests.py con ast). Actualiza el numero"
                )
            else:
                ok.append(f"{relativo}: declara los {defined} tests que run_tests.py tiene de verdad")

        # La tabla de `docs/ai/testing-guide.md` tiene una fila por test: si el
        # recuento de la tabla no es el del codigo, la tabla es la que caduca.
        guia = os.path.join(root, "docs", "ai", "testing-guide.md")
        if os.path.exists(guia):
            with open(guia, encoding="utf-8") as f:
                cuerpo_guia = f.read()
            filas = re.findall(r"^\|\s*(\d+)\s*\|\s*`test_", cuerpo_guia, re.MULTILINE)
            if len(filas) != defined:
                errors.append(
                    f"docs/ai/testing-guide.md: la tabla tiene {len(filas)} filas de test y "
                    f"run_tests.py tiene {defined}. Una tabla de una fila menos que el codigo "
                    "se lee como si todo estuviera medido"
                )
            else:
                ok.append(
                    f"docs/ai/testing-guide.md: {len(filas)} filas de test, una por test definido"
                )
        else:
            errors.append("docs/ai/testing-guide.md: NO EXISTE, no se puede comprobar la tabla")


# --- TASK-057 (ciclo 47): el ancla del changelog deja de depender SOLO de quien
# escribe el registro. Tres funciones extraidas CON RAIZ, por el mismo motivo que
# `_comprobar_recuento_de_tests` en el ciclo 27: `main()` deriva `root` de
# `__file__` y no admite argv, asi que sin extraccion el residuo que estas cazan
# NO se puede construir en un test. Una guarda que solo se despierta lanzando el
# validador entero contra el repo entero es una guarda que nadie ejecuta.

_RE_MARCADOR_DE_CICLO = re.compile(r"\b(?:ciclo|cycle)s?\b[\s:#-]*#?(\d{1,4})", re.IGNORECASE)


def _marcador_de_ciclo(asunto):
    """`int | None`: el numero de ciclo que declara el ASUNTO de un commit.

    Regex `\\b(?:ciclo|cycle)s?\\b[\\s:#-]*#?(\\d{1,4})`, case-insensitive, PRIMERA
    coincidencia. Tres decisiones MEDIDAS, no de estilo:

    - `\\b` en los dos extremos: sin el, "ciclo" casaria dentro de "ciclon" y de
      "ciclope", que es ruido y no un ciclo.
    - `[\\s:#-]*#?`: el repo escribe el numero de las TRES formas que existen en
      el historial real ("ciclo #46", "cycle-43", "ciclo 26"); exigir solo una
      dejaba fuera commits que SI corroboran.
    - PROHIBIDO leer `TASK-\\d+`, y no por gusto: el numero de tarea y el de
      ciclo DIVERGEN (ciclo 46 = TASK-056, ciclo 45 = TASK-055, medido). Un
      parser que confunda ambos devuelve 56 y exige `## CYCLE-056`, que no
      existe: pone el repo real en rojo. Medido hoy sobre los subjects reales:
      los `TASK-` dan {47..57}, todos fuera del journal.
    """
    m = _RE_MARCADOR_DE_CICLO.search(asunto or "")
    return int(m.group(1)) if m else None


def _ciclos_de_commits(asuntos):
    """`(ciclos, con_marcador, sin_marcador)` de una lista de asuntos.

    El TERCER numero no es decorativo: es el punto ciego MEDIDO y lo imprime el
    informe. Medido sobre el historial real: 43 de 154 subjects llevan marcador
    y 111 no lo llevan (son los `feat(...)`, `fix(...)`, `test(...)`). Medirlo
    en el informe es lo que impide que ese agujero se lea como cerrado.
    """
    ciclos = set()
    con_marcador = 0
    for asunto in asuntos:
        n = _marcador_de_ciclo(asunto)
        if n is None:
            continue
        con_marcador += 1
        ciclos.add(n)
    return ciclos, con_marcador, len(asuntos) - con_marcador


def _comprobar_ancla_de_commits(root, errors, ok, journal_cycles=()):
    """Historial de commits como TERCER testigo. -> `set[int]` de ciclos.

    Por que el historial y no otra cosa: ya esta FUERA del arbol de trabajo
    (`GIT_DIR` desacoplado, el mismo `GIT_DIR` que usa `git_safe_commit.py:67-79`),
    es append-only y direccionado por contenido. Para que el ciclo N deje de ser
    exigible hay que REESCRIBIR HISTORIA, no editar una clave de un JSON.

    El `GIT_DIR` del entorno se respeta A PROPOSITO: es el hook que permite tests
    hermeticos y es la precedencia documentada en AGENTS.md.

    `journal_cycles` no es adorno: es lo que permite distinguir "el historial no
    aporta ningun ciclo" (un parser ROTO, que no puede pasar por verde) de "el
    historial tampoco dice nada porque el journal tampoco" (fallo que ya reporta
    la rama del journal). El cableado lo pasa SIEMPRE; el default existe solo
    para que un test pueda despertar el ancla sola.

    NUNCA verde por omision: si el historial no se puede leer se reporta el MOTIVO
    LITERAL y se devuelve `set()`. Un `except: return set()` silencioso es la misma
    clase de bug que la rama `if n_tests is None:`, que era codigo muerto en el
    ciclo 27: una guarda que se salta sola cuando no puede comprobar ya no
    guarda nada.
    """
    env = os.environ.copy()
    env["GIT_DIR"] = env.get("GIT_DIR") or os.path.expandvars(
        r"%LOCALAPPDATA%\woptimizer_git\.git"
    )
    env["GIT_WORK_TREE"] = root
    # `--all`: un ciclo cerrado en una rama tambien cuenta. Sin limite: son 154
    # subjects, y truncar dejaria ciclos sin exigir, que es el fallo que esto
    # viene a cerrar.
    args = ["git", "log", "--format=%s", "--all"]
    salida, motivo = None, None
    # UN reintento, por el `spawn EPERM` intermitente de este host. Si vuelve a
    # fallar, el fallo es real y se dice cual fue.
    for _intento in (1, 2):
        try:
            res = subprocess.run(
                args, cwd=root, env=env, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=120,
            )
        except Exception as exc:                    # noqa: BLE001
            # No se estrecha a OSError: aqui valen tambien `FileNotFoundError`
            # (git no instalado), `PermissionError` y el propio fallo del
            # sandbox. "No pude ni comprobar" es un estado, no una excepcion
            # concreta, y narrowed lo dejaria salir con traceback.
            motivo = f"git no llego a ejecutarse: {type(exc).__name__}: {exc}"
            continue
        if res.returncode != 0:
            motivo = (
                f"git devolvio {res.returncode}: "
                f"{((res.stderr or '') + (res.stdout or '')).strip()}"
            )
            continue
        salida, motivo = res.stdout or "", None
        break
    if salida is None:
        errors.append(
            "historial de commits: NO SE PUEDE LEER y un ancla ilegible no certifica. "
            f"Motivo literal: {motivo}. El requisito de registrar cada ciclo se queda "
            "en rd_journal.json, que es un artefacto distinto pero lo escribe el MISMO "
            "actor (limitacion residual documentada en docs/ai/sandbox-rules.md)"
        )
        return set()

    subjects = [s for s in salida.splitlines() if s.strip()]
    ciclos, con_marcador, sin_marcador = _ciclos_de_commits(subjects)
    ok.append(
        f"historial de commits: {len(subjects)} subject(s), {con_marcador} con marcador "
        f"de ciclo y {sin_marcador} SIN marcador (punto ciego medido); "
        f"{len(ciclos)} ciclo(s) corroborables frente a los {len(journal_cycles)} del journal"
    )
    if not ciclos and journal_cycles:
        errors.append(
            "historial de commits: se lee pero NO aporta ningun ciclo (0 subjects con "
            f"marcador de ciclo sobre {len(subjects)} leidos) mientras rd_journal.json si "
            f"registra {len(journal_cycles)} ciclo(s). Un parser que no encuentra nada es "
            "un parser ROTO, y un parser roto en verde es el falso verde que esta union "
            "viene a cerrar"
        )
    return ciclos


def _comprobar_ancla_del_changelog(root, errors, ok):
    """Check 5b, su parte de ANCLA: cobertura de entradas de ciclo del changelog.

    El requisito es la UNION de las dos fuentes:

        ciclos_requeridos = ciclos_del_journal | ciclos_del_historial

    SUSTITUIR el journal por el historial seria peor que no hacer nada: medido,
    los cierres de los ciclos 1, 2, 3 y 15 a 20 no llevan marcador de ciclo, asi
    que perderian su unico requisito. Eso seria el falso verde del ciclo 15
    renacido. Y la union no puede ser mas laxa que hoy: solo mas estricta, porque
    el historial puede exigir lo que el journal no exige, nunca al reves.
    """
    root_changelog = os.path.join(root, "CHANGELOG.md")
    if not os.path.exists(root_changelog):
        errors.append(
            "CHANGELOG.md (raiz): NO EXISTE. El registro legible por el usuario "
            "es obligatorio; el de .taskmaster/ esta en una carpeta oculta"
        )
        return
    with open(root_changelog, encoding="utf-8") as f:
        rch = f.read()

    # Ancla EXTERNA. El check 5b deriva el ciclo exigido del propio registro
    # tecnico, asi que borrar el ultimo ciclo de LOS DOS ficheros hacia
    # desaparecer el requisito (falso verde demostrado por el verificador del
    # ciclo #15). Ancla en rd_journal.json, que es un artefacto distinto y que
    # el orquestador escribe ANTES que los changelogs.
    journal_cycles = []
    journal_path = os.path.join(root, ".taskmaster", "rd_journal.json")
    journal_usable = True
    if not os.path.exists(journal_path):
        # AUSENTE y CORRUPTO son el mismo fallo para este check: sin journal
        # no hay contra que anclar. El primer fix solo cubria el `except`
        # y dejaba pasar el fichero ausente en verde (verificador, ciclo 16).
        journal_usable = False
        errors.append(
            ".taskmaster/rd_journal.json: NO EXISTE. El ancla del changelog de raiz "
            "no se puede comprobar, y sin el no hay garantia de que el ultimo ciclo "
            "este registrado en CHANGELOG.md"
        )
    else:
        try:
            with open(journal_path, encoding="utf-8") as f:
                journal = json.load(f)
            for entry in journal if isinstance(journal, list) else []:
                cyc = entry.get("cycle") if isinstance(entry, dict) else None
                if isinstance(cyc, int):
                    # Se guarda el numero, no el string: un max() sobre
                    # cadenas de 3 caracteres ordenaria "999" por encima de
                    # "1000" y pediria un ciclo que no existe.
                    journal_cycles.append(cyc)
        except (ValueError, OSError):
            journal_cycles = []
            journal_usable = False
            # Fallo explicito, no salto silencioso: si el ancla no se puede
            # leer, el check 5b NO debe dar verde por omision (falso verde
            # reportado por el verificador del ciclo #16).
            errors.append(
                ".taskmaster/rd_journal.json: ESTA CORRUPTO. El ancla del changelog "
                "de raiz no se puede comprobar, y sin el no hay garantia de que el "
                "ultimo ciclo este registrado en CHANGELOG.md"
            )

    if not journal_cycles and journal_usable:
        # Se lee el fichero pero no aporta ningun ciclo utilizable: mismo
        # fallo funcional que no tenerlo, y no debe pasar en verde.
        errors.append(
            ".taskmaster/rd_journal.json: se lee pero no contiene ningun ciclo valido "
            "(ninguna entrada con 'cycle' entero). El ancla del changelog de raiz no "
            "se puede comprobar"
        )

    # TERCER testigo. Va DESPUES de la politica del journal, que no se toca:
    # son dos fallos distintos y mezclarlos haria mas dificil leer el informe.
    ciclos_historial = _comprobar_ancla_de_commits(root, errors, ok, journal_cycles)

    ciclos_journal = set(journal_cycles)
    ciclos_requeridos = ciclos_journal | ciclos_historial

    sin_journal = sorted(ciclos_historial - ciclos_journal)
    if sin_journal:
        residuo = ", ".join(f"{c:03d}" for c in sin_journal)
        errors.append(
            f"historial de commits: hay trabajo COMITEADO del/los ciclo/s {residuo} "
            "y rd_journal.json NO lo registra. Ese es el residuo que este check persigue: "
            "el journal no puede ser el unico testigo de si un ciclo se cerro, porque lo "
            "escribe el mismo actor que despues pide la validacion"
        )

    if journal_cycles:
        jlatest = f"{max(journal_cycles):03d}"
        has_jentry = (
            f"## CYCLE-{jlatest}" in rch
            or f"## [CYCLE-{jlatest}]" in rch
        )
        if not has_jentry:
            errors.append(
                f"CHANGELOG.md (raiz): rd_journal.json registra el ciclo {jlatest} pero "
                "el changelog legible no tiene su entrada. Borrarla en los dos ficheros "
                "no puede hacer desaparecer la obligacion de registrarla"
            )
        else:
            ok.append(f"CHANGELOG.md (raiz): anclado al ciclo {jlatest} de rd_journal.json")

        # Cobertura COMPLETA: el ancla anterior solo miraba el ultimo ciclo,
        # asi que un encabezado de ciclo perdido en medio pasaba inadvertido
        # (CYCLE-016 quedo sin encabezado y el validador dio 0 FAIL).
        # Ahora se exige una entrada por ciclo exigido, y el conjunto exigido es
        # la UNION: solo el historial puede exigir ciclos que el journal no
        # registra, y por eso el mensaje dice "exigido por" y no "que
        # rd_journal.json registra", que seria FALSO para un ciclo comiteado
        # que el journal no conoce.
        missing_entries = [
            f"{c:03d}" for c in sorted(ciclos_requeridos)
            if f"## CYCLE-{c:03d}" not in rch
            and f"## [CYCLE-{c:03d}]" not in rch
        ]
        if missing_entries:
            errors.append(
                f"CHANGELOG.md (raiz): sin entrada para el/los ciclo/s "
                f"{', '.join(missing_entries)}, exigido por rd_journal.json y/o por el "
                "historial de commits. La tabla resumen los enlaza, pero el encabezado "
                "seccion no existe: enlace muerto"
            )
        else:
            ok.append(
                f"CHANGELOG.md (raiz): entrada presente para los {len(ciclos_requeridos)} "
                f"ciclos exigidos (journal {len(ciclos_journal)} | historial "
                f"{len(ciclos_historial)}; ninguno sin enlace muerto)"
            )



def main():
    root = os.path.dirname(os.path.abspath(__file__))
    errors = []
    ok = []

    # 1. llms.txt format
    with open(os.path.join(root, "llms.txt"), encoding="utf-8") as f:
        llms = f.read()

    if re.search(r"^# .+", llms, re.MULTILINE):
        ok.append("llms.txt: H1 project name presente")
    else:
        errors.append("llms.txt: falta H1 project name")

    if "> " in llms:
        ok.append("llms.txt: blockquote summary presente")
    else:
        errors.append("llms.txt: falta blockquote summary")

    if re.search(r"^## ", llms, re.MULTILINE):
        ok.append("llms.txt: tiene secciones H2 (formato v3)")
    else:
        errors.append("llms.txt: sin secciones H2")

    # 2. llms-full.txt debe existir y concatenar todos los docs/*.md
    full_path = os.path.join(root, "llms-full.txt")
    if not os.path.exists(full_path):
        errors.append("llms-full.txt: no existe")
    else:
        with open(full_path, encoding="utf-8") as f:
            full = f.read()
        full_size = os.path.getsize(full_path)
        docs_dir = os.path.join(root, "docs")
        docs_files = sorted(f for f in os.listdir(docs_dir) if f.endswith(".md"))
        missing = [d for d in docs_files if d not in full]
        if missing:
            errors.append(f"llms-full.txt: faltan secciones: {missing}")
        else:
            ok.append(f"llms-full.txt: incluye todos los {len(docs_files)} docs/*.md ({full_size} bytes)")

    # 3. OpenSpec structure (dinamico: detecta proposal id actual)
    openspec = os.path.join(root, "openspec")

    # Estructura base siempre requerida
    base_required = [
        "README.md",
        "specs/woptimizer/spec.md",
    ]
    for rel in base_required:
        full = os.path.join(openspec, rel)
        if os.path.exists(full):
            ok.append(f"openspec/{rel}: existe ({os.path.getsize(full)} bytes)")
        else:
            errors.append(f"openspec/{rel}: NO EXISTE")

    # Cambios activos en changes/ (excluyendo archive/)
    active_changes_dir = os.path.join(openspec, "changes")
    if os.path.isdir(active_changes_dir):
        active = [
            d for d in os.listdir(active_changes_dir)
            if os.path.isdir(os.path.join(active_changes_dir, d))
            and d not in ("archive",)
        ]
        for cid in active:
            # proposal.md es obligatorio
            proposal = os.path.join(active_changes_dir, cid, "proposal.md")
            if os.path.exists(proposal):
                ok.append(f"openspec/changes/{cid}/proposal.md: existe ({os.path.getsize(proposal)} bytes)")
            else:
                errors.append(f"openspec/changes/{cid}/proposal.md: NO EXISTE")
            # tasks.md es opcional (per decision matrix del SDD: cambios triviales/pequeños pueden no tenerlo)
            tasks = os.path.join(active_changes_dir, cid, "tasks.md")
            if os.path.exists(tasks):
                ok.append(f"openspec/changes/{cid}/tasks.md: existe ({os.path.getsize(tasks)} bytes)")

    # Archive debe existir y tener al menos un cambio
    archive_dir = os.path.join(openspec, "changes", "archive")
    if os.path.isdir(archive_dir):
        archived = [
            d for d in os.listdir(archive_dir)
            if os.path.isdir(os.path.join(archive_dir, d))
        ]
        if archived:
            ok.append(f"openspec/changes/archive/: {len(archived)} cambio(s) cerrado(s)")
            for cid in archived:
                for fn in ("proposal.md", "tasks.md"):
                    full = os.path.join(archive_dir, cid, fn)
                    if not os.path.exists(full):
                        errors.append(f"openspec/changes/archive/{cid}/{fn}: NO EXISTE")
        else:
            ok.append("openspec/changes/archive/: existe (vacio)")
    else:
        errors.append("openspec/changes/archive/: NO EXISTE")

    # 4. AGENTS.md estructura v3 (Stack + Invariantes + seccion de roles)
    with open(os.path.join(root, "AGENTS.md"), encoding="utf-8") as f:
        agents = f.read()
    v3_sections = ["Stack", "Invariantes"]
    missing_sections = [s for s in v3_sections if s not in agents]
    # El encabezado de roles cambio de "Skills Disponibles" a
    # "Roles del Pipeline" en el ciclo #16 (los tres roles pasaron de skills a
    # agentes). Se aceptan ambos nombres para no atar el validador a un titulo
    # que ya no describe la realidad, pero la seccion DEBE existir: es la que
    # explica como delegar y evita el "Unknown agent" que rompio el ciclo 14.
    if not ("Skills Disponibles" in agents or "Roles del Pipeline" in agents):
        missing_sections.append("Roles del Pipeline (o 'Skills Disponibles')")
    if not missing_sections:
        ok.append("AGENTS.md: secciones v3 + seccion de roles presentes")
    else:
        errors.append(f"AGENTS.md: faltan secciones v3: {missing_sections}")
    if "CHANGELOG" in agents and "MANDATORY" in agents:
        ok.append("AGENTS.md: menciona CHANGELOG.md como obligatorio")
    else:
        errors.append("AGENTS.md: no menciona CHANGELOG.md como mandatory")

    # 5. .taskmaster/CHANGELOG.md existe y tiene formato valido (MANDATORY desde ciclo 11)
    # `ch` se inicializa aqui: el check 5 lo usa, y sin esto un
    # .taskmaster/CHANGELOG.md ausente provocaba un NameError con traceback
    # en vez de un informe limpio (encontrado por el verificador del ciclo #15).
    ch = ""
    changelog = os.path.join(root, ".taskmaster", "CHANGELOG.md")
    if not os.path.exists(changelog):
        errors.append(".taskmaster/CHANGELOG.md: NO EXISTE (MANDATORY desde ciclo #11)")
    else:
        with open(changelog, encoding="utf-8") as f:
            ch = f.read()
        size = os.path.getsize(changelog)
        if "Changelog de pases" not in ch:
            errors.append(".taskmaster/CHANGELOG.md: falta encabezado 'Changelog de pases'")
        else:
            ok.append(f".taskmaster/CHANGELOG.md: existe ({size} bytes) con encabezado correcto")
        cycle_count = len(re.findall(r"\[CYCLE-\d{3}\]", ch))
        if cycle_count == 0:
            errors.append(".taskmaster/CHANGELOG.md: ninguna entrada [CYCLE-NNN] encontrada")
        else:
            ok.append(f".taskmaster/CHANGELOG.md: {cycle_count} entradas [CYCLE-NNN]")
        if "MANDATORY" in ch:
            ok.append(".taskmaster/CHANGELOG.md: marca MANDATORY presente")
        else:
            errors.append(".taskmaster/CHANGELOG.md: no marca la convencion como MANDATORY")

    # 5b. CHANGELOG.md de RAIZ existe y esta sincronizado con el tecnico.
    # .taskmaster/ es una carpeta OCULTA: un changelog escrito solo ahi es, para
    # el usuario, un changelog que no existe (fallo real del ciclo #14).
    root_changelog = os.path.join(root, "CHANGELOG.md")
    if not os.path.exists(root_changelog):
        errors.append("CHANGELOG.md (raiz): NO EXISTE. El registro legible por el usuario "
                      "es obligatorio; el de .taskmaster/ esta en una carpeta oculta")
    else:
        with open(root_changelog, encoding="utf-8") as f:
            rch = f.read()
        size = os.path.getsize(root_changelog)
        if "Changelog" not in rch:
            errors.append("CHANGELOG.md (raiz): falta el encabezado 'Changelog'")
        else:
            ok.append(f"CHANGELOG.md (raiz): existe ({size} bytes)")

        # Debe usar el estilo legible: secciones por tipo de cambio, no "What/Outcome".
        if "### Corregido" not in rch:
            errors.append("CHANGELOG.md (raiz): falta la seccion '### Corregido'; "
                          "el registro de raiz va escrito para el usuario, no en formato tecnico")
        else:
            ok.append("CHANGELOG.md (raiz): usa secciones legibles (### Corregido)")

        # Sincronia: el ciclo mas reciente del registro tecnico debe tener una
        # ENTRADA propia en el de raiz.
        # OJO: buscar el numero como substring daria falso verde, porque "015"
        # sobrevive dentro de "TASK-015" mentioned en otra entrada. Por eso se
        # exige el encabezado completo de la entrada (demostrado por el
        # verificador del ciclo #15: asi pasaba el test al borrar la entrada).
        #
        # Delegado a `_comprobar_ancla_del_changelog(root, errors, ok)`
        # (TASK-057, ciclo 47) por el mismo motivo que el check 7: `main()`
        # deriva `root` de `__file__` y no admite argv, asi que sin extraccion
        # el residuo que se persigue aqui (ciclo COMITEADO y NO registrado) no
        # se puede construir en un test. El cuerpo vive una sola vez, aqui
        # dentro: el camino real y el del test ejecutan el MISMO codigo, que es
        # lo contrario de un `--verify` con ruta propia.
        _comprobar_ancla_del_changelog(root, errors, ok)

    # 6. mkdocs.yml existe y tiene nav
    if os.path.exists(os.path.join(root, "mkdocs.yml")):
        with open(os.path.join(root, "mkdocs.yml"), encoding="utf-8") as f:
            mk = f.read()
        # Debe tener bloque nav: con al menos 3 entries
        nav_block = re.search(r"^nav:\s*\n((?:  - .+\n)+)", mk, re.MULTILINE)
        if nav_block and nav_block.group(1).count("  - ") >= 3:
            ok.append(f"mkdocs.yml: nav configurada ({nav_block.group(1).count('  - ')} entries)")
        else:
            errors.append("mkdocs.yml: nav incompleta")
    else:
        errors.append("mkdocs.yml: NO EXISTE")

    # 7. El RECUENTO DE TESTS no puede volver a caducar solo. Delegado a
    # `_comprobar_recuento_de_tests(root, errors, ok)`, que se extrajo a
    # funcion con raiz en el ciclo 27 T-27.2: sin eso su rama
    # `if n_tests is None:` solo se podia despertar lanzando el validador
    # entero contra el repo entero, es decir, nunca desde un test.
    _comprobar_recuento_de_tests(root, errors, ok)

    # Reporte
    print("=" * 60)
    print(" validate_docs.py — woptimizer SDD + llms.txt")
    print("=" * 60)
    print()
    for line in ok:
        print(f"  [OK]   {line}")
    if errors:
        print()
        for line in errors:
            print(f"  [FAIL] {line}")
    print()
    print(f"Resumen: {len(ok)} OK, {len(errors)} FAIL")
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()