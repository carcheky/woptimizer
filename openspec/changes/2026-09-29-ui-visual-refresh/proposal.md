# Propuesta: Sistema de diseño y refresco visual del front (UI-001 … UI-012)

- **Change ID**: `2026-09-29-ui-visual-refresh`
- **Ciclo**: #15 (segunda entrega del ciclo, a petición del propietario: *"el front podría mejorarse, ser más bonito"*)
- **Área de rotación**: 2 — Gaming & Telemetría UX
- **Taskmaster**: `TASK-029` (nueva)
- **Subagente de ejecución**: `openspec-dev`
- **Estado**: AUDITADA por architect-review — **aprobada con 1 decisión pendiente del propietario** (§3)
- **Alcance**: `src/woptimizer/ui/theme.py` (nuevo), `app.py`, `main_window.py`, las 3 vistas,
  `run_tests.py`, `docs/ai/ui-design-system.md`
- **Naturaleza**: este change **no arregla fallos**; reorganiza lo que ya funciona. Por eso va
  **detrás** de TASK-026/027 y no debe mezclarse con un fix de seguridad.

## 1. El hallazgo que domina todos los demás

**El color del Gaming Mode está en guerra consigo mismo: rojo y verde en la misma pantalla.**

| Dónde | Color | `archivo:línea` |
|---|---|---|
| Botón del pack Gaming en la portada | **rojo** `#c22d2d` | `dashboard_view.py:126-128` |
| Badge "PRESET" de la tarjeta | **rojo** `#c22d2d` | `pack_manager_view.py:90` |
| Botón `⛔ Apagar` | **rojo** `#c22d2d` | `pack_manager_view.py:109` |
| Banner de RAM tras activar Gaming | **verde** `#1B4332` / `#1DB954` | `dashboard_view.py:79-80` |
| `VERDE` de éxito = "el mismo del banner" | `#1DB954` | `confirmation.py:41` |

Consecuencias, en orden de gravedad:

1. **El rojo del semáforo está contaminado.** `config.py:112-118` reserves `#ff6b6b` / `#401616`
   para `🔴 NO CERRAR`, y `confirmation.py:39` `ROJO = "#c22d2d"` para bloqueos `⛔`. Si además
   el Gaming Mode es rojo, **el rojo deja de significar "peligro"**. En una app cuyo producto es
   "no mates esto", la señal de peligro no puede ser también la marca.
2. **El usuario ve un botón rojo y recibe un banner verde.** Es el mismo evento. La única lectura
   consistente es que el color no codifica nada.
3. **La documentación se contradice a sí misma**: `ui-design-system.md:9` dice que el Gaming es
   `#c22d2d`; `ui-design-system.md:74` dice que es `#1B4332`/`#1DB954`.

Este es el motivo por el que el resto del rediseño no es "poner cosas más bonitas": mientras el
color sea ambiguo, cualquier ajuste de estética es decoration sobre una base sin semántica.

## 2. No existe un sistema de diseño: hay tres fuentes de verdad

| Eje | Fuentes de verdad actuales | Nº de valores |
|---|---|---|
| Color | `config.get_safety_badge` + `confirmation.py:34-42` + hex sueltos en cada vista | **3 fuentes, ~20 hex** |
| Tipografía | inline, sin escala | **10 tamaños** (9,10,11,12,13,14,15,18,20,24) |
| Radio de esquina | inline | **5 valores** (4, 6, 8, 15, y el default de CTk) |

Hex sueltos con `archivo:línea`:

- `main_window.py:54,66,78` — acento de navegación `["#3B8ED0", "#1F6AA5"]`
- `pack_manager_view.py` — `#1f1f1f` (`:69`), `#151515` (`:132`, `:153`), `#262626`/`#303030`
  (`:168-169`), `#333333`/`#444444` (`:121-122`), `#333333`/`#552222` (`:126-127`),
  `#2b1515` (`:144`), `#888888` (`:137`), `#c22d2d`/`#a12525` (`:109`)
- `process_manager_view.py` — `#181818` (`:198`), `#a0a0a0` (`:233`)

**Consecuencia práctica**: cada arreglo visual de los últimos 14 ciclos ha reintroducido su propio
hex. Sin un módulo de tokens, un quinto rediseño garantiza otra capa de colores sueltos. Es el
único elemento de este change que evita trabajo futuro en vez de añadirlo.

## 3. DECISIÓN PENDIENTE DEL PROPIETARIO (una sola, y bloquea §4)

**¿De qué color es el Gaming Mode?** Hay dos respuestas válidas y no puedo elegirla solo:

