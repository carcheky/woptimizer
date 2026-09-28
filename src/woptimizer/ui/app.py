import sys
import customtkinter as ctk
from woptimizer.services.process_service import ProcessService
from woptimizer.services.profile_service import ProfileService
from woptimizer.services.gaming_service import GamingService
from woptimizer.ui.main_window import MainWindow

class WOptimizerApp:
    def __init__(self, process_service: ProcessService, profile_service: ProfileService, gaming_service: GamingService):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("🎮 woptimizer v3")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        self.main_window = MainWindow(
            master=self.root, 
            process_service=process_service, 
            profile_service=profile_service, 
            gaming_service=gaming_service
        )
        self.main_window.pack(fill="both", expand=True, padx=20, pady=20)

    def run(self):
        self.root.mainloop()
