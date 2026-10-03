"""Mensajes de feedback de ejecucion de packs: funciones PURAS (TASK-035, ciclo 26).

POR QUE ESTE MODULO EXISTE
Hay TRES puertas de cierre, no dos, y las tres devuelven la MISMA 4-tupla
`(killed, failed, skipped, freed_mb)`:

1. `GamingService.execute_gaming_pack` (respeta `keepers`, `target_categories` y
   la barrera roja G-2) — la usan `kill_pack` y `execute_pack`;
2. `ProcessService.kill_pack_apps` — la usan `kill_pack` y `execute_pack` con un
   pack normal;
3. `ProcessService.kill_processes` — la usa `ProcessManagerView.on_kill_selected`,
   el Gestor de Procesos, que mata UNO A UNO lo que el usuario marco a mano.

El mensaje se calcula AQUI, una sola vez, y se pasa a la vista. Es la forma de no
repetir el fallo del ciclo 14, donde un camino evaluaba `p.name` y el otro
`p.full_name` y uno de los dos dejaba de proteger en silencio. Y es la forma de
no repetir el fallo del ciclo 26, cuya primera auditoria encontro la TERCERA
puerta (`on_kill_selected`) pintando `"<tick> 0 cerrados, 0 fallidos."` en verde
con `killed == 0`: la UI miente en verde es la misma clase que el contador
`started` del ciclo 20.

OJO, ALCANCE REAL DE ESA AFIRMACION: el FORMATEADOR es comun, la LLAMADA no. Que
las tres alimenten `mensaje_cierre_pack` no basta si alguna puerta no lo llama o
si una rama se queda sin ejecutar nunca en la suite; las dos cosas se cubren con
pruebas que entran por la UI y con la guarda AST de
`test_los_workers_de_pack_solo_publican_por_after`.

LO QUE SE PARAMETRIZA Y POR QUE: el sustantivo ("procesos" / "apps"). El
Gestor de Procesos cuenta procesos marcados a mano y el Gestor de Packs cuenta
apps de un pack; duplicar el texto para cada uno seria volver a tener dos
verdades, que es justo lo que este modulo existe para evitar.

LA MENTIRA QUE ESTE MODULO ELIMINA (medida por el mutation-auditor del ciclo 26)
Con un pack sin apps vivas, `kill_pack` pintaba siempre
`"✅ 0 procesos cerrados (0.0 MB liberados)"` en VERDE Gaming: la app afirmaba un
exito que no habia ocurrido (todo estaba en `keepers`, el pack ya estaba vacio o
las rutas estaban muertas). La UI miente en verde es la misma clase que el
contador `started` del ciclo 20. Regla: **VERDE solo con `killed > 0`**.

`skipped` NO es "lo que no me apetece": `kill_processes` lo suma por blindaje
(`is_system_protected`, TASK-024) o por `NoSuchProcess` (ya no estaba), y
`execute_gaming_pack` lo suma ademas a los descartes del filtro de keepers (G9).
De ahi la palabra "protegidos o ya cerrados" y no un "fallaron".

FRONTERA DE CAPAS (AGENTS.md)
Solo importa `typing` y los literales de color de `ui.confirmation`. Ni
`tkinter`, ni `customtkinter`, ni `psutil`, ni `json`, ni `services`, ni
`models`: son funciones puras y se testean sin ventana.

LO QUE TAMBIEN VIVE AQUI (TASK-036)
El pack que NO PUEDE hacer nada. Un pack normal sin apps y un Gaming Mode con 0
apps y 0 categorias no producen un resultado que clasificar, asi que no tienen
desenlace: tienen su propio par de formateadores puros, con la misma disciplina
de "una sola frase por hecho" que el resto del modulo. La razon de que esten aqui
y no en la vista es la misma que justifica el modulo entero: una frase escrita en
la vista es una frase que se puede copiar y divergir.
"""

from typing import Tuple

from woptimizer.ui.confirmation import AMBAR, ROJO, VERDE
from woptimizer.ui import theme

#: Los cuatro desenlaces posibles de un cierre. El clasificador es UNICO para
#: las TRES puertas: si cada una decidiera por su cuenta, volveriamos a tener
#: tres verdades.
EXITO = "exito"
PARCIAL = "parcial"
NADA = "nada"
FALLO = "fallo"

#: Destino de la clausula de MB segun la familia que la publica: la inline la
#: enclose en parentesis y la de banner la separa con punto medio. El separador
#: es lo UNICO que distingue una familia de otra; la regla de si la clausula se
#: publica o no es la misma para las dos, y por eso vive en un solo sitio.
_MB_INLINE = " ({:.1f} MB liberados)"
_MB_BANNER = " · {:.1f} MB liberados"


