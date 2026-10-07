# Aplicaciones protegidas: un pack que no se ejecuta y cuyas apps no se matan nunca

**Tarea:** `TASK-071` (Feature pedida por el dueño el 2026-10-05).
**Área:** Modelos / Servicios / UI. **Depende de:** `TASK-069` (cerrada).
**Naturaleza de este documento:** Planificación de Arquitectura. Cero ediciones bajo `src/`.

---

## 1. Contexto y Requisito Original

El dueño solicitó textualmente el 2026-10-05:
> "aplicaciones protegidas. sera un pack especial, su funcionamiento sera que las aplicaciones que esten ahi, no seran matadas nunca por la ejecucion de otro pack. este pack no se puede matar ni iniciar ni nada, las aplicaciones que esten en este pack, no apareceran en ningun otro lugar, ni en la ventana de todos los procesos ni en los demas packs"

Este requerimiento introduce una nueva clase de entidad en el sistema: un pack de salvaguarda ("Protegidas") que no es destructivo ni ejecutable, sino un guardián declarativo de procesos de usuario.

---

## 2. Decisiones Arquitectónicas Fundamentales

### D-1: Representación en el Modelo de Datos (`Pack` y `models.py`)
- Se añade el campo booleano estricto `is_protected: bool = Field(default=False, strict=True)` en `Pack`.
- Al igual que `is_gaming: bool = Field(default=False, strict=True)`, utiliza `strict=True` para evitar coerciones laxas (`"true"`, `"1"`).
- **Invariante de Unicidad:** Solo puede existir **un** pack con `is_protected=True` en `AppData.packs`.
- **Invariante de Inmutabilidad Estructural:** El pack protegido no puede ser eliminado por el usuario (`PackService.delete_pack` debe rechazarlo con excepción, simétrico a `is_gaming=True`).
- **Invariante de No Ejecución:** `default_action` se fija por convención o centinela, pero los métodos `execute_pack`, `start_pack_apps` y `kill_pack_apps` deben rechazar o anular operaciones sobre este pack.
- **Persistencia de Apps:** Las aplicaciones agregadas a este pack se guardan en su array `apps` (rutas absolutas o nombres de ejecutables canónicos en minúsculas).
- **Semántica con `keepers`:** `PackService.get_protected_pack()` expone las apps protegidas. En runtime, toda rutina de apagado (`execute_pack`, `execute_gaming_pack`, `kill_processes`) suma automáticamente las apps del pack protegido a su lista efectiva de `keepers`.

### D-2: Invariante de Exclusión Mutua (La Protección Gana Siempre)
- Si un proceso o ejecutable `app.exe` está en el pack protegido:
  - **No puede ser matado** por ningún otro pack (Gaming mode, packs de usuario, ni apagado por categorías).
  - La protección gana **estáticamente y en runtime**:
    - Al evaluar categorías: si un proceso pertenece a una categoría seleccionada para matar (ej. `🟢 Sincronización`), pero su nombre/ruta coincide con una app protegida, el proceso se omite del kill.
    - Al evaluar apps directas: si otro pack lista `app.exe` en su array `apps`, el motor de kill lo descarta antes de enviar la señal `terminate()`.
  - **Indestructibilidad del Sistema:** Se mantiene intacto `SYSTEM_PROTECTED_PROCESSES` (los 34 procesos del sistema operativo nunca son tocados). Las apps protegidas forman el segundo anillo de blindaje (procesos de usuario blindados).

### D-3: La Invisibilidad en la Interfaz de Usuario
El requisito exige: *"las aplicaciones que esten en este pack, no apareceran en ningun otro lugar, ni en la ventana de todos los procesos ni en los demas packs"*.
1. **En la Ventana de Gestor de Procesos (`ProcessManagerView`):**
   - El escaneo obtiene la lista de procesos activos.
   - Los procesos cuyo nombre o ejecutable coincida con las apps del pack protegido son **filtrados de la vista**.
   - No aparecen en la tabla, no se pueden seleccionar y no se pueden añadir a otros packs desde esta vista.
   - *Nota de Recuperabilidad:* Para evitar el problema de procesos "fantasmas" inaccesibles si se cuelgan, la interfaz del Gestor de Packs muestra claramente la lista de apps dentro de la tarjeta del Pack Protegido con un botón individual para "Desproteger" (eliminar del pack protegido). Al desprotegerla, vuelve a ser visible en el Gestor de Procesos.
