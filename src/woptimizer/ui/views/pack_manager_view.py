import customtkinter as ctk
import threading
import uuid
from typing import Dict, List
from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService
from woptimizer.models import Pack

class PackManagerView(ctk.CTkFrame):
    def __init__(self, master, process_service: ProcessService, pack_service: PackService):
        super().__init__(master, fg_color="transparent")
        self.process_service = process_service
        self.pack_service = pack_service
        self._build_ui()
        self.refresh_packs()

    def _build_ui(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 10))
        
        self.title_label = ctk.CTkLabel(self.header, text="📁 Gestor de Packs", font=("Segoe UI", 20, "bold"))
        self.title_label.pack(side="left")
        
        self.btn_new = ctk.CTkButton(self.header, text="➕ Nuevo Pack", command=self.on_new_pack, width=120)
        self.btn_new.pack(side="right")
        
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)

    def refresh_packs(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        packs = self.pack_service.get_all_packs()
        if "gaming" in packs:
            self._render_pack_card(packs["gaming"])
        
        for p_id, p in packs.items():
            if p_id != "gaming":
                self._render_pack_card(p)

    def _render_pack_card(self, pack: Pack):
        card = ctk.CTkFrame(self.scroll_frame, fg_color="#1f1f1f", corner_radius=8)
        card.pack(fill="x", pady=4, padx=4)
        
        # --- FILA SUPERIOR: CABECERA Y ACCIONES ---
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=8, pady=(6, 4))
        
        # Izquierda: Favorito + Título + Badge
        left_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_box.pack(side="left", fill="x", expand=True)
        
        fav_text = "⭐" if pack.is_favorite else "☆"
        btn_fav = ctk.CTkButton(left_box, text=fav_text, width=28, height=26, fg_color="transparent", hover_color="#333333",
                                font=("Segoe UI", 13), command=lambda p=pack.id: self.toggle_favorite(p))
        btn_fav.pack(side="left", padx=(0, 4))
        
        title_text = f"{pack.name} ({len(pack.apps)} apps)"
        title_lbl = ctk.CTkLabel(left_box, text=title_text, font=("Segoe UI", 13, "bold"), anchor="w")
        title_lbl.pack(side="left", padx=2)
        
        if pack.is_gaming:
            badge_gaming = ctk.CTkLabel(left_box, text="PRESET", fg_color="#c22d2d", text_color="#ffffff",
                                       font=("Segoe UI", 9, "bold"), corner_radius=4, width=50, height=18)
            badge_gaming.pack(side="left", padx=6)
        
        # Derecha: Toolbar de botones compactos
        right_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_box.pack(side="right")
        
        # Dropdown de acción por defecto
        def change_default(choice, p_id=pack.id):
            p = self.pack_service.get_all_packs()[p_id]
            p.default_action = choice
            self.pack_service.save()
            
        combo_action = ctk.CTkOptionMenu(right_box, values=["kill", "start"], command=change_default,
                                         width=70, height=26, font=("Segoe UI", 11))
        combo_action.set(pack.default_action)
        combo_action.pack(side="left", padx=3)
        
        btn_kill = ctk.CTkButton(right_box, text="⛔ Apagar", fg_color="#c22d2d", hover_color="#a12525",
                                 width=75, height=26, font=("Segoe UI", 11, "bold"),
                                 command=lambda p=pack: self.kill_pack(p))
        btn_kill.pack(side="left", padx=3)
        
        btn_start = ctk.CTkButton(right_box, text="🚀 Iniciar", width=75, height=26,
                                  font=("Segoe UI", 11, "bold"), command=lambda p=pack: self.start_pack(p))
        btn_start.pack(side="left", padx=3)
        
        if pack.is_gaming:
            btn_restore = ctk.CTkButton(right_box, text="🔄", width=28, height=26,
                                        fg_color="#333333", hover_color="#444444",
                                        command=self.restore_gaming)
            btn_restore.pack(side="left", padx=(3, 0))
        else:
            btn_del = ctk.CTkButton(right_box, text="🗑️", width=28, height=26,
                                    fg_color="#333333", hover_color="#552222",
                                    command=lambda p=pack.id: self.delete_pack(p))
            btn_del.pack(side="left", padx=(3, 0))

        # --- SECCIÓN APPS (COMPACTA) ---
        apps_frame = ctk.CTkFrame(card, fg_color="#151515", corner_radius=6)
        apps_frame.pack(fill="x", padx=8, pady=(2, 6))
        
        if not pack.apps:
            ctk.CTkLabel(apps_frame, text="Sin aplicaciones manuales. Añádelas desde el Gestor de Procesos.",
                         text_color="#888888", font=("Segoe UI", 10)).pack(anchor="w", padx=8, pady=3)
        else:
            for app in pack.apps:
                app_row = ctk.CTkFrame(apps_frame, fg_color="transparent")
                app_row.pack(fill="x", padx=8, pady=1)
                ctk.CTkLabel(app_row, text=f"• {app}", font=("Segoe UI", 11)).pack(side="left")
                btn_remove = ctk.CTkButton(app_row, text="❌", width=20, height=18, fg_color="transparent",
                                           text_color="#c22d2d", hover_color="#2b1515",
                                           command=lambda p=pack.id, a=app: self.remove_app_from_pack(p, a))
                btn_remove.pack(side="right")
                
        # --- SECCIÓN ACORDEÓN CATEGORÍAS (SÓLO GAMING) ---
        if pack.is_gaming:
            active_count = len(pack.target_categories)
            acc_state = {"open": False}
            
            cat_body = ctk.CTkFrame(card, fg_color="#151515", corner_radius=6)
            
            def toggle_acc():
                acc_state["open"] = not acc_state["open"]
                if acc_state["open"]:
                    acc_btn.configure(text=f"⚙️ Configurar Categorías Automáticas ({len(pack.target_categories)} activas) ▲")
                    cat_body.pack(fill="x", padx=8, pady=(0, 6))
                else:
                    acc_btn.configure(text=f"⚙️ Configurar Categorías Automáticas ({len(pack.target_categories)} activas) ▼")
                    cat_body.pack_forget()

            acc_btn = ctk.CTkButton(
                card,
                text=f"⚙️ Configurar Categorías Automáticas ({active_count} activas) ▼",
                font=("Segoe UI", 11),
                fg_color="#262626",
                hover_color="#303030",
                height=24,
                anchor="w",
                command=toggle_acc
            )
            acc_btn.pack(fill="x", padx=8, pady=(0, 4))
            
            # Poblar cuerpo del acordeón
            all_cats = set()
            for row in getattr(self.process_service, 'process_db', []):
                if "? Otros" not in row.category:
                    all_cats.add(row.category)
            if not all_cats:
                all_cats = {"🟢 Sincronización", "🟢 Navegadores", "🟢 Productividad",
                            "🟡 Chat y Comunicación", "🟡 Launchers Gaming", "🟡 Media y Streaming",
                            "🔴 Sistema de Windows", "🔴 Antivirus y Seguridad", "🔴 Overlays e Info"}
                
            grid = ctk.CTkFrame(cat_body, fg_color="transparent")
            grid.pack(fill="x", padx=6, pady=4)
            grid.grid_columnconfigure((0, 1), weight=1)
            
            def create_command(c, v):
                def toggle():
                    if v.get() == 1:
                        if c not in pack.target_categories:
                            pack.target_categories.append(c)
                    else:
                        if c in pack.target_categories:
                            pack.target_categories.remove(c)
                    self.pack_service.save()
                    acc_btn.configure(text=f"⚙️ Configurar Categorías Automáticas ({len(pack.target_categories)} activas) ▲")
                return toggle
                
            sorted_cats = sorted(list(all_cats))
            for i, cat in enumerate(sorted_cats):
                var = ctk.IntVar(value=1 if cat in pack.target_categories else 0)
                cb = ctk.CTkCheckBox(grid, text=cat, variable=var, font=("Segoe UI", 11), command=create_command(cat, var))
                cb.grid(row=i // 2, column=i % 2, padx=6, pady=3, sticky="w")

    def toggle_favorite(self, pack_id: str):
        self.pack_service.set_favorite(pack_id)
        self.refresh_packs()
        
    def restore_gaming(self):
        self.pack_service.reset_gaming_pack()
        self.refresh_packs()
        
    def delete_pack(self, pack_id: str):
        try:
            self.pack_service.delete_pack(pack_id)
            self.refresh_packs()
        except ValueError:
            pass

    def on_new_pack(self):
        dialog = ctk.CTkInputDialog(text="Introduce el nombre del nuevo Pack:", title="Nuevo Pack")
        name = dialog.get_input()
        if name and name.strip():
            pack_id = str(uuid.uuid4())[:8]
            self.pack_service.create_user_pack(pack_id, name.strip(), [])
            self.refresh_packs()

    def remove_app_from_pack(self, pack_id: str, app_name: str):
        pack = self.pack_service.get_all_packs().get(pack_id)
        if pack and app_name in pack.apps:
            pack.apps.remove(app_name)
            self.pack_service.save()
            self.refresh_packs()

    def kill_pack(self, pack: Pack):
        if not pack.apps: return
        threading.Thread(target=self.process_service.kill_pack_apps, args=(pack.apps,), daemon=True).start()

    def start_pack(self, pack: Pack):
        if not pack.apps: return
        threading.Thread(target=self.process_service.start_pack_apps, args=(pack.apps,), daemon=True).start()
