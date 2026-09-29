"""
Doble pulsacion para acciones destructivas (TASK-023).

POR QUE EXISTE
En la v2 (`process_manager.py` v2.0.2) las acciones destructivas exigian una segunda
pulsacion, con un helper de confirmacion y otro de reset que la reescritura borro. El patron
se instaURO (ver `docs/known-issues.md`, Trampa #14) tras un incidente real: un dialogo
modal de confirmacion se abria POR DETRAS de la ventana principal, el usuario pulsaba
"Cerrar", no veia nada y concluido "se ha roto, no mata procesos". Conclusion registrada:
NUNCA un dialogo modal en la ventana principal; la seguridad se consigue con la segunda
pulsacion, no con un dialogo. Ese patron se perdio en la reescritura v3 y esta es su unica
copia en el proyecto.

QUE HAY DENTRO (dos capas, y solo dos)
1. `DoubleTapGuard` -- maquina de estados PURA. No conoce widgets, no importa tkinter ni
   customtkinter y recibe un `scheduler` inyectable, asi que se testea headless con un doble.
   Aqui vive el test que discrimina (`test_double_tap_guard` en `run_tests.py`).
2. `Confirmable` -- mixin FINO para las vistas. Solo configura widgets (text / fg_color /
   hover_color del boton) y escribe en el `status_label`. No decide nada de negocio.

INVARIANTE DE FRONTERA DE CAPAS (AGENTS.md)
La UI no toca el sistema operativo ni el JSON, y aqui la frontera es doble: este modulo solo
puede importar `typing`. PROHIBIDO `psutil`, `json`, `woptimizer.services` y
`woptimizer.models`. `tkinter` tampoco se importa a nivel de modulo, para que la maquina de
estado se pueda importar en un test sin ninguna dependencia de Tk.
"""

from typing import Any, Callable, Dict, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Literales de estado. Compartidos por las 5 acciones: el mismo aspecto en
# todas, para que el usuario reconozca el patron a la primera.
# ---------------------------------------------------------------------------
PENDIENTE_TEXT = "⚠️ ¿SEGURO? PULSA OTRA VEZ"
PENDIENTE_FG = "#b8860b"       # ambar
PENDIENTE_HOVER = "#8a6508"
CANCEL = "#5a4a1e"            # fondo del aviso inline en la portada

ROJO = "#c22d2d"              # bloqueos (⛔)
AMBAR = "#b8860b"             # avisos (⚠️)
VERDE = "#1DB954"             # exitos (✅), el mismo del banner de la portada
GRIS = "gray"

VENTANA_MS = 3000             # ventana estandar de confirmacion
VENTANA_MS_PORTADA = 2000     # portada: boton enorme con vecinos pegados
REHABILITAR_MS = 300          # boton inutilizado tras confirmar

MSG_EXPIRADO = "Cancelado por tiempo de espera."
MSG_SELECCION_CAMBIADA = "⚠️ Selección cambiada. Vuelve a pulsar para confirmar."
MSG_SIN_SELECCION = "⚠️ Selecciona procesos primero."
MSG_SIN_PROCESOS = "⚠️ Esos procesos ya no están en ejecución."
MSG_PACK_INEXISTENTE = "⚠️ Ese pack ya no existe."

_CUALQUIERA = object()  # centinela: distingue "sin comprobar" de "token None"


class TkScheduler:
    """Adaptador de Tk sobre el widget dueno: `after` / `after_cancel`.

    Vive en el modulo, no en la maquina de estado, para que `DoubleTapGuard` se pueda
    construir con cualquier doble en los tests. Usa SIEMPRE `widget.after` y no
    `widget.master.after`: el timer pertence a la vista y no sobrevive a la navegacion
    entre pestanas (main_window destruye la vista actual en cada cambio).
    """

    def __init__(self, widget: Any) -> None:
        self.widget = widget

    def schedule(self, delay_ms: int, callback: Callable[[], None]) -> Any:
        return self.widget.after(delay_ms, callback)

    def cancel(self, handle: Any) -> None:
        if handle is None:
            return
        try:
            self.widget.after_cancel(handle)
        except Exception:  # tk.TclError: el widget ya no existe
            pass


