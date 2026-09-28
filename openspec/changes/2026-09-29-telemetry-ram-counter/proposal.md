# Propuesta: Telemetría de Impacto Gaming y Contador de RAM Liberada

## Contexto y Motivación
Cuando un usuario pulsa el botón gigante de la Portada `🚀 Preparar para Gaming`, el sistema mata silenciosamente decenas de procesos en segundo plano. Sin embargo, el usuario no recibe feedback cuantitativo inmediato del beneficio real obtenido (cuánta memoria RAM se ha recuperado para el videojuego).

## Objetivos (What)
1. **Medición Precisa de RAM Liberada:**
   - Antes de matar los procesos seleccionados en `ProcessService.kill_pack_apps`, calcular la suma de `memory_info().rss` de todos los procesos (y sus hijos recursivos).
2. **Feedback Visual en Tiempo Real (Portada / Dashboard):**
   - Mostrar una tarjeta / banner de telemetría en la Portada:
     `⚡ Última Optimización: 1,845 MB liberados (24 procesos cerrados)`.
3. **Persistencia Ligera de Métricas:**
   - Registrar la última optimización en `profiles.json` o un campo volátil en memoria para mantener el valor visible entre cambios de pestaña.
4. **Toast / Banner de Éxito:**
   - Un indicador visual temporal verde en la interfaz confirmando la liberación de recursos.

## Arquitectura (How)
- **Backend (`ProcessService`):**
  - Ampliar `kill_pack_apps(apps)` para que devuelva una tupla o diccionario de telemetría:
    `{"killed_count": int, "freed_ram_mb": float}`.
- **Frontend (`DashboardView`):**
  - Añadir un widget de telemetría superior en la Portada con animación suave o badge destacado con el consumo recuperado.
  - Al ejecutar el pack desde la Portada, actualizar el widget en el hilo principal (`self.master.after`).
