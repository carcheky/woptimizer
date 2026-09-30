import customtkinter as ctk
import threading
import uuid
from typing import Dict, List
from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService
from woptimizer.services.gaming_service import GamingService
from woptimizer.services.notification_service import NotificationService
from woptimizer.models import Pack
from woptimizer.config import ordenar_categorias
from woptimizer.ui.confirmation import AMBAR, ROJO, VERDE, MSG_PACK_INEXISTENTE, Confirmable
from woptimizer.ui import theme


class NewPackModal(ctk.CTkToplevel):
    """Dialogo acoplado y themed para creacion de packs (UI-009, reemplaza CTkInputDialog)."""
    def __init__(self, master, on_confirm):
        super().__init__(master)
        self.title("Nuevo Pack")
        self.geometry("380x160")
        self.resizable(False, False)
        self.configure(fg_color=theme.SURFACE_ALT)
        self.transient(master)
        self.grab_set()

        try:
            x = master.winfo_rootx() + (master.winfo_width() // 2) - 190
            y = master.winfo_rooty() + (master.winfo_height() // 2) - 80
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        lbl = ctk.CTkLabel(
            self,
            text="Introduce el nombre del nuevo Pack:",
            font=("Segoe UI", theme.FONT_SIZE_BODY),
            text_color=theme.TEXT_PRIMARY
        )
        lbl.pack(padx=20, pady=(16, 8), anchor="w")

        self.entry = ctk.CTkEntry(
            self,
            font=("Segoe UI", theme.FONT_SIZE_BODY),
            height=32,
            border_color=theme.BORDER,
            fg_color=theme.SURFACE_SUNKEN,
            text_color=theme.TEXT_PRIMARY
        )
        self.entry.pack(padx=20, fill="x", pady=(0, 16))
        self.entry.focus_set()

        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(padx=20, fill="x", pady=(0, 12))

        def _submit(event=None):
            val = self.entry.get().strip()
            self.destroy()
            if val:
                on_confirm(val)

        def _cancel(event=None):
            self.destroy()

        self.entry.bind("<Return>", _submit)
        self.bind("<Escape>", _cancel)

        btn_cancel = ctk.CTkButton(
            btn_box,
            text="Cancelar",
            font=("Segoe UI", theme.FONT_SIZE_BODY),
            width=90,
            height=28,
            fg_color="transparent",
            border_width=1,
            border_color=theme.BORDER,
            hover_color=theme.SURFACE_HOVER,
            text_color=theme.TEXT_MUTED,
            command=_cancel
        )
        btn_cancel.pack(side="right", padx=(8, 0))

        btn_ok = ctk.CTkButton(
            btn_box,
            text="Crear",
            font=("Segoe UI", theme.FONT_SIZE_BODY, "bold"),
            width=90,
            height=28,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT_PRIMARY,
            command=_submit
        )
        btn_ok.pack(side="right")


class PackManagerView(Confirmable, ctk.CTkFrame):
    def __init__(self, master, process_service: ProcessService, pack_service: PackService, notification_service: NotificationService = None, gaming_service: GamingService = None):
        super().__init__(master, fg_color="transparent")
        self.process_service = process_service
        self.pack_service = pack_service
        self.notification_service = notification_service or NotificationService()
        self.gaming_service = gaming_service or GamingService(process_service, pack_service)
        self._build_ui()
        self.refresh_packs()

    def _build_ui(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 10))
        
        self.title_label = ctk.CTkLabel(
            self.header,
            text="📁 Gestor de Packs",
            font=("Segoe UI", theme.FONT_SIZE_HEADER, "bold"),
            text_color=theme.TEXT_PRIMARY
        )
        self.title_label.pack(side="left")
        
        self.btn_new = ctk.CTkButton(
            self.header,
            text="➕ Nuevo Pack",
            command=self.on_new_pack,
            width=120,
            height=28,
            font=("Segoe UI", theme.FONT_SIZE_BODY),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT_PRIMARY
        )
        self.btn_new.pack(side="right")
        
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            text_color=theme.TEXT_MUTED,
            anchor="w",
            wraplength=700,
            font=("Segoe UI", theme.FONT_SIZE_BODY)
        )
        self.status_label.pack(fill="x", pady=(0, 6))
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=theme.SURFACE)
        self.scroll_frame.pack(fill="both", expand=True)
        
        self._init_confirmable(self.status_label)

    def destroy(self):
        self.cancel_on_destroy()
        super().destroy()

    def refresh_packs(self):
        self._forget_buttons()
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        packs = self.pack_service.get_all_packs()
        if "gaming" in packs:
            self._render_pack_card(packs["gaming"])
        
        for p_id, p in packs.items():
            if p_id != "gaming":
                self._render_pack_card(p)

    def _render_pack_card(self, pack: Pack):
        # UI-005: Pack gaming destacado con borde GAMING
        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=theme.SURFACE_ALT,
            corner_radius=theme.RADIUS_LARGE,
            border_width=2 if pack.is_gaming else 1,
            border_color=theme.GAMING if pack.is_gaming else theme.BORDER
        )
        card.pack(fill="x", pady=4, padx=4)
        
        # --- FILA SUPERIOR: CABECERA Y ACCIONES ---
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=8, pady=(6, 4))
        
        # Izquierda: Favorito + Titulo + Badge
        left_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_box.pack(side="left", fill="x", expand=True)
        
        fav_text = "⭐" if pack.is_favorite else "☆"
        btn_fav = ctk.CTkButton(
            left_box,
            text=fav_text,
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=theme.SURFACE_HOVER,
            text_color=theme.TEXT_PRIMARY,
            font=("Segoe UI", theme.FONT_SIZE_BODY),
            command=lambda p=pack.id: self.toggle_favorite(p)
        )
        btn_fav.pack(side="left", padx=(0, 4))
        
        title_text = f"{pack.name} ({len(pack.apps)} apps)"
        title_lbl = ctk.CTkLabel(
            left_box,
            text=title_text,
            font=("Segoe UI", theme.FONT_SIZE_BODY, "bold"),
            text_color=theme.TEXT_PRIMARY,
            anchor="w"
        )
        title_lbl.pack(side="left", padx=2)
        
        if pack.is_gaming:
            badge_gaming = ctk.CTkLabel(
                left_box,
                text="PRESET",
                fg_color=theme.GAMING,
                text_color=theme.SURFACE,
                font=("Segoe UI", theme.FONT_SIZE_TINY, "bold"),
                corner_radius=theme.RADIUS_SMALL,
                width=54,
                height=20
            )
            badge_gaming.pack(side="left", padx=6)
        
        # Derecha: Toolbar de botones compactos (UI-007: min 28x28)
        right_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_box.pack(side="right")
        
        def change_default(choice, p_id=pack.id):
            p = self.pack_service.get_all_packs()[p_id]
            p.default_action = choice
            self.pack_service.save()
            
        combo_action = ctk.CTkOptionMenu(
            right_box,
            values=["kill", "start"],
            command=change_default,
            width=70,
            height=28,
            font=("Segoe UI", theme.FONT_SIZE_SMALL)
        )
        combo_action.set(pack.default_action)
        combo_action.pack(side="left", padx=3)
        
        btn_kill = ctk.CTkButton(
            right_box,
            text="⛔ Apagar",
            fg_color=theme.DANGER,
            hover_color=theme.DANGER_HOVER,
            text_color=theme.TEXT_PRIMARY,
            width=75,
            height=28,
            font=("Segoe UI", theme.FONT_SIZE_SMALL, "bold")
        )
        btn_kill.pack(side="left", padx=3)
        btn_kill.configure(command=lambda p=pack.id: self.kill_pack(p, btn_kill))
        
        btn_start = ctk.CTkButton(
            right_box,
            text="🚀 Iniciar",
            width=75,
            height=28,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT_PRIMARY,
            font=("Segoe UI", theme.FONT_SIZE_SMALL, "bold"),
            command=lambda p=pack: self.start_pack(p)
        )
        btn_start.pack(side="left", padx=3)
        
        if pack.is_gaming:
            btn_restore = ctk.CTkButton(
                right_box,
                text="🔄",
                width=28,
                height=28,
                fg_color=theme.SURFACE_SUNKEN,
                hover_color=theme.SURFACE_HOVER,
                text_color=theme.TEXT_PRIMARY,
                command=self.restore_gaming
            )
            btn_restore.pack(side="left", padx=(3, 0))
        else:
            btn_del = ctk.CTkButton(
                right_box,
                text="🗑️",
                width=28,
                height=28,
                fg_color=theme.SURFACE_SUNKEN,
                hover_color=theme.DANGER_HOVER,
                text_color=theme.TEXT_PRIMARY
            )
            btn_del.pack(side="left", padx=(3, 0))
            btn_del.configure(command=lambda p=pack.id: self.delete_pack(p, btn_del))

        # --- SECCION APPS (COMPACTA) ---
        apps_frame = ctk.CTkFrame(card, fg_color=theme.SURFACE_SUNKEN, corner_radius=theme.RADIUS_MEDIUM)
        apps_frame.pack(fill="x", padx=8, pady=(2, 6))
        
        if not pack.apps:
            ctk.CTkLabel(
                apps_frame,
                text="Sin aplicaciones manuales. Añádelas desde el Gestor de Procesos.",
                text_color=theme.TEXT_MUTED,
                font=("Segoe UI", theme.FONT_SIZE_SMALL)
            ).pack(anchor="w", padx=8, pady=4)
        else:
            for app in pack.apps:
                app_row = ctk.CTkFrame(apps_frame, fg_color="transparent")
                app_row.pack(fill="x", padx=8, pady=2)
                ctk.CTkLabel(
                    app_row,
                    text=f"• {app}",
                    font=("Segoe UI", theme.FONT_SIZE_SMALL),
                    text_color=theme.TEXT_PRIMARY
                ).pack(side="left")
                btn_remove = ctk.CTkButton(
                    app_row,
                    text="❌",
                    width=28,
                    height=28,
                    fg_color="transparent",
                    text_color=theme.DANGER,
                    hover_color=theme.SURFACE_HOVER
                )
                btn_remove.pack(side="right")
                btn_remove.configure(command=lambda p=pack.id, a=app: self.remove_app_from_pack(p, a, btn_remove))
                
        # --- SECCION ACORDEON CATEGORIAS (SOLO GAMING) ---
        if pack.is_gaming:
            active_count = len(pack.target_categories)
            acc_state = {"open": False}
            
            cat_body = ctk.CTkFrame(card, fg_color=theme.SURFACE_SUNKEN, corner_radius=theme.RADIUS_MEDIUM)
            
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
                font=("Segoe UI", theme.FONT_SIZE_SMALL),
                fg_color=theme.SURFACE_SUNKEN,
                hover_color=theme.SURFACE_HOVER,
                text_color=theme.TEXT_PRIMARY,
                height=28,
                anchor="w",
                command=toggle_acc
            )
            acc_btn.pack(fill="x", padx=8, pady=(0, 4))
            
            all_cats = set()
            for row in getattr(self.process_service, 'process_db', []):
                if "⚪ Otros" not in row.category:
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
                
            sorted_cats = ordenar_categorias(all_cats)
            for i, cat in enumerate(sorted_cats):
                var = ctk.IntVar(value=1 if cat in pack.target_categories else 0)
                cb = ctk.CTkCheckBox(
                    grid,
                    text=cat,
                    variable=var,
                    font=("Segoe UI", theme.FONT_SIZE_SMALL),
                    text_color=theme.TEXT_PRIMARY,
                    command=create_command(cat, var)
                )
                cb.grid(row=i // 2, column=i % 2, padx=6, pady=3, sticky="w")

    def toggle_favorite(self, pack_id: str):
        pack = self.pack_service.get_all_packs().get(pack_id)
        if pack is None:
            self.refresh_packs()
            return
        if pack.is_favorite:
            self.pack_service.set_favorite(None)
        else:
            self.pack_service.set_favorite(pack_id)
        self.refresh_packs()
        
    def restore_gaming(self):
        self.pack_service.reset_gaming_pack()
        self.refresh_packs()
        
    def delete_pack(self, pack_id: str, button=None):
        pack = self.pack_service.get_all_packs().get(pack_id)
        if pack is None:
            self._cancel_confirm()
            self._inline_status(MSG_PACK_INEXISTENTE, AMBAR)
            return
        if not self._require_double_tap(f"pack_del:{pack_id}", button,
                                        f"⚠️ Segunda pulsación para borrar el pack '{pack.name}'."):
            return
        try:
            borrado = self.pack_service.delete_pack(pack_id)
        except ValueError:
            self._inline_status(f"⛔ El pack '{pack.name}' es de sistema y no se puede borrar.", ROJO)
            return
        if not borrado:
            self._inline_status(MSG_PACK_INEXISTENTE, AMBAR)
            return
        self.refresh_packs()
        self._inline_status(f"✅ Pack '{pack.name}' borrado.", VERDE)

    def on_new_pack(self):
        # UI-009: Dialogo acoplado modal (reemplaza CTkInputDialog huérfano)
        def _create(name: str):
            pack_id = str(uuid.uuid4())[:8]
            self.pack_service.create_user_pack(pack_id, name, [])
            self.refresh_packs()

        NewPackModal(self.winfo_toplevel(), _create)

    def remove_app_from_pack(self, pack_id: str, app_name: str, button=None):
        pack = self.pack_service.get_all_packs().get(pack_id)
        if pack is None:
            self._cancel_confirm()
            self._inline_status(MSG_PACK_INEXISTENTE, AMBAR)
            return
        if not self._require_double_tap(f"pack_app:{pack_id}:{app_name}", button,
                                        f"⚠️ Segunda pulsación para quitar '{app_name}' de '{pack.name}'."):
            return
        pack = self.pack_service.get_all_packs().get(pack_id)
        if pack is None:
            self._inline_status(MSG_PACK_INEXISTENTE, AMBAR)
            return
        if app_name not in pack.apps:
            self._inline_status(f"⚠️ '{app_name}' ya no está en '{pack.name}'.", AMBAR)
            return
        pack.apps.remove(app_name)
        self.pack_service.save()
        self.refresh_packs()
        self._inline_status(f"✅ '{app_name}' quitada de '{pack.name}'.", VERDE)

    def kill_pack(self, pack_id: str, button=None):
        pack = self.pack_service.get_all_packs().get(pack_id)
        if pack is None:
            self._cancel_confirm()
            self._inline_status(MSG_PACK_INEXISTENTE, AMBAR)
            return
        if not pack.is_gaming and not pack.apps:
            self._cancel_confirm()
            self._inline_status(f"⚠️ '{pack.name}' no tiene apps que apagar.", AMBAR)
            return
        if pack.is_gaming:
            aviso = f"⚠️ Segunda pulsación para preparar el Gaming Mode de '{pack.name}'."
        else:
            aviso = f"⚠️ Segunda pulsación para apagar {len(pack.apps)} apps de '{pack.name}'."
        if not self._require_double_tap(f"pack_kill:{pack_id}", button, aviso):
            return
        pack = self.pack_service.get_all_packs().get(pack_id)
        if pack is None:
            self._inline_status(MSG_PACK_INEXISTENTE, AMBAR)
            return
        if not pack.is_gaming and not pack.apps:
            self._inline_status(f"⚠️ '{pack.name}' no tiene apps que apagar.", AMBAR)
            return
        apps = list(pack.apps)
        nombre = pack.name
        def _run():
            if pack.is_gaming:
                killed, _failed, _skipped, freed_mb = self.gaming_service.execute_gaming_pack(pack)
            else:
                killed, _failed, _skipped, freed_mb = self.process_service.kill_pack_apps(apps)
            self.notification_service.notify_pack_activated(nombre, killed, freed_mb)
        threading.Thread(target=_run, daemon=True).start()

    def start_pack(self, pack: Pack):
        self._cancel_confirm()
        if not pack.apps: return
        def _run():
            started, failed = self.process_service.start_pack_apps(pack.apps)
            self.notification_service.notify_apps_launched(pack.name, started, failed)
        threading.Thread(target=_run, daemon=True).start()
