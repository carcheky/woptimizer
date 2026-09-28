import customtkinter as ctk
import threading
from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService
from woptimizer.models import Pack

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, process_service: ProcessService, pack_service: PackService):
        super().__init__(master, fg_color="transparent")
        self.process_service = process_service
        self.pack_service = pack_service
        self._build_ui()
        self.refresh_dashboard()

    def _build_ui(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 20))
        
        self.title_label = ctk.CTkLabel(self.header, text="🏠 Inicio / Favoritos", font=("Segoe UI", 24, "bold"))
        self.title_label.pack(side="left")
        
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.pack(fill="both", expand=True)
        # Configurar grid para que los botones se centren o expandan
        self.buttons_frame.grid_columnconfigure((0, 1), weight=1)

    def refresh_dashboard(self):
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
            "command": lambda p=pack: self.execute_pack(p)
        }
        
        if pack.is_gaming:
            kwargs["fg_color"] = "#c22d2d"
            kwargs["hover_color"] = "#a12525"
            
        btn = ctk.CTkButton(**kwargs)
        btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    def execute_pack(self, pack: Pack):
        if not pack.apps:
            return
            
        if pack.default_action == "kill":
            threading.Thread(target=self.process_service.kill_pack_apps, args=(pack.apps,), daemon=True).start()
        else:
            threading.Thread(target=self.process_service.start_pack_apps, args=(pack.apps,), daemon=True).start()
