# Los cinco tickets de trazabilidad que dejó CYCLE-054

**Change ID:** `2026-10-05-trazabilidad-ciclo-054`
**Área:** Testing & Calidad / Documentación & Arquitectura
**Origen:** los cinco tickets nombrados y medidos por el `mutation-auditor` en CYCLE-054,
fila de CYCLE-054 de `STATUS.md` § *Deuda Técnica Conocida* y `.taskmaster/CHANGELOG.md` bajo
`[CYCLE-054]`. El backlog de `.taskmaster/tasks.json` está vacío (66/66 `completed`), luego
esta es Deuda Técnica Conocida y es **elegible y prioritaria** por la regla de precedencia.

**Estado:** PLAN. `HEAD a82dca5` en `beta`, `validate_docs.py` en **126 OK / 0 FAIL** (medido
este ciclo, RC=0), suite en **159** = **112 backend + 47 headless**.

---

## 1. Por qué es UN ciclo y no cinco tareas

Los cinco son la misma clase de fallo y el mismo arreglo: **una promesa escrita que nada mide**.
En los cinco hay un texto que afirma una cosa y un mecanismo que no la vigila, y en los cinco el
texto es el que gana cuando discrepa. T54-2 y T54-4 son los dos que dejan el hueco de guard; T54-1,
T54-5 y T54-6 son una o dos líneas. Partirlos en cinco tareas daría cinco commits, cinco
verificaciones del validador y cinco mutaciones de paperwork para un resultado que es una sola
invariante.

**La invariante común, y el criterio de cierre del ciclo:**

> Toda afirmación escrita que este ciclo toca tiene que ir acompañada del guard que la
> comprueba, y toda cita de línea que este ciclo toca tiene que apuntar a la línea que dice.

Consecuencias concretas que hacen del ciclo uno solo:

- **Un solo criterio de recuento.** Ninguna de las cinco subtareas añade una función `test_*()`
  nueva: las sondas van **dentro** de tests que ya existen. El total sigue siendo **159**, el
  reparto sigue siendo **112 + 47**, y los cuatro declarantes (`STATUS.md`, `AGENTS.md`,
  `README.md`, `docs/ai/testing-guide.md` tabla 1..159) **no se tocan**. Si alguna añadiera un
  test, el ciclo arrastraría el recuento y su tabla, y eso sería trabajo de andamiaje, no de
  trazabilidad.
- **Un solo guard nuevo** (el del contenido del agregado, T-1) y **una sola medición** que lo
  valida.
- **Una sola regla para las citas** (T-4) que se aplica a los tres sitios donde vive la misma
  cita rota.

## 2. Orden y agrupamiento

| Sub | Ticket | Peso | Qué es |
|---|---|---|---|
| **T-1** | T54-4 🟡 MEDIA | el más pesado | El agregado `llms-full.txt` está caducado y sin guard de contenido |
| **T-2** | T54-2 🟡 MEDIA | el más pesado | La 4.ª forma de extracción y el reconocimiento de vallas no los vigila nadie |
| **T-3** | T54-1 🟡 BAJA | una línea de datos | La capa `#` del filtro de la regla de rama no tiene guard |
| **T-4** | T54-5 🟡 BAJA | re-anclar | Las citas de línea no apuntan a lo que dicen |
| **T-5** | T54-6 🟡 BAJA | una frase | Una afirmación refutada por mutación, y su lección general |

**Orden de ejecución: T-1 → T-2 → T-3 → T-4 → T-5.** T-1 primero porque su guard nuevo es la
herramienta con la que se comprueban los demás: el verificador de citas de T-4 necesita leer el
agregado, y el agregado lo reconstruye T-1. T-5 el último, porque su lección es la que se
escribe después de haber tenido las cinco delante.

---

## T-1 · T54-4 · el agregado y su guard de contenido

### Medición (este ciclo, con `ast` y comparación de contenido)

Secciones reales del agregado, cortando por el marcador `<!-- source: -->` y saltando vallas:

| Sección | Fuente | Líneas de contenido de la fuente | Ausentes en su sección | Divergencia |
|---|---|---|---|---|
| `api` | `docs/api.md` | 91 | 90 | **98,9 %** |
| `known-issues` | `docs/known-issues.md` | 304 | 176 | **57,9 %** |
| `github-setup-checklist` | `docs/GITHUB-SETUP-CHECKLIST.md` | 501 | 91 | **18,2 %** |
| `testing` | `docs/testing.md` | 69 | 11 | **15,9 %** |
| `architecture` | `docs/architecture.md` | 75 | 0 | 0 % |
| `extending` | `docs/extending.md` | 69 | 0 | 0 % |
| `index` | `docs/index.md` | 43 | 0 | 0 % |
| `mini-app-status` | `docs/mini-app-status.md` | 68 | 0 | 0 % |
| `ui-design-system` | `docs/ai/ui-design-system.md` | 511 | 0 | 0 % |

**4 de 9 secciones divergen**, que confirma el ticket. (Las cifras del auditor fueron 109/109,
189/381, 93/542 y 11/128; cuentan líneas crudas y no de contenido. La dirección y el número de
secciones afectadas coinciden.)

### EL HALLAZGO QUE CAMBIA EL TRATO: `api.md` es el BUENO

El briefing hipotetizaba que `api.md` al 100 % divergente podía ser "otro texto" y que había que
medir si el agregado lo.replaceaba entero. Medido, **la dirección es la contraria**:

- **`docs/api.md` es el documento VIGENTE.** Se titula *"Referencia de API (v3)"*, describe
  `ProcessService` en `src/woptimizer/services/`, cita `psutil` 5 veces y
  `SYSTEM_PROTECTED_PROCESSES`, y menciona `process_manager` **0 veces**. Todo lo que nombra
  existe: `src/woptimizer/services/process_service.py` está en disco.
- **El agregado lleva el fósil v2.** `llms-full.txt:12` es *"## Funciones de `process_manager.py`
  (módulo)"*, `llms-full.txt:29` *"Muestra messagebox de error si PowerShell falla"*, y el PID va
  *"string (de PowerShell)"*. `src/woptimizer/process_manager.py` **no existe** y no aparece en
  el árbol de `src/` de ninguna forma.

**Consecuencia de diseño, y es la razón de no hacer `.replace()`:** un reemplazo agregado→fuente
escribiría el fósil v2 encima del documento correcto. La única dirección segura es
**fuente→agregado**, y por eso el arreglo es un **generador**, no una reparación.

### El formato ya está escrito en el fichero

El agregado no es un volcado a mano: cada una de las 9 secciones lleva su procedencia y su
separador, y el patrón es de cinco líneas exactas:

```
# <slug>
<vacía>
<!-- source: docs/<fichero>.md -->
<vacía>
---
<vacía>
<cuerpo de la fuente>
```

Los 9 marcadores están medidos en `llms-full.txt:4,171,330,493,1023,1123,1422,1555,1736`. O sea
que **la convención de la que depende el generador ya existe** y verificada; lo que falta es el
generador que la obedece y el guard que la verifica.

### Decisión de diseño

1. **Generador versionado**, en la raíz siguiendo la convención de los scripts del repo
   (`validate_docs.py`, `verify_ui_syntax.py`, `force_build.py`): `build_llms_full.py`, con dos
   modos, `--write` y `--check`.
   - `--write` re-emite el agregado desde las fuentes nombradas en los marcadores, en el orden
     de los marcadores, con el formato de cinco líneas.
   - `--check` **no escribe**: compara el cuerpo de cada sección con su fuente y sale con código
     distinto de 0 si algo diverge. Es el guard.
   - Un `llms-full.txt` que se regenera a mano es exactamente el `tm.py` que este repo ya sufrió;
     por eso el generador es un fichero versionado con dos modos y no un paso documentado.
2. **El guard va en `validate_docs.py`, no solo en el script.** El check 2 de
   `validate_docs.py:2143-2157` pasa a asentar por el generador. Hoy mira
   `if d not in full` (`:2153`), que es el **nombre** del fichero; el check nuevo compara el
   **cuerpo** y además exige que el conjunto de secciones sea el que el generador declara.
3. **La lista de fuentes se declara en un solo sitio y ese sitio es el generador.** Hoy el check
   2 deriva su lista de `os.listdir(docs_dir)` filtrando `.md` (`:2152`), lo que le da una lista
   distinta de la del agregado sin que nadie lo note: el agregado trae 9 secciones y
   `validate_docs.py` espera las de `docs/` de primer nivel, y el desajuste de `ui-design-system`
   (que viene de `docs/ai/`) no lo detecta nadie porque su nombre sí aparece.

### EL HALLAZGO NUEVO: la colisión de slug `architecture` (T54-7)

