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

class PackManagerView(Confirmable, ctk.CTkFrame):
    def __init__(self, master, process_service: ProcessService, pack_service: PackService, notification_service: NotificationService = None, gaming_service: GamingService = None):
        super().__init__(master, fg_color="transparent")
        self.process_service = process_service
        self.pack_service = pack_service
        self.notification_service = notification_service or NotificationService()
        # TASK-025: el Gaming Mode se ejecuta por `GamingService`, que es quien
        # consulta `keepers` y `target_categories`. Mismo patron defensivo que
        # `notification_service`: si no se inyecta se crea uno local para no
        # romper constructores antiguos ni tests.
        self.gaming_service = gaming_service or GamingService(process_service, pack_service)
        self._build_ui()
        self.refresh_packs()

    def _build_ui(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 10))
        
        self.title_label = ctk.CTkLabel(self.header, text="📁 Gestor de Packs", font=("Segoe UI", 20, "bold"))
        self.title_label.pack(side="left")
        
        self.btn_new = ctk.CTkButton(self.header, text="➕ Nuevo Pack", command=self.on_new_pack, width=120)
        self.btn_new.pack(side="right")
        
        # TASK-023: la vista no tenia ningun `status_label` y sin el no hay forma de
        # dar el feedback inline de la doble pulsacion.
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray", anchor="w", wraplength=700)
        self.status_label.pack(fill="x", pady=(0, 6))
        
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)
        
        # TASK-023: doble pulsacion para apagar / borrar / quitar apps
        self._init_confirmable(self.status_label)

    def destroy(self):
        # Sin esto, el `after` de la pendiente sobrevive al cambio de pestaña y
        # reconfigura botones ya destruidos (regla §6.1).
        self.cancel_on_destroy()
        super().destroy()

    def refresh_packs(self):
        # Los botones de tarjeta se recrean: una pendiente sobre ellos no tiene a que
        # reconfigurarse, asi que se cancela antes de destruirlos.
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
                                 width=75, height=26, font=("Segoe UI", 11, "bold"))
        btn_kill.pack(side="left", padx=3)
        # El pack se re-obtiene por id al confirmar: `reset_gaming_pack` clona el objeto
        # y una referencia capturada puede quedar obsoleta (TASK-023).
        btn_kill.configure(command=lambda p=pack.id: self.kill_pack(p, btn_kill))
        
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
                                    fg_color="#333333", hover_color="#552222")
            btn_del.pack(side="left", padx=(3, 0))
            btn_del.configure(command=lambda p=pack.id: self.delete_pack(p, btn_del))

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
                                           text_color="#c22d2d", hover_color="#2b1515")
                btn_remove.pack(side="right")
                btn_remove.configure(command=lambda p=pack.id, a=app: self.remove_app_from_pack(p, a, btn_remove))
                
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
            # TASK-026 (FIX-005): el centinela se compara con el circulo U+26AA que
            # ya usan config.py (CATEGORY_ORDER) y models.py, no con la
            # interrogacion ASCII. Con "? Otros" el filtro era un no-op: si la DB
            # trae ya la categoria canonica, "Otros" se ofrecia como casilla
            # activable de target_categories.
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
                
            # TASK-027 (FIX-004): SEGUNDO sitio del defecto, el que el encargo
            # original no declaro. `sorted(list(all_cats))` ordenaba por punto de
            # codigo (⚪ U+26AA del BMP sale primero, 🟢🟡🔴 del plano suplementario
            # despues) y por eso el acordeon que decide QUE se cierra en el Gaming
            # Mode mostraba las casillas en el orden contrario al del semaforo. Se
            # resuelve con la MISMA funcion de `config.py` que usa el Gestor de
            # Procesos, para que los dos sitios no puedan volver a divergir.
            sorted_cats = ordenar_categorias(all_cats)
            for i, cat in enumerate(sorted_cats):
                var = ctk.IntVar(value=1 if cat in pack.target_categories else 0)
                cb = ctk.CTkCheckBox(grid, text=cat, variable=var, font=("Segoe UI", 11), command=create_command(cat, var))
                cb.grid(row=i // 2, column=i % 2, padx=6, pady=3, sticky="w")

    def toggle_favorite(self, pack_id: str):
        # TASK-027 (FIX-006): el bug es de UNA LINEA aqui, no en el servicio.
        # `PackService.set_favorite(None)` ya existe (pack_service.py:652) y ya
        # esta testeado, asi que la UI solo tiene que pasar `None` en la segunda
        # pulsacion de la estrella.
        #
        # De donde se lee el estado: EN VIVO, de `get_all_packs()`. NO del `pack`
        # capturado en el render (`lambda p=pack.id`) ni del glifo ⭐/☆: son
        # instantaneas de un render que puede quedar obsoleto (`reset_gaming_pack`
        # devuelve un `model_copy`, asi que el objeto de la tarjeta anterior ya no
        # es el de `self._data`). Es ademas la MISMA llamada que hace
        # `refresh_packs`, asi que no anade API.
        #
        # Y NO `get_favorite_pack()`: devuelve el PRIMER favorito
        # (`pack_service.py:628`), y con dos favoritos (alcanzable editando
        # `profiles.json` a mano) pulsar la estrella del segundo lo MARCARIA en
        # vez de desmarcarlo. El atajo tampoco se puede testear bien.
        pack = self.pack_service.get_all_packs().get(pack_id)
        if pack is None:
            # Un id que ya no existe NO se marca: `set_favorite("z")` desmarca
            # TODOS los favoritos y ademas lo persiste. No hay nada que
            # alternar. Sin esta guarda, el `else` de abajo cumple el criterio
            # de T-27.4 caso 3 ("no llama a set_favorite") solo si no existe.
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
            # El boton 🗑️ no se crea en el pack de sistema, pero el guard no puede ser
            # el unico que protege: si llegase aqui, el usuario tiene que enterarse.
            self._inline_status(f"⛔ El pack '{pack.name}' es de sistema y no se puede borrar.", ROJO)
            return
        if not borrado:
            # Fallo silencioso real: `delete_pack` devuelve False si el pack ya no existe
            # y antes la vista se lo tragaba sin decir nada (TASK-023).
            self._inline_status(MSG_PACK_INEXISTENTE, AMBAR)
            return
        self.refresh_packs()
        self._inline_status(f"✅ Pack '{pack.name}' borrado.", VERDE)

    def on_new_pack(self):
        dialog = ctk.CTkInputDialog(text="Introduce el nombre del nuevo Pack:", title="Nuevo Pack")
        name = dialog.get_input()
        if name and name.strip():
            pack_id = str(uuid.uuid4())[:8]
            self.pack_service.create_user_pack(pack_id, name.strip(), [])
            self.refresh_packs()

    def remove_app_from_pack(self, pack_id: str, app_name: str, button=None):
        pack = self.pack_service.get_all_packs().get(pack_id)
        if pack is None:
            self._cancel_confirm()
            self._inline_status(MSG_PACK_INEXISTENTE, AMBAR)
            return
        if not self._require_double_tap(f"pack_app:{pack_id}:{app_name}", button,
                                        f"⚠️ Segunda pulsación para quitar '{app_name}' de '{pack.name}'."):
            return
        pack = self.pack_service.get_all_packs().get(pack_id)  # re-fetch, el objeto pudo clonarse
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
        # TASK-025 (spec 5.1): un Gaming Mode puede no tener apps manuales, su
        # configuracion esta en `keepers` + `target_categories`. Sin esta excepcion
        # el aviso "no tiene apps que apagar" hacia el Gaming Mode a un sitio sin
        # configuracion, que es justo el caso por defecto del pack de fábrica.
        if not pack.is_gaming and not pack.apps:
            self._cancel_confirm()
            self._inline_status(f"⚠️ '{pack.name}' no tiene apps que apagar.", AMBAR)
            return
        if pack.is_gaming:
            aviso = f"⚠️ Segunda pulsación para preparar el Gaming Mode de '{pack.name}'."
        else:
            aviso = f"⚠️ Segunda pulsación para apagar {len(pack.apps)} apps de '{pack.name}'."
        # El guard es el mismo de siempre: no hay dialogo (Trampa #14).
        if not self._require_double_tap(f"pack_kill:{pack_id}", button, aviso):
            return
        # Re-fetch en el instante de la confirmacion: el `pack` de la 1a pulsacion pudo
        # quedar obsoleto (`reset_gaming_pack` devuelve un `model_copy`).
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
                # Ruta de Gaming Mode: consulta keepers y categorias.
                killed, _failed, _skipped, freed_mb = self.gaming_service.execute_gaming_pack(pack)
            else:
                killed, _failed, _skipped, freed_mb = self.process_service.kill_pack_apps(apps)
            # TASK-019: toast nativo con el resumen del cierre
            self.notification_service.notify_pack_activated(nombre, killed, freed_mb)
        threading.Thread(target=_run, daemon=True).start()

    def start_pack(self, pack: Pack):
        # Arrancar no es destructivo, pero pulsar otra accion resetea la pendiente
        # anterior: si no, el boton ⛔ se queda en ambar sin nadie que lo confirme.
        self._cancel_confirm()
        if not pack.apps: return
        def _run():
            started, failed = self.process_service.start_pack_apps(pack.apps)
            # TASK-019: toast nativo con el resumen del arranque
            self.notification_service.notify_apps_launched(pack.name, started, failed)
        threading.Thread(target=_run, daemon=True).start()
