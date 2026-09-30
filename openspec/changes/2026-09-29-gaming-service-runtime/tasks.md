# Tareas OpenSpec: Conectar GamingService al runtime de Gaming Mode (TASK-025)

> Contrato: [`proposal.md`](proposal.md). Orden de ejecución: **1 → 2 → 3 → 4 → 5**.
> Las correcciones marcadas **[OBLIGATORIO 7.x]** invalidan la especificación heredada de
> `openspec/changes/2026-09-29-bugfix-audit-v3/proposal.md:36-44`. No las omitas: sin ellas la tarea
> introduce un vector de brick (`svchost`) y desactiva los `keepers` en silencio.

- [ ] **1. `GamingService.execute_gaming_pack()` — el servicio**
  - [ ] Añadir `execute_gaming_pack(self, gaming_pack: Pack) -> Tuple[int, int, int, float]` en
        `src/woptimizer/services/gaming_service.py`. Importar `Tuple` de `typing`.
  - [ ] **[OBLIGATORIO 7.3]** Snapshot con
        `self.process_service.get_running_processes(force_refresh=True)`. **Nunca** sin `force_refresh`:
        el TTL es de 2 s (`process_service.py:72`) y la doble pulsación tarda ~0,4 s.
  - [ ] **[OBLIGATORIO 7.1]** Barrera de categoría roja **antes** de evaluar nada:
        `permitidas = {c for c in gaming_pack.target_categories if get_safety_badge(c)["tier"] != "danger"}`
        (importar de `woptimizer.config`). Sin esto, `svchost` es un objetivo legítimo
        (`process_db.json:47-48` lo pone en `🔴 Sistema de Windows` y **no** está en
        `SYSTEM_PROTECTED_PROCESSES`).
  - [ ] **[OBLIGATORIO 7.2]** Evaluar contra `p.full_name or p.name`, **nunca** `p.name`.
        `get_running_processes` quita `.exe` del `name` (`process_service.py:235`) y
        `DEFAULT_GAMING_PACK.keepers` son `["steam.exe", "discord.exe"]` (`pack_service.py:14`):
        con `p.name` la comparación por subcadena falla y los keepers dejan de proteger.
  - [ ] Orden de filtros, normativo: (1) `is_system_protected(p.name/full_name)` → `protected++`;
        (2) `get_safety_badge(p.category)["tier"] == "danger"` → `protected++`;
        (3) `not should_kill_for_gaming(nombre, pack)` → descartar; (4) si no, a `to_kill`.
  - [ ] Matar **delegando**: `self.process_service.kill_processes(to_kill)`. Prohibido llamar a
        `psutil` desde este módulo (invariante **G-1**: una sola puerta de kill).
  - [ ] **[OBLIGATORIO 7.6/G-6]** Leer `p.category` del snapshot. No añadir una cuarta llamada a
        un método privado de otro servicio (no replicar el `process_service._categorize` de la
        línea 31).
  - [ ] Retornar `(killed, failed, skipped + protected, freed_mb)`. Agregar `protected` a `skipped`
        para que el descarte sea **visible** en la UI y no silencioso.
  - [ ] `gaming_pack.is_gaming is False` → `ValueError` con mensaje explicativo.
  - [ ] Mismo tipo de retorno 4-tupla que `kill_processes` (`process_service.py:260-264`), para no
        romper el banner (`dashboard_view.py:68-79`) ni los toasts.

- [ ] **2. Cableado de los 3 puntos de entrada**
  - [ ] **Tray** (`ui/app.py:89-107`): sustituir la línea `:97`
        (`kill_pack_apps(gaming_pack.apps)`) por
        `self.gaming_service.execute_gaming_pack(gaming_pack)`. `self.gaming_service` ya existe
        (`app.py:22`): **no hay que inyectar nada aquí**. Mantener el `threading.Thread(daemon=True)`.
  - [ ] **`DashboardView`** (`ui/views/dashboard_view.py`): añadir `gaming_service=None` a
        `__init__` con fallback `GamingService(process_service, pack_service)` — mismo patrón
        defensivo que ya usa `notification_service` (`dashboard_view.py:14`) para no romper
        constructores ni tests existentes.
  - [ ] **[OBLIGATORIO 7.4]** `execute_pack:131-132`: cambiar `if not pack.apps: return` por
        `if not pack.is_gaming and not pack.apps: return`. Con `apps` vacía, un Gaming Mode solo por
        categorías no se ejecuta hoy.
  - [ ] En la rama `kill` de `execute_pack`, si `pack.is_gaming` → `execute_gaming_pack` en
        `threading.Thread(daemon=True)`, con el `self.after(0, self._show_banner, ...)` ya existente.
        `self.after`, **nunca** `self.master.after` (`main_window.py:42-45` destruye la vista en
        toda navegación).
  - [ ] **`PackManagerView`** (`ui/views/pack_manager_view.py`): mismo `gaming_service=None` con
        fallback en `__init__`.
  - [ ] **[OBLIGATORIO 7.4]** `kill_pack:269-272`: mismo relaxation del `if not pack.apps`.
  - [ ] En `kill_pack`, si `pack.is_gaming` → `execute_gaming_pack`. Mantener el **re-fetch del pack
        por id** en la segunda pulsación (`:278`), porque `reset_gaming_pack` reemplaza el objeto por
        un `model_copy` (`pack_service.py:94`).
  - [ ] **`MainWindow`** (`ui/main_window.py`): pasar `self.gaming_service` como 5.° argumento en
        `_show_home` (`:55-60`) y `_show_packs` (`:66-71`). **El briefing daba por hecho que ya
        llegaba a las vistas: no llega** (`main_window.py:15` lo guarda, no lo pasa).
  - [ ] **[OBLIGATORIO 7.5]** Prohibido añadir un método equivalente en `ProcessService`: la política
        de keepers/categorías es de dominio y `GamingService` ya es su dueño. Duplicar la regla
        crearía dos fuentes de verdad para el orden de las reglas.

