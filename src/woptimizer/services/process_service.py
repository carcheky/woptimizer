import psutil
import time
from typing import List, Tuple, Optional, Dict
from woptimizer.models import ProcessInfo
from woptimizer.config import PROCESS_CATEGORIES, CATEGORY_ORDER, logger

_DEFAULT_META = ("? Otros", "none", "Sin descripción")


class ProcessService:
    """Servicio de procesos con hashmap O(1) y cache TTL.

    Optimizaciones (TASK-018):
    - _db_map: dict hashmap en lugar de lista lineal para lookups O(1).
    - _meta_cache: memoize de fuzzy matches para evitar re-escaneos de la DB.
    - _proc_cache + TTL: cache temporal de get_running_processes (2s por defecto).
    """

    def __init__(self):
        # Hashmap O(1): pattern -> (category, priority, description)
        self._db_map: Dict[str, Tuple[str, str, str]] = {}
        # Memoize fuzzy matches: cleaned_name -> (category, priority, description)
        self._meta_cache: Dict[str, Tuple[str, str, str]] = {}
        self.is_db_loaded = False
        # Cache de procesos con TTL
        self._proc_cache: Optional[List[ProcessInfo]] = None
        self._proc_cache_ts: float = 0.0
        self._CACHE_TTL: float = 2.0  # segundos
        self._load_local_db()

    @property
    def process_db(self) -> list:
        """Compatibilidad: devuelve una lista de ProcessInfo desde el hashmap.
        Solo se usa si algún código externo accede a process_db directamente."""
        return [
            ProcessInfo(name=k, full_name=k, pid=0,
                        category=v[0], priority=v[1], description=v[2])
            for k, v in self._db_map.items()
        ]

    def _load_local_db(self):
        """Carga la base de datos local como hashmap {pattern: (cat, prio, desc)}."""
        import json, os
        try:
            from woptimizer.config import _data_dir
            local_path = os.path.join(_data_dir(), "assets", "process_db.json")
            if os.path.exists(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    db_dict = json.load(f)
                    self._db_map = {
                        pattern.lower(): (
                            props.get('category', '? Otros'),
                            props.get('priority', 'none'),
                            props.get('description', 'Sin descripción')
                        )
                        for pattern, props in db_dict.items()
                    }
                    self._meta_cache.clear()
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
        """Lookup O(1) con fallback a fuzzy match cacheado."""
        name_clean = name.lower().replace('.exe', '')

        # Check memoize cache first
        cached = self._meta_cache.get(name_clean)
        if cached is not None:
            return cached

        # O(1) exact match
        hit = self._db_map.get(name_clean)
        if hit:
            self._meta_cache[name_clean] = hit
            return hit

        # Fuzzy: check if any DB pattern is substring of name or vice versa
        for pattern, meta in self._db_map.items():
            if pattern in name_clean or name_clean in pattern:
                self._meta_cache[name_clean] = meta
                return meta

        self._meta_cache[name_clean] = _DEFAULT_META
        return _DEFAULT_META

    def _get_priority(self, category: str) -> str:
        for meta in self._db_map.values():
            if meta[0] == category:
                return meta[1]
        return 'none'

    def _categorize(self, name: str) -> str:
        cat, _, _ = self._get_process_meta(name)
        return cat

    def invalidate_cache(self) -> None:
        """Fuerza el re-escaneo en la próxima llamada a get_running_processes."""
        self._proc_cache = None
        self._proc_cache_ts = 0.0

    def get_running_processes(self, force_refresh: bool = False) -> List[ProcessInfo]:
        """Lista todos los procesos activos usando psutil, ordenados por categoría.

        Incorpora un cache con TTL para evitar re-escaneos costosos
        cuando la UI pide el listado repetidamente en intervalos cortos.
        El TTL por defecto es 2 segundos (configurable vía self._CACHE_TTL).
        Pasar force_refresh=True ignora el cache.
        """
        now = time.monotonic()
        if (not force_refresh
                and self._proc_cache is not None
                and (now - self._proc_cache_ts) < self._CACHE_TTL):
            return self._proc_cache

        result = []
        seen = set()

        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                info = proc.info
                name = info['name']
                if not name:
                    continue

                name_lower = name.lower()
                if name_lower in ('idle', 'system'):
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

        # Guardar en cache
        self._proc_cache = result
        self._proc_cache_ts = time.monotonic()

        return result

    def kill_processes(self, processes: List[ProcessInfo]) -> Tuple[int, int, int, float]:
        """
        Mata una lista de procesos (y sus hijos).
        Retorna (killed, failed, skipped, freed_mb).
        """
        killed = 0
        failed = 0
        skipped = 0
        freed_bytes = 0

        for pinfo in processes:
            try:
                parent = psutil.Process(pinfo.pid)

                # Capturar memoria del padre ANTES de matar
                try:
                    parent_rss = parent.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    parent_rss = 0

                # Obtener hijos y capturar memoria física ANTES de matar
                children_data = []
                try:
                    for child in parent.children(recursive=True):
                        try:
                            c_rss = child.memory_info().rss
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            c_rss = 0
                        children_data.append((child, c_rss))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    children_data = []

                # Matar hijos recursivamente primero (evita procesos huérfanos)
                for child, c_rss in children_data:
                    try:
                        child.kill()
                        freed_bytes += c_rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                # Matar el padre
                parent.kill()
                freed_bytes += parent_rss
                killed += 1

            except psutil.NoSuchProcess:
                # El proceso ya no existe, objetivo cumplido indirectamente
                skipped += 1
            except psutil.AccessDenied:
                logger.warning(f"Access denied killing {pinfo.name}")
                failed += 1

        # Invalidar cache tras matar procesos
        self.invalidate_cache()

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        return killed, failed, skipped, freed_mb

    def kill_pack_apps(self, apps: List[str]) -> Tuple[int, int, int, float]:
        """Mata todos los procesos cuyos nombres o rutas coincidan con la lista apps."""
        if not apps:
            return 0, 0, 0, 0.0

        killed, failed, skipped = 0, 0, 0
        freed_bytes = 0
        apps_lower = [a.lower() for a in apps]

        for proc in psutil.process_iter(['name', 'exe']):
            try:
                info = proc.info
                name = (info.get('name') or '').lower()
                exe = (info.get('exe') or '').lower()

                if name in apps_lower or exe in apps_lower:
                    # Capturar memoria del padre ANTES de matar
                    try:
                        proc_rss = proc.memory_info().rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        proc_rss = 0

                    # Capturar hijos y su memoria ANTES de matar
                    children_data = []
                    try:
                        for child in proc.children(recursive=True):
                            try:
                                c_rss = child.memory_info().rss
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                c_rss = 0
                            children_data.append((child, c_rss))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        children_data = []

                    # Matar hijos recursivamente primero
                    for child, c_rss in children_data:
                        try:
                            child.kill()
                            freed_bytes += c_rss
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    # Matar el padre
                    proc.kill()
                    freed_bytes += proc_rss
                    killed += 1
            except psutil.AccessDenied:
                failed += 1
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                skipped += 1

        # Invalidar cache tras matar procesos
        self.invalidate_cache()

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        return killed, failed, skipped, freed_mb

    def start_pack_apps(self, apps: List[str]) -> Tuple[int, int]:
        """Inicia todas las apps de la lista de forma asíncrona."""
        import subprocess
        started, failed = 0, 0
        for app in apps:
            try:
                subprocess.Popen(app, shell=True)
                started += 1
                logger.info(f"Launched app: {app}")
            except Exception as e:
                failed += 1
                logger.warning(f"Failed to launch app '{app}': {e}")
        return started, failed