**MEDIDO:** `docs/architecture.md` son 6 255 bytes y `docs/ai/architecture.md` son **62 819** bytes.
Los dos se llaman `architecture`. La sección `# architecture` del agregado trae la fuente
**pequeña** (0 % de divergencia contra `docs/architecture.md`, y el contenido de la grande no
está). Un generador quederive su fuente del **slug** —que es lo natural, porque el slug es lo que
aparece en la cabecera— elegiría la fuente equivocada para una de las nueve y publicaría un
documento de 6 KB donde debía ir uno de 62 KB, **sin ningún error visible**.

**Por eso el generador se indexa por la RUTA del marcador `<!-- source: -->`, nunca por el
slug.** Y por eso el slug es solo etiqueta de navegación. Esto no estaba en la lista de cinco.

### Criterio de cierre de T-1

- `python build_llms_full.py --check` sale **0** en el árbol limpio y **distinto de 0** en un
  árbol donde se edita una sola línea de una sola fuente, nombrando fichero y sección.
- `validate_docs.py` sigue en **0 FAIL** con el agregado regenerado, y su recuento de OK
  **sube** (un check nuevo más) sin que eso rompa a nadie: las cifras de OK en prosa llevan
  "de aquel día" y fecha.
- Las 9 secciones del agregado tienen **0 % de divergencia** contra su fuente.
- Cero ediciones en `src/`.

---

## T-2 · T54-2 · la 4.ª forma y el reconocimiento de vallas

### Medición (funciones reales extraídas con `ast` y ejecutadas sobre los ficheros reales)

- `total` sobre los ficheros reales = **11**, y con el mutante `P2-SIN-GIT-COMMIT` (quitar la
  alternativa `git commit … -m "…"` del patrón de valla) sigue siendo **11**. El
  `assert total >= 6` (`run_tests.py:18303`) **no lo nota**.
- Líneas dentro de una valla plantilla: **45** (`SKILL.md` 40, `AGENTS.md` 5), y **45** con el
  mutante puesto.
- Líneas que **solo** la 4.ª forma puede ver: **0**. Por eso `total` no se mueve: en los ficheros
  reales no hay ni una ocurrencia que dependa de la 4.ª forma.
- El docstring de `_destinos_de_versionado_de_un_fichero` (`run_tests.py:18204-18222`) promete
  cuatro formas y que `total` cuenta "todo lo extraído". Es **falso** en la parte de `total`, y
  eso es lo que hay que arreglar.

### Por qué la sonda que ya existe no lo coge

La mitad 1 de `test_ninguna_plantilla_de_commit_nombra_main` (`run_tests.py:18317-18328`) monta
una valla plantilla cuya marca es `git_safe_commit.py "…"`, y con el mutante **sigue disparando**
(medido: `[(3, 'git push origin main')]`, PASA). La sonda que falta es la de una valla cuya
**única** marca es `git commit … -m "…"`, que con el mutante sale `[]` (MUERE) y sin él dispara.

### Criterio discriminante exacto

Una fila nueva dentro de `test_ninguna_plantilla_de_commit_nombra_main` (**no un test nuevo**):

1. **La sonda de la 4.ª forma por la otra marca.** Valla plantilla con
   `git commit -m "…"` y `git push origin main` sin comillas dentro, y se exige que salga como
   infracción. *Falla sin el fix* porque el mutante deja de reconocer esa valla como plantilla y
   la cuarta forma no la ve: sin la fila, el mutante sobrevive a los 159.
2. **La fila de `de_plantilla` no vacía.** El extractor tiene que devolver líneas de plantilla
   sobre los ficheros reales. *Falla sin el fix* porque hoy `total` no baja de 6 ni con el
   reconocimiento de vallas muerto, y esta fila es la que ata el reconocimiento a una cifra
   medida en lugar de a una promesa del docstring.
3. **El docstring pasa a decir la verdad.** `total` cuenta las tres formas entrecomilladas y la
   cuarta **solo cuando hay ocurrencia**, y eso está escrito, con la medición que lo justifica.

**Posición de la sonda:** dentro del test existente, que está **antes** del marcador headless de
`run_tests.py:20770`, luego va al recuento de **backend**. No abre ventana: no usa `psutil`, ni
tkinter, ni la red. **Cero cambio en 159 y en 112 + 47.**

### Criterio de cierre de T-2

- El mutante `P2-SIN-GIT-COMMIT` sobre una **copia** deja la suite en rojo, y el rojo lo produce
  una de las dos filas nuevas, no el `assert total >= 6`.