- **Opción A — Gaming = verde `#1DB954` (recomendada).** Deja el **rojo exclusivo para peligro**
  (`⛔` y `🔴 NO CERRAR`), con lo que el semáforo de `get_safety_badge` recupera su significado
  entero. Reutiliza el color que el banner ya usa (`dashboard_view.py:80`), así que el botón y
  su resultado coinciden. Coste: hay que repintar 3 widgets (`dashboard_view.py:126-128`,
  `pack_manager_view.py:90`, `pack_manager_view.py:109`).
- **Opción B — Gaming = naranja/ámbar `#e8590c`.** Separa marca de peligro y de éxito, y es el
  color habitual de "modo juego". Coste: introduce un cuarto color de marca y **choca** con el
  ámbar de confirmación de `confirmation.py:36` (`PENDIENTE_FG = "#b8860b"`), que significa
  "pulsación pendiente".

**Mi recomendación es A**, porque no colisiona con nada existente. Si el propietario no contesta, se
aplica A y se anota en el changelog como decisión reversible (cambiar un token, no 20 widgets).

**Lo que NO depende de esa decisión** es todo lo demás de este change: tokens, navegación, jerarquía,
icono, micro-UX. Está diseñado para que §4-§9 se puedan hacer en paralelo.

## 4. La barra de navegación es el elemento más visible y el peor diseñado

`main_window.py:29-40`:

- `nav_frame = ctk.CTkFrame(self, height=40)` **sin `fg_color`** → hereda la superficie por defecto
  del tema `"blue"` (`:12` de `app.py`), un gris-azulado que **choca** con las superficies negras
  del resto de la app (`#1f1f1f`, `#181818`, `#151515`).
- `height=40` **no limita nada**: sin `pack_propagate(False)` el frame se ajusta al contenido.
- Los 3 botones son idénticos: `fg_color="transparent", border_width=1` (`:33,36,39`) → parecen
  **campos de entrada**. El activo sí es un rectángulo relleno (`:54`).
  **A affordancia invertida**: lo inactivo parece input, lo activo parece botón.
- **Ningún `hover_color`** → cada paso del ratón dispara el gris por defecto del tema.
- `_clear_content()` (`:48-50`) pone los 3 en transparente y el que navega pone uno en azul
  (`:54/66/78`): **4 escrituras de color por navegación** para un resultado de 2 estados.

**Diseño propuesto**: franja con `fg_color = surface_alt`, altura fija con `pack_propagate(False)`,
3 botones con el mismo tamaño, `hover_color` propio, y **el activo se marca con una barra de acento
de 3px bajo el texto + texto en `text_primary`**, no con un relleno. Un solo punto de verdad del
estado activo, escrito una vez.

## 5. La portada desperdicia la mitad de una ventana de 860x560

- `dashboard_view.py:105-112`: grid de 2 columnas con botones de 120px (`height=120`, `:129`).
  Entre el header (`:28`) y el grid queda una banda vacía enorme.
- **Estado vacío = una label gris centrada** (`:101`) que dice "Ve al Gestor de Packs". Es la
  pantalla que ve el usuario en su instalación limpia, y es un párrafo gris sobre negro.
- **No hay nada en reposo**: la telemetría de RAM solo aparece *después* de actuar
  (`_show_banner:84`). Una app de gestión de RAM con cero RAM visible en reposo es contraintuitivo.
- `refresh_dashboard()` **destruye y recrea todos los botones** (`:94-95`) → parpadeo en cada
  refresco y pérdida del foco de teclado.
- El botón dice `"3 apps - KILL"` (`:116`) pero, tras TASK-025, el Gaming Mode mata **por
  categoría**, no por las 3 apps. **La etiqueta miente**: muestra un número que ya no es lo que
  va a pasar. Este es el punto más importante de la portada y es el menos informativo.

**Diseño propuesto**: (a) reetiquetar la línea del botón con lo que realmente va a cerrar
(`N apps · M categorías`); (b) una banda de estado en reposo con RAM usada, nº de procesos y
último Gaming Mode; (c) reutilizar los widgets en vez de recrearlos.

## 6. El icono es lo que el usuario ve siempre, y es un placeholder

`app.py:76-78`:

```python
image = Image.new('RGB', (64, 64), color = (30, 30, 30))
d = ImageDraw.Draw(image)
d.text((20, 20), "W3", fill=(255, 255, 255))
```

Un cuadrado oscuro con el texto "W3" en la bandeja del sistema. Y como el modo por defecto del
`.exe` es **ocultar la ventana** (`on_window_close:45-46` → `hide_window`), el icono de bandeja es
**la única superficie de la app para la mayoría de los usuarios**.

Además **no hay icono de ventana**: `root.iconbitmap(...)` no se llama en ningún sitio, así que la
barra de título muestra el icono genérico de Python.

**Diseño propuesto**: un `.ico` real en `assets/` (múltiplo tamaño, generado por script, no binario
a mano), usado por `pystray` y por `root.iconbitmap`. Es el cambio de **mayor impacto visual por
línea de código** de todo el change.

