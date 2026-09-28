import psutil
from typing import List, Tuple
from woptimizer.models import ProcessInfo
from woptimizer.config import PROCESS_CATEGORIES, CATEGORY_ORDER

class ProcessService:
    def __init__(self):
        self.process_db = []
        self.is_db_loaded = False
        
    def load_csv_db_async(self, callback=None):
        def _download():
            import csv, urllib.request, os, threading
            url = "https://raw.githubusercontent.com/carch/woptimizer/main/assets/fallback.csv"
            # _app_dir is better, but since it's in services, we use relative to __file__
            try:
                from woptimizer.config import _app_dir
                assets_dir = os.path.join(_app_dir(), "assets")
            except Exception:
                assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
            
            fallback_path = os.path.join(assets_dir, "fallback.csv")
            
            db_temp = []
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    lines = [l.decode('utf-8') for l in response.readlines()]
                    reader = csv.DictReader(lines)
                    for row in reader:
                        db_temp.append(row)
            except Exception:
                if os.path.exists(fallback_path):
                    try:
                        with open(fallback_path, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                db_temp.append(row)
                    except Exception:
                        pass
                        
            self.process_db = db_temp
            self.is_db_loaded = True
            
            if callback:
                callback()
                
        import threading
        threading.Thread(target=_download, daemon=True).start()

    def _get_process_meta(self, name: str) -> Tuple[str, str, str]:
        name_lower = name.lower()
        for row in self.process_db:
            if row.get('pattern', '').lower() in name_lower:
                return row.get('category', '⚪ Otros'), row.get('priority', 'none'), row.get('description', 'Sin descripción')
                
        for cat, data in PROCESS_CATEGORIES.items():
            for pattern in data['patterns']:
                if pattern in name_lower:
                    return cat, data.get('priority', 'none'), data.get('description', 'Sin descripción')
                    
        return "⚪ Otros", "none", "Sin descripción"

    def _get_priority(self, category: str) -> str:
        return PROCESS_CATEGORIES.get(category, {}).get('priority', 'none')

    def _categorize(self, name: str) -> str:
        cat, _, _ = self._get_process_meta(name)
        return cat

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
                cat, priority, desc = self._get_process_meta(clean_name)
                
                result.append(ProcessInfo(
                    name=clean_name,
                    full_name=name,
                    pid=pid,
                    exe_path=info['exe'] or "",
                    category=cat,
                    priority=priority,
                    description=desc
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

    def kill_pack_apps(self, apps: List[str]) -> None:
        """Mata todos los procesos cuyos nombres o rutas coincidan con la lista apps."""
        if not apps:
            return
            
        apps_lower = [a.lower() for a in apps]
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                info = proc.info
                name = (info.get('name') or '').lower()
                exe = (info.get('exe') or '').lower()
                
                if name in apps_lower or exe in apps_lower:
                    for child in proc.children(recursive=True):
                        try:
                            child.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    def start_pack_apps(self, apps: List[str]) -> None:
        """Inicia todas las apps de la lista de forma asíncrona."""
        import subprocess
        for app in apps:
            try:
                subprocess.Popen(app, shell=True)
            except Exception:
                pass


