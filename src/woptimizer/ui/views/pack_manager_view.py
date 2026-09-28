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
        card = ctk.CTkFrame(self.scroll_frame)
        card.pack(fill="x", pady=5, padx=5)
        
        # Titulo y favoritos
        fav_text = "⭐" if pack.is_favorite else "☆"
        btn_fav = ctk.CTkButton(card, text=fav_text, width=30, command=lambda p=pack.id: self.toggle_favorite(p))
        btn_fav.pack(side="left", padx=5, pady=10)
        
        title_text = f"{pack.name} ({len(pack.apps)} apps)"
        title_lbl = ctk.CTkLabel(card, text=title_text, font=("Segoe UI", 14, "bold"))
        title_lbl.pack(side="left", padx=5)
        
        # Botones de Accion
        btn_kill = ctk.CTkButton(card, text="⛔ Apagar Apps", fg_color="#c22d2d", hover_color="#a12525", width=100,
                                 command=lambda p=pack: self.kill_pack(p))
        btn_kill.pack(side="right", padx=5, pady=10)
        
        btn_start = ctk.CTkButton(card, text="🚀 Arrancar Apps", width=100,
                                  command=lambda p=pack: self.start_pack(p))
        btn_start.pack(side="right", padx=5, pady=10)
        
        # Default action
        def change_default(choice, p_id=pack.id):
            p = self.pack_service.get_all_packs()[p_id]
            p.default_action = choice
            self.pack_service.save()
            
        combo_action = ctk.CTkOptionMenu(card, values=["start", "kill"], command=change_default, width=80)
        combo_action.set(pack.default_action)
        combo_action.pack(side="right", padx=5, pady=10)
        ctk.CTkLabel(card, text="Default:").pack(side="right", padx=5)
        
        if pack.is_gaming:
            btn_restore = ctk.CTkButton(card, text="🔄 Restaurar", width=80, command=self.restore_gaming)
            btn_restore.pack(side="right", padx=5, pady=10)
        else:
            btn_del = ctk.CTkButton(card, text="🗑️ Borrar", width=80, fg_color="gray", command=lambda p=pack.id: self.delete_pack(p))
            btn_del.pack(side="right", padx=5, pady=10)

        # Edit apps list below header
        apps_frame = ctk.CTkFrame(card, fg_color="transparent")
        apps_frame.pack(fill="x", padx=10, pady=5)
        
        if not pack.apps:
            ctk.CTkLabel(apps_frame, text="Sin aplicaciones. Añade desde el Gestor de Procesos.", text_color="gray").pack(anchor="w")
        else:
            for app in pack.apps:
                app_row = ctk.CTkFrame(apps_frame, fg_color="transparent")
                app_row.pack(fill="x", pady=2)
                ctk.CTkLabel(app_row, text=app).pack(side="left")
                btn_remove = ctk.CTkButton(app_row, text="❌", width=30, height=20, fg_color="transparent", text_color="#c22d2d", 
                                           command=lambda p=pack.id, a=app: self.remove_app_from_pack(p, a))
                btn_remove.pack(side="right")

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
