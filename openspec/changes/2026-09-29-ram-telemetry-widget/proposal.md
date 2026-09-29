# Propuesta OpenSpec: Telemetría de RAM Liberada y Feedback Visual en Portada

## Contexto y Motivación
Actualmente, al activar el Modo Gaming o cerrar un Pack desde la Portada (`DashboardView`), el usuario no recibe confirmación visual de cuántas aplicaciones se cerraron ni cuánto impacto positivo tuvo en la memoria RAM de su equipo. Medir y mostrar la RAM liberada (en MB/GB) proporciona una recompensa psicológica inmediata al jugador y valida la utilidad del software.

## Diseño Técnico
1. **Cálculo de RAM en `ProcessService` (`services/process_service.py`):**
   - En `kill_processes` y `kill_pack_apps`, antes de matar cada proceso y sus procesos hijos, capturar la memoria física (`proc.memory_info().rss`).
   - Sumar los bytes de los procesos exitosamente terminados.
   - Retornar una 4-tupla estructurada: `(killed: int, failed: int, skipped: int, freed_mb: float)`.
2. **Visualización en `DashboardView` (`ui/views/dashboard_view.py`):**
   - Incorporar un panel de estado / banner animado o persistente bajo el encabezado.
   - Al ejecutar `execute_pack` con acción `kill`, capturar el resultado en el hilo secundario y llamar a la UI vía `self.after(0, ...)` mostrando:
     `"⚡ Modo Gaming Activado: {killed} procesos cerrados · {freed_mb:.1f} MB de RAM liberados"`.
3. **Invariantes a Respetar:**
   - Separación estricta: CustomTkinter **no** llama a `psutil`; únicamente recibe el valor `freed_mb` de `ProcessService`.
   - Kill recursivo preservado: Hijos primero, luego el padre.
