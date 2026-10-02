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
        _comprobar_reparto_de_tests(root, errors, ok, defined)

# --- TASK-057 (ciclo 47): el ancla del changelog deja de depender SOLO de quien
# escribe el registro. Tres funciones extraidas CON RAIZ, por el mismo motivo que
# `_comprobar_recuento_de_tests` en el ciclo 27: `main()` deriva `root` de
# `__file__` y no admite argv, asi que sin extraccion el residuo que estas cazan
# NO se puede construir en un test. Una guarda que solo se despierta lanzando el
# validador entero contra el repo entero es una guarda que nadie ejecuta.
#
# G1 (cierre del ciclo #47): el PLURAL declara MAS DE UN ciclo. La semantica es
# una DECISION DE PRODUCTO, no una eleccion del implementador: un asunto con
# plural ("ciclos", "cycles") seguido de un rango declara mas de un ciclo y se
# interpreta como RANGO con extremos incluidos -- `ciclos 14-20` corrobora 14,
# 15, 16, 17, 18, 19 y 20. Un plural con un numero suelto ("ciclos 47")
# corrobora solo ese, que es el caso trivial de un rango de longitud uno.
#
# El grupo `s?` se CAPTURA en vez de consumirse porque la expansion depende de
# el: con plural y guion, rango; sin plural, el primer numero y nada mas, que es
# la lectura de siempre. Un `ciclo 14-20` en singular es un asunto prolijo y se
# lee como el 14, no como siete ciclos que nadie declaro.
_RE_MARCADOR_DE_CICLO = re.compile(
    r"\b(?:ciclo|cycle)(s?)\b[\s:#-]*#?(\d{1,4})(?:\s*-\s*(\d{1,4}))?",
    re.IGNORECASE,
)

# Techo de la expansion de un rango. MEDIDO sobre el historial real: hay UN
# asunto con plural, `feat(ciclos 14-20)`, o sea siete ciclos. Sin tope, un
# `ciclos 1-9999` escrito en cualquier parrafo exigiria 9999 entradas
# `## CYCLE-` y el validador devolveria un FAIL de 40.000 caracteres: un texto
# cualquiera no puede fabricar un requisito asi, y un requisito que nadie
# puede satisfacer no es un requisito. Lo que excede el tope degrada al PRIMER
# numero, que es exactamente lo que hacia el parser sin rango: acota el dano,
# no lo inventa.
MAX_CICLOS_DE_UN_RANGO = 50


def _ciclos_del_asunto(asunto):
    """`set[int]`: los ciclos que declara el ASUNTO de UN commit. Vacio = nada.

    Antes devolvia `int | None` con el PRIMER numero, y por eso el `s?` del
    plural era DECORACION: quitarlo de la regex no cambiaba ningun veredicto y
    la suite entera lo toleraba. Medido el 2026-10-02 sobre los 159 subjects
    reales: hay UN UNICO commit que depende del plural, `feat(ciclos 14-20)`, y
    al quitarselo el historial deja de corroborar los ciclos 15 a 20 (que el
    journal ya exigia, luego el veredicto no cambia hoy: lo que cambia es el
    testigo, y un testigo que no corrobora no corrobora).

    Regex `\\b(?:ciclo|cycle)(s?)\\b[\\s:#-]*#?(\\d{1,4})(?:\\s*-\\s*(\\d{1,4}))?`,
    case-insensitive, PRIMERA coincidencia. Decisiones MEDIDAS, no de estilo:

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
    - El rango se expande SOLO con plural y con el tope de arriba. Un rango
      invertido ("ciclos 20-14") o por encima del tope degrada al primer numero
      en vez de inventar el hueco o el tamano.
    """
    m = _RE_MARCADOR_DE_CICLO.search(asunto or "")
    if not m:
        return set()
    primero = int(m.group(2))
    fin = m.group(3)
    if not (m.group(1) and fin):
        return {primero}
    hasta = int(fin)
    if hasta < primero or hasta - primero + 1 > MAX_CICLOS_DE_UN_RANGO:
        return {primero}
    return set(range(primero, hasta + 1))


def _ciclos_de_commits(asuntos):
    """`(ciclos, con_marcador, sin_marcador)` de una lista de asuntos.

    `ciclos` es el conjunto CORROBORABLE, donde un `ciclos 14-20` aporta siete,
    pero `con_marcador` cuenta SUBJECTS con marcador y no ciclos: un rango es
    un commit que declara siete. Sumar ciclos donde la linea de informe dice
    subjects haria que el informe mintiera en la cifra que justamente existe
    para no mentir.

    El TERCER numero no es decorativo: es el punto ciego MEDIDO y lo imprime el
    informe. La cifra EXACTA no se escribe aqui, y no por vaguedad: caduca con
    cada commit, y una cifra caducada en un docstring se relee como verdad. Lo
    que si se afirma, porque es estable, es que MAS DE LA MITAD de los subjects
    del repo no llevan marcador (son los `feat(...)`, `fix(...)`, `test(...)`).
    El numero vivo lo reimprime el informe de `_comprobar_ancla_de_commits` en
    cada pasada, y medirlo en el informe es lo que impide que ese agujero se lea
    como cerrado.
    """
    ciclos = set()
    con_marcador = 0
    for asunto in asuntos:
        del_asunto = _ciclos_del_asunto(asunto)
        if not del_asunto:
            continue
        con_marcador += 1
        ciclos |= del_asunto
    return ciclos, con_marcador, len(asuntos) - con_marcador


