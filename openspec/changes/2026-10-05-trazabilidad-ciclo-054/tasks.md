# Tareas — los cinco tickets de trazabilidad de CYCLE-054

**Spec:** `openspec/changes/2026-10-05-trazabilidad-ciclo-054/proposal.md`
**Tarea del tablero:** `TASK-067`
**Un solo ciclo, cinco subtareas.** El criterio común está en `proposal.md` §1.

**REGLA DE RECUENTO, vigente en las cinco:** ninguna subtarea añade una función `test_*()` nueva.
Las sondas van **dentro** de tests que ya existen, antes del marcador headless
(`run_tests.py:20770`). El total queda en **159**, el reparto en **112 + 47**, y los cuatro
declarantes (`STATUS.md`, `AGENTS.md`, `README.md`, tabla 1..159 de `docs/ai/testing-guide.md`)
**no se tocan**. Si una subtarea acabara necesitando un test nuevo, se para y se vuelve al
arquitecto: sería andamiaje, no trazabilidad.

---

## T-1 · T54-4 🟡 MEDIA · El agregado y su guard de contenido

**Estado:** [ ] pending

**Por qué es la primera:** su guard es la herramienta con la que se comprueban T-4 y T-5, y el
agregado lo reconstruye él.

**Trabajo:**

1. `build_llms_full.py` en la raíz, con `--write` y `--check`. Indexa por la **ruta** del
   marcador `<!-- source: -->`, **nunca por el slug** (T54-7: `docs/architecture.md` son 6 255
   bytes y `docs/ai/architecture.md` son 62 819, y comparten slug; un generador por nombre
   publicaría el equivocado sin error visible).
2. Re-emite las 9 secciones con el formato medido de 5 líneas (`# slug` / vacía /
   `<!-- source: … -->` / vacía / `---` / vacía / cuerpo).
3. Regenerar el agregado desde las fuentes. **Dirección única: fuente → agregado.** El agregado
   lleva el fósil v2 (`process_manager.py`, messagebox, *"string (de PowerShell)"*) y
   `docs/api.md` lleva la API v3 vigente; un `.replace()` agregado→fuente escribiría el fósil
   encima del documento bueno.
4. `validate_docs.py`: el check 2 (`:2143-2157`) deja de mirar solo el **nombre**
   (`if d not in full`, `:2153`) y pasa a asentar por el generador, comparando **cuerpo**.
5. El docstring del propio check 2, que hoy promete "concatenar todos los `docs/*.md`" cuando la
   lista real son 9 secciones y una de ellas viene de `docs/ai/`.

**Criterio de cierre:**

- [ ] `python build_llms_full.py --check` sale **0** en limpio y **≠ 0** si se edita una línea de
      una fuente, nombrando fichero y sección.
- [ ] Las **9** secciones tienen **0 %** de divergencia contra su fuente (medido hoy: 4 de 9 la
      tienen, hasta 98,9 %).
- [ ] El guard muere por **contenido**: mutar una línea de `docs/known-issues.md` en una copia
      produce FAIL, aunque el **nombre** siga presente.
- [ ] `validate_docs.py` en **0 FAIL**, con un OK más que antes.
- [ ] El generador elige `docs/ai/ui-design-system.md` y no `docs/ui-design-system.md` para esa
      sección, y para `architecture` la fuente la marca el marcador, no el nombre.
- [ ] Cero ediciones en `src/`.

---

## T-2 · T54-2 🟡 MEDIA · La 4.ª forma y el reconocimiento de vallas

**Estado:** [ ] pending

**Trabajo:** dos filas nuevas dentro de `test_ninguna_plantilla_de_commit_nombra_main`.

1. **La sonda de la 4.ª forma por la otra marca.** Valla plantilla marcada con
   `git commit -m "…"` y `git push origin main` **sin** comillas dentro, y se exige que salga como
   infracción. *Medido:* la sonda que ya existe (`run_tests.py:18317-18328`) usa
   `git_safe_commit.py "…"` como marca y **con el mutante sigue disparando**, por eso no lo coge;
   con la marca `git commit` el mutante deja la lista **vacía** y esta fila lo mata.
2. **La fila de `de_plantilla` no vacía**, atada a la medición: hoy **45** líneas de plantilla
   (`SKILL.md` 40, `AGENTS.md` 5) y **0** ocurrencias que solo la 4.ª forma pueda ver. Sin esta
   fila, `assert total >= 6` sigue en verde con el reconocimiento muerto, porque `total` = **11**
   antes y después del mutante.
3. **El docstring dice la verdad** (`run_tests.py:18204-18222`): hoy promete cuatro formas y que
   `total` cuenta "todo lo extraído"; `total` cuenta las tres entrecomilladas y la cuarta solo
   cuando hay ocurrencia.

**Criterio de cierre:**

- [ ] El mutante `P2-SIN-GIT-COMMIT` deja la suite en **rojo** por una de las dos filas nuevas.
- [ ] El rojo **no** lo produce `assert total >= 6` (`:18303`).
- [ ] `run_tests.py` sigue en **159** y el reparto en **112 + 47**.
- [ ] Cero ediciones en `src/`.

---

## T-3 · T54-1 🟡 BAJA · La capa `#` del filtro de la regla de rama

**Estado:** [ ] pending

**Trabajo:** una línea de datos de test, más su docstring.

