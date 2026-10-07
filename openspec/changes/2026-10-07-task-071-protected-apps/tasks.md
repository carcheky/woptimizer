# Tasks — Aplicaciones protegidas (`TASK-071`)

Documento de especificación de subtareas para ejecución por `openspec-dev`.
Cero ediciones bajo `src/` en este documento: esto es el plan arquitectónico.

---

## T-1 — Modelo de Datos y Contrato de Persistencia (`models.py` y `pack_service.py`)

**Qué:**
1. En `src/woptimizer/models.py`, añadir al modelo `Pack`:
   ```python
   is_protected: bool = Field(default=False, strict=True)
   ```
2. En `src/woptimizer/services/pack_service.py`:
   - Definir constante de pack protegido por defecto:
     ```python
     DEFAULT_PROTECTED_PACK = Pack(
         id="protected_apps",
         name="Aplicaciones Protegidas",
         default_action="kill",
         is_protected=True,
         apps=[],
     )
     ```
   - Implementar `_ensure_protected_pack()`: si no existe un pack con `is_protected=True`, crearlo e insertarlo.
   - En `delete_pack(pack_id)`: si el pack tiene `is_protected=True`, lanzar `ValueError("No se puede eliminar el pack de aplicaciones protegidas")`, exactamente igual que con `is_gaming`.
   - Implementar método `get_protected_pack() -> Optional[Pack]`.
   - Implementar método helper `get_protected_apps() -> set[str]` que devuelva el conjunto normalizado en minúsculas de nombres de ejecutables y rutas.

**Criterio de Aceptación (Tests en `run_tests.py`):**
- Test unitario: `Pack(..., is_protected="true")` lanza `ValidationError` (por `strict=True`).
- Test de persistencia: `delete_pack` sobre el pack protegido lanza `ValueError`.
- Test de auto-reparación: Cargar un JSON sin pack protegido lo inicializa sin pisar packs existentes.

---

## T-2 — Invariante de Exclusión Mutua en el Core de Kill (`process_service.py` y `gaming_service.py`)

**Qué:**
1. En `src/woptimizer/services/process_service.py`:
   - En `kill_processes(pids_or_procs, ...)`, asegurar que los ejecutables que coincidan con `protected_apps` (obtenidas vía `pack_service.get_protected_apps()`) sean excluidos de la lista a matar antes de invocar `terminate()`.
   - Simétrico a `SYSTEM_PROTECTED_PROCESSES`: las apps protegidas son indestructibles.
2. En `src/woptimizer/services/gaming_service.py`:
   - En `execute_gaming_pack()`, las apps protegidas se unen a los `keepers` efectivos:
     `effective_keepers = set(pack.keepers) | set(self.pack_service.get_protected_apps())`
   - Ninguna categoría roja o amarilla mata un proceso que esté en `effective_keepers`.
3. En `execute_pack()`:
   - Todo pack que ejecute acción de kill respeta la exclusión de apps protegidas.

**Criterio de Aceptación (Tests en `run_tests.py`):**
- Un test donde un pack normal tiene `apps=["discord.exe"]` o categoría `_CAT_CHAT`, y el pack protegido tiene `apps=["discord.exe"]`. Al ejecutar el pack normal, `discord.exe` **no** es enviado a `kill_processes` y permanece vivo.
- El mutante que omite unir `get_protected_apps()` en `execute_pack` o `execute_gaming_pack` muere por aserción.

---

## T-3 — Filtro de Invisibilidad en Gestor de Procesos (`process_manager_view.py`)

**Qué:**
1. En `src/woptimizer/ui/views/process_manager_view.py`:
   - Al renderizar la lista de procesos (`_render_list()` o durante el filtrado):
     Obtener `protected_apps = self.pack_service.get_protected_apps()`.
   - Omitir cualquier proceso cuyo `proc.name` o `proc.full_name` (en minúsculas) coincida con `protected_apps`.
   - El proceso no aparece en el scrollable frame, no cuenta en los totales visibles y no puede ser seleccionado para añadir a otros packs.

**Criterio de Aceptación (Tests en `run_tests.py`):**
- Test headless: montar `ProcessManagerView` con un snapshot que incluye un proceso protegido y procesos normales.
- Comprobar que el proceso protegido no genera fila visual (`len(self.process_rows)` no lo incluye).

---

## T-4 — Interfaz de Usuario del Pack Protegido (`pack_manager_view.py` y `dashboard_view.py`)

**Qué:**
1. En `src/woptimizer/ui/views/pack_manager_view.py`:
   - Al renderizar las tarjetas de packs:
     Si `pack.is_protected`:
       - No renderizar los botones "Iniciar" ni "Cerrar".
       - En su lugar, mostrar un badge informativo: `🛡️ Protegidas`.
       - No renderizar el botón de eliminar pack.
       - En el acordeón/lista de apps de la tarjeta, ofrecer la opción de eliminar app del pack protegido ("Desproteger").
       - Ofrecer botón "Añadir aplicación protegida..." (explorador de archivos para seleccionar `.exe`).
2. En `src/woptimizer/ui/views/dashboard_view.py`:
   - En `get_favorite_packs()`, excluir explícitamente cualquier pack donde `pack.is_protected == True`.

**Criterio de Aceptación (Tests en `run_tests.py`):**
- Test headless: La tarjeta de `pack.is_protected` no tiene botones de acción destructiva ni de inicio.
- Test headless: La portada nunca renderiza un botón gigante para el pack protegido.

---

## T-5 — Documentación y Sincronización del Sistema

**Qué:**
1. Actualizar `docs/ai/data-models.md` describiendo el campo `is_protected` y el nuevo invariante de protección.
2. Actualizar `docs/ai/ui-design-system.md` documentando la tarjeta de pack protegido y las reglas de visibilidad.
3. Actualizar `STATUS.md` reflejando el progreso del hito.
4. Ejecutar validaciones:
   - `python verify_ui_syntax.py` -> 100% OK.
   - `python validate_docs.py` -> 0 FAIL.
   - `python build_llms_full.py --check` -> 0.
