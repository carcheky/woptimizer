import customtkinter as ctk
import threading
from typing import Dict, List
from woptimizer.services.process_service import ProcessService
from woptimizer.services.profile_service import ProfileService
from woptimizer.services.gaming_service import GamingService
from woptimizer.models import ProcessInfo

class MainWindow(ctk.CTkFrame):
    def __init__(self, master, process_service: ProcessService, profile_service: ProfileService, gaming_service: GamingService):
        super().__init__(master)
        self.process_service = process_service
        self.profile_service = profile_service
        self.gaming_service = gaming_service
        
        self.processes: List[ProcessInfo] = []
        self.checkboxes: Dict[int, ctk.CTkCheckBox] = {}
        
        self._build_ui()
        self.refresh_processes()

    def _build_ui(self):
        # Header (Botones principales)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 20))
        
        self.btn_gaming = ctk.CTkButton(
            self.header_frame, 
            text="🚀 GAMING\nCerrar todo", 
            font=("Segoe UI", 18, "bold"),
            height=80,
            command=self.on_gaming_click,
            fg_color="#c22d2d",
            hover_color="#a12525"
        )
        self.btn_gaming.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_pack = ctk.CTkButton(
            self.header_frame, 
            text="📦 ABRIR PACK\nMi setup", 
            font=("Segoe UI", 18, "bold"),
            height=80,
            command=self.on_pack_click
        )
        self.btn_pack.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Lista de procesos
        self.list_label = ctk.CTkLabel(self, text="Procesos en ejecución:", font=("Segoe UI", 14, "bold"))
        self.list_label.pack(anchor="w", pady=(0, 10))
        
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)
        
        # Footer
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(fill="x", pady=(20, 0))
        
        self.btn_refresh = ctk.CTkButton(self.footer_frame, text="🔄 Actualizar", command=self.refresh_processes, width=120)
        self.btn_refresh.pack(side="left")
        
        self.btn_kill_selected = ctk.CTkButton(self.footer_frame, text="⛔ Cerrar Seleccionados", command=self.on_kill_selected, fg_color="#c22d2d", hover_color="#a12525")
        self.btn_kill_selected.pack(side="right")
        
        self.status_label = ctk.CTkLabel(self.footer_frame, text="✅ Listo.", text_color="gray")
        self.status_label.pack(side="left", padx=20)

    def refresh_processes(self):
        self.status_label.configure(text="⏳ Cargando procesos...")
        self.update_idletasks()
        
        def _load():
            self.processes = self.process_service.get_running_processes()
            self.master.after(0, self._render_list)
            
        threading.Thread(target=_load, daemon=True).start()

    def _render_list(self):
        # Limpiar frame
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.checkboxes.clear()
        
        current_cat = None
        for p in self.processes:
            if p.category != current_cat:
                current_cat = p.category
                cat_label = ctk.CTkLabel(self.scroll_frame, text=current_cat, font=("Segoe UI", 14, "bold"), text_color="#3a7ebf")
                cat_label.pack(anchor="w", pady=(10 if len(self.checkboxes) > 0 else 0, 5))
            
            cb = ctk.CTkCheckBox(self.scroll_frame, text=f"{p.name} (PID: {p.pid})", font=("Segoe UI", 12))
            cb.pack(anchor="w", padx=20, pady=2)
            self.checkboxes[p.pid] = cb
            
        self.status_label.configure(text=f"✅ {len(self.processes)} procesos listados.")

    def on_gaming_click(self):
        gaming_profile = self.profile_service.get_gaming_profile()
        to_kill = [p for p in self.processes if self.gaming_service.should_kill_for_gaming(p.name, gaming_profile)]
        
        if not to_kill:
            self.status_label.configure(text="ℹ️ No hay aplicaciones para cerrar.")
            return
            
        killed, failed, skipped = self.process_service.kill_processes(to_kill)
        self.status_label.configure(text=f"✅ Gaming Mode: {killed} cerrados, {failed} fallidos.")
        self.master.after(1500, self.refresh_processes)

    def on_pack_click(self):
        fav = self.profile_service.get_favorite_profile()
        if not fav:
            self.status_label.configure(text="⚠️ No hay un perfil favorito configurado.")
            return
            
        # Lanzar procesos (lógica básica de subprocess migrada)
        import subprocess
        launched = 0
        for app in fav.apps:
            try:
                subprocess.Popen([app], creationflags=0x08000000, shell=True)
                launched += 1
            except Exception:
                pass
        self.status_label.configure(text=f"✅ {launched} apps lanzadas del pack '{fav.label}'.")

    def on_kill_selected(self):
        selected_pids = {pid for pid, cb in self.checkboxes.items() if cb.get()}
        to_kill = [p for p in self.processes if p.pid in selected_pids]
        
        if not to_kill:
            return
            
        killed, failed, skipped = self.process_service.kill_processes(to_kill)
        self.status_label.configure(text=f"✅ Selección: {killed} cerrados, {failed} fallidos.")
        self.master.after(1500, self.refresh_processes)
