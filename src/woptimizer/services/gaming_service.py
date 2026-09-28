from woptimizer.models import ProcessInfo, Pack
from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService

class GamingService:
    def __init__(self, process_service: ProcessService, pack_service: PackService):
        self.process_service = process_service
        self.pack_service = pack_service

    def should_kill_for_gaming(self, process_name: str, gaming_pack: Pack) -> bool:
        """
        Evalúa si un proceso debe morir al preparar el Gaming Mode.
        Reglas:
        1. Si está en keepers -> False
        2. Si está explícitamente en apps (extra kills) -> True
        3. Si la categoría del proceso está en target_categories -> True
        4. Resto -> False
        """
        name_lower = process_name.lower()
        
        # 1. Verificar keepers (protegidos)
        for keeper in gaming_pack.keepers:
            if keeper.lower() in name_lower:
                return False
                
        # 2. Verificar apps a matar explícitas
        for extra_app in gaming_pack.apps:
            if extra_app.lower() in name_lower:
                return True
                
        cat = self.process_service._categorize(name_lower)
        
        # 3. Evaluar si la categoría está en el target
        if cat in gaming_pack.target_categories:
            return True
            
        return False
