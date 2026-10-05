"""build_llms_full.py — genera `llms-full.txt` desde sus fuentes. Sin dependencias.

`llms-full.txt` es el agregado que `llms.txt` ofrece a los agentes: las nueve
secciones de documentacion concatenadas. Y hasta este ciclo era un fichero que
se edits a mano, lo que es exactamente el `tm.py` que este repo ya sufrio: un
pasito que depende de que alguien se acuerde.

    python build_llms_full.py --check     # guarda: no escribe, sale != 0 si diverge
    python build_llms_full.py --write     # re-emite el agregado desde las fuentes

--------------------------------------------------------------------------------
DIRECCION UNICA: fuente -> agregado. NUNCA al reves. MEDIDO, no por tastes.
--------------------------------------------------------------------------------
Las cuatro secciones que divergian (api, known-issues, github-setup-checklist,
testing) NO estaban "desactualizadas por otra causa": el agregado lleva el FOSIL
v2 y las fuentes llevan lo vigente.

* `llms-full.txt` menciona `process_manager` **28** veces, y su seccion `api`
  empieza por `## Funciones de process_manager.py (modulo)`. Ese modulo
  **no existe** en `src/`.
* `docs/api.md` menciona `process_manager` **0** veces, cita `psutil` **5**,
  cita `SYSTEM_PROTECTED_PROCESSES` y se titula *"Referencia de API (v3)"*.

Un `.replace()` agregado->fuente escribiria el fosil encima del documento bueno.
Por eso esto es un GENERADOR, no una reparacion.

--------------------------------------------------------------------------------
SE INDEXA POR LA RUTA DEL MARCADOR, NUNCA POR EL SLUG (T54-7).
--------------------------------------------------------------------------------
`docs/architecture.md` son **6 255 bytes** y `docs/ai/architecture.md` son
**62 819**, y los dos se llaman `architecture`. Un generador que derivase su
fuente del slug —que es lo natural, porque el slug es lo que aparece en la
cabecera— publicaria 6 KB donde iban 62 KB **sin ningun error visible**. El slug
es una etiqueta de navegacion; la verdad es `<!-- source: ... -->`.

--------------------------------------------------------------------------------
LA LISTA DE SECCIONES VIVE AQUI Y EN NINGUN OTRO SITIO.
--------------------------------------------------------------------------------
Antes la derivaba `os.listdir(docs/)` filtrando `.md`, y por eso el validador
esperaba una lista distinta de la que el agregado traia sin que nadie lo notara.
`validate_docs.py` importa `SECCIONES` de aqui: dos listas son dos verdades, y
se separan en silencio.
"""

import os
import re
import sys

NOMBRE_AGREGADO = "llms-full.txt"
NOMBRE_GENERADOR = "build_llms_full.py"

# La lista de secciones: DECLARADA AQUI, en el orden en que va en el agregado.
# El primer elemento de cada par es el SLUG (etiqueta de navegacion) y el
# segundo es la RUTA de la fuente (la verdad). El caso que obliga a que las dos
# cosas sean campos separados esta en la ultima fila: `ui-design-system` vive
# en `docs/ai/`, no en `docs/`, asi que un generador que mirase `docs/*.md`
# perderia esa seccion entera.
SECCIONES = (
    ("api", "docs/api.md"),
    ("architecture", "docs/architecture.md"),
    ("extending", "docs/extending.md"),
    ("github-setup-checklist", "docs/GITHUB-SETUP-CHECKLIST.md"),
    ("index", "docs/index.md"),
    ("known-issues", "docs/known-issues.md"),
    ("mini-app-status", "docs/mini-app-status.md"),
    ("testing", "docs/testing.md"),
    ("ui-design-system", "docs/ai/ui-design-system.md"),
)

# El formato ya estaba escrito en el fichero y esta medido: cinco lineas
# (`# slug`, vacia, `<!-- source: ruta -->`, vacia, `---`) mas el cuerpo.
# MEDIDO 2026-10-05: la version a mano de la NOVENA seccion (`ui-design-system`)
# se saltaba el `---`, o sea que el formato "de nueve" era una costumbre y no
# un contrato. Aqui pasa a ser las dos cosas: `--write` pone las nueve iguales.
_RE_MARCADOR = re.compile(r"^<!-- source: (?P<ruta>[^\s>]+) -->[ \t]*$", re.M)
_RE_CABECERA = re.compile(
    r"(?:\A\n|\n\n)"
    r"# (?P<slug>[A-Za-z0-9._-]+)\n\n"
    r"<!-- source: (?P<ruta>[^\s>]+) -->\n\n"
    r"---\n\n"
)

# El agregado esta en CRLF y cinco de las nueve fuentes en LF (MEDIDO: `api`,
# `architecture`, `extending` y `mini-app-status` en LF; las otras cinco en
# CRLF). Por eso TODO lo de aqui dentro es LF y el unico sitio donde aparece un
# CRLF es la escritura: un guard que comparara bytes seria un guard que depende
# de `core.autocrlf` de la maquina que hizo el checkout, que es una promesa sin
# ancla con otra forma.
FIN_DE_LINEA_DE_ESCRITURA = "\r\n"