1. En `en_encabezado` (`run_tests.py:18079-18080`) las dos frases pasan de la línea **siguiente**
   al encabezado a estar **sobre** la línea del encabezado. *Medido:* hoy, con el filtro tirando
   también de `#`, el test sale **VERDE**; con el arreglo, sale **ROJO** con el motivo literal
   *"un ENCABEZADO con `#` es contenido valido en markdown y no se puede excluir"*.
2. El docstring (`:18016-18028`) deja de decir que ese control "no lo impide" y que "es una
   CONSTATACION, no una guarda": después del arreglo **sí** es una guarda.

**Lo que NO es el arreglo:** excluir `#` del filtro. En markdown `#` es encabezado y las reglas
empiezan con `>`, así que una regla en un encabezado es contenido válido; excluirlo abre otro
hueco del mismo tipo. Queda escrito en el código para que nadie lo intente después.

**Criterio de cierre:**

- [ ] El mutante P1-18 deja la suite en **rojo** por la fila del encabezado.
- [ ] `_sin_la_capa_que_el_bucle_no_lee` **no** excluye `#` (`:17983-17986`).
- [ ] El docstring y el comportamiento coinciden.
- [ ] `run_tests.py` sigue en **159** y el reparto en **112 + 47**.

---

## T-4 · T54-5 🟡 BAJA · Las citas de línea

**Estado:** [ ] pending

**Trabajo:** una cita rota, en tres sitios. Medido el estado real de las cuatro afirmaciones:

| Afirmación | Estado | Dónde |
|---|---|---|
| D5 `release-pipeline.md:54` → `:87` | ya corregida | `docs/GITHUB-SETUP-CHECKLIST.md:240` |
| D7 el checklist decía que salía con 0 | ya corregida | el texto ya no está |
| **D8 `mkdocs.yml:88`** | **VIVA en 3 sitios** | `docs/GITHUB-SETUP-CHECKLIST.md:165`, `STATUS.md:113`, `.taskmaster/CHANGELOG.md:162` |
| D10 "8 cabeceras largas" | ya corregida | `…CHECKLIST.md:321` y `llms-full.txt:799` dicen 7 |

1. Las tres citas de D8 pasan a `mkdocs.yml:81-82`, que es donde está la licencia de verdad
   (`mkdocs.yml` tiene **83** líneas).
2. La casilla de `LICENSE` (`…CHECKLIST.md:165`) sigue **abierta**, pero por su motivo real:
   **que no hay `LICENSE`**, no que la cita esté mal.
3. Declarar en el changelog del ciclo que hay **26** citas `fichero:línea` rotas más en
   `openspec/changes/**` y `CHANGELOG.md`, que son contrato e historia: **no se reescriben**.

**Criterio de cierre:**

- [ ] 0 citas `fichero:línea` rotas en **ficheros vivos** (las de `openspec/changes/**` y
      `CHANGELOG.md` quedan declaradas, con el número).
- [ ] La casilla de `LICENSE` sigue abierta por el motivo correcto.
- [ ] `STATUS.md:113` y el changelog no afirma que el fichero `mkdocs.yml` tiene 88 líneas.

---

## T-5 · T54-6 🟡 BAJA · La afirmación refutada y su lección

**Estado:** [ ] pending

**Trabajo:**

1. D11 se escribe en el changelog del ciclo con su **refutación y la medición que la refuta**:
   el check **5b** sí vigila (`validate_docs.py:833`), y quitar `## CYCLE-054` sube el validador
   de **1 FAIL a 2 FAIL**. No se escribe como afirmación.
2. En `docs/ai/testing-guide.md`, **junto a** la tabla de 159 filas y **sin tocarla**, la regla de
   las tres cifras:
   - toda cifra de veredicto escrita en prosa lleva **fecha** y su **"de aquel día"**, como ya
     hacen `docs/GITHUB-SETUP-CHECKLIST.md:581` y `llms-full.txt:993`;
   - un guard que **deriva** la cifra de la fuente no caduca; uno que la **cuenta a mano**
     caduca en el commit — el "126 OK / 0 FAIL" era cierto antes de `d68bf8b` y se rompió al
     commitear, y el rojo lo cerró `a82dca5` a mano;
   - **`commitlint` mira el rango del push y la release la decide `.releaserc.json`**
     (`type:docs -> release:false`): sin esa distinción se promete una release que no sale.

**Criterio de cierre:**

- [ ] D11 aparece refutada, con la cifra 1 → 2 FAIL.
- [ ] La regla está escrita en `docs/ai/testing-guide.md` **fuera** de la tabla 1..159, y esa
      tabla no cambia.
- [ ] El commit del ciclo es `chore`/`docs` y **no** se promete ninguna release.

---

## Verificación del ciclo (cierre)

- [ ] `python run_tests.py` → **159**, reparto **112 + 47**, 0 fallos.
- [ ] `P2-SIN-GIT-COMMIT` y `P1-18` muertos **por filas concretas**, no por `total >= 6`.
- [ ] `python build_llms_full.py --check` → 0.
- [ ] `python validate_docs.py` → **0 FAIL**.
- [ ] `python verify_ui_syntax.py` → EXITO.
- [ ] `python .taskmaster/sync_agents.py --check` → exit 0.
- [ ] Cero ediciones en `src/` desde `a82dca5`.
- [ ] `git_safe_commit.py` intacto; `LIMITE_CABECERA = 120` sin relajar.
- [ ] Todo commit por el wrapper, con `GIT_DIR` **y** `GIT_WORK_TREE`, y `git status --porcelain`
      vacío antes de cada `add -A`.