def clausula_mb(freed_mb: float, estilo: str = "inline") -> str:
    """La clausula de MB liberados, o cadena vacia si no se libero memoria.

    `format_kill_result` ya decidio esta regla y la tiene fijada por un test
    (`run_tests.py::test_notification_message_formatting`): con `freed_mb <= 0`
    la clausula NO se escribe. Antes de este helper los dos formateadores de este
    modulo la escribian siempre, de modo que la misma verdad se decia de dos
    maneras segun por donde se ejecutara, que es justo lo que este modulo vino a
    cerrar. `"0.0 MB liberados"` tampoco es una promesa imposible: es un numero
    que el usuario no puede cuadrar con lo que ve en el Administrador de tareas y
    que le hace sospechar de la telemetria entera.
    """
    if freed_mb <= 0:
        return ""
    return (_MB_BANNER if estilo == "banner" else _MB_INLINE).format(freed_mb)


def clasificar_cierre(killed: int, failed: int) -> str:
    """Clasifica el resultado REAL de un cierre. No mira el nombre del pack ni la ruta.

    Solo se fia del resultado del servicio, que es lo unico que sabe que paso:
    cuantos se cerraron, cuantos fallaron y cuantos quedaron intactos.
    """
    if killed > 0:
        return PARCIAL if failed else EXITO
    return FALLO if failed else NADA


def mensaje_cierre_pack(nombre: str, killed: int, failed: int,
                        skipped: int, freed_mb: float,
                        sustantivo: str = "procesos") -> Tuple[str, str]:
    """Feedback inline del Gestor de Packs y del Gestor de Procesos: `(texto, color)`.

    Las cuatro ramas:

    | desenlace | cuando | texto | color |
    |---|---|---|---|
    | exito | `killed > 0` y `failed == 0` | `"✅ N <sus> cerrados (X MB liberados) · 'pack'."` | VERDE |
    | parcial | `killed > 0` y `failed > 0` | `"⚠️ 'pack': N cerrados, M con error (X MB liberados)."` | AMBAR |
    | nada | `killed == 0` y `failed == 0` | `"⚠️ 'pack': 0 <sus> cerrados, K protegidos o ya cerrados."` | AMBAR |
    | fallo | `killed == 0` y `failed > 0` | `"⛔ No se cerró nada de 'pack': M con error."` | ROJO |

    La clausula `(X MB liberados)` sale de `clausula_mb` y **desaparece con
    `freed_mb <= 0`**, igual que en `format_kill_result`.

    `sustantivo` es lo unico que la vista aporta y no el resultado: el Gestor de
    Packs dice "procesos" y el Gestor de Procesos tambien, pero el punto es que
    quien quiera decir "apps" lo diga por parametro y NO copiando el texto.
    """
    caso = clasificar_cierre(killed, failed)
    if caso == EXITO:
        return (f"✅ {killed} {sustantivo} cerrados"
                f"{clausula_mb(freed_mb)} · '{nombre}'."), VERDE
    if caso == PARCIAL:
        return (f"⚠️ '{nombre}': {killed} cerrados, {failed} con error"
                f"{clausula_mb(freed_mb)}."), AMBAR
    if caso == FALLO:
        return f"⛔ No se cerró nada de '{nombre}': {failed} con error.", ROJO
    return (f"⚠️ '{nombre}': 0 {sustantivo} cerrados, "
            f"{skipped} protegidos o ya cerrados."), AMBAR


def mensaje_banner_cierre(killed: int, failed: int, skipped: int, freed_mb: float,
                          is_gaming: bool) -> Tuple[str, str]:
    """Banner de telemetria de la Portada: `(texto, color)`.

    Mismas cuatro ramas que `mensaje_cierre_pack` (comparten `clasificar_cierre`),
    con el COLOR DE MARCA de la portada: verde Gaming si es el Gaming Mode y azul
    de acento si es un pack normal. **Ese color de marca solo se concede con
    exito real**: sin `killed > 0` el banner cae a `theme.WARNING`, que es un
    color de atencion y no una promesa.

    La paleta no incluye `theme.DANGER` a proposito: `#c22d2d` sobre
    `SURFACE_ALT` da 3.07:1 y el design system exige 4.5:1 (ver
    `test_contrast_wcag_aa`). El fallo se distingue por el texto (`⛔`), no
    inventandose un par de color que no cumple.
    """
    caso = clasificar_cierre(killed, failed)
    marca = theme.GAMING if is_gaming else theme.ACCENT
    if caso == EXITO:
        return (f"⚡ {killed} procesos cerrados"
                f"{clausula_mb(freed_mb, estilo='banner')}"), marca
    if caso == PARCIAL:
        return (f"⚠️ {killed} procesos cerrados"
                f"{clausula_mb(freed_mb, estilo='banner')}"
                f" · {failed} con error."), theme.WARNING
    if caso == FALLO:
        return f"⛔ No se cerró nada: {failed} procesos con error.", theme.WARNING
    return f"⚠️ Nada que cerrar: {skipped} ya cerrados o protegidos.", theme.WARNING


