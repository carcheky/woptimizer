"""Mensajes de feedback de ejecucion de packs: funciones PURAS (TASK-035, ciclo 26).

POR QUE ESTE MODULO EXISTE
`kill_pack` (Gestor de Packs) y `execute_pack` (Portada) tienen DOS puertas de
cierre cada uno: `GamingService.execute_gaming_pack` (respeta `keepers`,
`target_categories` y la barrera roja G-2) y `ProcessService.kill_pack_apps`. Las
DOS devuelven la MISMA 4-tupla `(killed, failed, skipped, freed_mb)`, asi que el
mensaje se calcula AQUI, una sola vez, y se pasa a la vista. Es la forma de no
repetir el fallo del ciclo 14, donde un camino evaluaba `p.name` y el otro
`p.full_name` y uno de los dos dejaba de proteger en silencio: aqui ninguna
puerta puede mentir por su cuenta porque las dos alimentan el mismo texto.

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
"""

from typing import Tuple

from woptimizer.ui.confirmation import AMBAR, ROJO, VERDE
from woptimizer.ui import theme

#: Los cuatro desenlaces posibles de un cierre. El clasificador es UNICO para
#: las dos vistas: si cada una decidiera por su cuenta, volveriamos a tener dos
#: verdades.
EXITO = "exito"
PARCIAL = "parcial"
NADA = "nada"
FALLO = "fallo"


def clasificar_cierre(killed: int, failed: int) -> str:
    """Clasifica el resultado REAL de un cierre. No mira el nombre del pack ni la ruta.

    Solo se fia del resultado del servicio, que es lo unico que sabe que paso:
    cuantos se cerraron, cuantos fallaron y cuantos quedaron intactos.
    """
    if killed > 0:
        return PARCIAL if failed else EXITO
    return FALLO if failed else NADA


def mensaje_cierre_pack(nombre: str, killed: int, failed: int,
                        skipped: int, freed_mb: float) -> Tuple[str, str]:
    """Feedback inline del Gestor de Packs: `(texto, color)`.

    Las cuatro ramas:

    | desenlace | cuando | texto | color |
    |---|---|---|---|
    | exito | `killed > 0` y `failed == 0` | `"✅ N procesos cerrados (X MB liberados) · 'pack'."` | VERDE |
    | parcial | `killed > 0` y `failed > 0` | `"⚠️ 'pack': N cerrados, M con error (X MB liberados)."` | AMBAR |
    | nada | `killed == 0` y `failed == 0` | `"⚠️ 'pack': 0 procesos cerrados, K protegidos o ya cerrados."` | AMBAR |
    | fallo | `killed == 0` y `failed > 0` | `"⛔ No se cerró nada de 'pack': M con error."` | ROJO |
    """
    caso = clasificar_cierre(killed, failed)
    if caso == EXITO:
        return f"✅ {killed} procesos cerrados ({freed_mb:.1f} MB liberados) · '{nombre}'.", VERDE
    if caso == PARCIAL:
        return (f"⚠️ '{nombre}': {killed} cerrados, {failed} con error "
                f"({freed_mb:.1f} MB liberados)."), AMBAR
    if caso == FALLO:
        return f"⛔ No se cerró nada de '{nombre}': {failed} con error.", ROJO
    return f"⚠️ '{nombre}': 0 procesos cerrados, {skipped} protegidos o ya cerrados.", AMBAR


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
        return f"⚡ {killed} procesos cerrados · {freed_mb:.1f} MB liberados", marca
    if caso == PARCIAL:
        return (f"⚠️ {killed} procesos cerrados · {freed_mb:.1f} MB liberados "
                f"· {failed} con error."), theme.WARNING
    if caso == FALLO:
        return f"⛔ No se cerró nada: {failed} procesos con error.", theme.WARNING
    return f"⚠️ Nada que cerrar: {skipped} ya cerrados o protegidos.", theme.WARNING