- `run_tests.py` sigue en 159 y el reparto sigue en 112 + 47.
- Cero ediciones en `src/`.

---

## T-3 · T54-1 · la capa `#` del filtro de la regla de rama

### Medición (mutación real, en memoria, sin tocar el repo)

| Escenario | Resultado |
|---|---|
| Hoy, sin mutante | VERDE |
| Hoy, con el filtro tirando también de `#` | **VERDE → P1-18 sobrevive** |
| Con el arreglo, sin mutante | VERDE (no crea un rojo nuevo) |
| Con el arreglo **+** el mutante | **ROJO**, motivo literal: *"un ENCABEZADO con `#` es contenido valido en markdown y no se puede excluir"* |

El arreglo verificado es de **una línea de datos de test**: en `en_encabezado`
(`run_tests.py:18079-18080`) las frases pasan de la línea **siguiente** al encabezado a estar
**sobre** la línea del encabezado. Hoy están en la siguiente, y por diseño el control no puede
morir: si el filtro se lleva los encabezados, la línea siguiente sobrevive igual.

**Lo que NO es el arreglo**, y queda escrito para que nadie lo intente: **excluir `#` del filtro**
abre otro hueco del mismo tipo (en markdown `#` es encabezado y las reglas empiezan con `>`, así
que una regla en un encabezado es contenido válido). El arreglo es el dato, no el filtro.

### Criterio discriminante exacto

- El control 3 pasa a exigir que las dos frases **sobre** la línea del encabezado sobrevivan al
  recorte, con el motivo literal que ya está escrito en el assert. *Falla sin el fix* porque con
  el mutante el recorte devuelve `''` y el assert de "es contenido valido" salta.
- El docstring de `test_la_regla_de_rama_no_vive_en_un_comentario_ni_en_una_valla`
  (`run_tests.py:18016-18028`) deja de decir que ese control "no lo impide" y "es una
  CONSTATACION, no una guarda": después del arreglo **sí** es una guarda, y el docstring que dice
  lo contrario es otra promesa falsa de la misma clase.

**Posición de la sonda:** dentro del test existente, antes del marcador headless, sin ventana.
**Cero cambio en 159 y en 112 + 47.**

### Criterio de cierre de T-3

- P1-18 sobre una copia deja la suite en rojo por la fila del encabezado.
- El docstring y el comportamiento coinciden.
- `_sin_la_capa_que_el_bucle_no_lee` **no** excluye `#`.

---

## T-4 · T54-5 · las citas de línea

### Medición (esta es la parte que cambia respecto al ticket)

El ticket dice "las citas de D5/D7/D8/D10 no apuntan a lo que dicen (tres de cuatro se van
18-42 líneas)". Medido el estado actual:

| Afirmación | Estado real | Evidencia |
|---|---|---|
| **D5** `release-pipeline.md:54` → la real es `:87` | **YA CORREGIDA** | `docs/GITHUB-SETUP-CHECKLIST.md:240` cita ya `:87`, y `release-pipeline.md:87` es la línea que habla de `softprops` |
| **D7** el checklist decía que `git_safe_commit.py` salía con 0 | **YA CORREGIDA** | el texto ya no está; `git_safe_commit.py:97` es `CODE_FAIL = 1` |
| **D8** `mkdocs.yml:88` | **VIVA, y en tres sitios, no uno** | `mkdocs.yml` tiene **83** líneas y la licencia está en **81-82**. Vive en `docs/GITHUB-SETUP-CHECKLIST.md:165` (la casilla abierta), `STATUS.md:113` y `.taskmaster/CHANGELOG.md:162` |
| **D10** "peor que 8 cabeceras largas" | **YA CORREGIDA** | `docs/GITHUB-SETUP-CHECKLIST.md:321` y `llms-full.txt:799` dicen los dos **7** |

**Medición de Anchura:** de 1 433 citas `fichero:línea` del repo, **30** apuntan más allá del
final del fichero citado. **26 de las 30** están en `openspec/changes/**` y en `CHANGELOG.md`,
que son contratos e historia y **no se tocan en este ciclo**. Las 4 vivas son las de D8 de arriba.

**Así que T54-5 no es "cuatro citas rotas": es una cita rota en tres sitios.** El arreglo de las
tres es una línea cada una, y por eso es BAJA.

### Criterio de cierre de T-4

