"""
NotificationService — Notificaciones nativas de Windows (TASK-019).

Envuelve `pystray.Icon.notify()` para emitir balloons/toasts del sistema
operativo sin acoplar la UI a la libreria de bandeja.

Invariantes:
- **UI nunca llama a pystray directamente**: solo consume la API `notify_*()`.
- **Nunca lanza excepciones**: cualquier fallo degrada a `logger` y la app sigue.
- **Sin dependencias nuevas**: reutiliza `pystray`, ya presente por TASK-012.
- **Thread-safe**: `Icon.notify()` es seguro desde cualquier hilo en Windows;
  aun asi se protege con un lock para evitar condiciones de carrera en el
  intercambio de la referencia del icono.
"""

from __future__ import annotations

import threading
from typing import Any, Optional

from woptimizer.config import logger

# Radio de toast: True = exito, False = fallo parcial. Se expone para que
# los tests puedan verificar el formato sin depender del sistema operativo.
_GAMING_TITLE = "woptimizer"
_SUCCESS_ICON = None  # pystray usa el icono por defecto; no personalizamos bitmap


class NotificationService:
    """ Fachada de notificaciones del sistema.

    Se instancia una unica vez en `WOptimizerApp` y se inyecta por
    `MainWindow` hasta las vistas (dependencia explicita, sin singletons).
    """

    def __init__(self) -> None:
        self._tray_icon: Optional[Any] = None
        self._lock = threading.RLock()
        self._sent_count = 0
        self._dropped_count = 0

    # ------------------------------------------------------------------
    # Ciclo de vida del icono de bandeja
    # ------------------------------------------------------------------
    def attach_tray(self, icon: Any) -> None:
        """Registra el `pystray.Icon` vivo para poder emitir notificaciones."""
        with self._lock:
            self._tray_icon = icon
        logger.debug(f"NotificationService: tray adjunta ({type(icon).__name__})")

    def detach_tray(self) -> None:
        """Libera la referencia al icono (cierre limpio / ventana restaurada)."""
        with self._lock:
            self._tray_icon = None
        logger.debug("NotificationService: tray desadjunta")

    @property
    def has_tray(self) -> bool:
        """True si hay un icono de bandeja disponible para notificar."""
        with self._lock:
            return self._tray_icon is not None

    @property
    def stats(self) -> dict:
        """Contadores para diagnostico y tests headless."""
        with self._lock:
            return {"sent": self._sent_count, "dropped": self._dropped_count}

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------
    def notify(self, title: str, message: str) -> bool:
        """Emite una notificacion nativa. Devuelve True si se mostro.

        Nunca propaga excepciones: degrada a `logger.info`/`logger.warning`.
        """
        with self._lock:
            icon = self._tray_icon

        if icon is None:
            with self._lock:
                self._dropped_count += 1
            logger.info(f"[toast omitida, sin tray] {title}: {message}")
            return False

        try:
            # Guarda de plataforma: algunos backends no soportan notify().
            if hasattr(icon, "HAS_NOTIFICATION") and not icon.HAS_NOTIFICATION:
                with self._lock:
                    self._dropped_count += 1
                logger.info(f"[toast no soportada en esta plataforma] {title}: {message}")
                return False

            icon.notify(message, title)
        except Exception as exc:  # noqa: BLE001 - la UI no debe romperse nunca
            with self._lock:
                self._dropped_count += 1
            logger.warning(f"Fallo al emitir toast '{title}': {exc}")
            return False

        with self._lock:
            self._sent_count += 1
        logger.info(f"[toast] {title}: {message}")
        return True

    # ------------------------------------------------------------------
    # Helpers semanticos
    # ------------------------------------------------------------------
    def notify_kill_result(self, killed: int, failed: int, freed_mb: float = 0.0) -> bool:
        """Notifica el resultado de un cierre manual de procesos."""
        return self.notify(_GAMING_TITLE, format_kill_result(killed, failed, freed_mb))

    def notify_pack_activated(self, pack_name: str, killed: int, freed_mb: float = 0.0) -> bool:
        """Notifica que un pack con accion `kill` se ejecuto."""
        body = f"Pack '{pack_name}': {format_kill_result(killed, 0, freed_mb)}"
        return self.notify(_GAMING_TITLE, body)

    def notify_apps_launched(self, pack_name: str, launched: int, failed: int = 0) -> bool:
        """Notifica que un pack con accion `start` se ejecuto."""
        if failed:
            body = f"Pack '{pack_name}': {launched} apps iniciadas, {failed} fallaron."
        else:
            body = f"Pack '{pack_name}': {launched} apps iniciadas."
        return self.notify(_GAMING_TITLE, body)


def format_kill_result(killed: int, failed: int, freed_mb: float = 0.0) -> str:
    """Construye el texto de resumen de un cierre. Funcion pura y testeable."""
    parts = [f"{killed} cerrada{'s' if killed != 1 else ''}"]
    if failed:
        parts.append(f"{failed} fallida{'s' if failed != 1 else ''}")
    msg = " · ".join(parts)
    if freed_mb > 0:
        msg = f"{msg} · {freed_mb:.1f} MB liberados"
    return msg
