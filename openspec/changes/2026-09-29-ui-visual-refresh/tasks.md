# Tareas OpenSpec: Sistema de diseño y refresco visual del front (TASK-029)

- **Change ID**: `2026-09-29-ui-visual-refresh`
- **Taskmaster**: `TASK-029` (nueva)
- **Depende de**: `TASK-027` (FIX-004 ya reordena las categorías en `_render_list`; rediseñar la
  lista antes de que exista el orden semántico es hacer el trabajo dos veces)
- **Naturaleza**: mejora, **no fix**. No debe mezclarse con TASK-026/027 en el mismo ciclo.
- **Bloqueo**: UI-001 espera la decisión del propietario sobre el color de marca (`proposal.md` §3).
  Todo lo demás puede empezar ya.
- **Prohibido**: tocar `services/`, `models.py`, los contratos de las 5 acciones destructivas, o
  cualquier ruta de `after`/hilo. Un rediseño que reescriba el cableado de hilos reintroduce el bug
  que FIX-007 acaba de cerrar. Sin `messagebox`. Sin dependencias nuevas.

---

## Fase A — Fundamento (bloquea todo lo demás)

- [ ] **UI-006 · Icono real.** `app.py:76-78` dibuja un cuadrado 64x64 con el texto "W3" con PIL.
      Generar `assets/woptimizer.ico` (múltiplo tamaño) con un script reproducible y usarlo en
      `pystray` **y** en `root.iconbitmap(...)`, que hoy no se llama en ningún sitio y deja el icono
      genérico de Python en la barra de título. Es el cambio de mayor impacto visual por línea de
      código, porque el modo por defecto del `.exe` es **ocultar la ventana** (`app.py:45-46`).
      Bloquea: nada. Es lo primero que se hace.

- [ ] **UI-001 · Color de marca del Gaming Mode** (DECISIÓN DEL PROPIETARIO, §3).
      Por defecto se aplica **Opción A: Gaming = `#1DB954`**, el rojo queda exclusivo para peligro
      (`confirmation.ROJO` y el semáforo `🔴` de `config.get_safety_badge`). Repintar
      `dashboard_view.py:126-128`, `pack_manager_view.py:90` y `pack_manager_view.py:109`.
      Corregir la contradicción de la doc: `ui-design-system.md:9` (dice rojo) vs `:74` (dice verde).
      Bloquea: UI-002, UI-004, UI-005.

- [ ] **UI-002 · `ui/theme.py` con tokens.** Nuevo módulo, **sin widgets**: colores por rol
      (`surface`, `surface_alt`, `surface_sunken`, `text_primary`, `text_muted`, `accent`,
      `gaming`, `danger`, `warning`, `success`, `border`), escala tipográfica de **6** tamaños
      declarados y 3 radios. Migrar los ~20 hex sueltos de `main_window.py:54,66,78`,
      `pack_manager_view.py:69,90,109,121-127,132,137,144,153,168-169` y
      `process_manager_view.py:198,233`.
      **No** mover `config.get_safety_badge` ni `confirmation.py` a este módulo: son secretos de
      otra frontera y ya tienen sus propios tests.

- [ ] **UI-002a · `test_no_literal_colors_in_views`.** Parseo `ast` de las 3 vistas y
      `main_window.py`: **cero** literales hex en argumentos de `fg_color`, `hover_color`,
      `text_color` o `border_color`. *Discrimina: hoy falla en ~20 sitios.* Es el test que blinda
      la deriva described en `proposal.md` §2.
- [ ] **UI-002b · `test_theme_tokens_complete`.** Todo token usado existe; la escala tiene
      exactamente 6 tamaños y las vistas no inventan ninguno.

- [ ] **UI-010 · `test_contrast_wcag_aa`.** Luminancia relativa WCAG real sobre **cada** par
      token texto/fondo en uso, umbral 4.5:1. El repo no tiene hoy ninguna verificación de
      contraste. *Discrimina: hoy no hay nada que lo ejecute.*

## Fase B — Superficies visibles

- [ ] **UI-003 · Barra de navegación** (`main_window.py:29-40, 48-50, 54, 66, 78`).
      `fg_color` propio en vez del heredado del tema `"blue"`; altura fija real con
      `pack_propagate(False)` (hoy `height=40` no limita nada); `hover_color` en los 3 botones
      (hoy no hay ninguno y parpadea el gris del tema); el estado activo se marca con **barra de
      acento bajo el texto + `text_primary`**, no con un relleno azul. Escribir el estado activo
      **una** vez: hoy son 4 escrituras de color por navegación.
      *Corrige además la affordance invertida: hoy lo inactivo parece un campo de entrada y lo
      activo parece un botón.*

