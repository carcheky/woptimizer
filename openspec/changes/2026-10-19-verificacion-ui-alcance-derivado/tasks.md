# TASK-081 — El alcance de `verify_ui_syntax.py` esta vacio

**Propuesta:** `proposal.md` (mismo directorio) · **Ciclo 67** · **Rama `beta`**

> Todo lo que se toca esta **fuera** de `src/woptimizer/`. Cero cambios de codigo de
> produccion.

---

## FASE 1 — Blindaje (lo que hace que el guard no pueda volver a vaciarse)

- [ ] **1.1** `verify_ui_syntax.py` deriva su alcance con `rglob("*.py")` sobre
      `src/woptimizer/`. **Sin lista de exentos**: el derivado cubre tambien los
      `__init__.py`. → **AC-1**
- [ ] **1.2** El script imprime el **recuento derivado**, no una constante.
      `STATUS.md:11` y el `CHANGELOG.md` dejan de declarar una cifra de modulos
      escrita a mano. → **AC-2**, **AC-6**
- [ ] **1.3** Guard de **forma** (AC-5) con `ast`: ninguna funcion de `run_tests.py`,
      `validate_docs.py` ni `verify_ui_syntax.py` puede contener una lista/tupla de
      **dos o mas** literales de ruta bajo `src/woptimizer/**.py` sin derivar el
      alcance con `rglob`/`os.walk`/`iterdir`/`glob`. **Cada hallazgo se nombra con
      fichero y linea.**
- [ ] **1.4** ⚠️ **Las dos enumeraciones pre-existentes que 1.3 va a encontrar**
      (`run_tests.py:8198` en `test_no_literal_colors_in_views` y `run_tests.py:13184`
      en `_copiar_el_esqueleto_del_validador`) **no entran en una lista muda de
      permitidos.** Cada una recibe, **en el docstring de su propio guard**, una frase
      que dice **(a) por que existe la enumeracion** y **(b) que la retira**. Una
      entrada sin las dos frases se rechaza.
      **1.3 las denuncia; no las repara.** Repararlas es del ciclo que las recoja.

## FASE 2 — La contraprueba (lo que mide el PRODUCTO)

- [ ] **2.1** `test_la_verificacion_de_sintaxis_de_la_ui_agrega_un_modulo_nuevo`
      — en `%TEMP%`: `src/` real + `verify_ui_syntax.py` + un modulo **nuevo** con
      error de sintaxis. Exige **exit 1** y que la salida **nombre ese modulo**.
      → **AC-3**
- [ ] **2.2** **Control positivo del 2.1** — el mismo arbol **sin** el modulo roto da
      **exit 0**, y con un modulo **sano** anadido tambien **exit 0**.
      ⚠️ Sin 2.2, un script que sale siempre con 1 cumpliria 2.1.
      → **AC-4**
- [ ] **2.3** El test **no toca el repo real**: todo ocurre en `%TEMP%` y la
      ejecucion es un subproceso con su propio `cwd`.

## FASE 3 — Medidas de los tres guiones

- [ ] **3.1** `M-L` — reintroducir la tupla literal de 10 rutas.
      **Debe morir** en AC-1 (via AST) **y** en AC-3 (via producto).
- [ ] **3.2** `M-R` — dejar `rglob` en un comentario o en codigo muerto, con la
      lista de vuelta. **Debe morir** en AC-1. Un guard de texto pasaria.
- [ ] **3.3** `M-C` — camara que devuelve exit 1 siempre. **Debe morir** en AC-4.
- [ ] **3.4** `M-S` — volver a «10 modulos» como cifra fija en `STATUS.md`.
      **Debe morir** en AC-2.
- [ ] **3.5** `M-W` — reintroducir la enumeracion de 4 rutas en `run_tests.py:8198`.
      **Debe morir** en AC-5.
- [ ] **3.6** Declarar por adelantado, mutante a mutante, si un superviviente es
      **EQUIVALENTE** o **SIN COBERTURA**. Un guard que no puede fallar no puede pasar.

## FASE 4 — Cierre

- [ ] **4.1** `python verify_ui_syntax.py` → exit 0 con el recuento derivado.
- [ ] **4.2** `python run_tests.py` → `ALL TESTS PASSED`, exit 0.
- [ ] **4.3** `python validate_docs.py` → **0 FAIL**, exit 0.
- [ ] **4.4** `git status --porcelain` vacio antes de comitear; rama `beta`.
- [ ] **4.5** Commit por el wrapper, con identificador:
      `python .taskmaster/git_safe_commit.py "fix(tools): el alcance de la puerta de sintaxis UI se deriva, no se enumera (TASK-081)"`.
      ⚠️ **Nunca a `main`.** ⚠️ **Comprobar el codigo de salida.**
- [ ] **4.6** Actualizar `STATUS.md` (deuda nueva + la fila resuelta) y
      `docs/ai/testing-guide.md` con la regla de R1/R2/R5.

---

## Lo que este ciclo NO hace

- **TASK-080**: activar el validador en CI. Su propia medicion dice que CI no puede
  dar verde todavia (**25 hashes** de `rd_journal.json` sin pushear). Activarlo hoy
  rompe el pipeline.
- **`_copiar_el_esqueleto_del_validador`**: MEDIDO que quitar cualquiera de sus
  entradas da **ROJO con fichero y linea nombrados**. Es **bomba de
  mantenimiento, no agujero**. 1.4 lo deja nombrado y nada mas.
- **`test_no_literal_colors_in_views`**: su enumeracion es la misma clase; 1.3 la
  delata y 1.4 le exige justificacion escrita. Su cobertura real se arregla en otro
  ciclo.
- **`test_dead_code_ast_guard`**: su control negativo es casi tautologico, pero ya
  deriva el alcance y no es un agujero.
- **Los 24 guards (a) restantes**: sin medir uno a uno. El reparto exacto (b)/(c) de
  los 80 guards estructurales lo cierra el `mutation-auditor`.
- **`src/woptimizer/**`: cero ediciones.**