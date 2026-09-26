# Change: init-sdd-workflow

## Why

Hasta v2.1.0 el proyecto seguía Spec-First solo en AGENTS.md, sin una estructura formal de propuestas. Esto dificulta:

1. **Trazabilidad**: no hay historial de por qué cada cambio se hizo.
2. **Carga selectiva**: los agentes IA consumen todo `docs/` sin índice, gastando tokens.
3. **Reproducibilidad**: nuevos agentes no saben qué pasos seguir — el flujo está en prosa, no en artefactos.

Adoptar el patrón OpenSpec (Fission-AI, https://openspec.dev/) + el estándar llms.txt (Jeremy Howard / Answer.AI v2) nos da un flujo disciplinado sin dependencias externas.

## What Changes

- **NUEVO** `openspec/` con estructura `specs/<cap>/spec.md` + `changes/<id>/` + `changes/archive/`.
- **NUEVO** `openspec/README.md` documentando la convención adoptada.
- **NUEVO** `openspec/specs/woptimizer/spec.md` — capacidad raíz con requisitos `SHALL`.
- **NUEVO** `openspec/changes/2026-09-24-init-sdd-workflow/` (esta propuesta + tasks).
- **NUEVO** `openspec/changes/archive/2026-09-24-standalone-exe/` — backfill del cambio v2.1.0 ya cerrado, para mostrar el patrón.
- **NUEVO** `llms.txt` en raíz — índice curado LLM-friendly (estándar Answer.AI).
- **NUEVO** `llms-full.txt` en raíz — versión completa concatenada.
- **NUEVO** `mkdocs.yml` — config para servir `docs/` (estaba `requirements-mkdocs.txt` pero faltaba el yml).
- **MODIFICADO** `AGENTS.md`:
  - Spec rev 10 → 11.
  - Nueva sección "📜 Spec-Driven Development (SDD) — flujo OBLIGATORIO" entre Agent Role y Project Overview.
  - Sección "📚 Documentación relacionada" ahora enlaza `llms.txt`, `llms-full.txt`, `openspec/specs/`, `openspec/changes/`, `openspec/changes/archive/`.
  - Changelog del spec: entrada rev 11.
- **NO TOCADO**: `process_manager.py` ni tests. Esta propuesta es **solo docs/spec**.

## Impact

- **Capabilities affected**: `woptimizer` (alta — se crea spec inicial).
- **Risks**:
  - **Riesgo 1**: un agente nuevo no lea `llms.txt` y se trague todos los docs → desperdicia tokens pero no rompe nada.
  - **Riesgo 2**: humanos ignoren el flujo SDD → el spec es opt-in, no enforced por tooling. Mitigación: AGENTS.md lista el flujo en sección "Always" al leer el spec.
  - **Riesgo 3**: `mkdocs.yml` rompa builds locales → mínima, el yml es estándar mkdocs-material.
- **Tests required**:
  - ✅ No aplica — esta propuesta es 0% código.
  - ✅ `python -c "import py_compile; py_compile.compile('process_manager.py', doraise=True)"` debe seguir pasando (no tocamos código pero confirmamos).
- **Documentation**: este cambio ES la documentación. Cambios en sí mismo.

## Acceptance criteria

1. ✅ Existe `openspec/` con la estructura descrita.
2. ✅ Existe `openspec/specs/woptimizer/spec.md` con formato `SHALL`.
3. ✅ Existe `openspec/changes/2026-09-24-init-sdd-workflow/{proposal.md,tasks.md}`.
4. ✅ Existe `openspec/changes/archive/2026-09-24-standalone-exe/{proposal.md,tasks.md}` (backfill de v2.1.0).
5. ✅ Existe `llms.txt` y `llms-full.txt` en raíz.
6. ✅ Existe `mkdocs.yml` en raíz con nav sobre `docs/`.
7. ✅ `AGENTS.md` tiene sección "📜 Spec-Driven Development (SDD) — flujo OBLIGATORIO".
8. ✅ Spec rev 11.
9. ✅ `process_manager.py` no modificado (diff = 0).

## Notas de investigación

Sources consulted (web_fetch + knowledge base):
- https://github.com/Fission-AI/OpenSpec — OpenSpec (70k stars, MIT).
- https://openspec.dev/ — web oficial.
- https://llmstxt.org — estándar llms.txt v2 por Jeremy Howard (sep-2024, mod ago-2026).
- https://agents.md — AGENTS.md (60k+ proyectos).
- https://github.com/agentsmd/agents.md — spec canónica AGENTS.md.

No es necesario instalar nada de npm — solo adoptamos el patrón de carpetas + el estándar llms.txt.