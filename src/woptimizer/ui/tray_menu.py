"""Estado del menu de favoritos de la BANDEJA (sin widgets, sin pystray).

POR QUE ESTE MODULO EXISTE
El menu de la bandeja es la unica superficie del producto donde un `MenuItem` de pystray
no es un widget: no hay `status_label` donde explicar nada, ni ciclo de vida de vista que
permita armar y cancelar una pendiente. Por eso `docs/ai/ui-design-system.md` (TASK-025)
declaro el item "Preparar Gaming Mode" como la UNICA excepcion a `_require_double_tap`:
un solo clic apaga, sin confirmar.

Esa excepcion estaba justificada porque afectaba a UN pack, con nombre explicito y sin
vecinos. Al meter los packs FAVORITOS en el mismo menu, un clic empieza a poder apagar
N packs, y varios con `target_categories` activas, que cierran procesos que el usuario
nunca enumero. Eso convierte una excepcion acotada en un agujero general, y por eso este
modulo existe: reproduce la doble pulsacion DENTRO del menu, con un item de "Confirmar",
que es la unica via que la propia documentacion senala como aceptable
("si algun dia se le quiere dar confirmacion, hay que anadir antes una superficie de estado
al `MenuItem` (o un item de 'confirmar'), nunca un `messagebox`").

REUTILIZA LA MAQUINA DE ESTADOS, NO LA REESCRIBE
`DoubleTapGuard` (ui/confirmation.py) ya es una maquina de estados PURA: no conoce
widgets, no importa tkinter y recibe un `scheduler` inyectable. Este modulo NO crea una
segunda maquina: le pasa un `TrayScheduler` y usa `arm` / `consume` / `reset` / `is_pending`
exactamente como las vistas. Una copia propia seria una segunda politica de seguridad, que
es justo lo que `gaming_service` existe para evitar.

FRONTERA DE CAPAS (AGENTS.md)
La UI no toca el sistema operativo ni el JSON, y aqui la frontera es doble: este modulo
solo puede importar `typing` y `woptimizer.ui.confirmation`. PROHIBIDO `psutil`, `json`,
`os`, `threading`, `pystray`, `woptimizer.services` y `woptimizer.models`. Ni la lectura de
los packs ni la cuenta de procesos a apagar ocurren aqui: eso lo hacen `WOptimizerApp` y
sus servicios. Este modulo decide SI se puede pulsar "Confirmar" y que texto dice el item,
nada mas.

INVARIANTE
`armar` y `confirmar` son las DOS unicas funciones, y estan separadas A PROPOSITO. Una
sola que dijera "puedes ejecutar" seria inutilizable: devolveria `True` en la primera
pulsacion (que ya ha armado) y en la segunda, y entonces el llamante no tendria forma de
distinguir "la pendiente existe" de "el usuario ha pulsado Confirmar". Con dos funciones y
`armar` sin valor de retorno, el atajo por el que un item mataria con un clic NO SE PUEDE
ESCRIBIR: no existe ninguna expresion que valga para las dos pulsaciones.

La #1 de las sondas de `run_tests.py` mide precisamente eso, y durante el desarrollo
CAYO contra una primera version que si tenia `puede_ejecutar`: devolvia `True` con la
primera pulsacion. Ese es el fallo que hace necesaria esta forma.
"""

from typing import Any, Callable, List, Optional, Tuple

from woptimizer.ui.confirmation import DoubleTapGuard

# Ventana de confirmacion del menu. Es MAS LARGA que la de la Portada (2000 ms) y
# MENOS que la estandar (3000 ms) por una razon medida, no por gusto: entre el primer clic
# y el segundo el usuario tiene que ABRIR el menu otra vez, elegir el item y pulsarlo.
# La Portada no exige eso (el boton sigue ahi, con su estado pintado), asi que su ventana
# de 2 s es coherente para su ritmo y no lo seria para este.
VENTANA_MS_TRAY = 4000


class TrayScheduler:
    """Adaptador de expiracion para el menu, sin Tk y sin hilo.

    NO usa `threading.Timer` a proposito: `threading.Timer` dispararia su callback desde un
    hilo secundario, y la guarda de hilos de `ui-design-system.md` prohíbe en las vistas
    que un worker mute nada que no pase por `after(0, ...)`. Aqui no hay widget que mutar,
    y aun asi se evita el hilo porque no hace falta: `pystray` reconstruye el menu cada vez
    que se abre y `TrayMenuState.pendiente()` ya compara contra `monotonic()`, de modo que
    una pendiente caducada se ve caducada sin que nadie tenga que avisar a nadie.

    El scheduler existe para que `DoubleTapGuard` conserve SU ciclo de vida -- sobre todo
    `cancelar` al hacer `reset`, que es lo que impide que un timer velho dispare sobre una
    pendiente ya consumida -- sin que eso implique un hilo. Por eso los jobs se marcan
    como `cancelled` y no se ejecutan nunca: son la DEUDA que el guard contrae al armar,
    y el reloj de `TrayMenuState` es quien decide si la pendiente sigue viva.
    """

    def __init__(self) -> None:
        self._jobs: List[Tuple[int, Callable[[], None], bool]] = []
        self._contador = 0

    def schedule(self, delay_ms: int, callback: Callable[[], None]) -> Any:
        self._contador += 1
        handle = f"trayjob{self._contador}"
        self._jobs.append((delay_ms, callback, False))
        return handle

    def cancel(self, handle: Any) -> None:
        for i, (_, _, cancelled) in enumerate(self._jobs):
            if not cancelled and f"trayjob{i + 1}" == handle:
                self._jobs[i] = (self._jobs[i][0], self._jobs[i][1], True)
                return
        raise AssertionError(f"Se cancelo un handle que no existe: {handle!r}")


