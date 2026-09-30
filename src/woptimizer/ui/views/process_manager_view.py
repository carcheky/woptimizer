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
from woptimizer.ui.feedback import mensaje_cierre_pack
from woptimizer.ui import theme


def _agrupar(procs: List[ProcessInfo]) -> Dict[str, List[ProcessInfo]]:
    """Agrupa por nombre en minusculas. PURA y a nivel de modulo a proposito.

    Vive fuera de la clase para que el worker de carga (`_do_load`, hilo
    secundario) no tenga que llamar a `self._group`: el invariante de
    `test_los_workers_de_pack_solo_publican_por_after` es que un worker solo
    publica por `self.after(0, ...)` y no toca la vista de ninguna otra forma.
    `ProcessManagerView._group` se conserva como fachada porque es parte del
    contrato usado por `test_do_load_publica_sin_tk`.
    """
    grouped: Dict[str, List[ProcessInfo]] = {}
    for p in procs:
        grouped.setdefault(p.name.lower(), []).append(p)
    return grouped

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
        
        self.title_label = ctk.CTkLabel(
            self.header,
            text="⚡ Gestor de Procesos",
            font=("Segoe UI", theme.FONT_SIZE_HEADER, "bold"),
            text_color=theme.TEXT_PRIMARY
        )
        self.title_label.pack(side="left")
        
        self.btn_refresh = ctk.CTkButton(
            self.header,
            text="🔄 Actualizar Lista",
            command=self.refresh_processes,
            width=120,
            height=28,
            font=("Segoe UI", theme.FONT_SIZE_BODY),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT_PRIMARY
        )
        self.btn_refresh.pack(side="right")
        
        # Search bar
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_list())
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="🔍 Buscar proceso por nombre...",
            textvariable=self.search_var,
            height=32,
            font=("Segoe UI", theme.FONT_SIZE_BODY),
            fg_color=theme.SURFACE_SUNKEN,
            border_color=theme.BORDER,
            text_color=theme.TEXT_PRIMARY
        )
        self.search_entry.pack(fill="x", pady=(0, 10))
        
        # Scrollable list
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=theme.SURFACE)
        self.scroll_frame.pack(fill="both", expand=True)
        
        # Footer Action Bar (UI-007: min 28x28)
        self.footer = ctk.CTkFrame(
            self,
            height=54,
            fg_color=theme.SURFACE_ALT,
            corner_radius=theme.RADIUS_LARGE,
            border_width=1,
            border_color=theme.BORDER
        )
        self.footer.pack(fill="x", pady=(10, 0))
        
        # Desplegable Packs
        self.pack_var = ctk.StringVar(value="Seleccionar Pack ▼")
        self.pack_dropdown = ctk.CTkOptionMenu(
            self.footer,
            variable=self.pack_var,
            values=["Seleccionar Pack ▼"],
            height=28,
            font=("Segoe UI", theme.FONT_SIZE_SMALL)
        )
        self.pack_dropdown.pack(side="left", padx=10, pady=12)
        
        self.btn_add_pack = ctk.CTkButton(
            self.footer,
            text="➕ Añadir al Pack",
            command=self.on_add_to_pack,
            height=28,
            font=("Segoe UI", theme.FONT_SIZE_SMALL, "bold"),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT_PRIMARY
        )
        self.btn_add_pack.pack(side="left", padx=10, pady=12)
        
        self.btn_kill = ctk.CTkButton(
            self.footer,
            text="⛔ Cerrar Seleccionados",
            command=self.on_kill_selected,
            height=28,
            font=("Segoe UI", theme.FONT_SIZE_SMALL, "bold"),
            fg_color=theme.DANGER,
            hover_color=theme.DANGER_HOVER,
            text_color=theme.TEXT_PRIMARY
        )
        self.btn_kill.pack(side="right", padx=10, pady=12)
        
        self.status_label = ctk.CTkLabel(
            self.footer,
            text="",
            text_color=theme.TEXT_MUTED,
            font=("Segoe UI", theme.FONT_SIZE_SMALL)
        )
        self.status_label.pack(side="right", padx=20)

        # TASK-023: doble pulsacion para cerrar procesos
        self._init_confirmable(self.status_label)

    def destroy(self):
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
        def _load():
            procs = self.process_service.get_running_processes()
            self.after(0, self._apply_load, procs)

        threading.Thread(target=_load, daemon=True).start()

    def _apply_load(self, procs: List[ProcessInfo]):
        """Callback de `_load`. Corre en el HILO PRINCIPAL: aqui si se toca la vista."""
        self.processes = procs
        self.grouped_processes = _agrupar(procs)
        self._render_list()
        self._update_pack_dropdown()

    @staticmethod
    def _group(procs: List[ProcessInfo]) -> Dict[str, List[ProcessInfo]]:
        """Fachada de `_agrupar`. Ver la nota de por que la logica vive fuera."""
        return _agrupar(procs)

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
        self._cancel_confirm()
        previously_selected = {k for k, cb in self.checkboxes.items() if cb.get()}
        
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.checkboxes.clear()
        
        grouped = self.grouped_processes
        
        categories = {}
        for name_key, procs in grouped.items():
            if search_query and search_query not in name_key:
                continue
                
            cat = procs[0].category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((name_key, procs))
            
        for cat in ordenar_categorias(categories.keys()):
            items = sorted(categories[cat], key=lambda x: x[0])
            is_expanded = True
            self._create_category_section(cat, items, is_expanded, previously_selected)
                
        # UI-011: Estado vacio neutro y sin check verde
        if not grouped:
            self.status_label.configure(text="Sin procesos activos detectados.")
        else:
            self.status_label.configure(text=f"{len(grouped)} apps distintas en ejecución.")

    def _create_category_section(self, cat: str, items: list, is_expanded: bool, previously_selected: set):
        cat_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        cat_container.pack(fill="x", pady=(6, 0))
        
        content_frame = ctk.CTkFrame(cat_container, fg_color="transparent")
        
        actual_expanded = self.expanded_categories.get(cat, is_expanded)
        state = {"expanded": actual_expanded}
        
        cat_badge = get_safety_badge(cat)
        header_color = cat_badge["text_color"]
        count_str = f" ({len(items)})"
        
        def toggle():
            state["expanded"] = not state["expanded"]
            self.expanded_categories[cat] = state["expanded"]
            if state["expanded"]:
                btn.configure(text=f"▼ {cat}{count_str}")
                content_frame.pack(fill="x")
            else:
                btn.configure(text=f"▶ {cat}{count_str}")
                content_frame.pack_forget()

        # UI-008: Cabecera de categoria con fondo SURFACE_ALT, hover y contador
        btn = ctk.CTkButton(
            cat_container, 
            text=f"▼ {cat}{count_str}" if actual_expanded else f"▶ {cat}{count_str}", 
            font=("Segoe UI", theme.FONT_SIZE_SUBHEADER, "bold"), 
            text_color=header_color,
            fg_color=theme.SURFACE_ALT,
            hover_color=theme.SURFACE_HOVER,
            corner_radius=theme.RADIUS_MEDIUM,
            height=32,
            anchor="w",
            command=toggle
        )
        btn.pack(fill="x", pady=(0, 2))
        
        if actual_expanded:
            content_frame.pack(fill="x")
            
        for name_key, procs in items:
            count = len(procs)
            exe_name = procs[0].full_name if procs[0].full_name else name_key
            desc = getattr(procs[0], 'description', 'Sin descripción')
            prio = getattr(procs[0], 'priority', 'none')
            badge_info = get_safety_badge(cat, prio)
            
            row_frame = ctk.CTkFrame(content_frame, fg_color=theme.SURFACE_SUNKEN, corner_radius=theme.RADIUS_MEDIUM)
            row_frame.pack(fill="x", padx=6, pady=2)
            
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
                corner_radius=theme.RADIUS_SMALL,
                font=("Segoe UI", theme.FONT_SIZE_SMALL, "bold"),
                width=110,
                height=22
            )
            badge_lbl.pack(side="left", padx=5)
            
            name_text = f"{exe_name} ({count})"
            name_lbl = ctk.CTkLabel(
                row_frame,
                text=name_text,
                font=("Segoe UI", theme.FONT_SIZE_BODY, "bold"),
                text_color=theme.TEXT_PRIMARY
            )
            name_lbl.pack(side="left", padx=5)
            
            # UI-012: wraplength=380 para evitar desborde en el ancho minimo de 720px
            desc_text = f"• {desc}" if desc and desc != "Sin descripción" else f"• {badge_info['recommendation']}"
            desc_lbl = ctk.CTkLabel(
                row_frame,
                text=desc_text,
                font=("Segoe UI", theme.FONT_SIZE_SMALL),
                text_color=theme.TEXT_MUTED if desc and desc != "Sin descripción" else badge_info["text_color"],
                wraplength=380,
                anchor="w"
            )
            desc_lbl.pack(side="left", padx=5)
            
            def make_toggle(c_box):
                return lambda event: c_box.toggle()
            row_frame.bind("<Button-1>", make_toggle(cb))
            name_lbl.bind("<Button-1>", make_toggle(cb))
            desc_lbl.bind("<Button-1>", make_toggle(cb))

    def on_kill_selected(self):
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
            self.after(0, self._publicar_cierre, killed, failed, skipped, freed_mb,
                       len(to_kill))
            self.notification_service.notify_kill_result(killed, failed, freed_mb)

        threading.Thread(target=_kill, daemon=True).start()

    def _publicar_cierre(self, killed: int, failed: int, skipped: int,
                         freed_mb: float, cuantos: int):
        """Callback de `_kill`. Corre en el HILO PRINCIPAL.

        TASK-035 / ciclo 26 iteracion 3: esta es la TERCERA puerta de feedback y
        hasta aqui llegaba con su PROPIA verdad: pintaba
        `"<tick> {killed} cerrados, {failed} fallidos."` con tick y sin mirar
        `killed`, así que cerrar cero procesos (todo en `keepers` o ya muerto)
        se pintaba como exito en verde. Es el bug que motivó el ciclo, en la vista
        que mata lo que el usuario marcó a mano. Ahora el texto sale del MISMO
        formateador que las otras dos puertas (`mensaje_cierre_pack`), y con
        `killed == 0` no hay tick ni verde.
        """
        texto, color = mensaje_cierre_pack(
            f"{cuantos} seleccionadas", killed, failed, skipped, freed_mb,
            sustantivo="procesos",
        )
        self.status_label.configure(text=texto, text_color=color)
        self._schedule_ui(1000, self.refresh_processes)

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
            exe_path = procs[0].exe_path
            if not exe_path and procs[0].pid > 0 and getattr(self, "process_service", None):
                exe_path = self.process_service.get_process_exe_path(procs[0].pid)
            exe_name = exe_path or procs[0].full_name or procs[0].name
            if exe_name not in target_pack.apps:
                target_pack.apps.append(exe_name)
                added += 1
                
        self.pack_service.save()
        self.status_label.configure(text=f"✅ {added} apps añadidas a {target_pack.name}.")