- [ ] **UI-004 · Portada** (`dashboard_view.py`).
      - Reetiquetar la línea del botón (`:116`): tras TASK-025 el Gaming Mode mata **por
        categoría**, y `"3 apps - KILL"` muestra un número que ya no describe lo que va a pasar.
      - Banda de estado **en reposo** (`:33-39`): RAM usada, nº de procesos, último Gaming Mode.
        Hoy la telemetría solo aparece *después* de actuar (`_show_banner:84`).
      - Estado vacío (`:100-103`) con sesión de uso, no una label gris centrada.
      - `refresh_dashboard()` (`:94-95`) **reutiliza** los widgets en vez de destruirlos y
        recrearlos (parpadeo + pérdida de foco).

- [ ] **UI-005 · La tarjeta del pack de sistema** (`pack_manager_view.py:69, 90-91`).
      Hoy el pack más importante de la app usa el mismo `card` que cualquier otro y solo se
      distingue por un badge de 50x18 a 9pt. Borde de acento + badge con el mismo color de marca
      que el botón de la portada.

- [ ] **UI-008 · Lista de procesos** (`process_manager_view.py:176-185, 198-241`).
      Cabecera de categoría con fondo, contador y hover (hoy es un `CTkButton` transparente cuyo
      único cambio es el glifo ▼/▶); filas con hover, separación y jerarquía por indentación;
      orden de categorías **el de `CATEGORY_ORDER` que deja TASK-027**, no el actual.
      **Reutilizar el agrupado ya publicado por FIX-007**: nada de recalcular nada aquí.

- [ ] **UI-011 · Estado vacío correcto** (`process_manager_view.py:151`).
      Con 0 procesos se muestra hoy `"✅ 0 apps distintas."` — un check verde sobre un vacío.
      Mensaje neutro y sin check.

## Fase C — Micro-UX

- [ ] **UI-007 · Objetivos de puntero.** `pack_manager_view.py:143` (20x18), `:81`, `:121`,
      `:126` (28x26) → mínimo 28x28. Nuevo `test_hit_targets_minimum` que recorra el árbol con
      `winfo_width/height` tras `update_idletasks()` y falle por debajo.

- [ ] **UI-009 · Diálogo de alta de pack** (`pack_manager_view.py:246`).
      `ctk.CTkInputDialog` se crea **sin padre** → es un diálogo del sistema, fuera del tema, y
      puede abrirse **por detrás** de la ventana principal: exactamente el modo de fallo de la
      Trampa #14 (`ui-design-system.md:173`). Hoy es inocuo (crear no es destructivo), pero el
      patrón queda disponible. Sustituir por un diálogo propio themed, **sin `messagebox`**.

- [ ] **UI-012 · Responsive.** `process_manager_view.py:229-234`: las descripciones a 11px no
      tienen `wraplength` y se salen en el mínimo de 720px (`app.py:17`). `wraplength` en función
      del ancho, o `text` truncado con tooltip.

- [ ] **UI-012b · Contrato semántico de color** · `test_semantic_color_contract`.
      `theme.DANGER` no aparece en ningún widget que no sea acción destructiva o semáforo `danger`,
      y `theme.GAMING` no aparece en `config.get_safety_badge`. *Es el test que blinda
      `proposal.md` §1: si alguien vuelve a pintar el Gaming de rojo, falla.*

## Cierre

- [ ] `python verify_ui_syntax.py`, `python run_tests.py` y `python validate_docs.py` en verde.
- [ ] Los 6 tests nuevos registrados en el `__main__` de `run_tests.py`.
- [ ] `run_tests.py` **no toca** `profiles.json` real ni mata procesos del sistema.
- [ ] ASCII puro en los `print()` de los tests (Trampa #16, cp1252).
- [ ] `docs/ai/ui-design-system.md`: reescribir la §1-§3 con la escala, los roles de color y la
      decisión de §3; **borrar la contradicción rojo/verde de `:9` vs `:74`**.
- [ ] `docs/ai/ui-design-system.md` deja de ser una lista de widgets y pasa a ser un sistema
      (capas, roles, ritmo vertical, estados) + la excepción del tray, que **no cambia**.
- [ ] Cierre limpio: árbol de git con 0 cambios pendientes.