class TrayMenuState:
    """La maquina de confirmacion del menu de favoritos. Sin widgets, sin pystray.

    Un unico guard para todos los items, no uno por pack: el menu es una superficie pequeña
    y `DoubleTapGuard` ya resuelve el caso de "pulsar otra accion distinta descarta la
    pendiente" (§3.5). Pulsar un pack B mientras A esta pendiente DESCARTA la de A, que es
    el comportamiento correcto: la intencion del usuario es la ultima accion.
    """

    def __init__(self, window_ms: int = VENTANA_MS_TRAY) -> None:
        self._guard = DoubleTapGuard(TrayScheduler(), window_ms=window_ms)
        # `monotonic` inyectado para que los tests puedan mover el reloj sin esperar.
        self._reloj: Callable[[], float] = _monotonic_real
        self._armado_en: Optional[float] = None

    # -- reloj ---------------------------------------------------------------
    def set_reloj(self, reloj: Callable[[], float]) -> None:
        """Sustituye el reloj. Solo para tests: la expiry se mide contra el."""
        self._reloj = reloj

    # -- consulta ------------------------------------------------------------
    def pendiente(self, pack_id: str) -> bool:
        """Este pack tiene una confirmacion VIVA (pendiente y no caducada)."""
        if not self._guard.is_pending(f"tray:{pack_id}"):
            return False
        if self._caducada():
            self._guard.reset()
            return False
        return True

    def confirmar(self, pack_id: str) -> bool:
        """La pulsacion sobre el item de "Confirmar". `True` SOLO aqui se puede matar.

        Es la UNICA funcion del modulo cuyo `True` significa "ejecuta", y solo lo devuelve
        si hay una pendiente VIVA de ESTE pack. Por eso el atajo mortal es inimputable: no
        hay ninguna llamada que valga a la vez para "el item de apagar" y para "el item de
        confirmar" -- el primero llama a `armar`, que no devuelve nada, y este devuelve
        `True` unicamente con la pendiente puesta.
        """
        if not self.pendiente(pack_id):
            return False
        return self._guard.consume(f"tray:{pack_id}") is not None

    # -- transiciones --------------------------------------------------------
    def armar(self, pack_id: str) -> None:
        """La primera pulsacion sobre el item de apagar. NO devuelve nada, a proposito.

        Que no devuelva `bool` es la mitad del invariante: un `armar` que devolviera
        "quedate armado" invites a escribir `if estado.armar(id): preparar(...)` o, peor,
        a un `if estado.puede_ejecutar(id)` compartido con el item de confirmar, y las dos
        cosas devuelven `True` tras la primera pulsacion. Con `None`, el llamante no tiene
        nada que interpretar: solo redibuja el menu, y el siguiente clic tiene que pasar
        por `confirmar`.

        Pulsar dos veces el item de apagar sin pasar por el de confirmar NO ejecuta nada:
        esta funcion no ejecuta, y la que ejecuta es `confirmar`.
        """
        if self._guard.arm(f"tray:{pack_id}", f"tray:{pack_id}"):
            self._armado_en = self._reloj()

    def cancelar(self) -> None:
        """Olvida la pendiente viva. La usa el item de "Cancelar"."""
        self._guard.reset()
        self._armado_en = None

    def pendiente_alguno(self) -> bool:
        """Hay ALGUNA pendiente viva, sea de este pack o de otro.

        Es lo que decide si el item de "Cancelar" aparece. `DoubleTapGuard.is_pending()`
        sin argumento responde justamente eso, pero en este modulo la respuesta tiene que
        pasar por `pendiente()`: una pendiente cuyo reloj ya vencio existe todavia en el
        guard (nadie ha llamado a `reset`) y no debe hacer aparecer un "Cancelar" que no
        cancela nada.
        """
        if not self._guard.is_pending():
            return False
        if self._caducada():
            self._guard.reset()
            return False
        return True

    # -- interno -------------------------------------------------------------
    def _caducada(self) -> bool:
        if self._armado_en is None:
            return True
        return (self._reloj() - self._armado_en) * 1000.0 >= VENTANA_MS_TRAY


def texto_item(pack_id: str, nombre: str, accion: str,
               estado: TrayMenuState) -> str:
    """El texto EXACTO del item, derivado del estado. Sin widgets, sin pystray.

    Los dos verbos salen de `feedback.VERBOS` en el llamante, no de aqui: este modulo no
    conoce la palabra "apagar" ni "iniciar", conoce la ACCION. Es la misma regla que sigue
    `dashboard_view.execute_pack` ("quien llama pasa la accion, nunca el verbo").
    """
    if accion == "kill" and estado.pendiente(pack_id):
        return f"   ✅ Confirmar apagado de '{nombre}'"
    prefijo = "⛔" if accion == "kill" else "🚀"
    return f"{prefijo} {nombre}"


def texto_cancelar(estado: TrayMenuState) -> str:
    """El item de "Cancelar", o `None` si no hay nada que cancelar.

    `None` es lo que permite que el llamante lo OMITA del menu: un "Cancelar" sin nada
    pendiente es un item muerto que el usuario pulsaria sin efecto.
    """
    if not estado.pendiente_alguno():
        return None
    return "   ✖️ Cancelar"


def _monotonic_real() -> float:
    import time
    return time.monotonic()
