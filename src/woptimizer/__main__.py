import os
import sys

_current_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.dirname(_current_dir)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService
from woptimizer.services.gaming_service import GamingService
from woptimizer.ui.app import WOptimizerApp

def main():
    try:
        # Inicializar capa de servicios
        process_service = ProcessService()
        pack_service = PackService()
        gaming_service = GamingService(process_service, pack_service)

        # Inicializar e inyectar UI
        app = WOptimizerApp(process_service, pack_service, gaming_service)
        
        # Arrancar bucle principal
        app.run()
        return 0
    except KeyboardInterrupt:
        return 0

if __name__ == "__main__":
    sys.exit(main())