class DoubleTapGuard:
    """Maquina de estados pura de la doble pulsacion. Sin widgets, sin Tk.

    Estados: REPOSO -> (arm) PENDIENTE -> (consume) EJECUTADA, o -> (reset / expiry) REPOSO.
    Solo hay una pendiente viva a la vez: pulsar otra accion distinta la descarta (§3.5).
    """

    def __init__(self, scheduler: Any, window_ms: int = VENTANA_MS) -> None:
        self.scheduler = scheduler
        self.window_ms = window_ms
        self.token: Any = None
        self.label: str = ""
        self._on_expire: Optional[Callable[[], None]] = None
        self._handle: Any = None

    # -- consultas ----------------------------------------------------------
    def is_pending(self, token: Any = _CUALQUIERA) -> bool:
        """Hay una pendiente viva. Sin argumento, responde por la que sea."""
        if self.token is None:
            return False
        if token is _CUALQUIERA:
            return True
        return bool(self.token == token)

    # -- transiciones --------------------------------------------------------
    def arm(self, token: Any, label: str, on_expire: Optional[Callable[[], None]] = None) -> bool:
        """Primera pulsacion: deja la pendiente armada. False si ya habia una para ESE token."""
        if self.token is not None and self.token == token:
            return False
        self.reset()
        self.token = token
        self.label = label
        self._on_expire = on_expire
        self._handle = self.scheduler.schedule(self.window_ms, self._expire)
        return True

    def consume(self, token: Any) -> Optional[str]:
        """Segunda pulsacion: devuelve el label si confirma, None si no.

        Si la pendiente es de OTRO token se descarta sin ejecutar: el usuario pulso otra
        accion y la intencion anterior ya no es la suya.
        """
        if self.token is None:
            return None
        if not self.token == token:
            self.reset()
            return None
        label = self.label
        self.reset()
        return label

    def reset(self) -> Optional[str]:
        """Cancela la pendiente sin ejecutar. Devuelve el label que se estaba esperando."""
        label = self.label if self.token is not None else None
        self._descartar_timer()
        self.token = None
        self.label = ""
        self._on_expire = None
        return label

    def cancel_on_destroy(self) -> None:
        """Punto de entrada para `destroy()`: mata el `after` vivo y no ejecuta nada."""
        self.reset()

    # -- interno ------------------------------------------------------------
    def _expire(self) -> None:
        callback, self._on_expire = self._on_expire, None
        self.reset()
        if callback is not None:
            callback()

    def _descartar_timer(self) -> None:
        handle, self._handle = self._handle, None
        if handle is not None:
            self.scheduler.cancel(handle)


