import threading
from typing import List, Tuple
from woptimizer.config import get_safety_badge
from woptimizer.models import ProcessInfo, Pack
from woptimizer.services.process_service import ProcessService
from woptimizer.services.pack_service import PackService

class GamingService:
    def __init__(self, process_service: ProcessService, pack_service: PackService):
        self.process_service = process_service
        self.pack_service = pack_service
        self._lock = threading.RLock()
        self._last_closed_apps: List[str] = []

    def get_last_closed_apps(self) -> List[str]:
        """Retorna una copia de la lista de ejecutables pendientes de restauración."""
        with self._lock:
            return list(self._last_closed_apps)

    def clear_last_closed_apps(self) -> None:
        """Limpia la lista de ejecutables almacenados en la sesión actual."""
        with self._lock:
            self._last_closed_apps = []

    def restore_gaming_session(self) -> Tuple[int, int]:
        """Reabre las aplicaciones cerradas en la última sesión de Modo Gaming.

        Invoca ProcessService.start_pack_apps, vacía el historial y retorna (started, failed).
        """
        with self._lock:
            apps_to_restore = list(self._last_closed_apps)
            self._last_closed_apps = []
        if not apps_to_restore:
            return 0, 0
        try:
            return self.process_service.start_pack_apps(apps_to_restore)
        except Exception:
            with self._lock:
                for app in reversed(apps_to_restore):
                    if app not in self._last_closed_apps:
                        self._last_closed_apps.insert(0, app)
            raise

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

    # ------------------------------------------------------------------
    # TASK-063: LA PUERTA UNICA DE APAGADO POR PACK
    # ------------------------------------------------------------------
    # Por que esto vive en una puerta y no en cada llamante: la barrera anti-brick
    # (categoria roja) estaba PEGADA a `execute_gaming_pack`, que ademas RECHAZA
    # los packs que no son de Gaming Mode. Ampliar el consumo de categorias sin
    # mover la barrera dentro de una puerta comun es exactamente el ladrillo del
    # ciclo #14 (svchost seleccionable). Aqui las barreras son la RAZON de que
    # exista la puerta, no una copia por llamante: un llamante nuevo no puede
    # saltarselas porque no las tiene.
    def _pack_evaluable(self, pack: Pack) -> Pack:
        """Copia del pack con las dos listas ya depuradas. NUNCA el original.

        G1 - barrera de categoria roja sobre `target_categories`: una categoria
        roja marcada como objetivo es INERTE, sea cual sea el nombre. Se filtra
        una copia del pack, nunca el original: el orden de reglas de
        `should_kill_for_gaming` (keeper > apps > categorias) se conserva intacto
        y el `profiles.json` del usuario nunca se ve tocado por un filtro.

        El conflicto `start_categories INTERSECT target_categories` se resuelve
        AQUI y no en la UI, porque un `profiles.json` escrito a mano puede traerlo:
        gana la accion cuyo fallo es IRREVERSIBLE, que es apagar (arrancar, como
        mucho, abre una ventana que el usuario cierra). La categoria se queda en
        `target_categories` y sale de `start_categories`.

        El filtro es el MISMO predicado en las dos listas y en las dos puertas
        (`tier != "danger"`), para que no exista una categoria que se pueda apagar
        y no arrancar por un criterio distinto del suyo.
        """
        categorias_permitidas = sorted(
            c for c in pack.target_categories
            if get_safety_badge(c)["tier"] != "danger"
        )
        arranco_permitidas = sorted(
            c for c in pack.start_categories
            if (get_safety_badge(c)["tier"] != "danger"
                and c not in categorias_permitidas)
        )
        return pack.model_copy(update={
            "target_categories": categorias_permitidas,
            "start_categories": arranco_permitidas,
        })

    def _seleccion(self, pack: Pack, snapshot: List[ProcessInfo]) -> Tuple[List[ProcessInfo], int]:
        """`(a_apagar, protegidos)` de UN snapshot, con TODAS las barreras.

        Es el unico sitio donde se decide que proceso cae. Lo comparten
        `execute_pack` (que mata) y `cuenta_a_apagar` (que solo cuenta para el
        texto de la doble pulsacion): duplicar el filtro en la vista para
        escribir el texto de confirmacion seria una segunda politica de
        seguridad, que es lo que este modulo existe para evitar.

        Las garantias (spec 4.2/4.3), en orden y sin reordenar:
          G2  recorrido del snapshot
          G3  el nombre se evalua SIEMPRE con la extension (`full_name`).
              Los keepers y las apps explicitas se guardan como "discord.exe"
              mientras que `name` llega sin extension ("discord"): evaluar con
              `name` haria que los keepers y las apps murieran en silencio.
          G4  blindaje de nombres de TASK-024 (`is_system_protected`).
          G5  segunda barrera de categoria roja, sobre la categoria del propio
              proceso. Es una capa INDEPENDIENTE del blacklist de nombres y por
              eso cubre `svchost`/`explorer` y cualquier nombre futuro.
          G6  politica de keepers > apps > categorias, sin reordenar reglas.
        """
        pack_evaluable = self._pack_evaluable(pack)

        to_kill: List[ProcessInfo] = []
        protected = 0
        for p in snapshot:
            # G4 - blindaje de nombres de TASK-024 (lsass, dwm, services, ...).
            # Se llama alstaticmethod de la clase, no al servicio inyectado: es
            # metodo publico y asi el filtro no depende del doble que se inyecte.
            if (ProcessService.is_system_protected(p.name)
                    or ProcessService.is_system_protected(p.full_name)):
                protected += 1
                continue
            # G5 - segunda barrera, sobre la categoria que trae el snapshot.
            if get_safety_badge(p.category)["tier"] == "danger":
                protected += 1
                continue
            # G3 - con la extension, nunca `name` a solas.
            nombre = p.full_name or p.name
            # G6 - la politica de keepers/apps/categorias ya vive, y testada, en
            # `self.should_kill_for_gaming`. No se reordena ni se reimplementa aqui.
            if not self.should_kill_for_gaming(nombre, pack_evaluable):
                continue
            to_kill.append(p)
        return to_kill, protected

    def execute_pack(self, pack: Pack) -> Tuple[int, int, int, float]:
        """Apaga lo que el pack dice. Retorna (killed, failed, skipped, freed_mb).

        Es la UNICA puerta de apagado por pack del producto (tray, portada y
        gestor de packs entran aqui) y no abre ninguna via al sistema operativo
        que las otras no tengan: toda la matanza se delega en
        `ProcessService.kill_processes`, que ya aplica el blindaje de nombres,
        el kill recursivo (hijos antes que padre) y la invalidacion de cache.
        Por eso este modulo no importa el adaptador de procesos ni el de disco:
        la separacion de capas es un invariante verificable con grep.

        Acepta CUALQUIER pack, con o sin `is_gaming`: el Gaming Mode es un preset
        de esta puerta, no una puerta aparte. Lo que define el apagado son las
        listas del pack (`apps`, `keepers`, `target_categories`), y las barreras
        son de la PUERTA, no del preset.

        Garantias, en orden y sin reordenar:
          G0  snapshot forzado: la cache tiene TTL de 2 s y la doble pulsacion
              tarda ~0,4 s, asi que un snapshot cacheado dejaria fuera procesos
              recien lanzados. Es eficacia, no seguridad.
          G1  barrera de categoria roja sobre las dos listas, en `_pack_evaluable`
              (que ademas resuelve el conflicto `start` vs `target` a favor de
              apagar) y con el filtro de la copia, nunca del original.
          G2..G6  en `_seleccion`, el unico sitio que decide que proceso cae.
          G7  se acumulan los candidatos
          G8  unica llamada a la via de kill
          G9  `skipped` suma los descartes del filtro a los de la via de kill,
              para que la UI vea lo protegido en vez de silenciarlo.
        """
        # G0 - snapshot forzado. Sin esto la cache TTL de 2 s puede dejar fuera
        # lo que el usuario acaba de lanzar (no es un problema de seguridad).
        snapshot = self.process_service.get_running_processes(force_refresh=True)

        # G7 - la seleccion, con las barreras DENTRO de la puerta.
        to_kill, protected = self._seleccion(pack, snapshot)

        # TASK-038: Resolver exe_path ANTES de kill_processes (mientras el proceso
        # aún vive) para que el boton de restauracion tenga rutas de verdad.
        #
        # TASK-063 (H1) Y ESTE BLOQUE ES CONDICIONAL A `pack.is_gaming`, y no es
        # cosmetico: `_last_closed_apps` es la lista de la sesion GAMING, la que
        # consume y VACIA `restore_gaming_session()` (arriba) y la que enciende el
        # banner "Restaurar Apps Cerradas" de la Portada. Con `execute_pack` como
        # puerta comun, apagar un pack NORMAL con categorias escribia aqui y:
        #   (a) encendia un banner fantasma (no hay sesion Gaming que restaurar), y
        #   (b) si el usuario lo pulsaba, `restore_gaming_session()` vaciaba la
        #       lista ANTES de arrancar y se COMIA una restauracion Gaming
        #       pendiente de verdad: perdida de sesion, la misma clase que ya pago
        #       el `model_copy()` shallow del ciclo #10 y el `save()` que machacaba
        #       el `.bak` del ciclo #15.
        # Un pack que no es de Gaming Mode no deja sesion que restaurar.
        if pack.is_gaming:
            closed_paths: List[str] = []
            for p in to_kill:
                exe = p.exe_path or self.process_service.get_process_exe_path(p.pid)
                if exe and isinstance(exe, str):
                    exe_clean = exe.strip()
                    if exe_clean and exe_clean not in closed_paths:
                        closed_paths.append(exe_clean)
            with self._lock:
                self._last_closed_apps = closed_paths

        # G8 - la unica llamada a la via de kill (G-4 y G-5 heredados).
        killed, failed, skipped, freed_mb = self.process_service.kill_processes(to_kill)
        return killed, failed, skipped + protected, freed_mb

    def cuenta_a_apagar(self, pack: Pack) -> int:
        """Cuantos procesos apagaria AHORA `execute_pack(pack)`. No mata nada.

        Es el numero que la doble pulsacion escribe. Sale del MISMO filtro que
        mata, con la misma cache de 2 s que tiene el resto de la UI, y por eso no
        es una segunda politica: si el snapshot cambia entre el texto y la
        pulsacion, el texto queda viejo, que es un detalle; lo que no puede pasar
        es que el texto diga una cifra de otra lista.
        """
        snapshot = self.process_service.get_running_processes()
        to_kill, _ = self._seleccion(pack, snapshot)
        return len(to_kill)

    # ------------------------------------------------------------------
    # FIX-002 + FIX-008: runtime del Gaming Mode (task TASK-025)
    # ------------------------------------------------------------------
    def execute_gaming_pack(self, gaming_pack: Pack) -> Tuple[int, int, int, float]:
        """Ejecuta el Gaming Mode. Retorna (killed, failed, skipped, freed_mb).

        TASK-063: wrapper de compatibilidad, NO una segunda puerta. Se conserva
        porque `ui/app.py:119` lo sigue usando a proposito (su item de menu es
        "Preparar Gaming Mode" y lee `get_all_packs().get("gaming")` por
        construccion) y porque el contrato de este metodo es "solo Gaming Mode"
        sigue siendo verdad: un pack normal que entre aqui por error es un bug de
        cableado, no una llamada legitima, y por eso sigue levantando `ValueError`
        en vez de apagarse en silencio.
        """
        if not gaming_pack.is_gaming:
            raise ValueError(
                "execute_gaming_pack requiere un pack de Gaming Mode "
                f"(is_gaming=True); recibido: {getattr(gaming_pack, 'id', '?')!r}"
            )
        return self.execute_pack(gaming_pack)
