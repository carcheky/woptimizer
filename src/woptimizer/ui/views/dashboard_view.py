import customtkinter as ctk
import threading
from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService
from woptimizer.services.notification_service import NotificationService
from woptimizer.models import Pack
from woptimizer.ui.confirmation import AMBAR, CANCEL, MSG_EXPIRADO, VENTANA_MS_PORTADA, Confirmable

class DashboardView(Confirmable, ctk.CTkFrame):
    def __init__(self, master, process_service: ProcessService, pack_service: PackService, notification_service: NotificationService = None):
        super().__init__(master, fg_color="transparent")
        self.process_service = process_service
        self.pack_service = pack_service
        self.notification_service = notification_service or NotificationService()
        self._build_ui()
        self.refresh_dashboard()

    def _build_ui(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 20))

        self.title_label = ctk.CTkLabel(self.header, text="🏠 Inicio / Favoritos", font=("Segoe UI", 24, "bold"))
        self.title_label.pack(side="left")

        # Banner de telemetría de RAM — empieza oculto (no se hace pack aquí)
        self.status_banner_frame = ctk.CTkFrame(self, fg_color="transparent", height=36)
        self.status_label = ctk.CTkLabel(
            self.status_banner_frame,
            text="",
            font=("Segoe UI", 13, "bold"),
            wraplength=600,
            anchor="w",
        )
        self.status_label.pack(side="left", padx=12)

        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.pack(fill="both", expand=True)
        # Configurar grid para que los botones se centren o expandan
        self.buttons_frame.grid_columnconfigure((0, 1), weight=1)

        # TASK-023: doble pulsacion SOLO en la rama kill de execute_pack. Ventana mas
        # corta aqui (2000 ms) porque el boton es enorme y tiene vecinos pegados.
        self._init_confirmable(self.status_label, window_ms=VENTANA_MS_PORTADA)

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
    # Banner de Telemetría de RAM (TASK-014)
    # ------------------------------------------------------------------
    def _show_banner(self, killed: int, freed_mb: float, is_gaming: bool):
        """Muestra el banner de feedback con los datos de RAM liberada.

        Debe llamarse siempre desde el hilo principal (usar self.after(0, ...)).
        """
        fg = "#1B4332" if is_gaming else "#1a2a3a"
        txt = "#1DB954" if is_gaming else "#4a9fd4"
        msg = f"⚡ {killed} procesos cerrados · {freed_mb:.1f} MB liberados"
        self.status_banner_frame.configure(fg_color=fg)
        self.status_label.configure(text=msg, text_color=txt)
        self.status_banner_frame.pack(fill="x", pady=(0, 8), before=self.buttons_frame)
        self._schedule_ui(5000, self._hide_banner)

    def _hide_banner(self):
        """Oculta el banner de telemetría."""
        self.status_banner_frame.pack_forget()

    def refresh_dashboard(self):
        # Los botones se recrean: una pendiente sobre ellos no tiene a que reconfigurarse.
        self._forget_buttons()
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
            
        packs = self.pack_service.get_all_packs()
        favorites = [p for p in packs.values() if p.is_favorite]
        
        if not favorites:
            lbl = ctk.CTkLabel(self.buttons_frame, text="No tienes packs marcados como favoritos (⭐).\nVe al Gestor de Packs para añadir alguno.", font=("Segoe UI", 16), text_color="gray")
            lbl.grid(row=0, column=0, columnspan=2, pady=50)
            return

        row = 0
        col = 0
        for pack in favorites:
            self._create_favorite_button(pack, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

    def _create_favorite_button(self, pack: Pack, row: int, col: int):
        # El botón ejecuta la default_action del pack
        text = f"{pack.name}\n({len(pack.apps)} apps - {pack.default_action.upper()})"
        
        kwargs = {
            "master": self.buttons_frame,
            "text": text,
            "font": ("Segoe UI", 18, "bold"),
            "height": 120,
            "corner_radius": 15,
        }
        
        if pack.is_gaming:
            kwargs["fg_color"] = "#c22d2d"
            kwargs["hover_color"] = "#a12525"
            
        btn = ctk.CTkButton(**kwargs)
        btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        # El token lleva `dashboard:` para que la misma accion en la vista de packs no
        # se pise con esta (cada vista tiene su propia maquina de estados).
        btn.configure(command=lambda p=pack: self.execute_pack(p, btn))

    def execute_pack(self, pack: Pack, button=None):
        if not pack.apps:
            return

        if pack.default_action == "kill":
            if not self._require_double_tap(
                f"dashboard:{pack.id}", button,
                f"⚠️ Segunda pulsación para apagar {len(pack.apps)} apps de '{pack.name}'.",
            ):
                return

            def _run_kill(p: Pack):
                killed, _failed, _skipped, freed_mb = self.process_service.kill_pack_apps(p.apps)
                # Actualizar UI en el hilo principal — nunca tocar widgets desde un hilo secundario
                self.after(0, self._show_banner, killed, freed_mb, p.is_gaming)
                # TASK-019: toast nativo del sistema (visible con la ventana oculta)
                self.notification_service.notify_pack_activated(p.name, killed, freed_mb)

            threading.Thread(target=_run_kill, args=(pack,), daemon=True).start()
        else:
            # Arrancar no pide confirmacion, pero pulsar otra accion resetea la pendiente
            # anterior: si no, el boton quedaria en ambar sin nadie que lo confirme.
            self._cancel_confirm()
            def _run_start(p: Pack):
                launched, failed = self.process_service.start_pack_apps(p.apps)
                self.notification_service.notify_apps_launched(p.name, launched, failed)

            threading.Thread(target=_run_start, args=(pack,), daemon=True).start()
