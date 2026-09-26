# Tasks for refine-sdd-pattern

## 1. Refinar AGENTS.md

- [ ] Bumpear spec rev 11 → 12 (línea 4)
- [ ] Dentro de sección "📜 Spec-Driven Development (SDD) — flujo OBLIGATORIO", añadir sub-sección "## Decision matrix" con tabla:
  - Trivial (typo/comment fix): 0 artefactos, commit directo
  - Pequeño (1-3 archivos, <30 LOC): proposal.md (1 párrafo) + tasks.md
  - Mediano (1 feature nueva): proposal.md completo + tasks.md + code
  - Grande (cambio de capability): proposal.md + tasks.md + spec delta en `changes/<id>/specs/<cap>/spec.md`
- [ ] Añadir sub-sección "## Spec delta — formato ADDED/MODIFIED/REMOVED" con plantilla
- [ ] Añadir sub-sección "## todowrite ↔ tasks.md" con reglas de sincronización
- [ ] Añadir sub-sección "## Anti-burocracia" con heurísticas
- [ ] Changelog del spec: añadir entrada rev 12

## 2. Validar

- [ ] `python validate_docs.py` → 14/14 OK + nueva check de rev 12
- [ ] `python smoke_check.py` → 4/4 OK (process_manager.py sin tocar)

## 3. Archivar

- [ ] Mover `openspec/changes/2026-09-24-refine-sdd-pattern/` → `openspec/changes/archive/`
- [ ] Re-leer AGENTS.md (regla del usuario: spec al inicio Y al final)
- [ ] Reporte final al usuario