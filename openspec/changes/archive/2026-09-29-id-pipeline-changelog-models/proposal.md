# Change: id-pipeline-changelog-models

## Why

El motor autónomo de I+D (`id-pipeline`) lleva 10 ciclos completados (`.taskmaster/rd_journal.json`). El estado por ciclo se registra correctamente en `rd_journal.json` y el dashboard `STATUS.md` resume los hitos, pero:

1. **Falta un changelog humano- legible por pase**: `rd_journal.json` es machine-readable pero sin narrativa, y `STATUS.md` solo resume hitos (no cada ciclo individual). El usuario pide explícitamente un changelog de cada pasada.

2. **La alternancia de modelos no está formalizada**: la skill actual menciona `Modelo Recomendado` en una tabla del Paso 1 (descubrimiento) y algunos `Model:` en las plantillas de invocación, pero no hay una matriz consolidada paso + área, ni reglas claras de cuándo upgradear/downgradear modelo.

3. **No hay obligation explícita**: sin marcar como `MANDATORY` en la skill, es fácil que un agente en bucle perpetuo se salte el changelog durante un sprint largo.

## What Changes

- **NUEVO** `.taskmaster/CHANGELOG.md` — changelog append-only, una entrada por ciclo, con plantilla fija que incluye modelos usados por paso, outcome, commits, tests y docs afectados.
- **MODIFICADO** `.agents/skills/id-pipeline/SKILL.md`:
  - Añadir **Sección 6: Changelog obligatorio por pase** — cuándo y cómo escribir la entrada en `CHANGELOG.md`.
  - Añadir **Sección 7: Matriz de modelos consolidada** — qué modelo usar para cada combinación (paso × área × tamaño de cambio).
  - Marcar ambos bloques como **MANDATORY** en negrita con icono.
  - Hacer referencia cruzada entre `rd_journal.json` (machine), `STATUS.md` (dashboard) y `CHANGELOG.md` (per-pass human).
- **MODIFICADO** `AGENTS.md` — añadir una línea en "Skills Disponibles" o en una nueva mini-sección sobre el motor de I+D que mencione `CHANGELOG.md` como artefacto del pipeline.
- **MODIFICADO** `llms.txt` — añadir `.taskmaster/CHANGELOG.md` a la lista de recursos de orquestación.
- **MODIFICADO** `validate_docs.py` — añadir check de existencia y formato mínimo de `CHANGELOG.md`.

## Impact

- **Capabilities affected**: workflow / documentación / trazabilidad (meta).
- **Size**: mediano (1 nueva capability en `.taskmaster/`, skill refactor, 3 docs tocados).
- **Risks**:
  - **R1**: el changelog se vuelva ceremonia pesada y los agentes lo rellenen con Lorem Ipsum. Mitigación: plantilla fija con bullets cortos; cada bullet ≤1 frase.
  - **R2**: cambio de skill rompa el bucle perpetuo actual. Mitigación: añadir como **aditivo**, no modificar el flujo existente (los pasos 1-2-3 quedan igual).
  - **R3**: modelos cambiados dinámicamente se vuelvan incompatibles con subagentes que esperan `inherit`. Mitigación: documentar override explícito; mantener `inherit` como default seguro.
- **Tests required**:
  - `python validate_docs.py` pasa con la nueva check.
  - Backfill manual de los últimos 5 ciclos en `CHANGELOG.md` (sanity check visual).
- **Documentation**: este cambio actualiza `.agents/skills/id-pipeline/SKILL.md` que es la doc viva del motor.

## Acceptance criteria

1. ✅ `.taskmaster/CHANGELOG.md` existe con plantilla + ≥5 entradas backfilled (de cycles 6-10).
2. ✅ `.agents/skills/id-pipeline/SKILL.md` incluye Sección 6 (changelog MANDATORY) y Sección 7 (matriz de modelos).
3. ✅ `AGENTS.md` menciona `CHANGELOG.md` como artefacto del motor.
4. ✅ `llms.txt` enlaza a `.taskmaster/CHANGELOG.md`.
5. ✅ `validate_docs.py` valida existencia + formato mínimo del changelog (encabezado + ≥1 entrada).
6. ✅ No se rompió nada: `python run_tests.py` y `python verify_ui_syntax.py` siguen pasando (no tocamos código de `src/`).
7. ✅ Cambio archivado en `openspec/changes/archive/2026-09-29-id-pipeline-changelog-models/`.

## Plantilla de entrada del CHANGELOG.md (sección 6 de la skill)

```markdown
## [CYCLE-NNN] YYYY-MM-DD HH:MM — <slug>
**Área**: <de la matriz de rotación>
**Change**: openspec/changes/<slug>/
**Estado**: COMPLETED | BLOCKED | ROLLED-BACK
**Models**:
- Paso 1 (Buscar): <modelo>
- Paso 2 (Planear): <modelo>
- Paso 3 (Ejecutar): <modelo>

### What
- <bullets cortos concretos>

### Outcome
- Commits: `<hash1>`, `<hash2>`
- Tests: <n>/<total> PASS
- Docs: <qué docs/ai/ se actualizó>

### Impact
<1-2 frases>
```