## 7. Micro-UX y affordances con evidencia

| Hallazgo | Evidencia | Impacto |
|---|---|---|
| Objetivos de puntero por debajo de lo razonable: 20x18 (quitar app), 28x26 (favorito, borrar, restaurar) | `pack_manager_view.py:143, 81, 121, 126` | usability |
| `CTkInputDialog` **sin padre** → diálogo del sistema, fuera del tema, puede abrirse **por detrás** de la ventana principal | `pack_manager_view.py:246` | ⚠️ es el modo de fallo de la Trampa #14 (`ui-design-system.md:173`). Hoy es inocuo (crear no es destructivo), pero el patrón queda Available |
| Con 0 procesos se muestra `"✅ 0 apps distintas."`: check verde sobre vacío | `process_manager_view.py:151` | semántica |
| La cabecera de categoría es un `CTkButton` transparente: el único cambio es el glifo ▼/▶; sin fondo, sin hover, sin contador | `process_manager_view.py:176-185` | escaneo |
| La lista de 131 procesos es un muro plano: filas `#181818` sin zebra, sin hover, sin indentación | `process_manager_view.py:198-241` | escaneo |
| La tarjeta del pack de sistema es idéntica a las demás; solo un badge de 50x18 a 9pt la distingue | `pack_manager_view.py:69` vs `:90-91` | jerarquía |
| Sin `wraplength` en las descripciones de fila → texto a 11px que se sale en ventanas de 720px (`app.py:17`) | `process_manager_view.py:229-234` | responsive |

## 8. Lo que este change NO toca

- **Nada de lógica**: ni `services/`, ni `models.py`, ni los contratos de las 5 acciones
  destructivas (`ui-design-system.md:210-219`). `_require_double_tap` se queda igual.
- **Ninguna ruta de kill ni de `after`**: el patrón `self.after(0, ...)` de TASK-026/FIX-007 no se
  modifica. Un rediseño que reescriba el cableado de hilos reintroduce el bug que acabamos de
  cerrar.
- **Sin `messagebox`**, sin dependencias nuevas, sin reescritura de widgets desde hilos.

## 9. Plan de tests (discriminan, no comprueban tipos)

- **`test_no_literal_colors_in_views`**: parseo `ast` de las 3 vistas + `main_window.py` y
  `assert` de que **ningún** literal de color hexadecimal aparece como argumento de `fg_color`,
  `hover_color`, `text_color` o `border_color`. Obliga a pasar por `theme.py`.
  *Discrimina*: hoy falla en ~20 sitios. Es el test que blinda la deriva de §2.
- **`test_theme_tokens_complete`**: todo token que la UI use existe en `theme.T`; la escala tipográfica
  tiene **exactamente 6** tamaños declarados y las vistas no inventan ninguno.
- **`test_contrast_wcag_aa`**: cálculo de contraste real (luminancia relativa WCAG) para **cada**
  par token texto/fondo en uso. Hoy no hay ninguna verificación de contraste en el repo.
- **`test_hit_targets_minimum`**: recorrido del árbol de widgets con `winfo_width/height` tras
  `update_idletasks()`; ningún botón interactivo por debajo de 28x28.
- **`test_semantic_color_contract`**: `theme.ROJO` no se usa en ningún widget que **no** sea
  acción destructiva o semáforo `danger`; y `theme.GAMING` no aparece en `config.get_safety_badge`.
  Este es el test que blinda §1: si alguien vuelve a pintar el Gaming de rojo, falla.
- **`test_ui_render_smoke`**: las 3 vistas se construyen y se renderizan contra un
  `ProcessService`/`PackService` de prueba; `assert` de que no quedan literales sueltos y de que
  la navegación escribe el estado activo **una** vez.

## 10. Orden de ejecución

1. **UI-006 (icono)** — impacto máximo, riesgo cero, independiente de todo lo demás.
2. **UI-001 (§3, color de marca)** — desbloquea la semántica; es la decisión del propietario.
3. **UI-002 (tokens) + sus 2 tests** — es lo que hace que 4-9 no se pudran.
4. **UI-003 (navegación)** y **UI-004 (portada)** — los dos de mayor visibilidad.
5. **UI-005 (tarjeta de sistema)**, **UI-007 (micro-UX)**, **UI-008 (lista de procesos)**,
   **UI-009 (diálogo de alta)**, **UI-010 (responsive)**, **UI-011 (estado vacío de 0 procesos)**,
   **UI-012 (limpieza de la doc)**.

**Dependencias**: esta tarea depende de `TASK-027`, que ya reordena las categorías en
`process_manager_view._render_list` (FIX-004). Rediseñar la lista antes de que exista el orden
semántico es hacer el trabajo dos veces.