# ---------------------------------------------------------------------------
# PACK QUE NO PUEDE HACER NADA (TASK-036)
#
# NO es un quinto desenlace de `clasificar_cierre`. El clasificador clasifica un
# RESULTADO REAL y su docstring dice que no mira ni el pack ni la ruta. Un pack
# vacio no produce resultado: no se llama a ningun servicio, no se lanza worker
# y no hay 4-tupla que formatear. Meterlo ahi seria mentir sobre el contrato y
# abriria la puerta a un quinto color que ninguna puerta de cierre alcanza.
#
# Lo que hay abajo son funciones PURAS: la vista pide un par `(texto, color)` y
# lo publica. El verbo sale de la ACCION DENTRO del formateador (nunca desde la
# vista), y las dos familias (inline y banner) comparten la frase con un
# constructor privado para que no puedan divergir.
# ---------------------------------------------------------------------------

#: `Pack.default_action` es `Literal["start", "kill"]` (`models.py`), asi que el
#: mapa es TOTAL por construccion: no hay un tercer verbo posible, y por eso
#: `_verbo` NO lleva `default` (ver su docstring). La clave es la ACCION; el
#: valor es el verbo. Un verbo NUNCA es una clave.
VERBOS = {"kill": "apagar", "start": "iniciar"}


def es_pack_inerte(is_gaming: bool, n_apps: int, n_categorias: int) -> bool:
    """El Gaming Mode no tiene NADA que cerrar: 0 apps Y 0 categorias.

    Con ambas listas vacias `should_kill_for_gaming` cae a `False` para todo lo
    que no este protegido, asi que es **inerte por construccion**, no
    "probablemente inerte". Un gaming con apps **o** con categorias NO es inerte
    y no avisa: cierra de verdad por la via G-2/G-3.
    """
    return is_gaming and n_apps == 0 and n_categorias == 0


def _verbo(accion: str) -> str:
    """El verbo de la frase a partir de la ACCION que se esta ejecutando.

    Quien llama pasa la accion, nunca el verbo: en la Portada es
    `pack.default_action` (que es lo que decide la rama), y en `start_pack` es
    `"start"`, porque ese metodo ES arrancar aunque el pack sea gaming.

    UNA ACCION DESCONOCIDA ES UN FALLO, NO UN "apagar" (TASK-036, iter 7).
    Con `VERBOS.get(accion, VERBOS["kill"])` un cableado erroneo --cablear un
    VERBO donde va una ACCION, que es el bug que motivo este ciclo-- caia en
    silencio a "apagar"; y como la respuesta correcta de la puerta de apagar ES
    "apagar", la mentira era invisible. Medido: meter "apagar", "stop" o "Kill"
    en la puerta de apagar NO MATABA la suite entera.

    **Por que fallo duro y no un tercer desenlace** ("verbo desconocido" que la
    vista muestre al usuario, en vez de mentir):

    1. El dominio es TOTAL y lo garantiza el modelo, no este modulo:
       `default_action: Literal["start", "kill"]`, todo pack entra por
       `Pack(**validado)` en `pack_service`, y un `ValidationError` ahi se
       clasifica como CORRUPCION (TASK-031). O sea: una accion desconocida no
       puede llegar por datos, solo por un error de cableado, que es un fallo de
       programacion, no una situacion que el usuario pueda provocar.
    2. Un tercer desenlace mete un error de programacion DENTRO de una frase
       dirigida al usuario ("no tiene apps que <verbo desconocido>"), con su
       color y su politica: es una mentira nueva en lugar de la que se quita,
       y este modulo es puro, sin logger al que escribir.
    3. Una `KeyError` no se puede silenciar con un `.get`, que es justo lo que
       la hacia invisible. Y el fallo sale en el sitio donde se cablea, no
       semanas despues en un texto que nadie sabe de donde salio.
    """
    if accion not in VERBOS:
        raise KeyError(
            "feedback._verbo: accion desconocida {!r}. El mapa de ACCIONES es "
            "{!r} (quien llama pasa la ACCION, nunca el verbo, y un verbo nunca "
            "es una clave: cablear 'apagar' aqui es un bug, no una entrada "
            "nueva).".format(accion, sorted(VERBOS))
        )
    return VERBOS[accion]