- `docs/GITHUB-SETUP-CHECKLIST.md:165`, `STATUS.md:113` y `.taskmaster/CHANGELOG.md:162` citan
  `mkdocs.yml:81-82` (o dejan de citar línea), y la casilla abierta de `LICENSE` sigue abierta
  por su motivo real, que es que **no hay `LICENSE`**, no que la cita esté mal.
- Las 26 citas de `openspec/changes/**` y `CHANGELOG.md` quedan **declaradas** como historia en
  el changelog del ciclo, con el número, y no se reescriben.
- El recuento de citas rotas del ciclo es **0 en ficheros vivos**.

---

## T-5 · T54-6 · la afirmación refutada y su lección

### Medición

La afirmación de D11 ("nada vigila la entrada de los changelogs") está **refutada por
mutación**: el check **5b** sí vigila. Quitar `## CYCLE-054` del changelog sube el validador de
1 FAIL a 2 FAIL. El guard existe (`validate_docs.py:833` `_comprobar_ancla_del_changelog`, con
ancla externa en `rd_journal.json` para que borrar el ciclo de los dos changelog no borre el
requisito).

**Lo que sí queda, y es la parte que es mía:** la lección general que T54-4 y T54-6 confirman
juntas, y que este ciclo va a demostrar por tercera vez.

> **Una cifra escrita a mano caduca en el commit, no en el mes.** El "126 OK / 0 FAIL" era
> cierto antes de `d68bf8b` y se rompió **al commitear** (el journal no tenía el ciclo 54), y
> ese rojo lo tuvo que cerrar `a82dca5` a mano.

La regla que sale de aquí, y que se escribe en `docs/ai/testing-guide.md` junto a las demás:

1. **Toda cifra de veredicto que se escriba en prosa lleva su fecha y su "de aquel día"**, como
   ya hacen `docs/GITHUB-SETUP-CHECKLIST.md:581` y `llms-full.txt:993`. Sin fecha, una cifra es
   una promesa sin ancla.
2. **Un guard que deriva la cifra de la fuente no caduca**; uno que la cuenta a mano caduca en
   el commit. El total de tests ya está así (lo deriva el check 7 con `ast`); el de OK del
   validador, todavía no, y por eso se rompe.
3. Y el corolario que este ciclo midió por lo caro: **`commitlint` mira el rango del push y la
   release la decide `.releaserc.json`** (`type:docs -> release:false`). Sin esa distinción se
   promete una release que no sale.

### Criterio de cierre de T-5

- D11 aparece en el changelog del ciclo con su refutación y la medición que la refuta
  (1 FAIL → 2 FAIL), no como afirmación.
- La regla de las tres cifras está escrita en `docs/ai/testing-guide.md`, junto a la tabla de
  159 filas, sin tocar esa tabla.
- El commit de este ciclo es `chore`/`docs` y **no** se promete ninguna release.

---

## 3. Restricciones heredadas (no se tocan)

- **Cero ediciones en `src/`.** Ni `git_safe_commit.py` (intacto desde `d68bf8b`), ni
  `run_tests.py` fuera de las filas de sonda de T-2 y T-3, ni los workflows.
- `LIMITE_CABECERA = 120` y `_RE_TASK_ANCLA` **sin relajar**.
- La rama de publicación es **aviso, no rechazo**. La rama redundante de
  `git_safe_commit.py:349-350` es **inerte de verdad** y no se toca.
- El reparto **159 = 112 + 47** y la tabla 1..159 de `docs/ai/testing-guide.md` no se tocan.
- S3, S7, S8, P3, H1, H2, H3 y los 8 mutantes que un turno dio por no remedidos: cerrados.
- Todo commit por `python .taskmaster/git_safe_commit.py "<mensaje> (TASK-067)"`, con
  `GIT_DIR` **y** `GIT_WORK_TREE` (la puerta exige paridad), y con `git status --porcelain`
  vacío antes de cada `add -A`.

## 4. Verificación del ciclo

1. `python run_tests.py` → 159, reparto 112 + 47, y el mutante `P2-SIN-GIT-COMMIT` y `P1-18`
   muertos **por filas concretas**, no por el `assert total >= 6`.
2. `python build_llms_full.py --check` → 0, y ≠ 0 ante una línea editada en una fuente.
3. `python validate_docs.py` → 0 FAIL, con un OK más que antes y la cifra en prosa fechada.
4. `python verify_ui_syntax.py` → EXITO.
5. `python .taskmaster/sync_agents.py --check` → exit 0.
6. Ninguna cita `fichero:línea` rota en ficheros vivos.
