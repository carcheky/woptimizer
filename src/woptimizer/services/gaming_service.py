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
        2. Si prioridad es high/medium -> True
        3. Si prioridad es low (chat) -> True (se simplifica ya que no hay kill_low_chat)
        4. Resto -> False
        """
        name_lower = process_name.lower()
        
        # 1. Verificar keepers
        for keeper in gaming_pack.keepers:
            if keeper.lower() in name_lower:
                return False
                
        cat = self.process_service._categorize(name_lower)
        priority = self.process_service._get_priority(cat)
        
        # 2 y 3. Evaluar prioridades
        if priority in ('high', 'medium'):
            return True
            
        if priority == 'low' and cat == '🟡 Chat y Comunicación':
            return True
            
        # 4. Resto
        return False