def _ascii(texto, max_len=90):
    """`texto` en una sola linea ASCII. Trampa #16: la consola es cp1252.

    Los motivos de divergencia traen texto de las fuentes, que puede llevar
    acentos o emojis. Imprimirlos sin convertir tumba el `print` entero, que es
    justo donde vive el veredicto.
    """
    limpio = " ".join(str(texto).split())
    limpio = limpio.encode("ascii", "replace").decode("ascii")
    if len(limpio) > max_len:
        limpio = limpio[:max_len].rstrip() + "..."
    return limpio or "(vacio)"


def _leer(root, relativa):
    """El texto de `relativa` en LF, o `None` si no se puede leer.

    `newline=None` (el default) es lo que unifica los finales de linea: sin el,
    `_cola` tendria que decidir por su cuenta y el CRLF se colaria dos veces al
    escribir.
    """
    try:
        with open(os.path.join(root, relativa), encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def _cola(cuerpo):
    """El cuerpo de una seccion con UN salto final. `None` si no se pudo leer."""
    if cuerpo is None:
        return None
    return cuerpo.rstrip("\n") + "\n"


def _lineas(texto):
    """Las lineas que AFFIRMA el texto, sin los saltos que solo son formato."""
    return texto.rstrip("\n").split("\n")


def secciones_del_agregado(texto):
    """Las secciones que HAY en el agregado, tal cual, con su procedencia.

    Recorta por el marcador SIGUIENTE y no por un encabezado: MEDIDO, la
    primera medicion de este ciclo dio 100 % de las ocho secciones, y era falsa,
    porque corta por cualquier `#` y el `#` de una seccion es el TITULO de su
    propio fichero. Cutear por el marcador es lo unico que no confunde un
    encabezado del cuerpo con el encabezado de la seccion siguiente.
    """
    cabeceras = {}
    for m in _RE_CABECERA.finditer(texto):
        # El INICIO del match importa tanto como el final: la cabecera empieza
        # por los dos saltos que la separan de la seccion anterior, y el cuerpo
        # de la anterior tiene que acabar ANTES de ellos.
        cabeceras[m.start("ruta")] = (m.group("slug"), m.start(), m.end())

    marcas = list(_RE_MARCADOR.finditer(texto))
    secciones = []
    for i, marca in enumerate(marcas):
        cabecera = cabeceras.get(marca.start("ruta"))
        if cabecera is None:
            secciones.append({
                "slug": None, "ruta": marca.group("ruta"), "cuerpo": "",
                "linea": texto[:marca.start()].count("\n") + 1,
                "cabecera_ok": False,
            })
            continue
        slug, _inicio, fin = cabecera
        if i + 1 < len(marcas):
            # El cuerpo acaba donde empieza la cabecera SIGUIENTE, que se
            # lleva por delante los dos saltos que la separan de esta.
            siguiente = cabeceras.get(marcas[i + 1].start("ruta"))
            cuerpo = texto[fin:siguiente[1]] if siguiente else texto[fin:]
        else:
            cuerpo = texto[fin:]
        secciones.append({
            "slug": slug, "ruta": marca.group("ruta"), "cuerpo": cuerpo,
            "linea": texto[:marca.start()].count("\n") + 1,
            "cabecera_ok": True,
        })
    return secciones


def construir(root):
    """El agregado completo, en LF, como lo que `--write` tiene que dejar.

    Levanta `OSError` si una fuente no esta: `--write` no tiene nada que
    escribir a medias, y un agregado al que le falta una seccion es peor que no
    escribir.
    """
    partes = []
    for slug, ruta in SECCIONES:
        cola = _cola(_leer(root, ruta))
        if cola is None:
            raise OSError(f"la fuente declarada no se puede leer: {ruta}")
        partes.append(f"# {slug}\n\n<!-- source: {ruta} -->\n\n---\n\n{cola}")
    # MEDIDO en el fichero a mano: una linea vacia al principio, dos entre
    # secciones y dos al final. Se reproduce para que `--write` sea un no-op
    # sobre un agregado ya conforme y el diff sea solo del CONTENIDO.
    return "\n" + "\n\n".join(partes) + "\n"


def construir_bytes(root):
    """`construir` en los finales de linea con los que esta el agregado."""
    return construir(root).replace("\n", FIN_DE_LINEA_DE_ESCRITURA).encode("utf-8")


def _primera_linea_que_difiere(agregado, fuente):
    """`(numero, linea_del_agregado, linea_de_la_fuente)`, o `None` si son iguales."""
    la, lb = _lineas(agregado), _lineas(fuente)
    for i in range(max(len(la), len(lb))):
        x = la[i] if i < len(la) else "<seccion mas corta>"
        y = lb[i] if i < len(lb) else "<fuente mas corta>"
        if x != y:
            return (i + 1, x, y)
    return None


def comparar(root):
    """Los problemas que separan el agregado de sus fuentes. `[]` = cuadra.

    Asienta por CONTENIDO. Antes el check 2 del validador hacia
    `if d not in full`, que mira el NOMBRE del fichero: mutar una linea de
    `docs/known-issues.md` dejaba el nombre presente y el validador en verde.
    """
    problemas = []
    texto = _leer(root, NOMBRE_AGREGADO)
    if texto is None:
        return [f"{NOMBRE_AGREGADO}: no existe o no se puede leer"]

    encontradas = secciones_del_agregado(texto)

    # (1) La FORMA. Un marcador suelto, sin su cabecera de cinco lineas, es un
    # agregado que nadie sabe_bounds de donde sale: se declara aunque el
    # contenido cuadre.
    for s in encontradas:
        if not s["cabecera_ok"]:
            problemas.append(
                f"{NOMBRE_AGREGADO}:{s['linea']}: el marcador de '{s['ruta']}' no "
                f"lleva la cabecera de 5 lineas (# slug / vacia / marcador / "
                f"vacia / --- / vacia)")

    # (2) El CONJUNTO y el ORDEN declarados. Sin esto, borrar una seccion del
    # agregado dejaria un agregado "limpio" que ya no publica lo que promete.
    declaradas = [(slug, ruta) for slug, ruta in SECCIONES]
    pares = [(s["slug"], s["ruta"]) for s in encontradas if s["cabecera_ok"]]
    por_ruta = {ruta: slug for slug, ruta in declaradas}
    for slug, ruta in declaradas:
        if (slug, ruta) not in pares:
            problemas.append(
                f"{NOMBRE_AGREGADO}: falta la seccion '# {slug}' de {ruta}, que "
                f"{NOMBRE_GENERADOR} declara")
    for slug, ruta in pares:
        if (slug, ruta) not in declaradas:
            problemas.append(
                f"{NOMBRE_AGREGADO}: la seccion '# {slug}' de {ruta} NO esta "
                f"declarada en SECCIONES")
    if sorted(pares) == sorted(declaradas) and pares != declaradas:
        problemas.append(
            f"{NOMBRE_AGREGADO}: el orden de las secciones no es el declarado: "
            f"{[p[0] for p in pares]!r}")

    # (3) El CONTENIDO, seccion por seccion, contra SU ruta declarada.
    for s in encontradas:
        if not s["cabecera_ok"] or por_ruta.get(s["ruta"]) != s["slug"]:
            continue
        fuente = _leer(root, s["ruta"])
        if fuente is None:
            problemas.append(
                f"{s['ruta']}: la fuente de la seccion '# {s['slug']}' no existe o "
                f"no se puede leer")
            continue
        diferencia = _primera_linea_que_difiere(s["cuerpo"], fuente)
        if diferencia is not None:
            numero, en_agregado, en_fuente = diferencia
            problemas.append(
                f"{s['ruta']}: la seccion '# {s['slug']}' de {NOMBRE_AGREGADO} "
                f"diverge de su fuente en la linea {numero}: el agregado dice "
                f"{_ascii(en_agregado)!r} y la fuente dice {_ascii(en_fuente)!r}. "
                f"Arreglo: python {NOMBRE_GENERADOR} --write")

    return problemas


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    raiz = os.path.dirname(os.path.abspath(__file__))

    if argv == ["--check"]:
        problemas = comparar(raiz)
        if problemas:
            print(f"{NOMBRE_GENERADOR} --check: {len(problemas)} problema(s)")
            for problema in problemas:
                print(f"  - {_ascii(problema, 400)}")
            return 1
        print(f"{NOMBRE_GENERADOR} --check: las {len(SECCIONES)} secciones de "
              f"{NOMBRE_AGREGADO} coinciden con su fuente por CONTENIDO.")
        return 0

    if argv == ["--write"]:
        destino = os.path.join(raiz, NOMBRE_AGREGADO)
        try:
            nuevo = construir_bytes(raiz)
        except OSError as exc:
            print(f"{NOMBRE_GENERADOR} --write: {exc}")
            return 1
        anterior = None
        if os.path.exists(destino):
            with open(destino, "rb") as f:
                anterior = f.read()
        if anterior == nuevo:
            print(f"{NOMBRE_GENERADOR} --write: {NOMBRE_AGREGADO} ya estaba "
                  f"conforme ({len(nuevo)} bytes), no se escribe nada.")
            return 0
        with open(destino, "wb") as f:
            f.write(nuevo)
        antes = len(anterior) if anterior is not None else 0
        print(f"{NOMBRE_GENERADOR} --write: {NOMBRE_AGREGADO} re-emitido desde las "
              f"{len(SECCIONES)} fuentes declaradas ({antes} -> {len(nuevo)} bytes).")
        return 0

    print(f"uso: python {NOMBRE_GENERADOR} [--check | --write]")
    print("  --check  compara el CONTENIDO de cada seccion con su fuente y no "
          "escribe. Es el guard.")
    print("  --write  re-emite el agregado desde las fuentes declaradas en "
          "SECCIONES.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