2. **En el Gestor de Packs (`PackManagerView`):**
   - El desplegable para añadir procesos a otros packs no ofrece procesos que pertenezcan al pack protegido.
   - En la tarjeta del Pack Protegido:
     - Los botones "Iniciar" y "Cerrar" están **ausentes** o reemplazados por una insignia informativa estática: `🛡️ Apps Protegidas (No ejecutable)`.
     - El botón de eliminar pack está **oculto o deshabilitado** (invariante de preservación).
     - Se ofrece un botón dedicado o diálogo para agregar ejecutables/rutas manualmente o seleccionarlos antes de protegerlos.
3. **En la Portada (`DashboardView`):**
   - El pack protegido **no** se muestra como botón de acción ejecutable en la portada (no tiene sentido un botón gigante que no hace nada). Si `is_favorite` fuera marcado por error, la vista lo ignora para la botonera de ejecución.

### D-4: Blindaje contra la Reposición Silenciosa (Dependencia de TASK-069)
- En `TASK-069`, se descubrió que cuando `profiles.json` se corrompe o se repone el Gaming pack por defecto, se repone con `DEFAULT_GAMING_PACK`.
- El pack protegido debe tener una función constructora defensiva: `_ensure_protected_pack()` en `PackService`.
- Si `profiles.json` existe pero no tiene pack protegido, se inicializa un pack protegido vacío `DEFAULT_PROTECTED_PACK` con `is_protected=True`, `name="Protegidas"`, `apps=[]`.
- Si se repone, se registra en el log y no pisa apps de usuario.

---

## 3. Matriz de Componentes Afectados

| Componente | Rol | Modificaciones Planificadas |
|---|---|---|
| `src/woptimizer/models.py` | Modelo Pydantic | Añadir `is_protected: bool = Field(default=False, strict=True)` a `Pack`. |
| `src/woptimizer/services/pack_service.py` | Gestión de Packs | `get_protected_pack()`, inicialización por defecto, prohibición de borrado, validación de unicidad. |
| `src/woptimizer/services/process_service.py` | Lógica de Procesos | Inyección de apps protegidas en la lista de exclusión de `kill_processes` y `kill_pack_apps`. |
| `src/woptimizer/services/gaming_service.py` | Modo Gaming | Inclusión de apps protegidas en los `keepers` efectivos de `execute_gaming_pack`. |
| `src/woptimizer/ui/views/process_manager_view.py` | UI Procesos | Filtro de procesos protegidos (`_render_list` omite procesos en `protected_apps`). |
| `src/woptimizer/ui/views/pack_manager_view.py` | UI Packs | Renderizado especial de tarjeta protegida (sin botones de ejecución, sin borrar, gestión de lista). |
| `src/woptimizer/ui/views/dashboard_view.py` | UI Portada | Exclusión del pack protegido de la rejilla de ejecución rápida. |

---

## 4. Plan de Pruebas y Mutantes (Paso 4)

Los tests deben ejecutarse headless (`run_tests.py`) y cubrir:
1. **Modelo y Validación:** Pydantic valida `is_protected` como booleano estricto.
2. **Unicidad e Inmutabilidad:** No se puede borrar el pack protegido (`PackService.delete_pack` lanza excepción).
3. **Filtro Anti-Kill:** Un proceso marcado en el pack protegido sobrevive a `execute_pack` de otro pack aunque esté en sus `apps` o en sus categorías de kill.
4. **Filtro de Visibilidad en UI:** `ProcessManagerView` no lista procesos protegidos en su tabla.
5. **UI no ejecutable:** La tarjeta del pack en `PackManagerView` no ofrece acción `start` ni `kill`.
