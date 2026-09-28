import customtkinter as ctk
from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService
from woptimizer.services.gaming_service import GamingService
from woptimizer.ui.views.process_manager_view import ProcessManagerView

class MainWindow(ctk.CTkFrame):
    def __init__(self, master, process_service: ProcessService, pack_service: PackService, gaming_service: GamingService):
        super().__init__(master)
        self.process_service = process_service
        self.pack_service = pack_service
        self.gaming_service = gaming_service
        
        self.current_view = None
        self._build_sidebar()
        self._show_process_manager() # Por defecto mostramos la nueva vista

    def _build_sidebar(self):
        # Contenedor principal de las vistas
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        # Barra de navegación inferior
        self.nav_frame = ctk.CTkFrame(self, height=50)
        self.nav_frame.pack(fill="x", side="bottom", padx=10, pady=10)
        
        self.btn_nav_home = ctk.CTkButton(self.nav_frame, text="🏠 Portada", command=self._show_home, fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"))
        self.btn_nav_home.pack(side="left", expand=True, padx=5)
        
        self.btn_nav_packs = ctk.CTkButton(self.nav_frame, text="📁 Gestor de Packs", command=self._show_packs, fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"))
        self.btn_nav_packs.pack(side="left", expand=True, padx=5)
        
        self.btn_nav_procs = ctk.CTkButton(self.nav_frame, text="⚡ Gestor de Procesos", command=self._show_process_manager)
        self.btn_nav_procs.pack(side="left", expand=True, padx=5)

    def _clear_content(self):
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None
            
        # Reset nav buttons style
        self.btn_nav_home.configure(fg_color="transparent")
        self.btn_nav_packs.configure(fg_color="transparent")
        self.btn_nav_procs.configure(fg_color="transparent")

    def _show_home(self):
        self._clear_content()
        self.btn_nav_home.configure(fg_color=["#3B8ED0", "#1F6AA5"])
        self.current_view = ctk.CTkLabel(self.content_frame, text="🏠 Portada\n(En construcción - TASK-004)", font=("Segoe UI", 24))
        self.current_view.pack(expand=True)

    def _show_packs(self):
        self._clear_content()
        self.btn_nav_packs.configure(fg_color=["#3B8ED0", "#1F6AA5"])
        self.current_view = ctk.CTkLabel(self.content_frame, text="📁 Gestor de Packs\n(En construcción - TASK-003)", font=("Segoe UI", 24))
        self.current_view.pack(expand=True)

    def _show_process_manager(self):
        self._clear_content()
        self.btn_nav_procs.configure(fg_color=["#3B8ED0", "#1F6AA5"])
        self.current_view = ProcessManagerView(
            self.content_frame, 
            self.process_service, 
            self.pack_service
        )
        self.current_view.pack(fill="both", expand=True)
