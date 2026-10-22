#!/usr/bin/env python3
"""El emisor del veredicto de mutacion (TASK-087, ciclo 70).

QUE HACE. Dado un CATALOGO commiteado (`mutaciones.json`) y los logs de las
corridas, decide el estado de cada mutante y escribe la LINEA CANONICA:

    WOPT_VEREDICTO <mutante> <MUERTO|SOBREVIVIENTE|NO MEDIDO> <sha>

El estado sale de la COLA del log (la evidencia), no de la prosa: el nombre del
test que MURIO se deriva del frame del traceback, y el nombre del test que
DEBIA morir (el "asa") lo DECLARA quien muta, en el catalogo.

LOS TRES ESTADOS (los tres, no dos):

    MUERTO        el log esta en ROJO, el test que murio es EXACTAMENTE el `asa`
                  declarado y el motivo literal de la asercion contiene el
                  `motivo` declarado.
    SOBREVIVIENTE la suite completa termino en VERDE (rc=0 y la ultima linea es
                  'ALL TESTS PASSED.').
    NO MEDIDO     todo lo demas: log cortado, el test que murio no es el `asa`,
                  el motivo no nombra la infraccion, o dos corridas del mismo
                  mutante dan veredictos distintos.

POR QUE NO SE REPITE LA SUITE N VECES. Repetir cuesta N x 734,9 s por mutante
(N=3 -> 8,0 h por ciclo) y, SIN exigir consistencia, EMPEORA el veredicto
falso: `1-(1-p)^N` con p=1/16 da 6,25 % (N=1) -> 17,6 % (N=3) -> 27,5 % (N=5).
El killer-check cuesta CERO corridas extra porque el harness ya captura el log.

LO QUE ESTE CONTRATO NO PRUEBA: que el `asa` declarada sea la guard
SEMANTICAMENTE correcta para esa mutacion. Lo que si prueba es que el veredicto
es coherente con la evidencia commiteada. La lista COMPLETA de lo que el
contrato no prueba, con los motivos MEDIDOS de cada limite, esta en el
docstring del gate (`validate_docs.py`, check 11): aqui no se duplica, porque
dos listas de limites se separan sin avisar.

LO QUE NO ESCRIBE: la evidencia de los mutantes a los que no se le pasan
corridas. Emitir el veredicto de uno NO destruye la evidencia de los demas
(medido en la auditoria del ciclo 70: antes la reescribia con "no hay ninguna
corrida", y con el mutante pisado declarado NO MEDIDO el gate no se enteraba).

INDEPENDENCIA CON EL GATE. El gate de `validate_docs.py` (check 11) RE-DERIVA
el estado con su PROPIA implementacion y NO importa este modulo. Si compartieran
la derivacion, un mutante en ella moveria los dos y el gate no podria ver al
emisor mentir: el gate tiene que poder CONTRASTEAR al emisor, y para eso los
dos tienen que ser dos.

Uso:

    python .taskmaster/veredicto.py emitir --catalogo mutaciones.json \\
        --evidencia evidencia --sha <sha> --log M-3=suite_M3.log \\
        --log M-3=suite_M3b.log [--salida veredictos.txt] [--bloque bloque.md]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

PREFIJO_CANONICO = "WOPT_VEREDICTO"
ESTADOS = ("MUERTO", "SOBREVIVIENTE", "NO MEDIDO")

# La gramatica es ESTRICTA: tres campos, el estado cerrado, y un sha de 7 a 40
# hex. `fullmatch`, nunca `search`: una linea que TRAIGA una linea canonica no
# es una linea canonica.
RE_LINEA_CANONICA = re.compile(
    r"WOPT_VEREDICTO (?P<mutante>[A-Za-z][A-Za-z0-9_.-]*) "
    r"(?P<estado>MUERTO|SOBREVIVIENTE|NO MEDIDO) "
    r"(?P<sha>[0-9a-f]{7,40})"
)

# La marca de bloque de la evidencia. Una corrida = un bloque, con su rc.
RE_MARCA_DE_RUN = re.compile(r"^=== WOPT_RUN (?P<run>\d+) RC=(?P<rc>-?\d+) ===$")

# El frame del traceback: de aqui sale el nombre del test que murio.
# `re.MULTILINE` es OBLIGATORIO: sin el, `^` y `$` solo casan al principio y al
# final de la cola entera, y los frames del medio (que son los del test) no
# casarian nunca. Un frame que no casa es un test que no se ve, luego un
# veredicto NO MEDIDO sin motivo aparente.
RE_FRAME = re.compile(
    r'^  File "(?P<fichero>.+?)", line (?P<linea>\d+), in (?P<funcion>.+)$',
    re.MULTILINE)

# La ultima linea verde de la suite. Es el unico sitio donde se lee el VERDE.
LINEA_VERDE = "ALL TESTS PASSED."

# Cuanto se guarda del log cuando NO hay traza: lo suficiente para ver la
# ultima linea. MEDIDO: la cola con traza son 624-961 B (3,4-4,8 % del log).
BYTES_SIN_TRAZA = 200


def linea_canonica(mutante, estado, sha):
    """La linea canonica de un mutante. -> `str`"""
    if estado not in ESTADOS:
        raise ValueError(f"estado desconocido: {estado!r}")
    return f"{PREFIJO_CANONICO} {mutante} {estado} {sha}"


def parsear_linea_canonica(texto):
    """`(mutante, estado, sha)` de una linea canonica, o `None` si no lo es."""
    m = RE_LINEA_CANONICA.fullmatch(texto.strip())
    if not m:
        return None
    return (m.group("mutante"), m.group("estado"), m.group("sha"))


def cola_del_log(texto):
    """La COLA del log: desde el ultimo traceback hasta el final.

    Sin traza se queda con las ultimas `BYTES_SIN_TRAZA`bytes. La cola es lo
    UNICO que hay que mirar para re-derivar el veredicto (MEDIDO: 624-961 B de
    un log de 30 KB), y es lo que se commitea como evidencia.
    """
    marca = texto.rfind("Traceback (most recent call last):")
    if marca >= 0:
        return texto[marca:]
    return texto[-BYTES_SIN_TRAZA:]


def test_que_murio(cola):
    """El nombre del `test_*` que murio, derivado del frame del traceback.

    `None` cuando la cola no tiene frame de un test (por ejemplo: el fallo fue
    un `ImportError` al importar, que no prueba nada).
    """
    encontrado = None
    for m in RE_FRAME.finditer(cola):
        funcion = m.group("funcion").strip()
        if funcion.startswith("test_"):
            encontrado = funcion
    return encontrado


def motivo_literal(cola):
    """El motivo LITERAL de la asercion: la ultima linea no vacia de la cola."""
    lineas = [l for l in cola.splitlines() if l.strip()]
    return lineas[-1].strip() if lineas else ""


def estado_de_una_corrida(cola, rc, asa, motivo):
    """El estado de UNA corrida. -> `(estado, por_que)`"""
    if rc == 0:
        if motivo_literal(cola) == LINEA_VERDE:
            return ("SOBREVIVIENTE", "la suite termino en VERDE")
        return ("NO MEDIDO", "log cortado: rc=0 pero la ultima linea no es "
                             f"'{LINEA_VERDE}'")
    # rc != 0: la suite esta en ROJO. Ahora el ROJO NO basta.
    muerto = test_que_murio(cola)
    if muerto is None:
        return ("NO MEDIDO", "la suite esta en ROJO pero la cola no tiene el "
                             "frame de un test: nadie puede decir que murio el "
                             "asa")
    if muerto != asa:
        return ("NO MEDIDO", f"murio `{muerto}` y el asa declarada es `{asa}`")
    literal = motivo_literal(cola)
    if motivo and motivo not in literal:
        return ("NO MEDIDO", f"el motivo literal no nombra la infraccion "
                             f"declarada ({motivo!r})")
    return ("MUERTO", f"murio `{asa}` por su asercion")


def estado_del_mutante(corridas, asa, motivo):
    """El estado del MUTANTE, agregado sobre sus corridas. -> `(estado, por_que)`

    MUERTO solo si TODAS las corridas mueren por el asa; SOBREVIVIENTE solo si
    TODAS son verdes; y cualquier otra cosa (una corrida NO MEDIDA, o dos
    corridas que discrepan) es NO MEDIDO. Un test NO DETERMINISTA no puede
    aportar la muerte de un mutante.
    """
    if not corridas:
        return ("NO MEDIDO", "no hay ninguna corrida: sin evidencia no hay "
                             "veredicto")
    estados = [estado for estado, _ in corridas]
    if len(set(estados)) != 1:
        return ("NO MEDIDO", "dos corridas del mismo mutante dan veredictos "
                             f"distintos ({', '.join(estados)})")
    estado = estados[0]
    if estado == "NO MEDIDO":
        return ("NO MEDIDO", corrida_por_que(corridas))
    return (estado, corrida_por_que(corridas))


def corrida_por_que(corridas):
    """La razon de la primera corrida que no es MUERTO."""
    for estado, por_que in corridas:
        if estado != "MUERTO":
            return por_que
    return "todas las corridas mueren por el asa"


def bloques_de_evidencia(texto):
    """Los bloques de una evidencia commiteada. -> `[(rc, cola), ...]`

    Cada bloque es `=== WOPT_RUN <n> RC=<rc> ===` seguido de su cola.
    """
    bloques = []
    rc_actual = None
    lineas = []
    for linea in texto.splitlines():
        m = RE_MARCA_DE_RUN.match(linea.strip())
        if m:
            if rc_actual is not None:
                bloques.append((rc_actual, "\n".join(lineas).strip("\n")))
            rc_actual = int(m.group("rc"))
            lineas = []
            continue
        if rc_actual is not None:
            lineas.append(linea)
    if rc_actual is not None:
        bloques.append((rc_actual, "\n".join(lineas).strip("\n")))
    return bloques


def escribir_evidencia(ruta, bloques):
    """Escribe la evidencia commiteada de un mutante. -> `None`"""
    with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
        for i, (rc, cola) in enumerate(bloques, 1):
            fh.write(f"=== WOPT_RUN {i} RC={rc} ===\n")
            fh.write(cola.rstrip("\n"))
            fh.write("\n")


def leer_catalogo(ruta):
    """Los mutantes del catalogo. -> `[(id, asa, motivo, sha), ...]`

    El catalogo es un objeto JSON con una lista `mutaciones`. Cada mutante
    declara `id`, `asa` (el nombre EXACTO del `test_*` que tiene que morir),
    `motivo` (el substring del mensaje de la asercion) y, opcionalmente,
    `sha_arbol_auditado`.
    """
    with open(ruta, encoding="utf-8") as fh:
        datos = json.load(fh)
    if isinstance(datos, dict):
        lista = datos.get("mutaciones", [])
    else:
        lista = datos
    salida = []
    for entrada in lista:
        if not isinstance(entrada, dict):
            raise ValueError(f"el catalogo tiene una entrada que no es un "
                             f"objeto: {entrada!r}")
        for campo in ("id", "asa", "motivo"):
            if not entrada.get(campo):
                raise ValueError(f"el mutante {entrada.get('id')!r} no declara "
                                 f"`{campo}`")
        salida.append((entrada["id"], entrada["asa"], entrada["motivo"],
                       entrada.get("sha_arbol_auditado")))
    return salida


def _cola_y_rc_de_un_log(ruta):
    """`(cola, rc)` de un log de la suite.

    El rc NO esta en el log: lo pone el runner. Si el log trae el rc en su
    ultima linea (convencion del runner de este repo) se usa; si no, se infiere
    del propio log (VERDE si la ultima linea es la de exito, ROJO si hay
    traceback) y se dice cual se infirio.
    """
    with open(ruta, "rb") as fh:
        datos = fh.read()
    texto = datos.decode("utf-8", errors="replace")
    cola = cola_del_log(texto)
    rc = None
    m = re.search(r"^RC=(\d+)$", texto, re.MULTILINE)
    if m:
        rc = int(m.group(1))
    elif "Traceback (most recent call last):" in texto:
        rc = 1
    else:
        rc = 0
    return (cola, rc)


def emitir(catalogo, logs_por_mutante, sha, dir_evidencia, salida=None,
           bloque=None, rcs_por_mutante=None):
    """Emite las lineas canonicas de un catalogo. -> `[str, ...]`

    `logs_por_mutante` mapea id de mutante -> lista de rutas de log (puede
    tener mas de una: dos corridas del mismo mutante). `rcs_por_mutante` mapea
    id -> rc de la corrida, cuando el runner lo dio y el log no lo trae.

    LO QUE NO ESCRIBE, y por que. La evidencia de un mutante al que NO se le
    paso ninguna corrida NO se toca: ni se crea, ni se sobrescribe, ni se
    vacia. MEDIDO (auditoria del ciclo 70, TASK-087): antes, emitir el
    veredicto de un mutante BORRABA la evidencia commiteada de los otros (la
    reescribia con "no hay ninguna corrida"), y con el mutante pisado
    declarado NO MEDIDO el gate no se enteraba: era un verde por omision. El
    que emite un veredicto no puede destruir la evidencia de quien no le paso
    sus logs.

    El mutante sin corridas sigue recibiendo su linea canonica (NO MEDIDO: sin
    evidencia no hay veredicto), pero SIN evidencia escrita. El gate exigira
    la evidencia commiteada y su ausencia es un FAIL, que es lo correcto:
    nadie puede publicar un veredicto sin la evidencia que lo sostiene.
    """
    rcs_por_mutante = rcs_por_mutante or {}
    if dir_evidencia:
        os.makedirs(dir_evidencia, exist_ok=True)
    lineas = []
    for identificador, asa, motivo, sha_del_catalogo in catalogo:
        sha_de_este = sha_del_catalogo or sha
        if not sha_de_este:
            raise SystemExit(
                f"WOPT_USO: el mutante {identificador} no tiene sha: ni el "
                f"catalogo lo declara ni se paso --sha")
        rutas = logs_por_mutante.get(identificador, [])
        bloques = []
        for indice, ruta in enumerate(rutas):
            cola, rc = _cola_y_rc_de_un_log(ruta)
            if indice == 0 and identificador in rcs_por_mutante:
                rc = rcs_por_mutante[identificador]
            bloques.append((rc, cola))
        if dir_evidencia and bloques:
            # SOLO la evidencia de los mutantes que tienen corridas. Un mutante
            # al que no se le paso ningun log conserva la evidencia que tenga:
            # sobrescribirla seria destruir la evidencia de otro.
            escribir_evidencia(os.path.join(dir_evidencia,
                                             f"{identificador}.cola"), bloques)
        corridas = [estado_de_una_corrida(cola, rc, asa, motivo)
                    for rc, cola in bloques]
        estado, por_que = estado_del_mutante(corridas, asa, motivo)
        if dir_evidencia and not bloques:
            por_que = (por_que + ". La evidencia de este mutante NO se ha "
                       "escrito: no se paso ninguna corrida suya, y la "
                       "evidencia commiteada de los demas no se toca")
        lineas.append(linea_canonica(identificador, estado, sha_de_este))
        print(f"{identificador}: {estado} ({por_que})")
    if salida:
        with open(salida, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lineas))
            fh.write("\n")
    if bloque:
        with open(bloque, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("<!-- WOPT_VEREDICTOS -->\n")
            for linea in lineas:
                fh.write(linea + "\n")
            fh.write("<!-- /WOPT_VEREDICTOS -->\n")
    return lineas


def _leer_logs(argv):
    """`{id: [rutas]}` de los `--log ID=RUTA`."""
    logs = {}
    for par in argv or ():
        if "=" not in par:
            raise SystemExit(f"WOPT_USO: --log espera ID=RUTA, no {par!r}")
        identificador, ruta = par.split("=", 1)
        logs.setdefault(identificador, []).append(ruta)
    return logs


def _leer_rcs(argv):
    """`{id: rc}` de los `--rc ID=N`."""
    rcs = {}
    for par in argv or ():
        if "=" not in par:
            raise SystemExit(f"WOPT_USO: --rc espera ID=N, no {par!r}")
        identificador, valor = par.split("=", 1)
        try:
            rcs[identificador] = int(valor)
        except ValueError:
            raise SystemExit(f"WOPT_USO: --rc espera un entero, no {valor!r}")
    return rcs


def main(argv=None):
    """Emite las lineas canonicas. Sale con 0."""
    parser = argparse.ArgumentParser(
        prog="veredicto.py",
        description="Emite la linea canonica del veredicto de mutacion.",
    )
    sub = parser.add_subparsers(dest="comando", required=True)
    em = sub.add_parser("emitir", help="emite las lineas canonicas")
    em.add_argument("--catalogo", required=True,
                    help="el catalogo commiteado (mutaciones.json)")
    em.add_argument("--evidencia", default=None,
                    help="directorio donde escribir <mutante>.cola")
    em.add_argument("--sha", default=None,
                    help="sha (7-40 hex) del arbol auditado")
    em.add_argument("--log", action="append", default=[],
                    help="ID=RUTA del log de una corrida (repetible)")
    em.add_argument("--rc", action="append", default=[],
                    help="ID=N del codigo de salida de la PRIMERA corrida, "
                         "cuando el runner lo dio y el log no lo trae")
    em.add_argument("--salida", default=None,
                    help="fichero donde escribir las lineas canonicas")
    em.add_argument("--bloque", default=None,
                    help="fichero donde escribir el bloque de maquina")
    args = parser.parse_args(argv)
    if args.comando == "emitir":
        catalogo = leer_catalogo(args.catalogo)
        lineas = emitir(catalogo, _leer_logs(args.log), args.sha,
                        args.evidencia, args.salida, args.bloque,
                        _leer_rcs(args.rc))
        print("")
        for linea in lineas:
            print(linea)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
