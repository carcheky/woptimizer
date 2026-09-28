import sys
import customtkinter as ctk
from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService
from woptimizer.services.gaming_service import GamingService
from woptimizer.ui.main_window import MainWindow

class WOptimizerApp:
    def __init__(self, process_service: ProcessService, pack_service: PackService, gaming_service: GamingService):
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
        
        self.main_window = MainWindow(
            master=self.root, 
            process_service=process_service, 
            pack_service=pack_service, 
            gaming_service=gaming_service
        )
        self.main_window.pack(fill="both", expand=True, padx=10, pady=10)

    def on_window_close(self):
        if getattr(sys, 'frozen', False):
            self.hide_window()
        else:
            self.quit_app()

    def quit_app(self):
        try:
            if hasattr(self, 'tray_icon') and self.tray_icon:
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
        import pystray
        from PIL import Image, ImageDraw
        
        image = Image.new('RGB', (64, 64), color = (30, 30, 30))
        d = ImageDraw.Draw(image)
        d.text((20, 20), "W3", fill=(255, 255, 255))
        
        def show_action(icon, item):
            icon.stop()
            self.root.after(0, self.root.deiconify)
            
        def quit_action(icon, item):
            self.quit_app()
            
        def gaming_action(icon, item):
            gaming_pack = self.pack_service.get_all_packs().get("gaming")
            if gaming_pack:
                import threading
                threading.Thread(target=self.process_service.kill_pack_apps, args=(gaming_pack.apps,), daemon=True).start()
                
        menu = (
            pystray.MenuItem('Mostrar App', show_action, default=True),
            pystray.MenuItem('🚀 Preparar Gaming Mode', gaming_action),
            pystray.MenuItem('Salir', quit_action)
        )
        icon = pystray.Icon("woptimizer", image, "woptimizer v3", menu)
        import threading
        threading.Thread(target=icon.run, daemon=True).start()

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()
