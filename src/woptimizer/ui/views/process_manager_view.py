import customtkinter as ctk
import threading
from typing import Dict, List
from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService
from woptimizer.services.notification_service import NotificationService
from woptimizer.models import ProcessInfo
from woptimizer.config import get_safety_badge, ordenar_categorias
from woptimizer.ui.confirmation import (
    AMBAR,
    MSG_SELECCION_CAMBIADA,
    MSG_SIN_PROCESOS,
    MSG_SIN_SELECCION,
    Confirmable,
)

class ProcessManagerView(Confirmable, ctk.CTkFrame):
    def __init__(self, master, process_service: ProcessService, pack_service: PackService, notification_service: NotificationService = None):
        super().__init__(master, fg_color="transparent")
        self.process_service = process_service
        self.pack_service = pack_service
        self.notification_service = notification_service or NotificationService()
        
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

        # TASK-023: doble pulsacion para cerrar procesos
        self._init_confirmable(self.status_label)

    def destroy(self):
        # El `after` de la pendiente vive en la vista: si no se mata aqui, el callback
        # sobrevive al cambio de pestaña y reconfigura widgets ya destruidos.
        self.cancel_on_destroy()
        super().destroy()

    def refresh_processes(self):
        self._cancel_confirm()
        self.status_label.configure(text="⏳ Cargando...")
        self.update_idletasks()
        
        if not getattr(self.process_service, 'is_db_loaded', False):
            self.process_service.load_db_async(callback=lambda: self.after(0, self._do_load))
        else:
            self._do_load()

    def _force_update_db(self):
        self.status_label.configure(text="⏳ Descargando DB JSON desde GitLab...")
        self.update_idletasks()
        self.process_service.load_db_async(callback=lambda: self.after(0, self._do_load))

    def _do_load(self):
        """TASK-026 (FIX-007): el hilo secundario SOLO calcula; publica con self.after(0, ...).

        Antes este hilo asignaba `self.processes` y hacia `.clear()` / `[k] = []`
        sobre `self.grouped_processes`, dos dicts que el hilo principal recorre en
        `_render_list` (tambien en cada pulsacion del buscador, por el trace de
        `search_var`). Eso producia `RuntimeError: dictionary changed size during
        iteration` y, con dos cargas solapadas, dejaba `processes` y
        `grouped_processes` describiendo snapshots distintos: el set de PIDs que
        mata `on_kill_selected` podia venir de un snapshot obsoleto.

        El agrupado se REBIND (no se muta in situ) y se entrega entero desde el
        hilo principal. OJO: `self.after` y NUNCA `self.master.after` (TASK-023),
        porque `main_window._clear_content` destruye la vista en toda navegacion y
        un `after` colgado en el master sobrevive y reconfigura widgets muertos.
        """
        def _load():
            procs = self.process_service.get_running_processes()
            grouped = self._group(procs)

            def _apply():
                self.processes = procs
                self.grouped_processes = grouped
                self._render_list()
                self._update_pack_dropdown()

            self.after(0, _apply)

        threading.Thread(target=_load, daemon=True).start()

    @staticmethod
    def _group(procs: List[ProcessInfo]) -> Dict[str, List[ProcessInfo]]:
        """Agrupa por nombre normalizado. Funcion PURA: devuelve un dict nuevo.

        No lee ni escribe estado de la vista, asi que se puede probar sin Tk y,
        sobre todo, el hilo secundario nunca toca el dict que el principal itera.
        """
        grouped: Dict[str, List[ProcessInfo]] = {}
        for p in procs:
            grouped.setdefault(p.name.lower(), []).append(p)
        return grouped

    def _update_pack_dropdown(self):
        packs = self.pack_service.get_all_packs()
        values = [p.name for p in packs.values()]
        if not values:
            values = ["Sin packs disponibles"]
        self.pack_dropdown.configure(values=values)
        if self.pack_var.get() not in values and self.pack_var.get() != "Seleccionar Pack ▼":
             self.pack_var.set(values[0] if values else "Seleccionar Pack ▼")

    def _filter_list(self):
        self._render_list(search_query=self.search_var.get().lower())

    def _render_list(self, search_query=""):
        # La lista se recrea entera: una pendiente sobre las casillas viejas no tiene
        # a que reconfigurarse, asi que se invalida (TASK-023).
        self._cancel_confirm()
        # Guardar estado de selección
        previously_selected = {k for k, cb in self.checkboxes.items() if cb.get()}
        
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.checkboxes.clear()
        
        # TASK-026 (FIX-007): snapshot local. `_apply` REBINDA el dict en vez de
        # mutarlo, pero tomar una referencia local deja claro que este render
        # trabaja sobre un solo snapshot coherente de principio a fin.
        grouped = self.grouped_processes
        
        # Categorizar los grupos
        categories = {}
        for name_key, procs in grouped.items():
            if search_query and search_query not in name_key:
                continue
                
            cat = procs[0].category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((name_key, procs))
            
        # TASK-027 (FIX-004): el orden lo manda `CATEGORY_ORDER` (config.ordenar_categorias),
        # NO `sorted()`. `sorted()` ordena por punto de codigo y el centinela
        # canonico ⚪ Otros (U+26AA, BMP) sale PRIMERO mientras que 🟢🟡🔴 viven en el
        # plano suplementario: medido, el bloque rojo "NO CERRAR" subia al primer
        # golpe de vista. Ojo: el orden NO es "por color" -- `CATEGORY_ORDER`
        # entrelaza verde y amarillo a proposito.
        for cat in ordenar_categorias(categories.keys()):
            items = sorted(categories[cat], key=lambda x: x[0])
            is_expanded = True if search_query else True
            self._create_category_section(cat, items, is_expanded, previously_selected)
                
        self.status_label.configure(text=f"✅ {len(grouped)} apps distintas.")

    def _create_category_section(self, cat: str, items: list, is_expanded: bool, previously_selected: set):
        cat_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        cat_container.pack(fill="x", pady=(5, 0))
        
        content_frame = ctk.CTkFrame(cat_container, fg_color="transparent")
        
        # Recuperar estado de plegado de esta categoría, o usar el default
        actual_expanded = self.expanded_categories.get(cat, is_expanded)
        state = {"expanded": actual_expanded}
        
        cat_badge = get_safety_badge(cat)
        header_color = cat_badge["text_color"]
        
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
            text_color=header_color,
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
            desc = getattr(procs[0], 'description', 'Sin descripción')
            prio = getattr(procs[0], 'priority', 'none')
            badge_info = get_safety_badge(cat, prio)
            
            row_frame = ctk.CTkFrame(content_frame, fg_color="#181818", corner_radius=6)
            row_frame.pack(fill="x", padx=10, pady=2)
            
            cb = ctk.CTkCheckBox(row_frame, text="", width=24)
            cb.pack(side="left", padx=(10, 5), pady=6)
            if name_key in previously_selected:
                cb.select()
            self.checkboxes[name_key] = cb
            
            badge_lbl = ctk.CTkLabel(
                row_frame,
                text=badge_info["text"],
                fg_color=badge_info["fg_color"],
                text_color=badge_info["text_color"],
                corner_radius=4,
                font=("Segoe UI", 11, "bold"),
                width=110,
                height=22
            )
            badge_lbl.pack(side="left", padx=5)
            
            name_text = f"{exe_name} ({count})"
            name_lbl = ctk.CTkLabel(
                row_frame,
                text=name_text,
                font=("Segoe UI", 12, "bold"),
                text_color="#ffffff"
            )
            name_lbl.pack(side="left", padx=5)
            
            desc_text = f"• {desc}" if desc and desc != "Sin descripción" else f"• {badge_info['recommendation']}"
            desc_lbl = ctk.CTkLabel(
                row_frame,
                text=desc_text,
                font=("Segoe UI", 11),
                text_color="#a0a0a0" if desc and desc != "Sin descripción" else badge_info["text_color"]
            )
            desc_lbl.pack(side="left", padx=5)
            
            def make_toggle(c_box):
                return lambda event: c_box.toggle()
            row_frame.bind("<Button-1>", make_toggle(cb))
            name_lbl.bind("<Button-1>", make_toggle(cb))
            desc_lbl.bind("<Button-1>", make_toggle(cb))

    def on_kill_selected(self):
        # TASK-023: se congela la INTENCION (claves marcadas) y se RECALCULAN los datos
        # en la segunda pulsacion. Congelar los ProcessInfo seria un fallo de seguridad:
        # entre pulsaciones el PID puede reciclarse y matarias a un proceso inocente.
        selected_keys = tuple(sorted(k for k, cb in self.checkboxes.items() if cb.get()))
        if not selected_keys:
            self._cancel_confirm()
            self._inline_status(MSG_SIN_SELECCION, AMBAR)
            return

        if not self._require_double_tap(
            selected_keys,
            self.btn_kill,
            f"⚠️ Segunda pulsación para cerrar {len(selected_keys)} apps seleccionadas.",
            changed_text=MSG_SELECCION_CAMBIADA,
        ):
            return

        to_kill = []
        for k in selected_keys:
            to_kill.extend(self.grouped_processes.get(k, []))

        if not to_kill:
            self._inline_status(MSG_SIN_PROCESOS, AMBAR)
            return

        self.status_label.configure(text="⏳ Cerrando...")
        self.update_idletasks()

        def _kill():
            killed, failed, skipped, freed_mb = self.process_service.kill_processes(to_kill)
            def _done():
                if freed_mb > 0:
                    self.status_label.configure(text=f"✅ {killed} cerrados ({freed_mb:.1f} MB liberados), {failed} fallidos.")
                else:
                    self.status_label.configure(text=f"✅ {killed} cerrados, {failed} fallidos.")
                self.after(1000, self.refresh_processes)
            self.after(0, _done)
            # TASK-019: toast nativo con el resumen del cierre manual
            self.notification_service.notify_kill_result(killed, failed, freed_mb)
            
        threading.Thread(target=_kill, daemon=True).start()

    def on_add_to_pack(self):
        selected_keys = [k for k, cb in self.checkboxes.items() if cb.get()]
        pack_name = self.pack_var.get()
        
        if not selected_keys:
            self.status_label.configure(text="⚠️ Selecciona procesos primero.")
            return
            
        packs = self.pack_service.get_all_packs()
        target_pack = next((p for p in packs.values() if p.name == pack_name), None)
        
        if not target_pack:
            self.status_label.configure(text="⚠️ Selecciona un pack válido.")
            return
            
        added = 0
        for k in selected_keys:
            procs = self.grouped_processes[k]
            # TASK-027 (FIX-003): se guarda la RUTA ABSOLUTA, no el nombre. Con el
            # nombre desnudo, `ProcessService._resolver_app` tendria que adivinarlo
            # en las raices permitidas y el arranque se rechaza con un log que el
            # usuario no puede ver en pantalla. La ruta ya esta disponible:
            # `ProcessInfo.exe_path` se rellena en `get_running_processes()`
            # (`info['exe'] or ""`).
            # DEGRADACION DOCUMENTADA: con `AccessDenied`, `psutil` deja `exe`
            # vacio; entonces se guarda `full_name` y el pack queda con un nombre
            # pelado que el arranque rechazara con su `logger.warning`. Sin esta
            # rama, un proceso sin `exe` deja el pack inservible sin explicacion.
            exe_name = procs[0].exe_path or procs[0].full_name or procs[0].name
            if exe_name not in target_pack.apps:
                target_pack.apps.append(exe_name)
                added += 1
                
        self.pack_service.save()
        self.status_label.configure(text=f"✅ {added} apps añadidas a {target_pack.name}.")
