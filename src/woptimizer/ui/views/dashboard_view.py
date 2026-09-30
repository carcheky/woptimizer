import customtkinter as ctk
import threading
from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService
from woptimizer.services.gaming_service import GamingService
from woptimizer.services.notification_service import NotificationService
from woptimizer.models import Pack
from woptimizer.ui.confirmation import AMBAR, CANCEL, MSG_EXPIRADO, VENTANA_MS_PORTADA, Confirmable
from woptimizer.ui import theme

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
        self.status_label = ctk.CTkLabel(
            self.status_banner_frame,
            text="",
            font=("Segoe UI", theme.FONT_SIZE_BODY, "bold"),
            wraplength=600,
            anchor="w",
        )
        self.status_label.pack(side="left", padx=12)

        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.pack(fill="both", expand=True)
        # Configurar grid para que los botones se centren o expandan
        self.buttons_frame.grid_columnconfigure((0, 1), weight=1)

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
    # Banner de Telemetría de RAM (TASK-014 / UI-004)
    # ------------------------------------------------------------------
    def _show_banner(self, killed: int, freed_mb: float, is_gaming: bool):
        """Muestra el banner de feedback con los datos de RAM liberada.

        Debe llamarse siempre desde el hilo principal (usar self.after(0, ...)).
        """
        fg = theme.SURFACE_ALT
        txt = theme.GAMING if is_gaming else theme.ACCENT
        msg = f"⚡ {killed} procesos cerrados · {freed_mb:.1f} MB liberados"
        if is_gaming:
            self._last_gaming_summary = f"{killed} cerrados, {freed_mb:.1f} MB"
        self._update_resting_bar()

        self.status_banner_frame.configure(fg_color=fg)
        self.status_label.configure(text=msg, text_color=txt)
        self.status_banner_frame.pack(fill="x", pady=(0, 8), before=self.buttons_frame)
        self._schedule_ui(5000, self._hide_banner)

    def _hide_banner(self):
        """Oculta el banner de telemetría."""
        self.status_banner_frame.pack_forget()

    def refresh_dashboard(self):
        self._update_resting_bar()
        packs = self.pack_service.get_all_packs()
        favorites = [p for p in packs.values() if p.is_favorite]

        current_fav_ids = {p.id for p in favorites}
        cached_ids = set(self._buttons_by_pack_id.keys())

        if not favorites:
            self._forget_buttons()
            for btn in self._buttons_by_pack_id.values():
                btn.destroy()
            self._buttons_by_pack_id.clear()

            if not self._empty_label:
                self._empty_label = ctk.CTkLabel(
                    self.buttons_frame,
                    text="No tienes packs marcados como favoritos (⭐).\nVe al Gestor de Packs para añadir alguno a la portada.",
                    font=("Segoe UI", theme.FONT_SIZE_SUBHEADER),
                    text_color=theme.TEXT_MUTED
                )
                self._empty_label.grid(row=0, column=0, columnspan=2, pady=50)
            return

        if self._empty_label:
            self._empty_label.destroy()
            self._empty_label = None

        # Reutilizar o reconstruir los botones
        if current_fav_ids != cached_ids:
            self._forget_buttons()
            for btn in self._buttons_by_pack_id.values():
                btn.destroy()
            self._buttons_by_pack_id.clear()

            row = 0
            col = 0
            for pack in favorites:
                btn = self._create_favorite_button(pack, row, col)
                self._buttons_by_pack_id[pack.id] = btn
                col += 1
                if col > 1:
                    col = 0
                    row += 1
        else:
            for pack in favorites:
                btn = self._buttons_by_pack_id.get(pack.id)
                if btn:
                    btn.configure(
                        text=self._get_pack_button_text(pack),
                        command=lambda p=pack, b=btn: self.execute_pack(p, b)
                    )

    def _get_pack_button_text(self, pack: Pack) -> str:
        if pack.is_gaming:
            cats = len(pack.target_categories)
            return f"{pack.name}\n({len(pack.apps)} apps · {cats} categorías · KILL)"
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

    def execute_pack(self, pack: Pack, button=None):
        if not pack.is_gaming and not pack.apps:
            return

        if pack.default_action == "kill":
            if pack.is_gaming:
                aviso = f"⚠️ Segunda pulsación para preparar el Gaming Mode de '{pack.name}'."
            else:
                aviso = f"⚠️ Segunda pulsación para apagar {len(pack.apps)} apps de '{pack.name}'."
            if not self._require_double_tap(f"dashboard:{pack.id}", button, aviso):
                return

            def _run_kill(p: Pack):
                if p.is_gaming:
                    killed, _failed, _skipped, freed_mb = self.gaming_service.execute_gaming_pack(p)
                else:
                    killed, _failed, _skipped, freed_mb = self.process_service.kill_pack_apps(p.apps)
                self.after(0, self._show_banner, killed, freed_mb, p.is_gaming)
                self.notification_service.notify_pack_activated(p.name, killed, freed_mb)

            threading.Thread(target=_run_kill, args=(pack,), daemon=True).start()
        else:
            self._cancel_confirm()
            def _run_start(p: Pack):
                launched, failed = self.process_service.start_pack_apps(p.apps)
                self.notification_service.notify_apps_launched(p.name, launched, failed)

            threading.Thread(target=_run_start, args=(pack,), daemon=True).start()
