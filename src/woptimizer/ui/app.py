import os
import sys
import customtkinter as ctk
from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService
from woptimizer.services.gaming_service import GamingService
from woptimizer.services.notification_service import NotificationService
from woptimizer.config import _data_dir
from woptimizer.ui.main_window import MainWindow

class WOptimizerApp:
    def __init__(self, process_service: ProcessService, pack_service: PackService, gaming_service: GamingService, autostart_tray: bool = True):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("🎮 woptimizer v3")
        self.root.geometry("860x560")
        self.root.minsize(720, 460)
        self.root.protocol('WM_DELETE_WINDOW', self.on_window_close)
        
        # UI-006: Asignar icono a la barra de titulo si existe assets/woptimizer.ico
        icon_path = os.path.join(_data_dir(), "assets", "woptimizer.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass
        
        self.process_service = process_service
        self.pack_service = pack_service
        self.gaming_service = gaming_service
        self.notification_service = NotificationService()
        # TASK-065: la maquina de confirmacion del menu de favoritos. Se crea aqui y NO
        # en `show_tray`, porque debe sobrevivir a la reconstruccion del menu: si viviera
        # dentro de `show_tray`, cada `hide_window` (que la vuelve a invocar) borraria la
        # pendiente y una confirmacion a medio hacer se perderia sola.
        from woptimizer.ui.tray_menu import TrayMenuState
        self._tray_state = TrayMenuState()
        
        self.main_window = MainWindow(
            master=self.root, 
            process_service=process_service, 
            pack_service=pack_service, 
            gaming_service=gaming_service,
            notification_service=self.notification_service
        )
        self.main_window.pack(fill="both", expand=True, padx=10, pady=10)

        # TASK-019: el icono de bandeja se levanta al arrancar para que
        # NotificationService.notify() tenga destino aunque la ventana siga
        # visible. `autostart_tray=False` lo omite (tests headless / CI).
        if autostart_tray:
            try:
                self.show_tray()
            except Exception as exc:  # noqa: BLE001 - nunca romper el arranque
                from woptimizer.config import logger
                logger.warning(f"No se pudo iniciar el tray al arrancar: {exc}")

    def on_window_close(self):
        if getattr(sys, 'frozen', False):
            self.hide_window()
        else:
            self.quit_app()

    def quit_app(self):
        try:
            if getattr(self, 'tray_icon', None):
                self.notification_service.detach_tray()
                self.tray_icon.stop()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def hide_window(self):
        self.root.withdraw()
        self.show_tray()

    # ------------------------------------------------------------------
    # Favoritos en el menu de la bandeja (TASK-065)
    # ------------------------------------------------------------------
    def _ejecutar_favorito(self, pack, icono, item):
        """Ejecuta un pack FAVORITO desde la bandeja, con la puerta que le toca.

        Un unico item por pack y UNA logica: el verbo lo decide `default_action` del pack,
        nunca el item. Los items de ARRANQUE ejecutan directos porque arrancar no es
        destructivo y no pide confirmacion desde TASK-023. Los de APAGADO pasan SIEMPRE por
        `tray_menu.TrayMenuState`, que es donde vive la segunda pulsacion: un item de
        apagado que no pase por ahi mataria con un solo clic, que es la excepcion que
        TASK-025 documento para UN pack y que este no amplia.
        """
        from woptimizer.config import logger
        import threading

        if pack.default_action == "start":
            threading.Thread(target=self._favorito_start, args=(pack,),
                             daemon=True).start()
            return

        # APAGADO: este item NUNCA ejecuta. Solo arma y redibuja el menu con el item de
        # "Confirmar". `armar` no devuelve nada precisamente para que aqui no haya nada
        # que interpretar como permiso: la UNICA llamada cuyo True significa "mata" es
        # `confirmar`, y la hace el item de "Confirmar".
        self._tray_state.armar(pack.id)
        self._refrescar_menu_tray()
        logger.info(f"Tray: pendiente de confirmar apagado de '{pack.id}'")

    def _confirmar_favorito(self, pack):
        """El item de "Confirmar". SI es el UNICO camino de kill desde la bandeja.

        `confirmar` devuelve True solo con una pendiente viva de ESE pack, asi que un
        "Confirmar" sin haber armado antes no hace nada, y un "Confirmar" repetido no
        repite el apagado.
        """
        if not self._tray_state.confirmar(pack.id):
            return
        from woptimizer.config import logger
        import threading
        logger.info(f"Tray: confirmada la pulsacion de '{pack.id}'")
        threading.Thread(target=self._favorito_kill, args=(pack,),
                         daemon=True).start()

    def _favorito_kill(self, pack):
        """Hilo secundario: apaga por la puerta UNICA y avisa con un toast nativo."""
        from woptimizer.config import logger
        try:
            killed, failed, skipped, freed_mb = self.gaming_service.execute_pack(pack)
            logger.info(f"Tray pack '{pack.id}': {killed} killed, {failed} failed, "
                        f"{freed_mb:.1f} MB freed")
            self.notification_service.notify_pack_activated(
                pack.name, killed, freed_mb
            )
        except Exception as e:  # noqa: BLE001 - un fallo aqui no puede tumbar la app
            logger.error(f"Tray pack '{pack.id}' kill error: {e}")

    def _favorito_start(self, pack):
        """Hilo secundario: arranca LAS DOS listas y suma los dos recuentos.

        La misma regla que `DashboardView.execute_pack`: elegir una lista y dejar la otra
        seria un apagado del criterio del usuario en silencio. El conflicto entre
        `start_categories` y `target_categories` lo resuelve el servicio.
        """
        from woptimizer.config import logger
        try:
            launched, failed = self.process_service.start_pack_apps(pack.apps)
            if pack.start_categories:
                launched_cats, failed_cats = self.process_service.start_pack_categories(
                    pack.start_categories, pack.target_categories
                )
                launched += launched_cats
                failed += failed_cats
            logger.info(f"Tray pack '{pack.id}': {launched} started, {failed} failed")
            self.notification_service.notify_apps_launched(
                pack.name, launched, failed
            )
        except Exception as e:  # noqa: BLE001 - idem
            logger.error(f"Tray pack '{pack.id}' start error: {e}")

    def _construir_items_favoritos(self, pystray):
        """Los items de los packs favoritos, en el orden de `get_favorite_packs()`.

        VUELVE una lista VACIA (no un separador huerfano) cuando no hay favoritos: un
        separador con nada debajo deja una linea en blanco en el menu que el usuario
        pulsaria sin efecto, y `pystray` no la limpia sola.
        """
        from woptimizer.ui.tray_menu import texto_cancelar, texto_item

        try:
            favoritos = self.pack_service.get_favorite_packs()
        except Exception as e:  # noqa: BLE001 - el menu no puede fallar por leer packs
            from woptimizer.config import logger
            logger.error(f"Tray: no se pudieron leer los favoritos: {e}")
            return []

        if not favoritos:
            return []

        items = [pystray.Menu.SEPARATOR]
        for pack in favoritos:
            # El callback se elige por el ESTADO, no por el item: un pack con pendiente
            # viva muestra "Confirmar" y su callback consume; sin pendiente, muestra su
            # verbo y su callback solo arma. Es la unica forma de que el texto y la
            # accion no puedan divergir, porque salen de la misma consulta.
            if pack.default_action == "kill" and self._tray_state.pendiente(pack.id):
                items.append(pystray.MenuItem(
                    texto_item(pack.id, pack.name, pack.default_action, self._tray_state),
                    lambda icon, item, p=pack: self._confirmar_favorito(p),
                ))
            else:
                items.append(pystray.MenuItem(
                    texto_item(pack.id, pack.name, pack.default_action, self._tray_state),
                    lambda icon, item, p=pack: self._ejecutar_favorito(p, icon, item),
                ))
        cancelar = texto_cancelar(self._tray_state)
        if cancelar:
            items.append(pystray.MenuItem(
                cancelar, lambda icon, item: self._cancelar_favorito()
            ))
        return items

    def _cancelar_favorito(self):
        """Item de "Cancelar": olvida la pendiente y redibuja."""
        from woptimizer.config import logger
        self._tray_state.cancelar()
        self._refrescar_menu_tray()
        logger.info("Tray: confirmacion cancelada")

    def _refrescar_menu_tray(self):
        """Redibuja el menu. `pystray` no muta un menu ya construido: hay que reponerlo.

        Es la UNICA razon por la que el menu es un metodo y no una tupla literal: armar la
        pendiente tiene que cambiar el TEXTO de un item, y un texto solo cambia si el item
        se reconstruye.
        """
        icono = getattr(self, "tray_icon", None)
        if icono is None:
            return
        try:
            icono.update_menu(self._menu_tray())
        except Exception as e:  # noqa: BLE001 - redibujar no puede tumbar la app
            from woptimizer.config import logger
            logger.error(f"Tray: no se pudo redibujar el menu: {e}")

    def _menu_tray(self):
        """El menu COMPLETO de la bandeja, reconstruido desde cero.

        Reconstruir entero (y no parchear) es lo que hace `pystray`: su API de actualizacion
        es `icon.update_menu(menu)`, que SUSTITUYE la referencia del menu, asi que un texto
        de item no se puede editar in situ. A cambio, `show_tray` y este metodo comparten la
        construccion, de modo que no hay dos listas de items que puedan divergir: antes los
        cuatro items vivian en una tupla literal dentro de `show_tray` y `_menu_tray` habria
        sido un segundo sitio que mantener.
        """
        import pystray

        def show_action(icon, item):
            icon.stop()
            self.tray_icon = None
            self.notification_service.detach_tray()
            self.root.after(0, self.root.deiconify)

        def quit_action(icon, item):
            self.quit_app()

        return pystray.Menu(*(
            [
                pystray.MenuItem('Mostrar App', show_action, default=True),
                *self._construir_items_favoritos(pystray),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('🚀 Preparar Gaming Mode', self._tray_gaming_action),
                pystray.MenuItem('🔄 Reabrir aplicaciones cerradas',
                                 self._tray_restore_action),
                pystray.MenuItem('Salir', quit_action),
            ]
        ))

    def show_tray(self):
        # Idempotente: TASK-019 la invoca en dos momentos (autostart y
        # hide_window). Sin este guard se crearian dos iconos en la bandeja.
        if getattr(self, "tray_icon", None) is not None:
            return
        import pystray
        from PIL import Image, ImageDraw
        
        icon_path = os.path.join(_data_dir(), "assets", "woptimizer.ico")
        if os.path.exists(icon_path):
            try:
                image = Image.open(icon_path)
            except Exception:
                image = Image.new('RGB', (64, 64), color = (30, 30, 30))
                d = ImageDraw.Draw(image)
                d.text((20, 20), "W3", fill=(255, 255, 255))
        else:
            image = Image.new('RGB', (64, 64), color = (30, 30, 30))
            d = ImageDraw.Draw(image)
            d.text((20, 20), "W3", fill=(255, 255, 255))
        
        self.tray_icon = pystray.Icon("woptimizer", image, "woptimizer v3",
                                     self._menu_tray())
        # TASK-019: el tray se registra en el NotificationService para poder emitir toasts
        self.notification_service.attach_tray(self.tray_icon)
        import threading
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _tray_gaming_action(self, icon, item):
        """El item "Preparar Gaming Mode".

        NO es un caso especial de los favoritos: sigue siendo la excepcion de TASK-025
        (un solo clic, sin confirmar) y sigue invocando `execute_gaming_pack`, que
        RECHAZA los packs que no son gaming. Por construccion no puede apagar un pack de
        usuario, y por eso meter los favoritos abajo no lo hace mas peligroso.
        """
        from woptimizer.config import logger
        try:
            gaming_pack = self.pack_service.get_all_packs().get("gaming")
            if gaming_pack:
                import threading
                def _run():
                    try:
                        # TASK-025: ruta de Gaming Mode. Un `MenuItem` de pystray
                        # no es un widget y no tiene donde mostrar una doble
                        # pulsacion; es la UNICA excepcion documentada a
                        # `_require_double_tap` (ver docs/ai/ui-design-system.md).
                        killed, failed, skipped, freed_mb = self.gaming_service.execute_gaming_pack(gaming_pack)
                        logger.info(f"Tray Gaming Mode: {killed} killed, {failed} failed, {freed_mb:.1f} MB freed")
                        # TASK-019: feedback nativo incluso con la ventana oculta
                        self.notification_service.notify_pack_activated(
                            "Gaming Mode", killed, freed_mb
                        )
                    except Exception as e:
                        logger.error(f"Tray Gaming Mode error: {e}")
                threading.Thread(target=_run, daemon=True).start()
        except Exception as e:
            logger.error(f"Tray gaming_action error: {e}")

    def _tray_restore_action(self, icon, item):
        """El item "Reabrir aplicaciones cerradas". No es destructivo: no confirma."""
        from woptimizer.config import logger
        try:
            import threading
            def _run():
                try:
                    started, failed = self.gaming_service.restore_gaming_session()
                    logger.info(f"Tray restore session: {started} started, {failed} failed")
                    if started == 0 and failed == 0:
                        self.notification_service.notify(
                            "woptimizer", "No hay aplicaciones pendientes de restauración."
                        )
                    else:
                        self.notification_service.notify_apps_launched(
                            "Restauración Gaming", started, failed
                        )
                except Exception as e:
                    logger.error(f"Tray restore_action error: {e}")
            threading.Thread(target=_run, daemon=True).start()
        except Exception as e:
            logger.error(f"Tray restore_action outer error: {e}")

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()
