import customtkinter as ctk
import threading
from typing import Dict, List
from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService
from woptimizer.models import ProcessInfo

class ProcessManagerView(ctk.CTkFrame):
    def __init__(self, master, process_service: ProcessService, pack_service: PackService):
        super().__init__(master, fg_color="transparent")
        self.process_service = process_service
        self.pack_service = pack_service
        
        self.processes: List[ProcessInfo] = []
        self.grouped_processes: Dict[str, List[ProcessInfo]] = {}
        self.checkboxes: Dict[str, ctk.CTkCheckBox] = {}
        self.expanded_categories: Dict[str, bool] = {}
        
        self._build_ui()
        self.refresh_processes()

    def _build_ui(self):
        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 10))
        
        self.title_label = ctk.CTkLabel(self.header, text="⚡ Gestor de Procesos", font=("Segoe UI", 20, "bold"))
        self.title_label.pack(side="left")
        
        self.btn_refresh = ctk.CTkButton(self.header, text="🔄 Actualizar Lista", command=self.refresh_processes, width=120)
        self.btn_refresh.pack(side="right")
        
        # Search bar
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_list())
        self.search_entry = ctk.CTkEntry(self, placeholder_text="🔍 Buscar proceso por nombre...", textvariable=self.search_var)
        self.search_entry.pack(fill="x", pady=(0, 10))
        
        # Scrollable list
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)
        
        # Footer Action Bar
        self.footer = ctk.CTkFrame(self, height=60)
        self.footer.pack(fill="x", pady=(10, 0))
        
        # Desplegable Packs
        self.pack_var = ctk.StringVar(value="Seleccionar Pack ▼")
        self.pack_dropdown = ctk.CTkOptionMenu(self.footer, variable=self.pack_var, values=["Seleccionar Pack ▼"])
        self.pack_dropdown.pack(side="left", padx=10, pady=15)
        
        self.btn_add_pack = ctk.CTkButton(self.footer, text="➕ Añadir al Pack", command=self.on_add_to_pack)
        self.btn_add_pack.pack(side="left", padx=10, pady=15)
        
        self.btn_kill = ctk.CTkButton(self.footer, text="⛔ Cerrar Seleccionados", command=self.on_kill_selected, fg_color="#c22d2d", hover_color="#a12525")
        self.btn_kill.pack(side="right", padx=10, pady=15)
        
        self.status_label = ctk.CTkLabel(self.footer, text="", text_color="gray")
        self.status_label.pack(side="right", padx=20)

    def refresh_processes(self):
        self.status_label.configure(text="⏳ Cargando...")
        self.update_idletasks()
        
        def _load():
            self.processes = self.process_service.get_running_processes()
            self._group_processes()
            self.master.after(0, self._render_list)
            self.master.after(0, self._update_pack_dropdown)
            
        threading.Thread(target=_load, daemon=True).start()

    def _group_processes(self):
        self.grouped_processes.clear()
        for p in self.processes:
            key = p.name.lower()
            if key not in self.grouped_processes:
                self.grouped_processes[key] = []
            self.grouped_processes[key].append(p)

    def _update_pack_dropdown(self):
        packs = self.pack_service.get_user_packs()
        values = [p.name for p in packs.values()]
        if not values:
            values = ["Sin packs disponibles"]
        self.pack_dropdown.configure(values=values)
        if self.pack_var.get() not in values and self.pack_var.get() != "Seleccionar Pack ▼":
             self.pack_var.set(values[0] if values else "Seleccionar Pack ▼")

    def _filter_list(self):
        self._render_list(search_query=self.search_var.get().lower())

    def _render_list(self, search_query=""):
        # Guardar estado de selección
        previously_selected = {k for k, cb in self.checkboxes.items() if cb.get()}
        
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.checkboxes.clear()
        
        # Categorizar los grupos
        categories = {}
        for name_key, procs in self.grouped_processes.items():
            if search_query and search_query not in name_key:
                continue
                
            cat = procs[0].category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((name_key, procs))
            
        for cat in sorted(categories.keys()):
            items = sorted(categories[cat], key=lambda x: x[0])
            is_expanded = True if search_query else True
            self._create_category_section(cat, items, is_expanded, previously_selected)
                
        self.status_label.configure(text=f"✅ {len(self.grouped_processes)} apps distintas.")

    def _create_category_section(self, cat: str, items: list, is_expanded: bool, previously_selected: set):
        cat_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        cat_container.pack(fill="x", pady=(5, 0))
        
        content_frame = ctk.CTkFrame(cat_container, fg_color="transparent")
        
        # Recuperar estado de plegado de esta categoría, o usar el default
        actual_expanded = self.expanded_categories.get(cat, is_expanded)
        state = {"expanded": actual_expanded}
        
        def toggle():
            state["expanded"] = not state["expanded"]
            self.expanded_categories[cat] = state["expanded"]
            if state["expanded"]:
                btn.configure(text=f"▼ {cat}")
                content_frame.pack(fill="x")
            else:
                btn.configure(text=f"▶ {cat}")
                content_frame.pack_forget()

        btn = ctk.CTkButton(
            cat_container, 
            text=f"▼ {cat}" if actual_expanded else f"▶ {cat}", 
            font=("Segoe UI", 14, "bold"), 
            text_color="#3a7ebf",
            fg_color="transparent", 
            hover_color="#2b2b2b",
            anchor="w",
            command=toggle
        )
        btn.pack(fill="x")
        
        if actual_expanded:
            content_frame.pack(fill="x")
            
        for name_key, procs in items:
            count = len(procs)
            exe_name = procs[0].full_name if procs[0].full_name else name_key
            label_text = f"{exe_name} ({count} proceso{'s' if count > 1 else ''})"
            
            cb = ctk.CTkCheckBox(content_frame, text=label_text, font=("Segoe UI", 12))
            cb.pack(anchor="w", padx=20, pady=2)
            
            if name_key in previously_selected:
                cb.select()
                
            self.checkboxes[name_key] = cb

    def on_kill_selected(self):
        selected_keys = [k for k, cb in self.checkboxes.items() if cb.get()]
        if not selected_keys:
            return
            
        to_kill = []
        for k in selected_keys:
            to_kill.extend(self.grouped_processes[k])
            
        if not to_kill:
            return
            
        self.status_label.configure(text="⏳ Cerrando...")
        self.update_idletasks()
        
        def _kill():
            killed, failed, skipped = self.process_service.kill_processes(to_kill)
            def _done():
                self.status_label.configure(text=f"✅ {killed} cerrados, {failed} fallidos.")
                self.master.after(1000, self.refresh_processes)
            self.master.after(0, _done)
            
        threading.Thread(target=_kill, daemon=True).start()

    def on_add_to_pack(self):
        selected_keys = [k for k, cb in self.checkboxes.items() if cb.get()]
        pack_name = self.pack_var.get()
        
        if not selected_keys:
            self.status_label.configure(text="⚠️ Selecciona procesos primero.")
            return
            
        packs = self.pack_service.get_user_packs()
        target_pack = next((p for p in packs.values() if p.name == pack_name), None)
        
        if not target_pack:
            self.status_label.configure(text="⚠️ Selecciona un pack válido.")
            return
            
        added = 0
        for k in selected_keys:
            procs = self.grouped_processes[k]
            exe_name = procs[0].full_name if procs[0].full_name else procs[0].name
            if exe_name not in target_pack.apps:
                target_pack.apps.append(exe_name)
                added += 1
                
        self.pack_service.save()
        self.status_label.configure(text=f"✅ {added} apps añadidas a {target_pack.name}.")
