# Change: refine-sdd-pattern

## Why

El SDD introducido en rev 11 ([`2026-09-24-init-sdd-workflow`](archive/2026-09-24-init-sdd-workflow/proposal.md)) tiene un flujo lineal de 9 pasos, pero le falta:

1. **Decisión por tamaño** — un typo en un comentario NO necesita proposal + tasks + archive. La gente deja de seguir procesos pesados.
2. **Spec delta** — los cambios que afectan capabilities (kill, profiles, gaming, executable) deben formalizar QUÉ requisitos cambian (ADDED/MODIFIED/REMOVED), no solo listarlos en la proposal.
3. **todowrite ↔ tasks.md binding** — sin una regla explícita de cómo se sincronizan, los agentes duplican trabajo o pierden tracking.
4. **Ejemplo vivo** — sin un sample completo visible en AGENTS.md, cada agente reinventa el patrón.

El usuario pidió "patrón muy claro y sostenible para humanos e ias, sobre todo ias". Esto lo hace explícito sin añadir burocracia a cambios triviales.

## What Changes

- **MODIFICADO** `AGENTS.md`:
  - Spec rev 11 → 12.
  - Sección "📜 Spec-Driven Development (SDD) — flujo OBLIGATORIO" ampliada con:
    - **Decision matrix** (trivial / pequeño / mediano / grande) → qué artefactos requiere cada uno.
    - **Spec delta** — `openspec/changes/<id>/specs/<cap>/spec.md` con formato ADDED/MODIFIED/REMOVED. Opcional salvo para cambios grandes.
    - **todowrite integration** — reglas de sincronización con `tasks.md`.
    - **Anti-burocracia** — heurísticas para evitar sobre-procesar.
  - Changelog del spec: entrada rev 12.
- **NO TOCADO**: `process_manager.py`, tests, builds, docs/.
- **NO TOCADO**: estructura `openspec/` (carpetas `specs/`, `changes/`, `archive/` siguen igual).

## Impact

- **Capabilities affected**: `woptimizer` (workflow — meta-cambio).
- **Risks**:
  - **Riesgo 1**: la matriz de decisión introduzca ambigüedad ("¿es trivial o pequeño?"). Mitigación: ejemplos concretos por cada tamaño en la sección.
  - **Riesgo 2**: spec delta genere burocracia. Mitigación: solo obligatoria para cambios de capability; pequeños/medianos no la necesitan.
  - **Riesgo 3**: agentes nuevos no lean la matriz. Mitigación: AGENTS.md sigue siendo la spec única, se lee al inicio SIEMPRE.
- **Tests required**:
  - ✅ `validate_docs.py` sigue pasando (estructura sin cambios estructurales).
  - ✅ `smoke_check.py` (process_manager.py no tocado).
- **Documentation**: este cambio ES el refinamiento de la doc.

## Acceptance criteria

1. ✅ AGENTS.md rev 12 (verificable con `validate_docs.py`).
2. ✅ Sección SDD incluye decision matrix con 4 categorías y ejemplos.
3. ✅ Spec delta documentado con formato ADDED/MODIFIED/REMOVED.
4. ✅ todowrite ↔ tasks.md reglas explícitas (cuándo se sincroniza, qué items, cuándo se marca done).
5. ✅ `validate_docs.py` y `smoke_check.py` siguen 100% OK.
6. ✅ Esta propuesta archivada en `openspec/changes/archive/`.