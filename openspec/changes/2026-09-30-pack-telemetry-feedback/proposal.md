# Propuesta: TASK-035 — Telemetría y Feedback Visual Unificado en Ejecución de Packs (Portada y Gestor)

## Contexto y Motivación
En el Área 2 (Gaming & Telemetría UX), la ejecución de packs ofrece feedback dispar e incompleto según desde qué vista se invoque y qué acción se ejecute:
1. **Portada (`DashboardView`)**:
   - La acción `kill` (Gaming Mode o packs de apagado) muestra un banner enriquecido en pantalla (`_show_banner`) indicando procesos cerrados y MB de RAM liberados, y actualiza la banda de telemetría permanente en reposo (`resting_bar`).
   - Sin embargo, la acción `start` (packs de lanzamiento de juegos o utilidades) ejecuta `self.process_service.start_pack_apps` en segundo plano, emite un toast en la bandeja del sistema pero **no muestra ningún banner en pantalla ni actualiza la telemetría en reposo**. Si el usuario tiene las notificaciones de Windows silenciadas (Asistente de concentración / Modo Juego), no recibe confirmación visual en pantalla.
2. **Gestor de Packs (`PackManagerView`)**:
   - Tanto `kill_pack` como `start_pack` ejecutan sus acciones en hilos secundarios y emiten toasts nativos, pero **dejan `self.status_label` completamente vacío**.
   - El usuario pulsa "Apagar" (doble pulsación confirmada) o "Iniciar" y no observa ninguna actualización en el texto de estado de la vista (`status_label`), a pesar de que la vista dispone de `Confirmable._inline_status()`.

## Objetivos
1. **En `DashboardView`**:
   - Implementar `_show_start_banner(self, launched: int, failed: int, pack_name: str)` para mostrar feedback inline en `status_banner_frame` con los tokens semánticos correspondientes (`theme.ACCENT` en éxito, `theme.WARNING` ante fallos parciales) y auto-ocultación a los 5 segundos vía `_schedule_ui`.
   - Conectar `_run_start` para invocar `self.after(0, self._show_start_banner, launched, failed, p.name)` y refrescar el contador de telemetría de procesos activos con `_update_resting_bar()`.
   - El auto-ocultado se programa **desde un único método** compartido por las dos puertas (`_reprogramar_autoocultado`), no desde cada una.
2. **En `PackManagerView`**:
   - En `kill_pack`: al finalizar el hilo de kill, **no** emitir un literal. El texto y el color se calculan en `ui/feedback.py` con `mensaje_cierre_pack(nombre, killed, failed, skipped, freed_mb)` a partir de la 4-tupla real y se publican enteros con `self.after(0, self._inline_status, texto, color)`. *(El contrato original pedía el literal `f"✅ {killed} procesos cerrados ... · '{nombre}'.", VERDE`; ese literal es exactamente la mentira que el ciclo 26 eliminó: con `killed == 0` pintaba un tick de éxito en verde.)*
   - En `start_pack`: al finalizar el arranque, emitir feedback vía `self.after(0, self._inline_status, ...)` informando apps iniciadas o fallidas.
   - En caso de packs sin apps en `start_pack`: mostrar aviso preventivo vía `mensaje_sin_apps(pack.name, "start")` → `self._inline_status(texto, color)`. *(TASK-036: el literal `⚠️ '{pack.name}' no tiene apps que iniciar.` estaba escrito a mano en la vista **y duplicado byte a byte dentro de `kill_pack`**. La frase vive ahora en un constructor privado de `ui/feedback.py` y las dos familias —inline y banner— la comparten, para que no puedan divergir.)*
3. **Pruebas y Validación**:
   - La sonda de honestidad del feedback (**`test_el_feedback_de_pack_dice_la_verdad`**) entra por la UI de verdad —`execute_pack`, `kill_pack`, `start_pack`, con doble pulsación, hilo secundario real y `self.after` encolado— y afirma sobre el **texto y el color** que produjo el código en los cuatro desenlaces y por las **tres** puertas de cierre.
   - **`test_el_gestor_de_procesos_tampoco_miente`** cubre la tercera puerta, `ProcessManagerView.on_kill_selected` (cierre uno a uno de lo que el usuario marcó a mano), que también se alimenta de `mensaje_cierre_pack`.
   - **`test_los_workers_de_pack_solo_publican_por_after`**: análisis AST del **objetivo real** de cada `threading.Thread(target=...)` de **cinco métodos de tres clases de vista** (`DashboardView.execute_pack`, `PackManagerView.kill_pack`, `PackManagerView.start_pack`, `ProcessManagerView._do_load` y `ProcessManagerView.on_kill_selected`), con la lista de lo permitido como pares `(raiz, metodo)`, bajando por `ast.Subscript`, `getattr`/`setattr`/`delattr` y `ast.Delete`, mirando también los **argumentos** de las llamadas permitidas, y exigiendo que cada `self.after` sea de 0 ms con un callback de la lista blanca. Lo que la guarda **no** cubre está escrito en `docs/ai/ui-design-system.md` (los `Thread` de `ui/app.py`, los workers que se añadan sin meterlos en la lista y los alias locales).
   - Actualizar `docs/ai/ui-design-system.md` y `docs/ai/testing-guide.md` documentando la unificación y sus límites.

## Criterios de Aceptación
- La ejecución de packs (start o kill) muestra feedback visual inmediato en pantalla tanto en la Portada como en el Gestor de Packs **como en el Gestor de Procesos**.
- **El verde es una promesa.** Con `killed == 0` ninguna de las tres puertas escribe tick ni color de éxito. Este criterio es normativo y lo cellspacing `mutation-auditor`: el texto y el color se calculan en `ui/feedback.py` a partir de la 4-tupla real, nunca en la vista.
- Las tres puertas de cierre se alimentan del **mismo formateador** (`mensaje_cierre_pack` / `mensaje_banner_cierre`, con `clasificar_cierre` como clasificador único). *Alcance honesto de este punto:* el formateador común no basta por sí solo; además ninguna puerta construye su propio texto y toda rama se ejecuta en la suite.
- Seguridad de hilos estricta: la UI nunca se muta desde hilos secundarios (siempre vía `self.after(0, ...)`).
- **Nada se traga en silencio (TASK-036).** Un pack no gaming sin apps **se avisa** en las dos ramas de `execute_pack` (kill y start) y en las dos puertas del Gestor, en ÁMBAR/`theme.WARNING`, **antes** de `_require_double_tap`, sin worker y sin nada encolado. Un Gaming Mode con 0 apps **y** 0 categorías se **diagnostica** con `⛔` en ROJO inline / `theme.WARNING` en banner; con apps **o** con categorías no avisa. El pack que no puede hacer nada **no** es un quinto desenlace de `clasificar_cierre`: no produce resultado, así que tiene formateadores puros propios. La cláusula de MB liberados se omite con `freed_mb <= 0`, como ya hacía `format_kill_result`.
- Suite de tests `run_tests.py` en verde al 100% y `verify_ui_syntax.py` sin errores.
