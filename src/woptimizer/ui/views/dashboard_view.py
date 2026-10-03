import customtkinter as ctk
import threading
from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService
from woptimizer.services.gaming_service import GamingService
from woptimizer.services.notification_service import NotificationService
from woptimizer.models import Pack
from woptimizer.ui.confirmation import AMBAR, CANCEL, MSG_EXPIRADO, VENTANA_MS_PORTADA, Confirmable
from woptimizer.ui.feedback import (
    clausula_mb, es_pack_inerte, mensaje_banner_cierre, mensaje_banner_gaming_inerte,
    mensaje_banner_sin_apps, texto_confirmacion_apagado,
)
from woptimizer.ui import theme

#: Auto-ocultado del banner de telemetria, en ms (TASK-035). Constante y no
#: literal suelto porque las DOS puertas (`_show_start_banner` y `_show_banner`)
#: la comparten desde `_reprogramar_autoocultado`: duplicada, cada una era un
#: sitio donde el bug se escondia (ciclo 26, iteracion 3).
AUTOOCULTADO_MS = 5000

class DashboardView(Confirmable, ctk.CTkFrame):
    def __init__(self, master, process_service: ProcessService, pack_service: PackService, notification_service: NotificationService = None, gaming_service: GamingService = None):
        super().__init__(master, fg_color="transparent")
        self.process_service = process_service
        self.pack_service = pack_service
        self.notification_service = notification_service or NotificationService()
        # TASK-025: el Gaming Mode se ejecuta por `GamingService`, que es quien
        # consulta `keepers` y `target_categories`. Mismo patron defensivo que
        # `notification_service`: si no se inyecta se crea uno local para no
        # romper constructores antiguos ni tests.
        self.gaming_service = gaming_service or GamingService(process_service, pack_service)
        self._last_gaming_summary = None
        self._banner_timer = None
        self._buttons_by_pack_id = {}
        self._empty_label = None
        self._build_ui()
        self.refresh_dashboard()

    def _build_ui(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 12))

        self.title_label = ctk.CTkLabel(
            self.header,
            text="🏠 Inicio / Favoritos",
            font=("Segoe UI", theme.FONT_SIZE_HERO, "bold"),
            text_color=theme.TEXT_PRIMARY
        )
        self.title_label.pack(side="left")

        # UI-004: Banda de estado permanente en reposo (NUNCA usa psutil, consulta process_service)
        self.resting_bar = ctk.CTkFrame(
            self,
            fg_color=theme.SURFACE_ALT,
            height=32,
            corner_radius=theme.RADIUS_MEDIUM,
            border_width=1,
            border_color=theme.BORDER
        )
        self.resting_bar.pack(fill="x", pady=(0, 10))
        self.resting_bar.pack_propagate(False)

        self.resting_label = ctk.CTkLabel(
            self.resting_bar,
            text=self._get_resting_status_text(),
            font=("Segoe UI", theme.FONT_SIZE_SMALL),
            text_color=theme.TEXT_MUTED,
            anchor="w"
        )
        self.resting_label.pack(side="left", padx=12, fill="x", expand=True)

        # Banner de telemetría de RAM — empieza oculto (se muestra tras actuar)
        self.status_banner_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            height=36,
            corner_radius=theme.RADIUS_MEDIUM
        )
        self.banner_frame = self.status_banner_frame
        self.status_label = ctk.CTkLabel(
            self.status_banner_frame,
            text="",
            font=("Segoe UI", theme.FONT_SIZE_BODY, "bold"),
            wraplength=600,
            anchor="w",
        )
        self.lbl_banner = self.status_label
        self.status_label.pack(side="left", padx=12)

        # TASK-038: Banner/botón para restaurar apps cerradas en sesión Gaming
        self.restore_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            height=36,
            corner_radius=theme.RADIUS_MEDIUM
        )
        self.restore_button = ctk.CTkButton(
            self.restore_frame,
            text="",
            font=("Segoe UI", theme.FONT_SIZE_BODY, "bold"),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT_PRIMARY,
            height=36,
            corner_radius=theme.RADIUS_MEDIUM,
            command=self._on_restore_clicked
        )
        self.restore_button.pack(fill="x", padx=0, pady=0)

        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.pack(fill="both", expand=True)
        self._max_allocated_cols: int = 2
        self.buttons_frame.bind("<Configure>", self._on_frame_configure)

        # TASK-023: doble pulsacion SOLO en la rama kill de execute_pack.
        self._init_confirmable(self.status_label, window_ms=VENTANA_MS_PORTADA)

    def _get_resting_status_text(self) -> str:
        try:
            procs = self.process_service.get_running_processes()
            proc_count = len(procs)
        except Exception:
            proc_count = 0
        
        status = f"⚡ Telemetría: {proc_count} procesos activos en el sistema"
        if self._last_gaming_summary:
            status += f" · Último Gaming Mode: {self._last_gaming_summary}"
        else:
            status += " · Gaming Mode en espera"
        return status

    def _update_resting_bar(self):
        if hasattr(self, "resting_label") and self.resting_label.winfo_exists():
            self.resting_label.configure(text=self._get_resting_status_text())

    def destroy(self):
        if getattr(self, "_banner_timer", None):
            try:
                self.after_cancel(self._banner_timer)
            except Exception:
                pass
            self._banner_timer = None
        # El `after` de la pendiente pertenece a la vista: sin esto sobrevive al cambio
        # de pestaña y reconfigura un boton ya destruido (regla §6.1).
        self.cancel_on_destroy()
        super().destroy()

    # ------------------------------------------------------------------
    # Feedback inline de la doble pulsacion (TASK-023)
    # ------------------------------------------------------------------
    def _inline_status(self, text: str, color: str = AMBAR) -> None:
        """El banner arranca oculto, asi que el aviso hay que enseñarlo."""
        self.status_banner_frame.configure(fg_color=CANCEL)
        self.status_label.configure(text=text, text_color=color)
        self.status_banner_frame.pack(fill="x", pady=(0, 8), before=self.buttons_frame)

    def _on_expirado(self, token, button, expire_text: str = MSG_EXPIRADO) -> None:
        super()._on_expirado(token, button, expire_text)
        # El banner de la portada es de usar y tirar: si no, se queda con el aviso.
        self._schedule_ui(2500, self._hide_banner)

    # ------------------------------------------------------------------
    # Banner de Telemetría y Feedback (TASK-014 / TASK-035 / UI-004)
    # ------------------------------------------------------------------
    def _reprogramar_autoocultado(self):
        """ÚNICA puerta del temporizador del banner (TASK-035, ciclo 26 iter. 3).

        El bloque de cancelacion estaba DUPLICADO byte a byte en `_show_start_banner`
        y en `_show_banner`. Con la copia solo instrumentada en la sonda, tres
        mutaciones vivian: borrar la cancelacion, mover los 5000 ms a 60 000 y quitar
        el `_timers_ui.discard` (que deja el handle vivo y lo vuelve a cancelar al
        destruir). `_show_banner` es la puerta que el gamer ve tras pulsar "Apagar",
        asi que ahora las dos llaman aqui y hay un solo sitio que testear.
        """
        if getattr(self, "_banner_timer", None):
            try:
                self.after_cancel(self._banner_timer)
                if hasattr(self, "_timers_ui"):
                    self._timers_ui.discard(self._banner_timer)
            except Exception:
                pass
        self._banner_timer = self._schedule_ui(AUTOOCULTADO_MS, self._hide_banner)

    def _publicar_en_banner(self, texto: str, txt_color: str) -> None:
        """LA puerta unica de publicacion del banner (TASK-036).

        Poner fondo, texto, color, `pack(...)` y auto-ocultado era un bloque de
        cuatro lineas copiado en `_show_start_banner` y en `_show_banner`, y la
        tercera puerta (el aviso de pack inerte) iba a ser la TERCERA copia: que
        es exactamente el patron que perdio el ciclo 26. Aqui no se decide nada,
        solo se pinta lo que le traiga el formateador.
        """
        self.status_banner_frame.configure(fg_color=theme.SURFACE_ALT)
        self.status_label.configure(text=texto, text_color=txt_color)
        self.status_banner_frame.pack(fill="x", pady=(0, 8), before=self.buttons_frame)
        self._reprogramar_autoocultado()

    def _show_aviso_banner(self, texto: str, txt_color: str) -> None:
        """Aviso de que el pack NO puede hacer nada (TASK-036).

        **No** reusa `_inline_status`, y por dos razones medidas:

        1. `_inline_status` pinta el fondo con `CANCEL`, que es la familia del
           aviso de "confirmacion pendiente" (`PENDIENTE_FG`): un aviso
           permanente con ese fondo se lee como "espera la segunda pulsacion".
        2. `_inline_status` llama a `pack()` y no a `_reprogramar_autoocultado()`:
           el aviso se quedaria pegado, contra la regla de `_on_expirado` ("el
           banner de la portada es de usar y tirar").
        """
        self._publicar_en_banner(texto, txt_color)

    def _show_start_banner(self, launched: int, failed: int, pack_name: str):
        """Muestra el banner de feedback tras arrancar apps de un pack.

        Debe llamarse siempre desde el hilo principal (usar self.after(0, ...)).
        """
        self.process_service.invalidate_cache()
        self._update_resting_bar()

        if failed == 0:
            txt_color = theme.ACCENT
            msg = f"🚀 Pack '{pack_name}' iniciado ({launched} apps)."
        else:
            txt_color = theme.WARNING
            msg = f"⚠️ Pack '{pack_name}': {launched} apps iniciadas, {failed} fallaron."

        self._publicar_en_banner(msg, txt_color)

    def _show_banner(self, killed: int, freed_mb: float, is_gaming: bool,
                     failed: int = 0, skipped: int = 0):
        """Muestra el banner de feedback con los datos de RAM liberada.

        Debe llamarse siempre desde el hilo principal (usar self.after(0, ...)).

        TASK-035 / ciclo 26: `failed` y `skipped` ya no se tiran. Con 0 procesos
        cerrados el banner dice lo que paso y baja a `theme.WARNING`: el verde
        Gaming o el azul de acento son marcas de EXITO y no se conceden cuando
        no se ha cerrado nada.
        """
        msg, txt = mensaje_banner_cierre(killed, failed, skipped, freed_mb, is_gaming)
        if is_gaming:
            # La misma regla de `clausula_mb` que en el texto: sin MB liberados
            # no se escribe una MB que el usuario no puede cuadrar con nada.
            self._last_gaming_summary = f"{killed} cerrados{clausula_mb(freed_mb)}"
        self._update_resting_bar()
        self._show_restore_banner()

        self._publicar_en_banner(msg, txt)

    def _hide_banner(self):
        """Oculta el banner de telemetría."""
        self._banner_timer = None
        self.status_banner_frame.pack_forget()

    # ------------------------------------------------------------------
    # Restauración Inteligente de Sesión Gaming (TASK-038)
    # ------------------------------------------------------------------
    def _show_restore_banner(self):
        """Muestra u oculta la barra de restauración según el estado de la sesión Gaming."""
        get_closed = getattr(self.gaming_service, "get_last_closed_apps", None)
        closed_apps = get_closed() if callable(get_closed) else []
        if closed_apps:
            count = len(closed_apps)
            self.restore_button.configure(text=f"🔄 Restaurar Apps Cerradas ({count})")
            self.restore_frame.pack(fill="x", pady=(0, 8), before=self.buttons_frame)
        else:
            self.restore_frame.pack_forget()

    def _on_restore_clicked(self):
        def _run_restore():
            started, failed = self.gaming_service.restore_gaming_session()
            self.after(0, self._on_restore_finished, started, failed)

        import threading
        threading.Thread(target=_run_restore, daemon=True).start()

    def _on_restore_finished(self, started: int, failed: int):
        self._show_restore_banner()
        self._show_start_banner(started, failed, "Restauración Gaming")
        if getattr(self, "notification_service", None):
            self.notification_service.notify_apps_launched("Restauración Gaming", started, failed)

    def _destroy_favorite_buttons(self):
        """TASK-049: Extrae la destrucción de botones favoritos de ambas ramas."""
        self._forget_buttons()
        for btn in self._buttons_by_pack_id.values():
            btn.destroy()
        self._buttons_by_pack_id.clear()

    def _calculate_columns(self, num_favorites: int) -> int:
        """TASK-049: Calcula columnas activas según ancho disponible y ANCHO_MIN_CARD."""
        ancho_disponible = self.buttons_frame.winfo_width()
        if ancho_disponible <= 1:
            ancho_disponible = 800
        max_cols = max(1, ancho_disponible // theme.ANCHO_MIN_CARD)
        if num_favorites <= 0:
            return max_cols
        return max(1, min(num_favorites, max_cols))

    def _reconfigure_grid_columns(self, cols: int):
        """TASK-049: Asigna weight=1 a columnas activas y weight=0 a las sobrantes."""
        for c in range(cols):
            self.buttons_frame.grid_columnconfigure(c, weight=1, uniform="fav")
        max_to_clean = max(getattr(self, "_max_allocated_cols", 2), cols)
        for c in range(cols, max_to_clean):
            self.buttons_frame.grid_columnconfigure(c, weight=0, uniform="")
        self._max_allocated_cols = max(getattr(self, "_max_allocated_cols", 2), cols)

    def _on_frame_configure(self, event=None):
        """TASK-049: Manejador de evento <Configure> con filtro estricto de emisor."""
        if event is not None and event.widget != self.buttons_frame:
            return
        self._regrid_favorites()

    def _regrid_favorites(self):
        """TASK-049: Re-maillado de favoritos al redimensionar la ventana."""
        if not self._buttons_by_pack_id and not self._empty_label:
            return
        if self._empty_label and self._empty_label.winfo_exists():
            cols = self._calculate_columns(0)
            self._reconfigure_grid_columns(cols)
            self._empty_label.grid(columnspan=cols)
            return

        favorites = [p for p in self.pack_service.get_favorite_packs() if p.id in self._buttons_by_pack_id]
        if not favorites:
            return
        cols = self._calculate_columns(len(favorites))
        self._reconfigure_grid_columns(cols)
        for i, pack in enumerate(favorites):
            row = i // cols
            col = i % cols
            btn = self._buttons_by_pack_id.get(pack.id)
            if btn and btn.winfo_exists():
                btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    def refresh_dashboard(self):
        self._update_resting_bar()
        self._show_restore_banner()
        favorites = self.pack_service.get_favorite_packs()

        current_fav_ids = {p.id for p in favorites}
        cached_ids = set(self._buttons_by_pack_id.keys())

        if not favorites:
            self._destroy_favorite_buttons()
            cols = self._calculate_columns(0)
            self._reconfigure_grid_columns(cols)
            if not self._empty_label:
                self._empty_label = ctk.CTkLabel(
                    self.buttons_frame,
                    text="No tienes packs marcados como favoritos (⭐).\nVe al Gestor de Packs para añadir alguno a la portada.",
                    font=("Segoe UI", theme.FONT_SIZE_SUBHEADER),
                    text_color=theme.TEXT_MUTED
                )
                self._empty_label.grid(row=0, column=0, columnspan=cols, pady=50)
            else:
                self._empty_label.grid(columnspan=cols)
            return

        if self._empty_label:
            self._empty_label.destroy()
            self._empty_label = None

        cols = self._calculate_columns(len(favorites))
        self._reconfigure_grid_columns(cols)

        # Reutilizar o reconstruir los botones
        if current_fav_ids != cached_ids:
            self._destroy_favorite_buttons()
            for i, pack in enumerate(favorites):
                row = i // cols
                col = i % cols
                btn = self._create_favorite_button(pack, row, col)
                self._buttons_by_pack_id[pack.id] = btn
        else:
            for i, pack in enumerate(favorites):
                row = i // cols
                col = i % cols
                btn = self._buttons_by_pack_id.get(pack.id)
                if btn:
                    btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                    btn.configure(
                        text=self._get_pack_button_text(pack),
                        command=lambda p=pack, b=btn: self.execute_pack(p, b)
                    )

    def _get_pack_button_text(self, pack: Pack) -> str:
        # TASK-036 iter 7: el verbo de la tarjeta sale del PACK en las DOS
        # ramas. La tarjeta es lo primero que el usuario lee antes de pulsar, y
        # `execute_pack` decide con `pack.default_action`: si la tarjeta dice
        # "KILL" y el boton arranca, la tarjeta miente. El literal "KILL" de la
        # rama gaming era un hecho congelado en la vista (mismo patron que el
        # `default` silencioso de `_verbo`: cierto hoy, falso en cuanto el dato
        # se mueve). Con `DEFAULT_GAMING_PACK`, que nace con
        # `default_action="kill"`, el texto es EXACTAMENTE el de antes: lo que
        # cambia es que ya no es una afirmacion que esta vista mantiene sola.
        if pack.is_gaming:
            cats = len(pack.target_categories)
            return (f"{pack.name}\n({len(pack.apps)} apps · {cats} categorías · "
                    f"{pack.default_action.upper()})")
        return f"{pack.name}\n({len(pack.apps)} apps · {pack.default_action.upper()})"

    def _create_favorite_button(self, pack: Pack, row: int, col: int) -> ctk.CTkButton:
        text = self._get_pack_button_text(pack)
        
        kwargs = {
            "master": self.buttons_frame,
            "text": text,
            "font": ("Segoe UI", theme.FONT_SIZE_HEADER, "bold"),
            "height": 120,
            "corner_radius": theme.RADIUS_LARGE,
            "text_color": theme.TEXT_PRIMARY,
        }
        
        if pack.is_gaming:
            kwargs["fg_color"] = theme.GAMING
            kwargs["hover_color"] = theme.GAMING_HOVER
            kwargs["text_color"] = theme.SURFACE
        else:
            kwargs["fg_color"] = theme.ACCENT
            kwargs["hover_color"] = theme.ACCENT_HOVER
            kwargs["text_color"] = theme.TEXT_PRIMARY
            
        btn = ctk.CTkButton(**kwargs)
        btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        btn.configure(command=lambda p=pack, b=btn: self.execute_pack(p, b))
        return btn

    def _texto_confirmacion_apagado(self, pack: Pack) -> str:
        """La frase de la doble pulsacion, con el numero de la PUERTA.

        El numero lo pone `gaming_service.cuenta_a_apagar(pack)`, que aplica el
        mismo filtro que `execute_pack` va a aplicar: si esta vista contara por su
        cuenta seria una segunda politica de seguridad en el sitio que menos
        puede tenerla. La frase vive en `ui/feedback.py` para que el Gestor y la
        Portada digan exactamente lo mismo.
        """
        return texto_confirmacion_apagado(
            pack.name,
            self.gaming_service.cuenta_a_apagar(pack),
            len(pack.apps),
            len(pack.target_categories),
        )

    def execute_pack(self, pack: Pack, button=None):
        # TASK-036: las guardas van ANTES de `_require_double_tap` y ANTES de
        # tocar nada, asi que el aviso sale de UN solo punto por puerta y el
        # verbo lo decide `default_action` solo. Armar la doble pulsacion sobre
        # un pack que no puede hacer nada produciria "Segunda pulsacion para
        # apagar 0 apps de 'X'", que es la fealdad que estas guardas evitan.
        #
        # TASK-063: las guardas son POR PUERTA y cada una mira las listas de SU
        # puerta. `es_pack_inerte` significa "el Gaming no tiene NADA que
        # CERRAR" (`feedback.py`: 0 apps y 0 categorias, o sea, inerte por la via
        # de kill), asi que se evalua DENTRO de la rama de apagar y no antes: antes
        # de la rama del verbo, un gaming con `default_action="start"` y
        # `start_categories` marcadas oia "Gaming inerte" en la puerta de ARRANCAR,
        # que es un diagnostico de otra puerta. Las dos guardas siguen antes de
        # `_require_double_tap`, que es lo que el comentario de arriba preserva.
        if pack.default_action == "kill":
            if es_pack_inerte(pack.is_gaming, len(pack.apps), len(pack.target_categories)):
                self._show_aviso_banner(*mensaje_banner_gaming_inerte(pack.name))
                return
            if not pack.apps and not pack.target_categories:
                # El silencio no es la opcion neutra: la pulsacion no dejaba ni
                # rastro, y con `default_action="start"` el usuario creia que se
                # abrian programas que nunca se abren. Sin hilo, sin `after` y sin
                # worker: ya estamos en el hilo principal dentro de un callback.
                self._show_aviso_banner(*mensaje_banner_sin_apps(pack.name, pack.default_action))
                return

            if pack.is_gaming:
                aviso = f"⚠️ Segunda pulsación para preparar el Gaming Mode de '{pack.name}'."
            else:
                aviso = self._texto_confirmacion_apagado(pack)
            if not self._require_double_tap(f"dashboard:{pack.id}", button, aviso):
                return

            def _run_kill(p: Pack):
                # Las dos puertas devuelven la misma 4-tupla y el texto se
                # calcula una sola vez en `ui/feedback.py` (ciclo 26).
                killed, failed, skipped, freed_mb = self.gaming_service.execute_pack(p)
                self.after(0, self._show_banner, killed, freed_mb, p.is_gaming, failed, skipped)
                self.notification_service.notify_pack_activated(p.name, killed, freed_mb)

            threading.Thread(target=_run_kill, args=(pack,), daemon=True).start()
        else:
            self._cancel_confirm()
            if not pack.apps and not pack.start_categories:
                # La puerta de arrancar mira `start_categories`, no
                # `target_categories`: apagar por una categoria no significa que
                # haya algo que iniciar, y al reves tampoco.
                self._show_aviso_banner(*mensaje_banner_sin_apps(pack.name, pack.default_action))
                return

            def _run_start(p: Pack):
                # TASK-063: la puerta de arranque ejecuta SUS DOS listas (las apps
                # explicitas y las categorias de arranque) y SUMA los dos
                # recuentos. Elegir una y dejar la otra seria un apagado del
                # criterio del usuario en silencio. El conflicto de las dos listas
                # lo resuelve el servicio, no esta vista.
                launched, failed = self.process_service.start_pack_apps(p.apps)
                if p.start_categories:
                    launched_cats, failed_cats = self.process_service.start_pack_categories(
                        p.start_categories, p.target_categories
                    )
                    launched += launched_cats
                    failed += failed_cats
                self.after(0, self._show_start_banner, launched, failed, p.name)
                self.notification_service.notify_apps_launched(p.name, launched, failed)

            threading.Thread(target=_run_start, args=(pack,), daemon=True).start()