def _frase_sin_apps(nombre: str, accion: str) -> str:
    """La frase UNICA del pack sin apps. Constructor privado de los dos pares.

    Si las familias inline y banner divergeieran, el usuario veria el mismo
    hecho con dos redacciones distintas segun donde pulse.
    """
    return (f"⚠️ '{nombre}' no tiene apps que {_verbo(accion)}. "
            f"Añádelas desde el Gestor de Procesos.")


def _frase_gaming_inerte(nombre: str) -> str:
    """La frase UNICA del Gaming Mode inerte (constructor privado del par)."""
    return (f"⛔ El Gaming Mode de '{nombre}' no tiene nada que cerrar: "
            f"0 apps y 0 categorías configuradas. "
            f"Revísalo en el Gestor de Packs.")


def mensaje_sin_apps(nombre: str, default_action: str) -> Tuple[str, str]:
    """`(texto, AMBAR)` de un pack normal sin apps. Inline (Gestor de Packs).

    `default_action` es la ACCION que se esta ejecutando (`"kill"` o `"start"`),
    no un verbo: el mapeo accion -> verbo vive aqui dentro y en ningun otro
    sitio. En la Portada lo que se pasa es `pack.default_action`, que es lo que
    decide la rama; en `start_pack` se pasa `"start"` porque arrancar es lo que
    ese metodo hace. Cualquier otro valor es un `KeyError` con el nombre de la
    puerta y la accion recibida (ver `_verbo`), no un verbo por defecto.

    El color es el de ATENCION en las dos familias: nunca verde (no hubo exito)
    ni rojo (no hubo error). En la Portada el mismo par se publica con
    `theme.WARNING` sobre `SURFACE_ALT` por la restriccion de contraste.
    """
    return _frase_sin_apps(nombre, default_action), AMBAR


def mensaje_banner_sin_apps(nombre: str, default_action: str) -> Tuple[str, str]:
    """El mismo par para la familia BANNER (Portada). Solo cambia el color."""
    return _frase_sin_apps(nombre, default_action), theme.WARNING


def mensaje_gaming_inerte(nombre: str) -> Tuple[str, str]:
    """`(texto, ROJO)` del Gaming Mode inerte. Inline.

    Es un DIAGNOSTICO de configuracion, no un desenlace de ejecucion: por eso
    lleva `⛔` y ROJO, y no el aviso ambar de "no hay nada que hacer". Sin esta
    diagnosis el gaming inerte caia en la puerta real y decia "Nada que cerrar:
    0 ya cerrados o protegidos", donde el `0` es el contador de blindaje, no de
    apps: el usuario leia "ya estaban cerrados" y culpaba al sistema operativo.
    """
    return _frase_gaming_inerte(nombre), ROJO


def mensaje_banner_gaming_inerte(nombre: str) -> Tuple[str, str]:
    """El mismo par para la familia BANNER. Solo cambia el color.

    NO puede ser `theme.DANGER` sobre `SURFACE_ALT`: da 3.07:1 y el design
    system exige 4.5:1 (ver `test_contrast_wcag_aa`). El bloqueo se distingue
    por el texto (`⛔`), no inventandose un par de color que no cumple.
    """
    return _frase_gaming_inerte(nombre), theme.WARNING


def texto_confirmacion_apagado(nombre: str, n_procesos: int,
                                n_apps: int, n_categorias: int) -> str:
    """El texto de la DOBLE PULSACION de la puerta de apagar. Las dos vistas.

    TASK-063. Antes decia `f"apagar {len(pack.apps)} apps"`, que con 0 apps y 3
    categorias marcadas decia **"apagar 0 apps"**: el contador de `apps` contando
    lo que la puerta no hace. Es la misma clase que el `started` en verde que
    motivo el ciclo 26 y que la frase vive aqui para que el Gestor y la Portada
    no puedan divergir otra vez.

    El numero que va delante es el que devuelve
    `GamingService.cuenta_a_apagar(pack)`, o sea el MISMO filtro que mata: la
    vista no cuenta nada por su cuenta. Los dos parentesis dicen de donde sale,
    porque un 0 con 3 categorias marcadas no es un pack vacio: es un pack con
    nada corriendo ahora mismo, y el usuario tiene que poder distinguir los dos.
    """
    return (f"⚠️ Segunda pulsación para apagar {n_procesos} procesos de '{nombre}' "
            f"({n_apps} apps y {n_categorias} categorías marcadas).")