- [ ] **3. Doble pulsación (Trampa #14)**
  - [ ] Las dos rutas de ventana **conservan** el `_require_double_tap` existente
        (`dashboard_view.py:135-139`, `pack_manager_view.py:273-275`). Solo adaptar el texto a
        Gaming Mode y contar categorías + apps, no solo `len(pack.apps)`.
  - [ ] **[OBLIGATORIO 7.7]** El menú del tray **no** puede pasar por el guard (un `MenuItem` de
        pystray no es widget y no tiene `status_label`; la alternativa sería un diálogo, prohibido
        por Trampa #14). Se mantiene **sin confirmar** — no es una vía nueva, ya mata hoy — y
        queda **documentada como la única excepción** en `docs/ai/ui-design-system.md`.
  - [ ] Invariante que debe dejar el cambio: *ningún camino de kill nuevo puede añadirse sin
        `_require_double_tap`*. Las 3 rutas existentes quedan inventariadas en esa sección.

- [ ] **4. Test headless que discrimina — `test_execute_gaming_pack_integration`**
  - [ ] **Capa A** (la que discrimina; sin matar nada): doble de `ProcessService` que captura la
        `List[ProcessInfo]` que llega a `kill_processes` y devuelve una 4-tupla enlatada;
        `get_running_processes` sustituido por un snapshot fijo. Pack explícito (patrón de
        `run_tests.py:385-396`).
  - [ ] Snapshot y aserciones exactas:

        | Proceso | Categoría | Config | Esperado en la lista capturada |
        |---|---|---|---|
        | `onedrive.exe` | `🟢 Sincronización` | en `target_categories` | **SÍ** |
        | `discord.exe` | `🟡 Chat y Comunicación` | categoría objetivo **y** en `keepers` | **NO** |
        | `chrome.exe` | `⚪ Otros` | solo en `apps` | **SÍ** |
        | `procesoXYZ.exe` | `⚪ Otros` | nada | **NO** |
        | `svchost.exe` | `🔴 Sistema de Windows` | **categoría roja marcada objetivo** | **NO** |
        | `lsass.exe` | `🟢 Productividad` (JSON envenenado) | en `target_categories` | **NO** |

  - [ ] Por qué discrimina: sin el fix, `kill_processes` **no se llama nunca** (se llamaba
        `kill_pack_apps`) → lista vacía → la primera aserción falla. `svchost` falla con el guard
        heredado de `bugfix-audit-v3/proposal.md:40` y pasa con la barrera roja. `discord` falla si
        se usa `p.name` en vez de `p.full_name` — punto ciego que la suite actual **no** cubre
        (`run_tests.py:404, 413, 422` pasan nombres con `.exe`).
  - [ ] Asertar además: la 4-tupla enlatada se devuelve **sin alterar**, con tipos
        `(int, int, int, float)`, y `skipped` incluye los descartes del filtro.
  - [ ] **Capa B** (integración real, guardada): reutilizar el patrón de `test_kill_recursive`
        (`run_tests.py:682-776`): espawnea `[sys.executable, "-c", "import time; time.sleep(120)"]`,
        espera el PID con `_esperar_pid_de_archivo` (`run_tests.py:50-56`) y verifica que el sleeper
        **y su nieto** mueren (invariante de kill recursivo en la ruta nueva). Si `Popen` falla →
        `print("  AVISO: ...")` y `return`, como `run_tests.py:717-719`. **Nunca** nombrar un proceso
        real del sistema en el test.
  - [ ] Sub-chequeo estático con el helper existente `_codigo_ejecutable`
        (`run_tests.py:796-805`): `gaming_service.py` sin `psutil`, y ninguna vista con `psutil` ni
        `import json`.
  - [ ] Registrar el test en el bloque `__main__` de `run_tests.py`.

- [ ] **5. Validación y documentación**
  - [ ] `python verify_ui_syntax.py` en verde.
  - [ ] `python run_tests.py` en verde, incluido `test_no_system_process_is_killable`
        (TASK-024, **no debe regresionar**) y `test_gaming_service_should_kill` (TASK-021).
  - [ ] `docs/ai/architecture.md` → nuevo punto en "Reglas de Arquitectura": la ruta de Gaming Mode,
        sus 6 garantías (G-1..G-6) y la barrera de categoría roja.
  - [ ] `docs/ai/ui-design-system.md` → la excepción documentada del tray y el inventario de los 3
        caminos de kill.
  - [ ] `.taskmaster/CHANGELOG.md` → entrada del pase (regla de `id-pipeline`, Sección 6).
  - [ ] Cierre limpio con `python .taskmaster/git_safe_commit.py` y 0 cambios pendientes.