class Confirmable:
    """Mixin fino de las vistas: configura widgets y escribe el feedback inline.

    No hereda de `CTkFrame` a proposito: instanciar un frame de Tk exigiria un root, y la
    maquina de estado tiene que poder probarse sin ventana. Las vistas se pasan a si
    mismos los widgets que hay que reconfigurar, asi que este mixin no guarda estado de
    negocio, solo el boton que esta en estado pendiente.
    """

    # -- ciclo de vida ------------------------------------------------------
    def _init_confirmable(self, status_label: Any = None, window_ms: int = VENTANA_MS,
                          scheduler: Any = None) -> None:
        self.status_label = status_label
        self._guard = DoubleTapGuard(scheduler or TkScheduler(self), window_ms=window_ms)
        self._reposo: Dict[Any, Tuple[Any, Any, Any]] = {}
        self._boton_pendiente: Any = None
        self._timers_ui: Set[Any] = set()

    def cancel_on_destroy(self) -> None:
        """Llamar desde `destroy()` ANTES de `super().destroy()` (regla §6.1)."""
        self._guard.cancel_on_destroy()
        for handle in list(self._timers_ui):
            self._guard.scheduler.cancel(handle)
        self._timers_ui.clear()
        self._boton_pendiente = None

    def _forget_buttons(self) -> None:
        """Olvida el estado de reposo capturado: los botones se acaban de recrear."""
        self.cancel_on_destroy()
        self._reposo.clear()

    # -- API para las vistas ------------------------------------------------
    def _require_double_tap(self, token: Any, button: Any = None, label: str = "",
                            expire_text: str = MSG_EXPIRADO,
                            changed_text: Optional[str] = None) -> bool:
        """True = segunda pulsacion (el llamante ejecuta). False = primera (queda armada).

        `changed_text` sustituye a `label` cuando la pendiente que se descarta es de otro
        token, que es el caso de "el usuario cambio la seleccion entre pulsaciones".
        """
        guard = self._guard
        anterior = guard.token

        if guard.consume(token) is not None:
            self._restaurar_boton(token, button, disable_ms=REHABILITAR_MS)
            return True

        if anterior is not None and anterior != token and changed_text:
            label = changed_text

        armado = guard.arm(
            token, label,
            on_expire=lambda t=token, b=button: self._on_expirado(t, b, expire_text),
        )
        if not armado:
            return False

        self._boton_pendiente = button
        self._recordar_reposo(token, button)
        self._configurar(button, text=PENDIENTE_TEXT, fg_color=PENDIENTE_FG,
                         hover_color=PENDIENTE_HOVER)
        self._inline_status(label, AMBAR)
        return False

    def _cancel_confirm(self) -> None:
        """Descarta la pendiente y devuelve el boton a reposo, sin ejecutar."""
        token, boton = self._guard.token, self._boton_pendiente
        self._boton_pendiente = None
        self._guard.reset()
        if token is not None:
            self._restaurar_boton(token, boton)

    def _on_expirado(self, token: Any, button: Any, expire_text: str) -> None:
        self._boton_pendiente = None
        self._restaurar_boton(token, button)
        self._inline_status(expire_text, AMBAR)

    # -- feedback -----------------------------------------------------------
    def _inline_status(self, text: str, color: str = GRIS) -> None:
        """Feedback inline. La portada lo sobreescribe para ensenar su banner."""
        self._configurar(self.status_label, text=text, text_color=color)

    # -- interno ------------------------------------------------------------
    def _recordar_reposo(self, token: Any, button: Any) -> None:
        """Guarda el estado de reposo del boton la primera vez, para poder restaurarlo."""
        if button is None or token in self._reposo:
            return
        try:
            self._reposo[token] = (button.cget("text"), button.cget("fg_color"),
                                   button.cget("hover_color"))
        except Exception:  # sin cget el boton no se podra restaurar, pero la app no se rompe
            pass

    def _restaurar_boton(self, token: Any, button: Any, disable_ms: int = 0) -> None:
        if button is None:
            return
        reposo = self._reposo.get(token)
        if reposo is not None:
            self._configurar(button, text=reposo[0], fg_color=reposo[1], hover_color=reposo[2])
        if disable_ms:
            self._configurar(button, state="disabled")
            self._schedule_ui(disable_ms, lambda: self._configurar(button, state="normal"))

    def _configurar(self, widget: Any, **kwargs: Any) -> bool:
        """`configure` a prueba de widget muerto: `winfo_exists` + red tk.TclError."""
        if widget is None:
            return False
        try:
            if not widget.winfo_exists():
                return False
            widget.configure(**kwargs)
            return True
        except Exception:  # incluye tk.TclError: la vista ya fue destruida
            return False

    def _schedule_ui(self, delay_ms: int, callback: Callable[[], None]) -> Any:
        """`after` de un solo disparo, registrado para poder cancelarlo al destruir."""
        manejador: list = []

        def _disparar() -> None:
            if manejador:
                self._timers_ui.discard(manejador[0])
            callback()

        try:
            handle = self._guard.scheduler.schedule(delay_ms, _disparar)
        except Exception:
            return None
        manejador.append(handle)
        self._timers_ui.add(handle)
        return handle
