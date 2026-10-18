"""Publicacion en el bucle de Tk desde un hilo secundario (TASK-073).

POR QUE EXISTE
Los workers de las vistas (`threading.Thread(daemon=True)`) no pueden tocar
widgets: su unico recurso es PUBLICAR un callback en el hilo principal. Eso se
hacia con `self.after(0, ...)` a mano en diez sitios de tres vistas, y al
desaparecer la ventana (navegacion, cierre) esa llamada puede reventar con
`RuntimeError: main thread is not in main loop`. Copiar un `try/except` a mano
diez veces es la deuda que este modulo deja de existir: aqui vive UNA vez.

POR QUE NO HAY SONDA DE EXISTENCIA (medido el 2026-10-18, contra Tk real)
El guard que se propuso para esto era `try: if self.winfo_exists(): ...`, y no
aporta nada. MEDIDO, 1 de 1: el `RuntimeError: main thread is not in main
loop` de una llamada Tcl hecha desde un hilo que no es el principal ocurre en
el mundo SIN bucle principal --root + `update()`, que es el caso de los tests
headless--; con `mainloop()` vivo NO lanza, y `winfo_exists()` hasta
discrimina: devuelve 1 con la vista viva y 0 con el widget ya destruido. Una
version anterior de este docstring afirmaba "incluso con la ventana
perfectamente viva"; era FALSA, lo reprodujo el `mutation-auditor` del ciclo 62
contra Tk real, y TASK-078 lo corrigio.

La sonda sigue sin ser la solucion por tres razones, y las tres estan medidas:
donde el probe pareceria util --el mundo sin bucle-- la consulta lanza
tambien, luego no decide nada; donde la consulta funciona --`mainloop()` vivo--
Tk descarta igual el callback si el widget muere despues, asi que no hay
carrera posterior que cerrar; y con el probe en medio, un fallo de la propia
consulta lo traga el `except` de la comprobacion y el callback no se publica
nunca, en silencio. Preguntar el estado de una llamada Tcl para decidir si se
hace esa misma llamada Tcl es consultar al sistema por una respuesta que el
sistema no tiene. El `try/except` alrededor de la PROGRAMACION cubre los dos
casos con el mismo codigo, y ademas se puede auditar y mutar.

Y la sonda tampoco hacia falta: con `mainloop()` vivo, `after(400)` programado y
la ventana destruida 150 ms despues, el callback **nunca se ejecuta**. Tk lo
descarta junto con el widget. No existe la ventana de carrera posterior que un
probe pretenderia cerrar, asi que el `try/except` alrededor de la PROGRAMACION es
la solucion completa y suficiente.

INVARIANTE DE FRONTERA DE CAPAS (AGENTS.md)
Intacto. Este modulo no importa `psutil`, ni `json`, ni `woptimizer.services`: no
toca el sistema operativo ni el JSON, solo llama a un metodo del widget que
recibe. Programar en el bucle de Tk ES una operacion de UI.
"""

from typing import Any, Callable

__all__ = ["publicar_en_bucle"]


def publicar_en_bucle(widget: Any, delay_ms: int, callback: Callable[..., Any],
                      *args: Any) -> Any:
    """Programa `callback` en el bucle de Tk. Devuelve el handle, o `None`.

    UNICO punto autorizado para publicar desde un hilo secundario. Las vistas
    llegan aqui por `Confirmable._publicar_en_el_bucle`, que es una delegacion
    de una linea: la vista conserva una sola superficie Tk que el guard AST
    (`test_los_workers_de_pack_solo_publican_por_after`) puede nombrar.

    Sin bucle principal --el caso headless de `run_tests.py`, que usa `update()`
    y nunca `mainloop()`-- `widget.after` lanza y se devuelve `None`. El
    retorno se distingue de un handle real porque `None` no es un id de Tcl.
    Las DOS razones del `except`:

      * `RuntimeError: main thread is not in main loop`, cuando no hay bucle
        principal: es lo que hacia aparecer el fallo intermitente;
      * `tk.TclError`, si la vista murio entre la decision y la llamada.

    TASK-078: de las dos, la segunda la declara el docstring y ningun test la
    provoca, asi que `except Exception` y `except RuntimeError` son
    INDISTINGUIBLES para la suite hoy. Se deja `except Exception` (es lo
    correcto) y el hueco queda anotado como mutante EQUIVALENTE en
    `openspec/changes/2026-10-18-tkinter-after-guard/mutation-report.md`, no
    como un fallo: "arreglar" el codigo para matar ese mutante seria cambiar
    produccion para tapar una falta de prueba.

    NO registra el handle en `Confirmable._timers_ui` a proposito: ese `set` lo
    itera `cancel_on_destroy` en el hilo principal, y mutarlo desde un worker
    seria una carrera entre dos hilos. Una publicacion de 0 ms, cuando el bucle
    la atienda ya no tiene nada que cancelar.
    """
    try:
        return widget.after(delay_ms, callback, *args)
    except Exception:  # RuntimeError sin bucle principal; TclError si la vista murio
        return None