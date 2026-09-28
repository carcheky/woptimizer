import psutil
from typing import List, Tuple
from woptimizer.models import ProcessInfo
from woptimizer.config import PROCESS_CATEGORIES, CATEGORY_ORDER, logger

class ProcessService:
    def __init__(self):
        self.process_db = []
        self.is_db_loaded = False
        self._load_local_db()

    def _load_local_db(self):
        """Carga la base de datos local empaquetada inmediatamente en memoria."""
        import json, os
        try:
            from woptimizer.config import _data_dir
            local_path = os.path.join(_data_dir(), "assets", "process_db.json")
            if os.path.exists(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    db_dict = json.load(f)
                    new_db = []
                    for pattern, props in db_dict.items():
                        new_db.append(ProcessInfo(
                            name=pattern,
                            full_name=pattern,
                            pid=0,
                            category=props.get('category', '? Otros'),
                            priority=props.get('priority', 'none'),
                            description=props.get('description', 'Sin descripción')
                        ))
                    self.process_db = new_db
                    self.is_db_loaded = True
        except Exception as e:
            logger.warning(f"Error cargando DB local: {e}")

    def load_db_async(self, callback=None):
        def _download():
            import json, urllib.request, os
            url = "https://gitlab.com/carcheky/woptimizer/-/raw/main/assets/process_db.json"
            try:
                from woptimizer.config import _data_dir
                assets_dir = os.path.join(_data_dir(), "assets")
            except Exception:
                assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
            
            os.makedirs(assets_dir, exist_ok=True)
            local_path = os.path.join(assets_dir, "process_db.json")
            
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = response.read().decode('utf-8')
                    with open(local_path, "w", encoding="utf-8") as f:
                        f.write(data)
            except Exception as e:
                logger.warning(f"Fallo descargando DB de GitLab: {e}")
                
            # Recargar en memoria
            self._load_local_db()
            
            if callback:
                try:
                    callback()
                except Exception as e:
                    logger.warning(f"Error ejecutando callback de load_db_async: {e}")
                
        import threading
        threading.Thread(target=_download, daemon=True).start()

    def _get_process_meta(self, name: str) -> Tuple[str, str, str]:
        name_clean = name.lower().replace('.exe', '')
        for row in self.process_db:
            pattern = row.name.lower().replace('.exe', '')
            if pattern == name_clean or pattern in name_clean or name_clean in pattern:
                return row.category, row.priority, row.description
        return "? Otros", "none", "Sin descripción"

    def _get_priority(self, category: str) -> str:
        for row in self.process_db:
            if row.category == category:
                return row.priority
        return 'none'

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
                logger.warning(f"Access denied killing {pinfo.name}")
                failed += 1
                
        return killed, failed, skipped

    def kill_pack_apps(self, apps: List[str]) -> Tuple[int, int, int]:
        """Mata todos los procesos cuyos nombres o rutas coincidan con la lista apps."""
        if not apps:
            return 0, 0, 0
            
        killed, failed, skipped = 0, 0, 0
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
                    killed += 1
            except psutil.AccessDenied:
                failed += 1
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                skipped += 1
                
        return killed, failed, skipped

    def start_pack_apps(self, apps: List[str]) -> Tuple[int, int]:
        """Inicia todas las apps de la lista de forma asíncrona."""
        import subprocess
        started, failed = 0, 0
        for app in apps:
            try:
                subprocess.Popen(app, shell=True)
                started += 1
            except Exception:
                failed += 1
        return started, failed


