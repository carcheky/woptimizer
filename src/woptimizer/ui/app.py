import sys
import customtkinter as ctk
from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService
from woptimizer.services.gaming_service import GamingService
from woptimizer.services.notification_service import NotificationService
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
        
        self.process_service = process_service
        self.pack_service = pack_service
        self.gaming_service = gaming_service
        self.notification_service = NotificationService()
        
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
        import sys
        sys.exit(0)

    def hide_window(self):
        self.root.withdraw()
        self.show_tray()

    def show_tray(self):
        # Idempotente: TASK-019 la invoca en dos momentos (autostart y
        # hide_window). Sin este guard se crearian dos iconos en la bandeja.
        if getattr(self, "tray_icon", None) is not None:
            return
        import pystray
        from PIL import Image, ImageDraw
        
        image = Image.new('RGB', (64, 64), color = (30, 30, 30))
        d = ImageDraw.Draw(image)
        d.text((20, 20), "W3", fill=(255, 255, 255))
        
        def show_action(icon, item):
            icon.stop()
            self.tray_icon = None
            self.notification_service.detach_tray()
            self.root.after(0, self.root.deiconify)
            
        def quit_action(icon, item):
            self.quit_app()
            
        def gaming_action(icon, item):
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
                
        menu = (
            pystray.MenuItem('Mostrar App', show_action, default=True),
            pystray.MenuItem('🚀 Preparar Gaming Mode', gaming_action),
            pystray.MenuItem('Salir', quit_action)
        )
        self.tray_icon = pystray.Icon("woptimizer", image, "woptimizer v3", menu)
        # TASK-019: el tray se registra en el NotificationService para poder emitir toasts
        self.notification_service.attach_tray(self.tray_icon)
        import threading
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()
