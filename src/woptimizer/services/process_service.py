import psutil
from typing import List, Tuple
from woptimizer.models import ProcessInfo
from woptimizer.config import PROCESS_CATEGORIES, CATEGORY_ORDER

class ProcessService:
    def _get_priority(self, category: str) -> str:
        return PROCESS_CATEGORIES.get(category, {}).get('priority', 'none')

    def _categorize(self, name: str) -> str:
        name_lower = name.lower()
        for cat, data in PROCESS_CATEGORIES.items():
            for pattern in data['patterns']:
                if pattern in name_lower:
                    return cat
        return "⚪ Otros"

    def get_running_processes(self) -> List[ProcessInfo]:
        """Lista todos los procesos activos usando psutil, ordenados por categoría."""
        result = []
        seen = set()
        
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                info = proc.info
                name = info['name']
                if not name:
                    continue
                    
                name_lower = name.lower()
                if name_lower in ['idle', 'system']:
                    continue
                    
                pid = info['pid']
                if (name_lower, pid) in seen:
                    continue
                seen.add((name_lower, pid))

                clean_name = name.replace('.exe', '')
                cat = self._categorize(clean_name)
                
                result.append(ProcessInfo(
                    name=clean_name,
                    full_name=name,
                    pid=pid,
                    exe_path=info['exe'] or "",
                    category=cat,
                    priority=self._get_priority(cat)
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        # Ordenar por el orden definido en CATEGORY_ORDER, luego alfabético, luego PID
        cat_idx = {c: i for i, c in enumerate(CATEGORY_ORDER)}
        result.sort(key=lambda p: (cat_idx.get(p.category, 999), p.name.lower(), p.pid))
        
        return result

    def kill_processes(self, processes: List[ProcessInfo]) -> Tuple[int, int, int]:
        """
        Mata una lista de procesos (y sus hijos).
        Retorna (killed, failed, skipped).
        """
        killed = 0
        failed = 0
        skipped = 0
        
        for pinfo in processes:
            try:
                parent = psutil.Process(pinfo.pid)
                
                # Matar hijos recursivamente primero (evita procesos huérfanos)
                for child in parent.children(recursive=True):
                    try:
                        child.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Matar el padre
                parent.kill()
                killed += 1
                
            except psutil.NoSuchProcess:
                # El proceso ya no existe, objetivo cumplido indirectamente
                skipped += 1
            except psutil.AccessDenied:
                # Requiere admin u otro permiso
                failed += 1
                
        return killed, failed, skipped

