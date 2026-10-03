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
from woptimizer.ui.feedback import (
    es_pack_inerte, mensaje_cierre_pack, mensaje_gaming_inerte, mensaje_sin_apps,
    texto_confirmacion_apagado,
)
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
            # BUG (TASK-062): `get_all_packs()` devuelve COPIAS defensivas
            # (`model_copy(deep=True)`, cache de 2 capas en `pack_service.py:593`),
            # y `save()` serializa `self._data`, que esa copia NUNCA toca. La
            # mutacion se perdia entera: el desplegable cambiaba, se escribia el
            # fichero con el valor viejo y al recargar volvia al anterior.
            # Ademas `save()` NO invalida la cache, asi que la UI seguia
            # enseñando el valor viejo aun con la mutacion bien hecha.
            # `update_pack()` hace las tres cosas: copia a `_data`, guarda e
            # invalida la cache. No volver a llamar a `save()` aqui.
            p = self.pack_service.get_all_packs()[p_id]
            p.default_action = choice
            self.pack_service.update_pack(p)
            
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
                
        # --- SECCION ACORDEON CATEGORIAS (TASK-063: para TODOS los packs) ---
        #
        # El `if pack.is_gaming:` que abria esta seccion se ha ido y no se ha
        # sustituido por su equivalente. Motivo: el gate era el sintoma de un
        # cableado que ya no existe. `Pack` es un solo modelo con las tres listas
        # (`apps`, `target_categories`, `start_categories`), `execute_pack` y
        # `start_pack_categories` son las dos puertas de todo el producto y ya no
        # miran `is_gaming` para decidir nada. Dejar el gate seria alinear el
        # formulario con lo que el servicio NO hace: el usuario veria un pack sin
        # donde elegir categorias, con un servicio que se las pregunta igual.
        active_count = len(pack.target_categories) + len(pack.start_categories)
        acc_state = {"open": False}

        cat_body = ctk.CTkFrame(card, fg_color=theme.SURFACE_SUNKEN, corner_radius=theme.RADIUS_MEDIUM)

        def _texto_acordeon(n: int, abierto: bool) -> str:
            return (f"⚙️ Configurar Categorías Automáticas ({n} activas)"
                    f" {'▲' if abierto else '▼'}")

        def _refrescar_contador():
            """El contador sale del registro VIVO (`_data`), no de esta tarjeta."""
            actual = self.pack_service.get_all_packs().get(pack.id)
            n = (len(actual.target_categories) + len(actual.start_categories)
                 if actual else active_count)
            acc_btn.configure(text=_texto_acordeon(n, acc_state["open"]))

        def toggle_acc():
            acc_state["open"] = not acc_state["open"]
            _refrescar_contador()
            if acc_state["open"]:
                cat_body.pack(fill="x", padx=8, pady=(0, 6))
            else:
                cat_body.pack_forget()

        acc_btn = ctk.CTkButton(
            card,
            text=_texto_acordeon(active_count, False),
            font=("Segoe UI", theme.FONT_SIZE_SMALL),
            fg_color=theme.SURFACE_SUNKEN,
            hover_color=theme.SURFACE_HOVER,
            text_color=theme.TEXT_PRIMARY,
            height=28,
            anchor="w",
            command=toggle_acc
        )
        acc_btn.pack(fill="x", padx=8, pady=(0, 4))

        # TASK-063: el catalogo lo da `ProcessService.categorias_disponibles()`.
        # Antes esta vista se lo armaba sola con DOS fuentes distintas --leer
        # `self.process_service.process_db`, y si venia vacio, ocho nombres
        # escritos a mano-- y las dos tenian que coincidir con la DB de verdad.
        # Cuando no coincidian, el proceso aparecia en "Otros" sin casilla donde
        # marcarlo. Ahora hay una sola fuente, y la vista deja de tocar el
        # atributo de DB del servicio: leerlo era una via lateral a la capa, y lo
        # era justo para decidir QUE puede matar el usuario.
        all_cats = set(self.process_service.categorias_disponibles())

        grid = ctk.CTkFrame(cat_body, fg_color="transparent")
        grid.pack(fill="x", padx=6, pady=4)
        grid.grid_columnconfigure((0, 1), weight=1)

        # TASK-063: las dos columnas son ESPEJO UNA DE OTRA. Marcar "apagar"
        # desmarca "arrancar" y al reves, y el estado final sale en UN solo
        # `update_pack()` -- una escritura, no dos: guardar dos veces la misma
        # tarjeta es dos veces la ventana en la que un fallo de disco deja
        # `_data` y el disco discrepando.
        def create_command(c, v_apagar, v_arrancar, p_id=pack.id):
            def toggle():
                # BUG (TASK-062): `pack` es la COPIA de `get_all_packs()` que
                # llego a esta tarjeta. Mutar la lista en ella y llamar a `save()`
                # no persiste NADA, porque `save()` serializa `_data` y la copia
                # nunca lo toca. Es decir: las categorias automaticas del pack
                # Gaming --justo lo que decide que cierra el Gaming Mode-- no se
                # guardaban. `update_pack()` copia a `_data`, guarda e invalida
                # la cache.
                actual = self.pack_service.get_all_packs()[p_id]
                # El conflicto de las dos listas se IMPONE aqui (una misma
                # categoria no puede estar en las dos) y se RESUELVE en
                # `ProcessService.start_pack_categories` por si un `profiles.json`
                # escrito a mano lo trae. Alli gana apagar, y por eso la que se
                # desmarca al marcar esta es la de arrancar.
                if v_apagar.get() == 1:
                    if c not in actual.target_categories:
                        actual.target_categories.append(c)
                    if c in actual.start_categories:
                        actual.start_categories.remove(c)
                    v_arrancar.set(0)
                elif c in actual.target_categories:
                    actual.target_categories.remove(c)
                if v_arrancar.get() == 1:
                    if c not in actual.start_categories:
                        actual.start_categories.append(c)
                    if c in actual.target_categories:
                        actual.target_categories.remove(c)
                    v_apagar.set(0)
                elif c in actual.start_categories:
                    actual.start_categories.remove(c)
                self.pack_service.update_pack(actual)
                _refrescar_contador()
            return toggle

        sorted_cats = ordenar_categorias(all_cats)
        for i, cat in enumerate(sorted_cats):
            apagar_var = ctk.IntVar(value=1 if cat in pack.target_categories else 0)
            arrancar_var = ctk.IntVar(value=1 if cat in pack.start_categories else 0)
            cb = ctk.CTkCheckBox(
                grid,
                text=cat,
                variable=apagar_var,
                font=("Segoe UI", theme.FONT_SIZE_SMALL),
                text_color=theme.TEXT_PRIMARY,
                command=create_command(cat, apagar_var, arrancar_var)
            )
            cb.grid(row=i // 2, column=i % 2, padx=6, pady=3, sticky="w")
        # Segunda tanda del grid: las MISMAS categorias, para arrancar.
        for i, cat in enumerate(sorted_cats):
            apagar_var = ctk.IntVar(value=1 if cat in pack.target_categories else 0)
            arrancar_var = ctk.IntVar(value=1 if cat in pack.start_categories else 0)
            cb = ctk.CTkCheckBox(
                grid,
                text=f"{cat} (arrancar)",
                variable=arrancar_var,
                font=("Segoe UI", theme.FONT_SIZE_SMALL),
                text_color=theme.TEXT_PRIMARY,
                command=create_command(cat, apagar_var, arrancar_var)
            )
            cb.grid(row=(len(sorted_cats) + i) // 2, column=i % 2, padx=6, pady=3, sticky="w")

    def toggle_favorite(self, pack_id: str):
        pack = self.pack_service.get_all_packs().get(pack_id)
        if pack is None:
            self.refresh_packs()
            return
        if hasattr(self.pack_service, "toggle_favorite"):
            self.pack_service.toggle_favorite(pack_id)
        elif pack.is_favorite:
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
        # Mismo bug y mismo arreglo que `change_default`: `pack` es una copia
        # defensiva de `get_all_packs()`, y `save()` sola no la persiste ni
        # invalida la cache. `update_pack()` si.
        self.pack_service.update_pack(pack)
        self.refresh_packs()
        self._inline_status(f"✅ '{app_name}' quitada de '{pack.name}'.", VERDE)

    def _aviso_pack_inerte(self, pack: Pack):
        """El par `(texto, color)` del pack que no puede hacer nada, o `None`.

        La frase NO esta aqui: sale de `ui/feedback.py`, igual que la del cierre,
        para que el Gestor y la Portada no puedan divergir. El diagnostico del
        Gaming Mode inerte va antes que el aviso de "no tiene apps" porque es
        otro hecho: no es que falten apps, es que no hay NADA que cerrar.

        Este helper es la puerta de APAGAR y solo la de APAGAR: lo llaman los dos
        puntos de `kill_pack` que leen el pack, y ninguno mas. Por eso el aviso
        de "no tiene apps" cablea el verbo a `"kill"` y no a `pack.default_action`
        (ver el comentario de la rama): la accion la sabe el metodo, no el pack.

        TASK-063: la segunda guarda ya no mira solo `apps`. Un pack con 0 apps y
        3 categorias marcadas SI tiene algo que apagar -- la puerta de aqui
        entra en `gaming_service.execute_pack`, que ademas consulta
        `target_categories` -- asi que decir "no tiene apps que apagar" seria la
        misma mentira que el "0 apps" del texto de confirmacion (spec 2.7). La
        guarda se queda, y lo que cambia es lo que considera vacio: apps Y
        categorias de apagado.

        El `not pack.is_gaming and` que estaba aqui ya no hace falta y por eso no
        se pone el equivalente: si `is_gaming` es True y las dos listas estan
        vacias, la primera rama (el diagnostico del Gaming inerte) ya ha
        devuelto. Es decir, quitarlo NO cambia el resultado de ningun pack: cambia
        por que ruta sale el mismo aviso.
        """
        if es_pack_inerte(pack.is_gaming, len(pack.apps), len(pack.target_categories)):
            return mensaje_gaming_inerte(pack.name)
        if not pack.apps and not pack.target_categories:
            # El verbo lo decide el METODO, no el pack (espejo de `start_pack`):
            # este helper lo llama solo `kill_pack`, que es apagar SIEMPRE, asi
            # que la accion que se le pasa es `"kill"`. Si se pasara
            # `pack.default_action`, un pack recien creado --que nace con
            # `default_action="start"`-- diria "no tiene apps que iniciar" en la
            # puerta de APAGAR, que es la primera accion de un usuario recien
            # instalado. El unico que sabe que puerta se esta pulsando es el
            # metodo de la puerta, no el dato guardado del pack.
            return mensaje_sin_apps(pack.name, "kill")
        return None

    def _texto_confirmacion_apagado(self, pack: Pack) -> str:
        """La frase de la doble pulsacion, con el numero de la PUERTA.

        El numero lo pone `gaming_service.cuenta_a_apagar(pack)`, que aplica el
        mismo filtro que `execute_pack` va a aplicar: contarlo aqui seria una
        segunda politica de seguridad en el sitio que menos puede tenerla. La
        frase vive en `ui/feedback.py` para que el Gestor y la Portada digan
        exactamente lo mismo.
        """
        return texto_confirmacion_apagado(
            pack.name,
            self.gaming_service.cuenta_a_apagar(pack),
            len(pack.apps),
            len(pack.target_categories),
        )

    def kill_pack(self, pack_id: str, button=None):
        pack = self.pack_service.get_all_packs().get(pack_id)
        if pack is None:
            self._cancel_confirm()
            self._inline_status(MSG_PACK_INEXISTENTE, AMBAR)
            return
        # Antes de `_require_double_tap`: armar la confirmacion sobre un pack
        # imposible no deja nada que confirmar.
        aviso_inerte = self._aviso_pack_inerte(pack)
        if aviso_inerte is not None:
            self._cancel_confirm()
            self._inline_status(*aviso_inerte)
            return
        if pack.is_gaming:
            aviso = f"⚠️ Segunda pulsación para preparar el Gaming Mode de '{pack.name}'."
        else:
            aviso = self._texto_confirmacion_apagado(pack)
        if not self._require_double_tap(f"pack_kill:{pack_id}", button, aviso):
            return
        pack = self.pack_service.get_all_packs().get(pack_id)
        if pack is None:
            self._inline_status(MSG_PACK_INEXISTENTE, AMBAR)
            return
        # El pack se vuelve a leer por `id` (TASK-026), y entre las dos lecturas
        # el usuario puede haber borrado sus apps. Es la MISMA comprobacion, no
        # una segunda: por eso esta en un metodo y no en dos literales.
        aviso_inerte = self._aviso_pack_inerte(pack)
        if aviso_inerte is not None:
            self._inline_status(*aviso_inerte)
            return
        nombre = pack.name
        def _run():
            # TASK-035 / ciclo 26: el mensaje sale de la TUPLA REAL, no de un
            # literal. La puerta devuelve la misma 4-tupla que antes devolvian las
            # dos y `mensaje_cierre_pack` es la unica que la formatea, de modo que
            # ninguna puerta puede mentir por su cuenta. Con 0 cerrados el texto NO
            # lleva tick y el color NO es verde.
            #
            # TASK-063: UN SOLO camino de apagado para TODOS los packs. Antes
            # estaba `if is_gaming: execute_gaming_pack / else: kill_pack_apps`,
            # y la rama de `kill_pack_apps` no miraba `target_categories`: con 0
            # apps y 3 categorias marcadas mataba 0 y lo decia como exito. Ahora las
            # dos ramas entran en `execute_pack`, que es donde viven las barreras
            # (nombres protegidos y categoria roja) y el filtro de keepers.
            killed, failed, skipped, freed_mb = self.gaming_service.execute_pack(pack)
            texto, color = mensaje_cierre_pack(nombre, killed, failed, skipped, freed_mb)
            self.after(0, self._inline_status, texto, color)
            self.notification_service.notify_pack_activated(nombre, killed, freed_mb)
        threading.Thread(target=_run, daemon=True).start()

    def start_pack(self, pack: Pack):
        self._cancel_confirm()
        if not pack.apps and not pack.start_categories:
            # Aqui la accion la decide el METODO, no el pack: `start_pack` es
            # arrancar siempre, y un pack gaming con `default_action="kill"`
            # iniciado desde el Gestor tiene que decir "iniciar". El verbo lo
            # sigue sacando el formateador de la accion, que es lo unico que la
            # vista le pasa.
            #
            # TASK-063: el "vacio" de esta puerta es `apps` Y `start_categories`,
            # no solo `apps`: son las dos listas que `start_pack` ejecuta, y con
            # 0 apps y 2 categorias de arranque marcadas el aviso seria la misma
            # mentira que el "apagar 0 apps" de la otra puerta.
            self._inline_status(*mensaje_sin_apps(pack.name, "start"))
            return
        nombre = pack.name
        apps = list(pack.apps)
        categorias = list(pack.start_categories)
        def _run():
            # TASK-063: las DOS listas y la SUMA de los dos recuentos. Elegir una
            # y dejar la otra seria ignorar en silencio la mitad de lo que el
            # usuario marco. El conflicto entre las dos listas lo resuelve el
            # servicio (`start_pack_categories` recibe `target_categories` y
            # descarta la que este marcada para apagar).
            started, failed = self.process_service.start_pack_apps(apps)
            if categorias:
                started_cats, failed_cats = self.process_service.start_pack_categories(
                    categorias, pack.target_categories
                )
                started += started_cats
                failed += failed_cats
            if failed == 0:
                self.after(0, self._inline_status, f"🚀 {started} apps iniciadas · '{nombre}'.", VERDE)
            else:
                self.after(0, self._inline_status, f"⚠️ '{nombre}': {started} iniciadas, {failed} con error.", AMBAR)
            self.notification_service.notify_apps_launched(nombre, started, failed)
        threading.Thread(target=_run, daemon=True).start()

