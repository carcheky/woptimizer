# Propuesta: Conectar `GamingService` al runtime de ejecución de Gaming Mode (FIX-002 + FIX-008)

- **Change ID**: `2026-09-29-gaming-service-runtime`
- **Ciclo**: #14
- **Área de rotación**: 2 — Gaming & Telemetría UX (retorno; sin tocar desde el ciclo #12)
- **Taskmaster**: `TASK-025`
- **Subagente de ejecución**: `openspec-dev`
- **Estado**: AUDITADA por architect-review — **aprobada con correcciones obligatorias** (ver §7)

## 1. Problema confirmado en el código

`GamingService.should_kill_for_gaming()` existe y está testeado
(`run_tests.py:368-439`, `test_gaming_service_should_kill`), pero **nunca se invoca en runtime**.
Las tres rutas de Gaming Mode hacen exactamente lo mismo y todas ignoran `keepers` y
`target_categories`:

| Punto de entrada | Código actual | Qué ignora |
|---|---|---|
| Menú del tray | `ui/app.py:97` → `self.process_service.kill_pack_apps(gaming_pack.apps)` | keepers, categorías |
| Portada (botón favorito) | `ui/views/dashboard_view.py:142` → `kill_pack_apps(p.apps)` | keepers, categorías |
| Gestor de Packs (⛔ Apagar) | `ui/views/pack_manager_view.py:285` → `kill_pack_apps(apps)` | keepers, categorías |

Consecuencia: `keepers` y `target_categories` son **configuración muerta**. El usuario marca
"🟢 Sincronización" y "🟡 Chat y Comunicación" en el acordeón de categorías
(`pack_manager_view.py:143-200`) y el motor nunca lo consulta. Es la promesa central del producto
y está desconectada.

**Precisión sobre el briefing**: `GamingService` sí se inyecta en `WOptimizerApp` (`app.py:22`) y en
`MainWindow` (`main_window.py:15`), pero **`MainWindow` nunca se lo pasa a las vistas**
(`main_window.py:55-60` y `:66-71` solo pasan `process_service`, `pack_service` y
`notification_service`). El campo existe y está muerto en dos niveles.

## 2. Falso positivo del guard de seguridad heredado

La spec de auditoría (`bugfix-audit-v3/proposal.md:23` y `:40`) prescribe:

> "Filtrar aquellos donde `should_kill_for_gaming(...)` sea `True` y **NO pertenezcan a
> `SYSTEM_PROTECTED_PROCESSES`**"

**Ese guard es insuficiente y abre una vía de brick.** Evidencia:

- `svchost` y `explorer` están en `assets/process_db.json:47-54` con categoría
  `🔴 Sistema de Windows`, y **no** figuran en `SYSTEM_PROTECTED_PROCESSES`
  (`process_service.py:23-38`). El propio `test_no_system_process_is_killable` los vigila
  (`run_tests.py:1117-1120`) pero solo para la capa de la DB, no para el kill.
- La categoría `🔴 Sistema de Windows` se ofrece **como casilla activable** en el acordeón de
  `pack_manager_view.py:171-178` (sale de `process_service.process_db`).
- Con esa casilla marcada, la ruta por categoría seleccionaría **todos los `svchost.exe`** y
  `kill_processes` los mataría: `is_system_protected('svchost')` es `False`
  (`process_service.py:91`), así que el blindaje de nombre no lo detiene.

Matar todos los `svchost.exe` deja Windows inservible. **El blacklist de nombres no es una garantía
suficiente para una evaluación por categoría**: depende de que alguien se acuerde de añadir cada
nombre nuevo. Hace falta una **barrera de categoría** (§4.2, G-2).

## 3. Segundo fallo silencioso: el nombre sin extensión rompe keepers y apps

`should_kill_for_gaming` hace *substring* en ambos sentidos
(`gaming_service.py:23` y `:28`): `if keeper.lower() in name_lower`.

| Fuente | Valor |
|---|---|
| `DEFAULT_GAMING_PACK.keepers` | `["steam.exe", "discord.exe"]` (`pack_service.py:14`) |
| `DEFAULT_GAMING_PACK.apps` | `["chrome.exe"]` (`pack_service.py:13`) |
| `get_running_processes` | `name = name.replace('.exe','')` → `"discord"`; `full_name` conserva `"discord.exe"` (`process_service.py:235-240`) |

Si `execute_gaming_pack` pasa `p.name`, `"discord.exe" in "discord"` es **False**: la regla 1
(keeper) y la regla 2 (apps explícitas) **mueren en silencio**. `steam.exe` y `discord.exe` se
matarían, y `chrome.exe` dejaría de cerrarse.

`test_gaming_service_should_kill` **no lo detecta**: sus 4 aserciones pasan nombres con `.exe`
(`run_tests.py:404, 413, 422, 436`). Es un punto ciego real de la suite.

**Obligatorio**: evaluar siempre contra `p.full_name or p.name`.

## 4. Especificación de `execute_gaming_pack`

### 4.1 Firma y ubicación

```python
# src/woptimizer/services/gaming_service.py
def execute_gaming_pack(self, gaming_pack: Pack) -> Tuple[int, int, int, float]:
    """Ejecuta el Gaming Mode. Retorna (killed, failed, skipped, freed_mb)."""
```

- Vive **entera** en `services/`. La UI no lee procesos, ni decide categorías, ni calcula PIDs.
- `gaming_pack.is_gaming is False` → `ValueError` (uso indebido; las 3 vistas ya envuelven en
  `try/except` y registran).
- Retorna la **misma 4-tupla** que `kill_processes` / `kill_pack_apps`
  (`process_service.py:260-264`, `architecture.md` §5), para no romper el contrato del banner
  (`dashboard_view.py:68-79`) ni de los toasts.

### 4.2 Algoritmo (el orden de las reglas es normativo)

```
G0  snapshot = process_service.get_running_processes(force_refresh=True)   # NUNCA sin forzar
G1  categorias_permitidas = {c for c in gaming_pack.target_categories
                             if get_safety_badge(c)["tier"] != "danger"}  # barrera roja
G2  for p in snapshot:
G3      nombre = p.full_name or p.name            # con .exe (ver §3)
G4      if is_system_protected(p.name) or is_system_protected(p.full_name): -> protected += 1; skip
G5      if get_safety_badge(p.category)["tier"] == "danger":              -> protected += 1; skip
G6      if not should_kill_for_gaming(nombre, gaming_pack):               -> seguir
G7      to_kill.append(p)
G8  killed, failed, skipped, freed_mb = process_service.kill_processes(to_kill)
G9  return (killed, failed, skipped + protected, freed_mb)
```

**`force_refresh=True` es obligatorio** (`process_service.py:202-214`): la cache TTL es de 2 s y el
doble pulsación tarda ~0,4 s, así que un snapshot cacheado de la exploración que el usuario acaba de
hacer en el Gestor de Procesos dejaría fuera procesos recién lanzados. No es un problema de
seguridad sino de efficacy, pero es la diferencia entre que la feature sirva y no.

### 4.3 Garantías de seguridad explícitas

| # | Garantía | Cómo se hace cumplir |
|---|---|---|
| **G-1** | **Una sola puerta de kill.** `execute_gaming_pack` no puede abrir una vía al SO que las otras no tengan. | No llama `psutil` en ningún punto; delega íntegro en `kill_processes`, que ya aplica `is_system_protected` (`process_service.py:275`). Invariante verificable por grep: `psutil` no aparece en `gaming_service.py`. |
| **G-2** | **Barrera de categoría roja.** Una categoría `🔴` en `target_categories` es inerte, sea cual sea el nombre. | `get_safety_badge(c)["tier"] == "danger"` (`config.py:98-116`) filtra `target_categories` **antes** de evaluar, y `G5` vuelve a filtrar por la categoría del proceso. Capa independiente del blacklist de nombres: cubre `svchost`/`explorer` y cualquier nombre futuro. |
| **G-3** | **Keeper gana a todo**, incluido `apps`. | Regla 1 de `should_kill_for_gaming`, ya implementada y testeada; se conserva sin reordenar. |
| **G-4** | **Recursión.** Hijos antes que padre. | Heredado de `kill_processes` (`process_service.py:290-308`). No reimplementar el bucle de kill en `gaming_service.py`. |
| **G-5** | **Cache invalidada tras el kill.** | `kill_processes` llama a `invalidate_cache()` (`process_service.py:320`). No hace falta añadir nada. |
| **G-6** | **Sin acoplamiento privado.** | Leer `p.category` del snapshot. No añadir una cuarta llamada a un método privado de otro servicio (`gaming_service.py:31` ya usa `process_service._categorize`; no replicarlo). |

`skipped` en la tupla de retorno **agrega** los descartes del propio filtro (`protected`) y los de
`kill_processes`. Es lo que hace visible en la UI que algo se protegió, en vez de silenciarlo.

## 5. Los tres puntos de entrada

**Decisión: inyectar `GamingService` en las vistas. NO añadir el método a `ProcessService`.**

Justificación contra la separación de capas (`AGENTS.md:47`, `architecture.md` §Invariante de 3
Capas): `ProcessService` es el adaptador de `psutil`; meterlo en él obligaría a la capa de
sistema a conocer el modelo `Pack` y la política de keepers, que es dominio. Además `GamingService`
ya existe, ya se construye en `__main__.py:19` y ya es el dueño de `should_kill_for_gaming`;
duplicar la regla en `ProcessService` crearía dos fuentes de verdad para el orden de las reglas.

| Punto de entrada | ¿Inyección? | Cambio |
|---|---|---|
| `WOptimizerApp.show_tray → gaming_action` (`app.py:89-107`) | **No.** Ya tiene `self.gaming_service` (`app.py:22`). | Sustituir la línea `:97`. |
| `DashboardView` (`dashboard_view.py:130-148`) | **Sí.** Nuevo `gaming_service=None` en `__init__`, con fallback `GamingService(process_service, pack_service)` — mismo patrón defensivo que ya usa `notification_service` (`dashboard_view.py:14`, `main_window.py:18`) para no romper constructores y tests existentes. | Rama `kill` → `execute_gaming_pack` si `pack.is_gaming`. |
| `PackManagerView` (`pack_manager_view.py:263-288`) | **Sí.** Mismo fallback defensivo. | `kill_pack` → `execute_gaming_pack` si `pack.is_gaming`. |
| `MainWindow._show_home` / `_show_packs` (`main_window.py:55-71`) | — | Pasar `self.gaming_service` como 5.° argumento. |

### 5.1 Dos `return` mudos que bloquean la feature (no estaban en el briefing)

- `dashboard_view.py:131-132` → `if not pack.apps: return`
- `pack_manager_view.py:269-272` → `if not pack.apps:` + aviso "no tiene apps que apagar"

Con `apps` vacía, un Gaming Mode válido (solo categorías) **no se ejecuta**. Corregir ambos a
`if not pack.is_gaming and not pack.apps`.

### 5.2 Confirmación (Trampa #14) — la única decisión de criterio

Las **dos rutas dentro de la ventana** pasan por el **mismo** `_require_double_tap` que ya existe
(Dashboard `dashboard_view.py:135-139`, Packs `pack_manager_view.py:273-275`). No hay que
inventar nada: solo adaptar el texto a Gaming Mode y **re-fetch del pack por id** en la segunda
pulsación (`reset_gaming_pack` reemplaza el objeto por un `model_copy`, `pack_service.py:94`).

**El menú del tray no puede pasar por el guard** y sigue **sin confirmar**. No es una vía nueva:
ya mata hoy sin confirmar (`app.py:89-107`). Y no *puede* recibir doble pulsación: un
`MenuItem` de pystray no es un widget, no tiene `status_label` donde explicar nada, y la única
alternativa sería un diálogo, que Trampa #14 prohíbe explícitamente
(`ui/confirmation.py:5-13`, y `bugfix-audit-v3/proposal.md:26`).

La objeción real a la doble pulsación (clic en el objetivo equivocado por adyacencia, ver
`bugfix-audit-v3/proposal.md:170-184`) **no aplica aquí**: un ítem de menú es una única entrada,
con nombre explícito, sin vecinos ni selección que fallar. Aun así, con categorías activas el radio
de impacto crece, así que **esta excepción queda escrita en `docs/ai/ui-design-system.md`**, no
implícita.

**Invariante que debe dejar el cambio**: *ningún camino de kill nuevo puede añadirse sin
`_require_double_tap`*. Las tres rutas existentes quedan inventariadas; el guard es la única puerta
dentro de la ventana y el tray es la única excepción documentada.

### 5.3 Threading

El kill va en `threading.Thread(target=..., daemon=True)`, igual que hoy. La UI **solo** se toca
con `self.after(0, ...)` (nunca `self.master.after` — `main_window.py:42-45` destruye la vista en
**toda** navegación y `master` es `content_frame`, que sobrevive). En el tray no hay `after`: solo
`logger` + `notification_service`, ambos seguros desde cualquier hilo.

## 6. Test headless que discrimina

Nombre: **`test_execute_gaming_pack_integration`**, en `run_tests.py`. Dos capas.

### Capa A — el test que discrimina de verdad (sin matar nada del sistema)

Doble de `ProcessService` que registra la `List[ProcessInfo]` que llega a `kill_processes` y
devuelve una 4-tupla enlatada, con `get_running_processes` sustituido por un snapshot fijo. Pack
explícito (patrón de `test_gaming_service_should_kill`, `run_tests.py:385-396`).

Snapshot de entrada:

| Proceso | Categoría | Config | **Esperado en la lista capturada** |
|---|---|---|---|
| `onedrive.exe` | `🟢 Sincronización` | en `target_categories` | **SÍ** |
| `discord.exe` | `🟡 Chat y Comunicación` | categoría objetivo **y** en `keepers` | **NO** |
| `chrome.exe` | `⚪ Otros` | solo en `apps` | **SÍ** |
| `procesoXYZ.exe` | `⚪ Otros` | nada | **NO** |
| `svchost.exe` | `🔴 Sistema de Windows` | **categoría roja marcada como objetivo** | **NO** ← mata la implementación ingenua |
| `lsass.exe` | `🟢 Productividad` (JSON envenenado) | en `target_categories` | **NO** |

Por qué discrimina:
- Sin el fix, `kill_processes` **no se llama nunca** (se llamaba `kill_pack_apps`), así que la
  lista capturada está vacía y la primera aserción ya falla. No es un test que "devuelve un int".
- `svchost` con la categoría roja marcada **falla** con el guard de `bugfix-audit-v3/proposal.md:40`
  y pasa con la barrera G-2. Es el test que protege contra el brick.
- `discord` con su categoría objetivo **falla** si se usa `p.name` en vez de `p.full_name` (§3) y
  si se pierde la precedencia del keeper. Cubre el punto ciego de §3 que la suite actual no ve.
- Asertar también: la 4-tupla enlatada se devuelve **sin alterar** y con los tipos correctos
  (`int,int,int,float`), y `skipped` incluye los descartes del filtro.

### Capa B — integración real contra la vía de kill (guardada)

Reutiliza el patrón de `test_kill_recursive` (`run_tests.py:682-776`): espawnea
`[sys.executable, "-c", "import time; time.sleep(120)"]`, espera el PID, y verifica que tras
`execute_gaming_pack` el sleeper **y su nieto** mueren. Si `subprocess.Popen` falla →
`print("  AVISO: ...")` y `return`, exactamente como `run_tests.py:717-719` (degradado, no falso
verde). Prueban por qué se snipería el `_esperar_pid_de_archivo` en vez de `children(recursive=True)`
(`run_tests.py:50-56`): en Windows ese listado devuelve también `conhost.exe` y el test no
discriminaría.

Ningún proceso real del sistema se nombra jamás en el test.

### Sub-chequeo estático (barato, con helper existente)

Con `_codigo_ejecutable` (`run_tests.py:796-805`, que quita comentarios y docstrings para que solo
pueda dispararse código **ejecutado**): `gaming_service.py` no contiene `psutil`, y ninguna vista
contiene `psutil` ni `import json`. Congela la separación de capas contra regresiones futuras.

## 7. Correcciones obligatorias respecto a la especificación heredada

| # | Corrección | Origen |
|---|---|---|
| 7.1 | El guard "`NO` en `SYSTEM_PROTECTED_PROCESSES`" **no basta**: añadir la barrera de categoría roja G-2. Sin ella, `svchost` es un objetivo legítimo de la ruta por categoría. | §2 |
| 7.2 | Evaluar contra `p.full_name or p.name`, **nunca** `p.name`: si no, keepers y apps dejan de funcionar en silencio. | §3 |
| 7.3 | `get_running_processes(force_refresh=True)` es obligatorio (TTL 2 s). | §4.2 |
| 7.4 | Levantar los dos `if not pack.apps: return` para que un Gaming Mode sin apps manuales funcione. | §5.1 |
| 7.5 | La inyección es de `GamingService`, **no** un método nuevo en `ProcessService`. | §5 |
| 7.6 | El menú del tray queda documentado como la **única** ruta de kill sin doble pulsación, con su justificación; las dos vistas pasan por el guard existente. | §5.2 |
| 7.7 | El briefing daba a entender que `GamingService` ya llegaba a las vistas: **no llega**. Hay que tocar también `MainWindow._show_home` y `_show_packs`. | §1 |

## 8. Criterios de aceptación

- [ ] `GamingService.execute_gaming_pack(pack: Pack) -> Tuple[int, int, int, float]` existe y vive
      entero en `services/gaming_service.py`, sin `psutil` ni `json`.
- [ ] Las 3 rutas invocan `execute_gaming_pack` cuando `pack.is_gaming`; `kill_pack_apps` solo queda
      para packs de usuario.
- [ ] La evaluación usa `full_name or name`: un keeper con extensión (`discord.exe`) protege de
      verdad.
- [ ] Una categoría `🔴` en `target_categories` no produce candidatos, y `svchost.exe` bajo
      `🔴 Sistema de Windows` **nunca** llega a `kill_processes`.
- [ ] `SYSTEM_PROTECTED_PROCESSES` sigue sin tocarse (TASK-024) y el blindaje de las tres vías sigue
      en pie.
- [ ] El kill recursivo se preserva (hijos antes que padre) en la ruta nueva.
- [ ] El cache TTL se invalida tras el kill.
- [ ] `execute_pack` y `kill_pack` funcionan con `pack.apps` vacía si `is_gaming`.
- [ ] Las dos rutas de ventana pasan por `_require_double_tap`; el tray es la única excepción
      documentada.
- [ ] `self.after` y nunca `self.master.after` en los `after(0, ...)` de resultado.
- [ ] `test_execute_gaming_pack_integration` (capa A + capa B) en `run_tests.py`, discrimina sin el
      fix y está registrado en el `__main__`.
- [ ] `python verify_ui_syntax.py` y `python run_tests.py` en verde.
- [ ] `docs/ai/architecture.md` y `docs/ai/ui-design-system.md` actualizados (regla de
      documentación viva de `AGENTS.md`).
- [ ] Cierre limpio: 0 cambios pendientes.

## 9. Riesgo

**Alto**, y dominado por seguridad, no por técnica. Sin las correcciones 7.1 y 7.2 la feature
introduciría un vector de brick real (`svchost`) y desactivaría en silencio la protección de keepers
— el usuario configuraría Steam y Discord como keepers y ambos morirían. Con ellas, el cambio es
pequeño, localizado en un método nuevo de servicio y cuatro call-sites, y totalmente reversible
porque no toca `SYSTEM_PROTECTED_PROCESSES` ni el modelo de datos.