def _comprobar_ancla_de_commits(root, errors, ok, journal_cycles):
    """Historial de commits como TERCER testigo. -> `set[int]` de ciclos.

    `journal_cycles` es POSICIONAL OBLIGATORIO, y no es estilo. Medido, el
    intento 3 del ciclo 47: con `journal_cycles=()` por defecto, el mutante que
    borra el cuarto argumento de la llamada es un CAMBIO DE COMPORTAMIENTO que
    nadie nota -- el parser roto pasa en verde y el validador da `108 OK /
    0 FAIL` -- porque el default convierte el error de cableado en un `()`
    silencioso. Sin default, ese mismo mutante es un `TypeError` en la llamada y
    tumba el validador entero, que es el unico estado en el que un cableado roto
    no puede disfrazarse de criterio.

    Por que el historial y no otra cosa: ya esta FUERA del arbol de trabajo
    (`GIT_DIR` desacoplado, el mismo `GIT_DIR` que usa `git_safe_commit.py:67-79`),
    es append-only y direccionado por contenido. Para que el ciclo N deje de ser
    exigible hay que REESCRIBIR HISTORIA, no editar una clave de un JSON.

    El `GIT_DIR` del entorno se respeta A PROPOSITO: es el hook que permite tests
    hermeticos y es la precedencia documentada en AGENTS.md.

    `journal_cycles` no es adorno: es lo que permite distinguir "el historial no
    aporta ningun ciclo" (un parser ROTO, que no puede pasar por verde) de "el
    historial tampoco dice nada porque el journal tampoco" (fallo que ya reporta
    la rama del journal). El cableado lo pasa SIEMPRE, y ahora no puede no
    pasarlo.

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
    # `--all`: un ciclo cerrado en una rama tambien cuenta. Sin limite: son ~157
    # subjects, y truncar dejaria ciclos sin exigir, que es el fallo que esto
    # viene a cerrar. La cifra viva la reimprime el informe, en la linea de
    # `ok` de esta misma funcion.
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
            # NO se estrecha, y la razon HONESTA no es la que estaba escrita
            # aqui hasta el ciclo 47. Medido: `FileNotFoundError.__mro__[1]` y
            # `PermissionError.__mro__[1]` son los dos `OSError`, o sea que
            # "no son OSError" era FALSO y las dos estaban covered de todos
            # modos. Lo que de verdad alcanza este `except` y no es `OSError` es
            # `subprocess.TimeoutExpired` (`SubprocessError` -> `Exception`),
            # alcanzable por el `timeout=120` de la llamada de arriba, mas el
            # propio fallo de `spawn EPERM` del sandbox cuando git ni llega a
            # arrancar. Estrecharlo a `OSError` deja el timeout -- y solo el
            # timeout -- saliendo con traceback, y "no pude ni comprobar" es un
            # estado que hay que INFORMAR, no una excepcion concreta.
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


# --- TASK-060 (ciclo #49), T3: el REPARTO de `run_tests.py`. Va como segunda
# derivacion de `_comprobar_recuento_de_tests` y NO dentro del check 8, por dos
# razones concretas: (i) es la MISMA derivacion `ast` sobre el MISMO fichero que
# ya declara las cifras, y el check 8 tiene otro sujeto --las filas de una
# seccion--; (ii) mezclar dos derivaciones en una funcion hace que un rojo no
# diga QUE esta mal, y el coste de un falso rojo es que nadie mire el validador.


def _reparto_de_tests(root):
    """`(antes, desde, total, linea_del_marcador)` del reparto de `run_tests.py`.

    Cuentas las llamadas `test_*()` del bloque `__main__` ANTES del marcador
    estructural `--- Running Headless UI Tests ---` y DESDE el. MEDIDO el
    2026-10-02: 93 antes y 10 desde, 103 exactas, que es el total que el check 7
    ya vigila. El total NO se vuelve a derivar aqui: se cruza contra el que le
    pasa el check 7, y si los dos no coinciden el reparto esta contando otra
    cosa.

    `None` cuando el marcador NO aparece, y NUNCA `0 + 0`: un reparto que no se
    deriva no se declara, y devolver ceros en verde seria un falso verde Built
    con la forma de un acierto. La linea del marcador se deriva del propio
    `ast` y se imprime en el informe, donde es informacion para el humano: el
    numero de linea no se verifica, porque verificarlo fabrica un rojo en
    cuanto alguien inserte una linea arriba.
    """
    ruta = os.path.join(root, "run_tests.py")
    try:
        with open(ruta, encoding="utf-8") as f:
            fuente = f.read()
    except OSError:
        return None
    try:
        arbol = ast.parse(fuente, filename=ruta)
    except SyntaxError:
        return None
    cuerpo_main = None
    for nodo in arbol.body:
        if (isinstance(nodo, ast.If) and isinstance(nodo.test, ast.Compare)
                and isinstance(nodo.test.left, ast.Name)
                and nodo.test.left.id == "__name__"):
            cuerpo_main = nodo.body
            break
    if cuerpo_main is None:
        return None
    antes = desde = 0
    visto = False
    linea_marcador = None
    for stmt in cuerpo_main:
        llamadas = sum(
            1 for nodo in ast.walk(stmt)
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
            and nodo.func.id.startswith("test_"))
        if visto:
            desde += llamadas
        else:
            antes += llamadas
        if MARCADOR_HEADLESS in (ast.get_source_segment(fuente, stmt) or ""):
            visto = True
            linea_marcador = stmt.lineno
    if not visto:
        return None
    return (antes, desde, antes + desde, linea_marcador)


def _comprobar_reparto_de_tests(root, errors, ok, defined):
    """El reparto que STATUS.md declara tiene que ser el que se deriva con `ast`.

    `defined` es el total que YA derivó `_recuento_de_tests`; el reparto es una
    segunda lectura del mismo `ast`, no un segundo total. Se exige que las dos
    derivaciones sumen lo mismo, y se exige que el panel declare el reparto con
    la forma que este check lee (`\\d+ backend + \\d+ headless`): un validador que
    no encuentra lo que valida no es un validador, y el mensaje lo dice con el
    patron exacto, como ya hace el check del total.
    """
    reparto = _reparto_de_tests(root)
    if reparto is None:
        # El prefijo NO es `run_tests.py:` a proposito. Ese prefijo lo usa el
        # check 7 para sus hallazgos, y hay un test del ciclo #27 que cuenta las
        # lineas `[FAIL]` que empiezan asi para exigir que un test huerfano dé
        # exactamente una. Un reparto que no se deriva es OTRO hallazgo de otro
        # contrato, asi que nombra el fichero dentro del mensaje en vez de
        # Vestirse con el prefijo de su vecino.
        errors.append(
            "reparto de la suite: NO SE ENCUENTRA el marcador estructural de las "
            f"pruebas headless en `run_tests.py` (`{MARCADOR_HEADLESS}`), asi que el "
            "reparto backend + headless NO SE PUEDE derivar. Un reparto que no se "
            "deriva no se declara: nunca 0 + 0 en verde"
        )
        return
    antes, desde, total, linea = reparto
    if total != defined:
        errors.append(
            f"run_tests.py: el reparto derivado suma {total} y el recuento de tests "
            f"es {defined}. Las dos derivaciones leen el mismo `ast`, asi que una "
            "diferencia aqui significa que una de las dos cuenta otra cosa"
        )
    else:
        ok.append(
            f"run_tests.py: reparto {antes} backend + {desde} headless derivado con "
            f"ast (marcador en run_tests.py:{linea}); suma el total que ya deriva el "
            "check 7"
        )

    ruta_status = os.path.join(root, "STATUS.md")
    if not os.path.exists(ruta_status):
        return
    with open(ruta_status, encoding="utf-8") as f:
        cuerpo_status = f.read()
    declarados = re.findall(
        r"(\d{1,4})\s*backend\s*\+\s*(\d{1,4})\s*headless", cuerpo_status)
    if not declarados:
        errors.append(
            "STATUS.md: no declara el reparto de tests con la forma que este check "
            "lee (\\d+ backend + \\d+ headless). Si el texto cambio, cambia el "
            "patron aqui tambien: un validador que no encuentra lo que valida no es "
            "un validador"
        )
    elif (str(antes), str(desde)) not in declarados:
        errors.append(
            "run_tests.py: STATUS.md declara "
            + ", ".join(f"{a} backend + {b} headless" for a, b in declarados)
            + f" y el reparto DERIVADO es {antes} backend + {desde} headless; el "
            f"marcador de run_tests.py:{linea} separa {antes}/{desde}. El total "
            f"puede seguir dando {defined} mientras el reparto miente"
        )
    else:
        ok.append(
            f"STATUS.md: declara el reparto {antes} backend + {desde} headless que "
            "deriva el marcador de run_tests.py"
        )


# --- TASK-060 (ciclo #49): CHECK 8. La seccion `## Deuda Tecnica Conocida` de
# `STATUS.md` gobierna que trabajo hace el bucle cuando el backlog esta vacio (el
# Paso 1 del bucle la lee literalmente), y hasta el ciclo #48 NADA en este repo
# la miraba: `validate_docs.py` tenia 0 coincidencias de la palabra `Deuda` y
# mencionaba `STATUS.md` una sola vez, en la lista del recuento de tests. El
# ciclo #48 sano 13 filas de esa seccion y su auditoria cerro PARTIAL por una
# razon MEDIDA, no supuesta: 8 de 9 mutaciones sobrevivieron porque nada vigila
# la seccion. Este bloque es ese arreglo de fondo.
#
# CINCO fuentes de verdad, TODAS fuera del panel, porque el panel no es fuente de
# verdad de si mismo (la clase de fallo que la fila 92 ya escribio):
#   S1 la ruta citada EXISTE en el arbol (sin numero de linea);
#   S2 la cita trae identificador (`fichero:linea identificador`) y el fichero lo
#      contiene: es lo que distingue "apunta a algo" de "apunta a lo que dice";
#   S3 `TASK-NNN` con `status` legible en `.taskmaster/tasks.json`;
#   S4 `CYCLE-NNN` con entrada en `CHANGELOG.md` o en `rd_journal.json`;
#   S5 una cifra que coincide con el recuento DERIVADO con `ast` de `run_tests.py`.
#
# NINGUN numero de linea se verifica, y no por vaguedad. MEDIDO el 2026-10-02: las
# citas que nombran una funcion o un test son exactas hoy, y lo unico desviado es
# el bloque INTRA-panel de la fila del criterio, por una unidad, porque el panel
# se cita a si mismo por numero de linea. Verificar el numero seria fabricar un
# rojo en cuanto alguien inserte una fila arriba, que es justo lo que este bucle
# hace cada ciclo: ese es el rojo que entrena a ignorar el validador.

MARCADOR_HEADLESS = "--- Running Headless UI Tests ---"

# Precedencias donde se busca una ruta citada POR SU NOMBRE. Medido: las filas
# del panel citan `rd_journal.json` y `git_safe_commit.py` sin su prefijo, y la
# verdad es que viven en `.taskmaster/`. Sin esta lista esas dos filas salen sin
# ancla por un detalle de escritura, que es un rojo sin motivo.
PREFIJOS_DE_ANCLA = ("", ".taskmaster/", "docs/", "docs/ai/", "docs/archive/")

# El marcador de cierre se busca DESPUES de borrar el codigo inline, y ese `sub`
# es el fix entero, no un detalle de estilo: la fila que escribe el criterio lleva
# el token dentro de comillas invertidas porque esta ESCRIBIENDO el criterio, y
# sin la limpieza el panel se declararia cerrado a si mismo. Medido al nacer: con
# el `sub`, 7 exentas y 8 vivas; sin el, la fila del criterio se autoexime y el
# check nace verde justo sobre lo que tiene que vigilar.
_RE_CODIGO_INLINE = re.compile(r"`[^`]*`")
# El marcador de cierre es una PALABRA, no un prefijo. MEDIDO el 2026-10-02 con
# `re.compile(r"CERRAD")`: el plural se colaba y convertia una fila VIVA en
# exenta con `0 FAIL` (la variante V3 del mutation-auditor, "**CERRADAS todas en
# TASK-061**"), y con el mismo hueco la comparativa "a diferencia de las
# CERRADAS, esta sigue viva" (V4) tambien. `\bCERRAD[OA]\b` exige la palabra
# entera y por construccion rechaza el plural y el comparativo.
_RE_CERRADA = re.compile(r"\bCERRAD[OA]\b")
_RE_CITAS = re.compile(r"`([^`]*)`")
_RE_NUMERO_DE_LINEA = re.compile(r":\d+(?:-\d+)?$")
_RE_RUTA = re.compile(
    r"^[A-Za-z0-9_.\\/-]+\.(?:py|md|json|txt|yml|yaml|ini|cfg|bat|toml|exe|log|git)$"
)
_RE_TAREAS = re.compile(r"TASK-\d+")
_RE_CICLOS = re.compile(r"CYCLE-\d+")
_RE_CIFRA_DE_TESTS = re.compile(r"(?<!\d)(\d{1,4})\s+tests\b")
# Un VEREDICTO de este panel es su tramo en negrita, y MEDIDO el 2026-10-02 las
# SIETE filas exentas escriben el marcador de cierre dentro de uno. Por eso el
# cierre se busca en los veredictos y no en la fila entera: una palabra suelta en
# prosa -- "y esta fila NO esta CERRADA todavia", o un `(marcada *CERRAD*)` al
# final -- deja de eximir a nadie, y esas dos son exactamente las formas que el
# mutation-auditor midio VIVAS contra este marcador.
_RE_NEGRITA = re.compile(r"\*\*(.+?)\*\*")
# El cierre tiene que ser TRAZABLE: un id que existe en el tablero o en un
# registro de este repo. MEDIDO: las 7 exentas tienen al menos uno (87 CYCLE-045 y
# TASK-055, 90 TASK-057, 93 TASK-031, 94 CYCLE-026/047 y TASK-057, 96 y 97
# TASK-037, 99 CYCLE-044 y TASK-054), luego exigirlo NO obliga a tocar ninguna fila.
_RE_ID_TRAZABLE = re.compile(r"(?:TASK|CYCLE)-\d+")
# Un veredicto que NIEGA el cierre no cierra, y la negacion se evalua donde
# HABLA LA FILA: en su prosa y en el veredicto que lleva el marcador. MEDIDO el
# 2026-10-02, con el predicado viejo (`NO|NUNCA|JAMAS` en los 40 caracteres
# ANTERIORES al marcador) cuatro frases mas convertian una fila viva en EXENTA
# con `0 FAIL`, todas sobre la 89: la negacion DESPUES del marcador (V1), la
# negacion FUERA de la negrita (V2), la negacion cortada por un punto y coma
# (V5) y la comparativa indirecta que el regex no puede conocer (V4). Una
# ventana cortable por puntuacion no es una negacion: se evalua la fila entera
# y sin ventana.
#
# Y el alcance NO es la fila entera, que es lo que haria passer a VIVA la fila
# 87: sus dos `NO` en mayusculas ("**NO lo importaba y NO estaba muerto**") son
# un aserto sobre el fichero archivado, no sobre el cierre de la fila, y estan
# dentro de OTRO veredicto. MEDIDO: con la negacion buscada en toda la fila, las
# 7 exentas pasan a 6, y la 87 tendria que exigir ancla siendo un registro
# historico cerrado. La prosa -- la fila menos sus veredictos -- mas el veredicto
# del marcador es lo que separa los dos asertos.
#
# `re.IGNORECASE` se APLICO y se QUITO, y el motivo medido es el que decide:
# en castellano `no` y `nunca` son palabras ordinarias, no una forma. MEDIDO el
# 2026-10-02 con el predicado insensible a caja: las SIETE exentas pasan a CERO
# y el repo se pone en rojo con 1 FAIL. Los falsos positivos no son ruido, son
# denegaciones de cierre escritas de verdad -- la 93 dice "**CERRADA en la
# cola, no en el cuerpo**" y la 96 "**CERRADA en CYCLE-027 (TASK-037) - guardas
# que no guardaban**" -- donde la negacion contrasta dos cosas y NO niega que
# la fila este cerrada. No hay ninguna forma que separe "no en el cuerpo" de
# "nunca se resolvio": las dos son negacion en minuscula sobre el mismo
# marcador. La caja es la FORMA, y por el mismo argumento que ya fija el
# limite 18 para `CERRADA`/`cerrada`. MEDIDO que el ataque que el auditor
# midio -- ` - **CERRADA en TASK-059, nunca se resolvio**` en la fila 88 -- muere
# IGUAL con la quinta condicion de `_esta_cerrada`, porque `TASK-059` esta
# `pending`: son el mismo ataque por la misma puerta. Queda declarado el
# residuo que si sobrevive, que es el unico que importa y se declara junto a
# el limite 19.
_RE_NEGACION_DEL_CIERRE = re.compile(r"\b(?:NO|NUNCA|JAMAS)\b")
# El panel se cita a si mismo y el contrato dice, textual, que la verdad de una
# fila se deriva FUERA de el. MEDIDO el 2026-10-02: 5 de las 15 filas reales (87,
# 89, 97, 100 y 101) citan `STATUS.md` y el check lo contaba como ruta valida,
# luego el panel ya se autocertificaba. NINGUNA de las cinco se queda sin fuente
# al rechazar esta: las cinco tienen ademas rutas y tareas propias. La
# COMPARACION es por IDENTIDAD de ruta resuelta y no por igualdad de cadena del
# nombre escrito: MEDIDO que cuatro formas del mismo panel (`status.md`, `./`,
# `docs/../` y `.\`) colaban con `0 FAIL` y 36 anclas porque solo se comparaba el
# texto. La quinta grafia (`STATUS.MD`) no colaba nunca, y no por esta regla sino
# porque `_RE_RUTA` exige la extension en minusculas.
#
# Y la identidad tiene una SEGUNDA forma, porque un enlace DURO evade la
# primera. MEDIDO el 2026-10-02: un hard link a `STATUS.md` en `docs/` es el
# MISMO fichero (`st_dev` y `st_ino` iguales, `st_nlink` 2) con un `realpath`
# DISTINTO, luego pasaba el filtro como ancla legitima: `36` anclas, `3` por
# contenido y `0 FAIL` de Deuda, cuelando S1 y S2 a la vez. Un enlace simbolico
# y una junction si los cierra `realpath`; el duro no cambia de nombre, luego
# no hay ruta que canonicalizar. Ver `_es_el_mismo_fichero`.
EL_PANEL_NO_ES_ANCLA = "STATUS.md"
# Fin de frase para decidir si una cifra `N tests` esta ATRIBUIDA a otro documento
# (S5). El punto cuenta solo seguido de espacio: los nombres de fichero lo llevan
# pegado ("`docs/index.md:25`") y un corte por `.` a secas partiria la frase
# justo donde esta la atribucion.
_RE_FIN_DE_FRASE = re.compile(r"\.\s")
# La gravedad del panel esta en EMOJI, no en palabra: MEDIDO el 2026-10-02 con
# `_gravedad_declarada` fila a fila, de las 15 filas reales **cinco** no
# declaran ninguna (88, 91, 92, 95 y 97) y las otras diez si: **ocho** declaran
# `ROJO` (87, 89, 90, 93, 94, 96, 98 y 99) y **dos** `AMARILLO` (100 y 101). La
# version anterior de este comentario decia "14 de las 15 no tienen ni una
# palabra" y se apoyaba en que la unica con palabra era la 98: es falso, y lo
# era porque se habia mirado el TEXTO sin mapear los glifos que se estaba
# contando. La 98 usa `ROJO` como el COLOR de un diagnostico de UI y no como
# severidad, lo cual no la invalida para este proposito. El suelo se leia por
# palabra, luego no se ejecutaba nunca -- lo que el mutation-auditor midio como
# G2 y G3a. Se mapea el glifo a la palabra AL LEER, y el informe sigue siendo
# ASCII puro (trampa #16: la consola es cp1252).
GLIFOS_DE_GRAVEDAD = {
    "\U0001f534": "ROJO",
    "\U0001f7e1": "AMARILLO",
    "\U0001f7e2": "VERDE",
}
# La gravedad se lee como PALABRA y no como simbolo en el INFORME: la consola es
# cp1252 (trampa #16) y un emoji en el `print()` tumba el validador entero.
_RE_GRAVEDAD = re.compile(r"\b(ROJO|AMARILLO|VERDE)\b")
CODIGOS_DE_SALIDA_SOBRECARGADOS = ("WOPT_COMMIT_OK", "WOPT_NOOP")
# Que un fichero DECLARE el codigo de salida sobrecargado es una FORMA, no una
# mencion. MEDIDO el 2026-10-02 con el predicado viejo ("un 0 antes del nombre en
# cualquier linea"): casaba en `validate_docs.py`, en `run_tests.py`, en
# `tasks.json` y en el propio `STATUS.md`, y por eso el suelo ataba a filas cuya
# materia prima es otra y bajar el emoji de la 100 habria puesto el repo en rojo.
# La DECLARACION es la linea que EMPIEZA por el token `0` seguido del nombre, que
# es como lo escribe `.taskmaster/git_safe_commit.py:13-14`; una tabla que TABULA
# el contrato (`docs/ai/sandbox-rules.md:55-56`) lo documenta, no lo declara.
_RE_DECLARACION_DE_CODIGO = re.compile(r"^[ \t]*0[ \t]+")
# Marca de la fila que ESCRIBE el criterio. MEDIDO: solo la nombra esa fila, y
# ninguna de las 7 exentas. Se usa el nombre de la funcion y no la palabra
# "criterio" porque la fila 93, que esta CERRADA de verdad, habla de "el check de
# anclas pendiente (TASK-060)" y se refiere a trabajo futuro.
NOMBRE_DE_LA_FILLA_DEL_CRITERIO = "_comprobar_deuda_con_anclas"


def _leer_texto(root, relativa):
    """El texto de un fichero del arbol por su ruta relativa, o `None`.

    `None` y no `""`: un fichero ausente y un fichero vacio son fallos
    distintos, y quien cita un ancla tiene que poder nombrar cual de los dos es.
    SIN CACHE de ningun tipo, y a proposito: los tests construyen arboles
    sinteticos en el MISMO proceso, y una cache de modulo devolveria el contenido
    del arbol anterior, que es un falso verde con forma de acierto.
    """
    try:
        with open(os.path.join(root, *relativa.split("/")), encoding="utf-8",
                  errors="replace") as f:
            return f.read()
    except OSError:
        return None


def _seccion_de_deuda(cuerpo):
    """`(lineas, numero_de_linea_de_la_primera)`, o `None` si no hay seccion.

    Desde el encabezado `## ` que contiene `Deuda` hasta el siguiente `## `.
    MEDIDO: la seccion es la ULTIMA de `STATUS.md` y llega hasta el final del
    fichero. `None` NO es `[]`: una seccion ausente y una seccion vacia son
    fallos distintos, y el check acusa los dos con motivos distintos.
    """
    lineas = (cuerpo or "").split("\n")
    inicio = None
    for i, linea in enumerate(lineas):
        if linea.startswith("## ") and "Deuda" in linea:
            inicio = i
            break
    if inicio is None:
        return None
    fin = len(lineas)
    for j in range(inicio + 1, len(lineas)):
        if lineas[j].startswith("## "):
            fin = j
            break
    return lineas[inicio:fin], inicio + 1


def _filas_de_deuda(cuerpo):
    """`[(numero_de_linea, fila)]` de la seccion de Deuda. `[]` si no hay seccion.

    Una fila es una linea que empieza por `- **`, y el corte es POR LINEA a
    proposito: una fila de deuda escrita como sub-vineta no es una fila, y
    contarla haria que el check seudocomprobara algo que no lee.
    """
    seccion = _seccion_de_deuda(cuerpo)
    if seccion is None:
        return []
    lineas, primera = seccion
    return [(primera + i, linea) for i, linea in enumerate(lineas)
            if linea.startswith("- **")]


def _porta_el_marcador_de_cierre(fila):
    """`True` si la fila PORTA el marcador de cierre, sin mirar el ESTADO de sus ids.

    Son las condiciones 1, 2 y 4 de `_esta_cerrada`: la palabra `CERRADA`/
    `CERRADO` en mayusculas y fuera de codigo inline, DENTRO de un veredicto en
    negrita, y sin negacion en ese veredicto ni en la prosa de la fila.

    Va SEPARADA de `_esta_cerrada` por una razon medida, no por estilo: la
    AUTOEXENCION de la fila del criterio tiene que evaluarse ANTES del requisito
    de estado. MEDIDO el 2026-10-02: con el orden contrario, la fila del criterio
    que se marca `**CERRADA en TASK-002**` -- y `TASK-002` esta `pending` -- deja
    de estar cerrada, el veredicto pasa de "la fila del criterio se ha
    autoeximido" a "VIVA sin ancla resoluble" y el escenario (f2) de la suite se
    rompe. Eso es el guard que vigila al vigilante apagandose a si mismo, y es
    justo la clase de fallo que este check existe para cerrar: la
    autoexencion se juzga por la FORMA de la fila, no por si su id|worko ya
    estaba hecho.
    """
    texto = fila or ""
    # La negacion se evalua en la PROSA -- la fila menos sus veredictos -- y en
    # el veredicto del marcador. No en la fila entera: la 87 lleva dos `NO` en
    # un veredicto que habla del fichero archivado, y con la fila entera pasaria
    # a VIVA siendo un registro historico cerrado.
    prosa = _RE_NEGRITA.sub(" ", texto)
    for veredicto in _RE_NEGRITA.findall(texto):
        limpio = _RE_CODIGO_INLINE.sub(" ", veredicto)
        if not _RE_CERRADA.search(limpio):
            continue
        if _RE_NEGACION_DEL_CIERRE.search(limpio):
            continue
        if _RE_NEGACION_DEL_CIERRE.search(prosa):
            continue
        return True
    return False


def _esta_cerrada(root, fila):
    """`True` si la fila esta CERRADA de verdad: cuatro condiciones a la vez.

    El marcador de cierre solo se aceptaba como palabra suelta, y MEDIDO el
    2026-10-02 eso no hacia nada: la fila 89 (la 🔴 del `spawn EPERM`) se
    eximia a si misma con CUALQUIER frase normal que hablara de cierre --
    "y esta fila NO esta CERRADA todavia" la volvia EXENTA y el validador
    respondia 115 OK / 0 FAIL. Cuatro condiciones, todas medidas sobre las 7
    filas exentas reales, que las cumplen sin tocar una sola:

    1. La PALABRA `CERRADA`/`CERRADO` en mayusculas FUERA de codigo inline (el
       `sub` que ya estaba: sin el, el panel se exime escribiendo el criterio
       entre comillas). Con final de palabra, porque el plural y el comparativo
       ("CERRADAS todas", "a diferencia de las CERRADAS") no son un veredicto.
    2. El marcador esta dentro de un VEREDICTO en negrita. Una mencion en
       prosa o en cursiva no cierra nada.
    3. La fila nombra un id TRAZABLE (`TASK-NNN` o `CYCLE-NNN`) que existe en
       `.taskmaster/tasks.json` o en un changelog o en el journal.
    4. Ni el veredicto ni la prosa de la fila NIEGAN el cierre.

    Las cuatro son `_porta_el_marcador_de_cierre` y se preguntan sin mirar el
    estado de los ids, porque la AUTOEXENCION de la fila del criterio las usa
    sola (ver ahi por que el orden importa).

    Y hay una **quinta**, que es la que cierra el agujero G2f': el id que cierra
    la fila tiene que estar **CERRADO**, no pendiente. La razon esta medida, no
    supuesta: los ids de las 7 exentas estan todos DENTRO del veredicto -- 87
    `TASK-055`/`CYCLE-045`, 99 `TASK-054`/`CYCLE-044`, 96 y 97
    `TASK-037`/`CYCLE-027` -- luego "el id tiene que estar fuera del veredicto"
    NO los separa del ataque. Lo que los separa del ataque es que las 7 nombran
    solo trabajo TERMINADO: MEDIDO que los dos unicos ids `pending` del tablero
    son `TASK-059` y `TASK-061`, que son exactamente los que usaba el ataque al
    anadir ` - **CERRADA en TASK-059**` a la fila 88 (`8 exenta(s) / 7 viva(s)`,
    `33` anclas, `0 FAIL`). Con la quinta puesta y el panel intacto el repo
    sigue en `7 exenta(s) / 8 viva(s) / 35` anclas y `0 FAIL` sin tocar una fila.

    La quinta **subsume** la tercera --un id cerrado es por definicion
    trazable--, y por eso `_ids_trazables` se borro en vez de quedarse como una
    funcion sin un solo llamante.

    Las cinco fallan ABIERTO: lo que no demuestra su cierre queda VIVA y tiene
    que demostrar su ancla, que es la direccion en la que un validador puede
    equivocarse sin dejar de vigilar nada.
    """
    if not _porta_el_marcador_de_cierre(fila):
        return False
    return bool(_ids_cerrados(root, fila))


def _ids_cerrados(root, fila):
    """Los ids de la fila que ademas estan CERRADOS: trabajo ya terminado.

    Que un id RESUELVA no basta para cerrar una fila: basta con nombrar el
    trabajo que sigue PENDIENTE, que es exactamente lo que hacia el ataque
    G2f'. MEDIDO el 2026-10-02: anadir ` - **CERRADA en TASK-059**` al final de
    la fila 88 la dejaba muda con `8 exenta(s) / 7 viva(s)`, `33` anclas y
    `0 FAIL` de Deuda, y `TASK-059` esta `pending` en el tablero.

    Aqui vivia antes una condicion mas debil, «la fila nombra un id que EXISTE»
    (`_ids_trazables`), y se **borra** en vez de quedarse como codigo muerto:
    exigir que exista es implicito en exigir que este cerrado -- un id cerrado
    es por definicion trazable -- luego la condicion no perderia nada y
    `_ids_trazables` se queda sin un solo llamante. Sin ella, `CERRADA` sola o
    `CERRADA en CYCLE-999` siguen sin alcanzar para eximirse de nada, que era
    justo lo que hacia falta.

    - Una `TASK` esta cerrada si su `status` es `completed`. MEDIDO: los dos
      unicos ids `pending` del tablero son `TASK-059` y `TASK-061`, y los dos
      son los que usaba el ataque.
    - Un `CYCLE` esta cerrado si tiene entrada en uno de los DOS changelogs,
      que es donde un ciclo terminado deja su recuento. Un `CYCLE` que solo
      aparece en `rd_journal.json` esta EN VUELO: el journal se escribe
      mientras el ciclo pasa, luego no es un cierre.

    BASTA UNO cerrado y no todos, y es una decision medida: las 7 exentas
    reales citan mas de un id (la 87, `TASK-055` y `CYCLE-045`; la 94,
    `TASK-057`, `CYCLE-026` y `CYCLE-047`) y MEDIDO que con "al menos uno
    cerrado" las 7 siguen exentas, con el panel intacto y sin tocar una fila.
    Exigir que TODOS estuvieran cerrados es un criterio MAS fuerte que este
    check no ha medido, y se declara como lo que es: una unexplored.
    """
    estados = _estados_de_tareas(root)
    cerradas = [t for t in dict.fromkeys(_RE_TAREAS.findall(fila or ""))
                if estados.get(t) == "completed"]
    return cerradas + _ciclos_cerrados(root, fila)


def _ciclos_cerrados(root, fila):
    """Los `CYCLE-NNN` de la fila con entrada en uno de los DOS changelogs.

    Deliberadamente NO mira `rd_journal.json`, que `_ciclos_de_la_fila` si mira
    para exigir que el id exista. Un ciclo se "traza" en cuanto se nombra, y se
    "cierra" cuando su entrada esta publicada en un changelog: son dos hechos
    distintos, y exigir solo el primero es lo que dejaba pasar al ataque.
    """
    registros = []
    for relativa in ("CHANGELOG.md", ".taskmaster/CHANGELOG.md"):
        texto = _leer_texto(root, relativa)
        if texto:
            registros.append(texto)
    return [c for c in dict.fromkeys(_RE_CICLOS.findall(fila or ""))
            if any(c in registro for registro in registros)]


def _ruta_de_ancla(root, nombre):
    """La ruta REAL del arbol a la que apunta `nombre`, o `None` si no ancla.

    `STATUS.md` NO es una fuente: el panel no puede certificarse a si mismo, y
    el contrato de `TASK-060` lo dice textual ("la verdad debe derivarse de
    FUERA del panel") sin que ninguna parte del codigo lo aplicara. MEDIDO el
    2026-10-02: cinco de las quince filas reales (87, 89, 97, 100 y 101) citan
    `STATUS.md` y el check lo contaba como ruta resuelta.

    Y el rechazo es por IDENTIDAD de la ruta RESUELTA, no por igualdad de cadena
    del nombre escrito. MEDIDO el 2026-10-02 que la igualdad de cadena dejaba
    cuatro puertas al mismo panel -- `status.md`, `./STATUS.md`, `docs/../STATUS.md`
    y `.\\STATUS.md` -- y las cuatro con `0 FAIL` y 36 anclas: una fila que se
    certifica a si misma por cualquiera de ellas salia en verde. MEDIDO
    tambien que rechazar el panel no deja a ninguna de las cinco filas sin
    fuente: todas tienen ademas rutas y tareas propias, luego el veredicto no
    cambia ni una vez.
    """
    real = _ruta_existente(root, nombre)
    if real is None:
        return None
    return None if _es_el_propio_panel(root, real) else real


def _es_el_propio_panel(root, relativa):
    """`True` si la ruta `relativa` del arbol ES el propio `STATUS.md`.

    DOS formas, y hacen falta las dos porque cada una cierra una puerta
    distinta.

    1. IDENTIDAD DE RUTA RESUELTA. MEDIDO: en Windows `os.path.realpath` llama
       a `_getfinalpathname`, que devuelve el nombre REAL del fichero, luego
       las cinco grafias (`STATUS.md`, `status.md`, `./STATUS.md`,
       `docs/../STATUS.md` y `.\\STATUS.md`) colapsan al mismo camino CON LA
       MISMA CAJA. En POSIX `realpath` devuelve el nombre tal cual y un
       `status.md` en un arbol donde el fichero se llama `STATUS.md` no existe,
       luego `_ruta_existente` ni lo encuentra: la misma regla sirve en las dos
       plataformas sin normalizar nada a mano.
    2. IDENTIDAD DE FICHERO, para el ENLACE DURO. MEDIDO el 2026-10-02: un hard
       link a `STATUS.md` creado en `docs/` comparte `st_dev` y `st_ino` con el
       panel y tiene `st_nlink == 2`, pero su `realpath` es OTRO, luego la
       forma 1 lo aceptaba como ancla legitima -- `36` anclas, `3` por
       contenido y `0 FAIL` de Deuda, cuelando S1 y S2 a la vez. Un enlace
       simbolico y una junction SI los cierra la forma 1; el duro no cambia de
       nombre, luego no hay nada que canonicalizar. Ver `_es_el_mismo_fichero`.

    `os.path.normcase` se ha QUITADO y no es una perdida. MEDIDO contra la
    stdlib: `posixpath.normcase` es literalmente `return os.fspath(s)` con
    docstring "Has no effect under Posix", luego en POSIX no hace NADA y no
    puede ser una segunda garantia ahi; y en Windows `realpath` ya devuelve el
    nombre real, luego la forma 1 no necesita mas. La version anterior de este
    docstring lo llamaba "segunda garantia para los sistemas donde `realpath` no
    canonicaliza la caja", y esa frase era FALSA en las dos plataformas: lo que
    queda inerte no es una garantia, es una llamada.
    """
    if not relativa:
        return False
    panel = os.path.join(root, EL_PANEL_NO_ES_ANCLA)
    otra = os.path.join(root, *relativa.split("/"))
    if os.path.realpath(panel) == os.path.realpath(otra):
        return True
    return _es_el_mismo_fichero(panel, otra)


def _es_el_mismo_fichero(uno, otro):
    """`True` si las dos rutas son el MISMO fichero y no dos nombres de uno.

    `os.stat` y la pareja `(st_dev, st_ino)`, que es la identidad de fichero en
    cualquier plataforma con `stat`. El guardia del `st_ino` NO es cosmetico: en
    un sistema de ficheros que no da indice, `st_ino` vale `0` para todo, y sin
    el guardia `0 == 0` declararia el panel IDENTICO a cualquier fichero del
    arbol -- que es peor que el agujero que cierra. MEDIDO en Windows:
    `st_ino` vale `6755399442173827` para el panel y para su hard link, y
    `6755399442173791` para `run_tests.py`, luego la identidad separa los tres.
    """
    try:
        a, b = os.stat(uno), os.stat(otro)
    except OSError:
        return False
    if not a.st_ino or not b.st_ino:
        return False
    return a.st_dev == b.st_dev and a.st_ino == b.st_ino


def _ruta_existente(root, nombre):
    """La ruta del arbol a la que apunta `nombre`, o `None` si no existe.

    La EXISTENCIA sola, sin el filtro del panel: el mensaje de "ancla no
    resoluble" tiene que distinguir "no existe en el arbol" de "existe pero no
    es fuente de verdad", y son dos hechos distintos.
    """
    for prefijo in PREFIJOS_DE_ANCLA:
        relativa = prefijo + nombre
        if os.path.isfile(os.path.join(root, *relativa.split("/"))):
            return relativa
    return None


def _citas_de_la_fila(fila):
    """`[(ruta, identificador_o_None)]`: lo que la fila CITA, no lo que dice.

    Solo se lee lo que va entre acentos graves, y un token cuenta como ruta si su
    primera palabra tiene extension de fichero. El `:linea` se descarta SIEMPRE
    (no se verifica nunca) y lo que queda a su derecha es el IDENTIFICADOR que
    la fila le atribuye a ese fichero. Medido: la atribucion explicita
    (`fichero:linea identificador`) es la unica forma que el panel usa de verdad
    -- `run_tests.py:1352 test_git_safe_commit_fail_safe` -- y es la que permite
    distinguir S1 de S2 sin inventar emparejamientos que el panel no escribe.

    Un tramo VACIO (`` `` `` o `` ` ` ``) se salta. MEDIDO el 2026-10-02:
    `palabras[0]` sobre un token vacio reventaba con `IndexError` y el validador
    entero moria con traceback SIN IMPRIMIR INFORME -- la misma clase que
    `_recuento_de_tests` en el ciclo 27 y el journal en el 47, aqui como
    regresion en codigo nuevo. Se arregla el PRODUCTOR y no el consumidor, que es
    la unica forma de no dejar la expectativa escrita a mano.
    """
    citas = []
    for token in _RE_CITAS.findall(fila or ""):
        palabras = token.split(None, 1)
        if not palabras:
            continue
        nombre = _RE_NUMERO_DE_LINEA.sub("", palabras[0].strip().rstrip(",.;:)"))
        if not _RE_RUTA.match(nombre):
            continue
        identificador = palabras[1].strip() if len(palabras) > 1 else ""
        citas.append((nombre, identificador or None))
    return citas


def _estados_de_tareas(root):
    """`{TASK-NNN: status}` de `.taskmaster/tasks.json`. `{}` si no se puede leer.

    Un `tasks.json` ilegible NO es un error propio de este check: se comporta
    como un tablero sin estados, y por eso una fila cuya unica fuente fuera una
    `TASK` sale en rojo por la regla de la tarea cerrada, que es el fallo real.
    """
    try:
        with open(os.path.join(root, ".taskmaster", "tasks.json"),
                  encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        return {}
    tareas = datos.get("tasks") if isinstance(datos, dict) else datos
    estados = {}
    for tarea in (tareas or []):
        if isinstance(tarea, dict) and tarea.get("id") and tarea.get("status"):
            estados[tarea["id"]] = str(tarea["status"])
    return estados


def _ciclos_de_la_fila(root, fila):
    """Los `CYCLE-NNN` que la fila nombra Y que existen en un registro de este repo."""
    registros = []
    for relativa in ("CHANGELOG.md", ".taskmaster/CHANGELOG.md",
                     ".taskmaster/rd_journal.json"):
        texto = _leer_texto(root, relativa)
        if texto:
            registros.append(texto)
    return [c for c in dict.fromkeys(_RE_CICLOS.findall(fila or ""))
            if any(c in registro for registro in registros)]


def _anclas_resolubles(root, fila):
    """Las CINCO fuentes de verdad de UNA fila, todas fuera del panel.

    - S1 `rutas`: la cita resuelve si el fichero EXISTE. Es la fuente mas debil
      --un fichero puede existir y decir lo contrario-- y por eso no sostiene
      sola una fila que solo se apoya en una `TASK` ya cerrada.
    - S2 `contenido`: la cita trae identificador y el fichero lo contiene.
    - S3 `tareas`: `TASK-NNN` con `status` legible. Un `completed` NO computa
      como comprobable de una fila viva: lo escribe la propia fila 93.
    - S4 `ciclos`: `CYCLE-NNN` con entrada en un changelog o en el journal.
    - S5 `numeros`: las cifras que la fila declara como numero de tests. La
      coincidencia con el derivado la juzga el cuerpo, que ya tiene el `ast`.
    """
    rutas, contenido = [], []
    for nombre, identificador in _citas_de_la_fila(fila):
        real = _ruta_de_ancla(root, nombre)
        if real is None:
            continue
        if real not in rutas:
            rutas.append(real)
        if identificador:
            cuerpo = _leer_texto(root, real) or ""
            if identificador in cuerpo:
                contenido.append((real, identificador))
    estados = _estados_de_tareas(root)
    return {
        "rutas": rutas,
        "contenido": contenido,
        "tareas": {tid: estados[tid] for tid in dict.fromkeys(
            _RE_TAREAS.findall(fila or "")) if tid in estados},
        "ciclos": _ciclos_de_la_fila(root, fila),
        "numeros": [int(n) for n in _RE_CIFRA_DE_TESTS.findall(fila or "")],
    }


def _declara_el_codigo_sobrecargado(root, relativa):
    """`True` si el fichero DECLARA `0` para los DOS codigos de salida `0`.

    El suelo de gravedad (el S1 del ciclo #48) se apoya en UN comprobable, y este
    es el unico que existe en el repo de forma estable: `git_safe_commit.py`
    declara `0` para `WOPT_COMMIT_OK` y para `WOPT_NOOP`. Se exigen los DOS en el
    MISMO fichero porque un `0` suelto en un fichero cualquiera no demuestra
    nada.

    DECLARAR es una FORMA y no una mencion, y el cambio no es cosmetico. MEDIDO
    el 2026-10-02: buscando "un 0 antes del nombre en cualquier linea" el
    predicado casaba en `validate_docs.py` (su propio docstring), en `run_tests.py`
    (la cadena de una fixture), en `.taskmaster/tasks.json` (la descripcion de
    una tarea) y en el propio `STATUS.md`. Con esa lectura, mapear el emoji
    habria puesto el repo en rojo HOY: las filas 100 y 101 declaran 🟡 y citan
    ficheros que solo MENCIONAN el contrato. Se exige la linea que empieza por el
    token `0` seguido del nombre, que es como lo escribe
    `.taskmaster/git_safe_commit.py:13-14`; la tabla de
    `docs/ai/sandbox-rules.md:55-56` lo TABULA y no lo DECLARA.
    """
    cuerpo = _leer_texto(root, relativa) or ""
    for codigo in CODIGOS_DE_SALIDA_SOBRECARGADOS:
        forma = re.compile(r"^[ \t]*0[ \t]+" + codigo + r"\b", re.MULTILINE)
        if not forma.search(cuerpo):
            return False
    return True


def _gravedad_declarada(fila):
    """La severidad que la fila DECLARA, como palabra ASCII, o `None`.

    El panel se expresa en emoji y el validador leia en palabras, luego el suelo
    no se ejecutaba nunca: MEDIDO el 2026-10-02, 14 de las 15 filas no tienen ni
    una palabra `ROJO`/`AMARILLO`/`VERDE`, y la unica que la tiene (la 98) la usa
    para el color de un diagnostico de UI. El mapeo va al LEER, no al imprimir:
    el informe sigue siendo ASCII puro porque la consola es cp1252 (trampa #16).
    """
    texto = _RE_CODIGO_INLINE.sub(" ", fila or "")
    for glifo, palabra in GLIFOS_DE_GRAVEDAD.items():
        texto = texto.replace(glifo, " " + palabra + " ")
    encontrado = _RE_GRAVEDAD.search(texto)
    return encontrado.group(1) if encontrado else None


def _severidad_minima(root, anclas):
    """`"ROJO"` si algun ancla de ruta DECLARA el codigo sobrecargado; `""` si no.

    UN solo suelo, y es una DECISION: la gravedad de una fila es un TEXTO, y
    derivarla exigiria escribir a mano la politica de gravedad, que es la misma
    mentira un nivel mas arriba. Lo unico que se deriva de verdad es si el
    PROBLEMA sigue vivo.

    Se recorre la lista de ANCLAS y no la de asuntos del titulo, y es una
    decision medida. El auditor propuso atar el suelo a los asuntos porque al
    mapear el emoji las filas 100 y 101 salen en rojo; medido, esas dos filas NO
    citan `git_safe_commit.py` y lo que las hacia tropezar era el predicado, que
    caseba en `validate_docs.py`, `run_tests.py`, `tasks.json` y el propio panel.
    Arreglado el PREDICADO (que era la causa), atar el suelo al titulo lo dejaria
    muerto para siempre -- ni una sola fila nombra en su titulo un fichero que
    declare el contrato -- y con el se iria el unico criterio del contrato que
    este suelo tiene que matar (M5: bajar la 🔴 de la 88 o de la 89).

    `root` va de primero y no es mio: el contrato de la tarea lo decia con un
    solo argumento, pero un auxiliar que LEE el arbol no puede derivar `root` de
    si mismo, y la regla que ese contrato impone ("todo se deriva de `root`")
    solo se puede cumplir si `root` le llega. Se reporta como desviacion.
    """
    for relativa in anclas.get("rutas", ()):
        if _declara_el_codigo_sobrecargado(root, relativa):
            return "ROJO"
    return ""


def _cita_un_fichero(frase):
    """`True` si `frase` cita un fichero del arbol entre acentos graves."""
    for token in _RE_CITAS.findall(frase or ""):
        palabras = token.split(None, 1)
        if not palabras:
            continue
        nombre = _RE_NUMERO_DE_LINEA.sub("", palabras[0].strip().rstrip(",.;:)"))
        if _RE_RUTA.match(nombre):
            return True
    return False


def _cifras_declaradas_sin_atribuir(fila):
    """`[int]`: las cifras `N tests` que la fila DECLARA sin atribuirlas.

    Una cifra ATRIBUIDA es la que la fila le endosa a otro documento -- dentro
    de codigo inline, o en la misma frase que cita un fichero. Una cifra SUELTA
    es una AFIRMACION de la fila sobre el recuento, y solo esa se comprueba
    contra el derivado con `ast`.

    MEDIDO el 2026-10-02 sobre el panel real: las TRES cifras que declaran las
    filas vivas (100 declara «96 tests» dos veces y 101 declara «103 tests») son
    atribuciones a `docs/index.md`, y sin esta distincion el arreglo de N1 --
comparar las declaradas contra el derivado -- pondria el repo en rojo hoy por
    una fila que cita un numero A PROPOSITO para explicar una correccion. Y al
    reves: verificarlas contra el fichero al que se atribuyen es peor, porque la
    fila 100 existe para documentar que un documento declaraba una cifra
    desfasada, y comprobarla contra el contenido actual de ese documento haria
    su sujeto imposible de redactar.
    """
    texto = fila or ""
    tramos = [(m.start(), m.end()) for m in _RE_CITAS.finditer(texto)]
    sueltas = []
    for m in _RE_CIFRA_DE_TESTS.finditer(texto):
        if any(inicio <= m.start() < fin for inicio, fin in tramos):
            continue
        antes = _RE_FIN_DE_FRASE.split(texto[:m.start()])[-1]
        despues = _RE_FIN_DE_FRASE.split(texto[m.end():])[0]
        frase = antes + texto[m.start():m.end()] + despues
        if _cita_un_fichero(frase):
            continue
        sueltas.append(int(m.group(1)))
    return sueltas


def _comprobar_deuda_con_anclas(root, errors, ok):
    """CHECK 8 (TASK-060, ciclo #49): toda fila VIVA de la Deuda Tecnica Conocida
    necesita un ancla resoluble cuya verdad se derive FUERA del panel.

    Sin defaults y sin parametros extra: todo se deriva de `root`, por el motivo
    que ya pago TASK-037. `main()` deriva `root` de `__file__` y no admite argv,
    asi que sin raiz el residuo que este check caza NO se puede construir en un
    test; y un default convertiria un cableado roto en un `None` silencioso, que
    es la clase de fallo que D1 cerro en el ciclo #47.

    MEDIDO el 2026-10-02 al nacer: 15 filas, 7 exentas y 8 vivas, y de las 8 vivas
    solo `STATUS.md:91` se quedaba sin ninguna fuente resoluble -- por eso el
    nacimiento toco UNA fila y no tres. Las exentas NO son filas mudas por
    capricho: son registros historicos, y exigirles anclas haria que el check
    fallara siempre y luego nadie lo mirara, que es como muere un validador.
    """
    ruta_status = os.path.join(root, "STATUS.md")
    if not os.path.exists(ruta_status):
        errors.append(
            "STATUS.md: NO EXISTE, no se puede comprobar la seccion de Deuda "
            "Tecnica Conocida, que es la que gobierna el Paso 1 del bucle"
        )
        return
    with open(ruta_status, encoding="utf-8") as f:
        cuerpo = f.read()

    if _seccion_de_deuda(cuerpo) is None:
        errors.append(
            "STATUS.md: no existe la seccion de Deuda Tecnica Conocida. Sin "
            "seccion no hay bucle que priorizar, y un validador que no encuentra "
            "lo que valida no es un validador"
        )
        return

    filas = _filas_de_deuda(cuerpo)
    if not filas:
        errors.append(
            "STATUS.md Deuda Tecnica Conocida: 0 fila(s). La seccion que gobierna "
            "el Paso 1 vaciada es indistinguible de la que aun no existe"
        )
        return

    recuento = _recuento_de_tests(os.path.join(root, "run_tests.py"))
    derivado = recuento[0] if recuento else None
    exentas = vivas = rutas_resueltas = contenido_resuelto = 0

    for numero, fila in filas:
        anclas = _anclas_resolubles(root, fila)

        # La AUTOEXENCION se juzga ANTES y POR SEPARADO del estado de los ids,
        # y no por orden de lectura sino porque son dos preguntas distintas.
        # MEDIDO el 2026-10-02: si se preguntara solo a `_esta_cerrada`, la fila
        # del criterio que se marca `**CERRADA en TASK-002**` (pending) dejaria
        # de estar cerrada, el veredicto pasaria de "la fila del criterio se ha
        # autoeximido" a "VIVA sin ancla resoluble" y el escenario (f2) se
        # romperia. La pregunta es "esta fila se ha eximido a si misma?", y eso
        # lo decide la FORMA -- que nombre este check -- no si el trabajo que
        # cita ya estaba hecho. Medirla despues de exigir el estado es dejar el
        # guard que vigila al vigilante condicionado a que el vigilante pase.
        autoeximida = (NOMBRE_DE_LA_FILLA_DEL_CRITERIO in fila
                       and _porta_el_marcador_de_cierre(fila))

        if _esta_cerrada(root, fila) or autoeximida:
            exentas += 1
            # Una fila que ESCRIBE el criterio no puede declararse CERRADA: se
            # vigila a si misma y el check nace verde sobre lo que tiene que
            # vigilar. MEDIDO el 2026-10-02: de las 7 exentas, ni una nombra este
            # check, y la unica que lo nombra es la fila 101, que esta VIVA. La
            # marca es el NOMBRE de la funcion, no la palabra "criterio": la
            # fila 93 (CERRADA de verdad) dice "el check de anclas pendiente
            # (TASK-060)" y se refiere a trabajo FUTURO, que es un puntero
            # legitimo y no una autoexencion. Sin esta clausula, poner `CERRADA`
            # en la fila del criterio la deja muda y en verde, que es el fallo
            # que el criterio describe. Y la mira `autoeximida`, que ya se
            # resolvio ARRIBA y sin mirar el estado: repetir aqui el
            # `NOMBRE_DE_LA_FILLA_DEL_CRITERIO in fila` solo seria otra forma
            # de preguntar lo mismo.
            if autoeximida:
                pendientes = sorted(t for t, s in anclas["tareas"].items()
                                     if s != "completed")
                errors.append(
                    f"STATUS.md Deuda fila {numero}: la fila del criterio se ha "
                    "autoeximido: lleva el marcador de cierre en un veredicto y es "
                    f"la fila que escribe este check"
                    + (f", declarando ademas {', '.join(pendientes)} sin cerrar"
                       if pendientes else "")
                    + ". Una fila que exige anclas no puede quedarse sin vigilar"
                )
            continue

        vivas += 1
        rutas_resueltas += len(anclas["rutas"])
        contenido_resuelto += len(anclas["contenido"])

        # La atribucion rota se acusa SIEMPRE, con o sin otras fuentes: un
        # fichero que existe NO demuestra que la fila apunte a lo que dice, y esa
        # es justo la diferencia entre S1 y S2.
        for nombre, identificador in _citas_de_la_fila(fila):
            real = _ruta_de_ancla(root, nombre)
            if real is None or not identificador:
                continue
            if identificador not in (_leer_texto(root, real) or ""):
                errors.append(
                    f"STATUS.md Deuda fila {numero}: {real} existe pero NO contiene "
                    f"el identificador que la fila le atribuye: {identificador}. "
                    "Un fichero que existe no demuestra que la cita apunte a lo "
                    "que dice"
                )

        tareas_vivas = {t: s for t, s in anclas["tareas"].items()
                        if s != "completed"}
        fuentes = []
        if anclas["rutas"]:
            fuentes.append("ruta")
        if anclas["contenido"]:
            fuentes.append("contenido")
        # Una `TASK` cuenta como fuente RESUELTA tambien cuando esta cerrada: la
        # fila la nombra y existe. Lo que no vale es que sea la UNICA, y eso lo
        # acusa la regla de mas abajo. Contarlas solo si estan abiertas hacia el
        # mensaje equivocado --una fila con una `TASK` cerrada y nada mas salia
        # como "0 fuentes de 5" en vez de "su unica fuente es una tarea cerrada"--
        # y hacia que la regla de la tarea cerrada no se ejecutase nunca.
        if anclas["tareas"]:
            fuentes.append("tarea")
        if anclas["ciclos"]:
            fuentes.append("ciclo")
        if anclas["numeros"]:
            if derivado is None:
                errors.append(
                    f"STATUS.md Deuda fila {numero}: declara el numero "
                    f"{anclas['numeros']} y NO SE PUEDE derivar el recuento de "
                    "run_tests.py, asi que la cifra que declara esta fila no se "
                    "puede comprobar. Nunca verde por omision"
                )
            elif derivado in anclas["numeros"]:
                # S5 acredita la cifra que la fila DECLARA, no la que la fila
                # menciona de pasada. MEDIDO: el predicado viejo era
                # `re.search(derivado, fila)`, asi que basta con que el derivado
                # apareciera en CUALQUIER frase de la fila -- y mutar la cifra
                # que la fila declara ("96 tests" -> "42 tests" en la 100)
                # conservando el 104 en otra frase salia en verde.
                fuentes.append("numero")
            elif _cifras_declaradas_sin_atribuir(fila):
                # Si TODAS las cifras de la fila son CITAS de otro documento
                # (`docs/index.md` declara «96 tests», «(103 tests)») no se acusa
                # nada: una cita es informacion, no una afirmacion de la fila, y
                # comprobarla contra el contenido actual de ese documento haria
                # imposible de redactar la fila 100, que existe para documentar
                # precisamente que ese documento declaraba una cifra desfasada.
                # Queda declarado como limite residual, no escondido.
                errors.append(
                    f"STATUS.md Deuda fila {numero}: declara el numero "
                    f"{_cifras_declaradas_sin_atribuir(fila)} que NO es el "
                    f"derivado con ast de run_tests.py ({derivado}). El panel no "
                    "es fuente de verdad de si mismo"
                )

        if not fuentes:
            errors.append(
                f"STATUS.md Deuda fila {numero}: VIVA sin ancla resoluble "
                "(0 fuentes de 5). Una fila de la seccion que gobierna el bucle "
                "sin prueba fuera del panel es la que manda hacer un trabajo ya "
                "hecho"
            )
            for nombre, _ in _citas_de_la_fila(fila):
                # Por IDENTIDAD de ruta resuelta, no por el nombre escrito: con
                # la igualdad de cadena, una cita `status.md` que SI existe
                # recebia el motivo de "no existe en el arbol", que es falso.
                if _es_el_propio_panel(root, _ruta_existente(root, nombre)):
                    errors.append(
                        f"STATUS.md Deuda fila {numero}: ancla NO RESOLUBLE: "
                        f"{nombre} EXISTE pero es el propio panel. La verdad de "
                        "una fila se deriva de fuera del panel; el panel "
                        "certificandose a si mismo no es un ancla, es la "
                        "ausencia de ancla"
                    )
                elif _ruta_de_ancla(root, nombre) is None:
                    errors.append(
                        f"STATUS.md Deuda fila {numero}: ancla NO RESOLUBLE: "
                        f"{nombre} no existe en el arbol (probado en la raiz, "
                        ".taskmaster/, docs/, docs/ai/ y docs/archive/). Una cita "
                        "que no resuelve no es un ancla: es decoracion"
                    )
            continue

        # La regla que se audita a si misma: una fila viva no puede apoyarse
        # SOLO en una tarea cerrada. Sin esta clausula, reabrir una fila cerrada
        # borrando su `CERRADA` la dejaria en verde si su unica prueba es un
        # `TASK-057` completado, que es exactamente el fallo que describe.
        # MEDIDO: la condicion es "la unica CLASE de fuente es una tarea Y
        # ninguna esta abierta". Con la primera parte sola, la fila 95 (que
        # cita `TASK-057` cerrado y `TASK-059` pendiente) sale en rojo: tiene
        # fuente viva y exigir mas seria un rojo sin motivo.
        if fuentes == ["tarea"] and not tareas_vivas:
            errors.append(
                f"STATUS.md Deuda fila {numero}: VIVA y su UNICA fuente es una "
                "TAREA YA CERRADA: "
                + ", ".join(f"{t}.status == {s}"
                            for t, s in sorted(anclas["tareas"].items()))
                + ". Una fila cerrada reabierta sin decirlo es el fallo que el "
                "criterio describe"
            )

        gravedad = _gravedad_declarada(fila)
        suelo = _severidad_minima(root, anclas)
        if suelo and gravedad and gravedad != "ROJO":
            vivos = [r for r in anclas["rutas"]
                     if _declara_el_codigo_sobrecargado(root, r)]
            errors.append(
                f"STATUS.md Deuda fila {numero}: declara {gravedad} pero "
                f"su comprobable SIGUE VIVO: {vivos[0] if vivos else suelo} declara "
                "0 para WOPT_COMMIT_OK y para WOPT_NOOP. La gravedad solo baja si "
                "el problema se cierra"
            )

    ok.append(
        f"STATUS.md: Deuda Tecnica Conocida: {len(filas)} fila(s), {exentas} "
        f"exenta(s) CERRADA(s), {vivas} viva(s) con {rutas_resueltas} ancla(s) de "
        f"ruta resuelta(s) y {contenido_resuelto} por contenido"
    )


def validar(root):
    """Los checks 1-8 enteros. -> `(errors, ok)`. Sin imprimir y sin salir.

    D1 (TASK-057, ciclo 47, intento 3). Por que existe, medido: durante dos
    iteraciones la suite llamo a las funciones PRIVADAS pasandoles a mano los
    argumentos, asi que el cableado que suministra esos argumentos -- `main()` ->
    `validar` -> `_comprobar_ancla_del_changelog` -> `_comprobar_ancla_de_commits`
    -- no lo probaba NADIE. Borrada una linea de ese cableado, la suite entera
    seguiria en verde: codigo testeado que el producto ya no invoca, la misma
    clase de bug que TASK-056 y en el propio ciclo que debia cerrarlo.

    Extrayendo el cuerpo a UNA funcion que `main()` llama, el producto y los
    tests ejecutan la MISMA ruta por construccion, y "el cableado que nadie
    prueba" deja de ser una categoria de bug: no hay dos rutas de validacion
    posibles que puedan divergir. `root` es parametro -- y no se deriva de
    `__file__` -- precisamente para que un test pueda apuntar el validador real
    a un arbol sintetico.
    """
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
    # 8. La seccion `## Deuda Tecnica Conocida` de STATUS.md gobierna que trabajo
    # hace el bucle cuando el backlog esta vacio, y hasta el ciclo #48 no la
    # miraba nadie. Delegado a `_comprobar_deuda_con_anclas(root, errors, ok)`,
    # con raiz y SIN defaults por el motivo de TASK-037 y de D1: un default
    # convierte un cableado roto en un `None` silencioso.
    _comprobar_deuda_con_anclas(root, errors, ok)
    return errors, ok


def main():
    """Imprime el informe de `validar(root)` y sale con su codigo. Nada mas.

    Todo lo que decide ocurre en `validar`; aqui no hay ni una condicion. Un
    `main()` con logica propia es una segunda ruta de validacion posible, que es
    justo lo que D1 viene a hacer desaparecer.
    """
    root = os.path.dirname(os.path.abspath(__file__))
    errors, ok = validar(root)

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