from woptimizer.models import ProcessInfo, GamingProfile
from woptimizer.services.process_service import ProcessService
from woptimizer.services.profile_service import ProfileService

class GamingService:
    def __init__(self, process_service: ProcessService, profile_service: ProfileService):
        self.process_service = process_service
        self.profile_service = profile_service

    def should_kill_for_gaming(self, process_name: str, gaming_profile: GamingProfile) -> bool:
        """
        Evalúa si un proceso debe morir al preparar el Gaming Mode.
        Reglas:
        1. Si está en keepers -> False
        2. Si prioridad es high/medium -> True
        3. Si prioridad es low (chat) Y kill_low_chat es True -> True
        4. Resto -> False
        """
        name_lower = process_name.lower()
        
        # 1. Verificar keepers
        for keeper in gaming_profile.keepers:
            if keeper.lower() in name_lower:
                return False
                
        # Para saber la prioridad, necesitamos categorizarlo
        cat = self.process_service._categorize(name_lower)
        priority = self.process_service._get_priority(cat)
        
        # 2 y 3. Evaluar prioridades
        if priority in ('high', 'medium'):
            return True
            
        if priority == 'low' and cat == '🟡 Chat y Comunicación':
            return gaming_profile.kill_low_chat
            
        # 4. Resto
        return False
