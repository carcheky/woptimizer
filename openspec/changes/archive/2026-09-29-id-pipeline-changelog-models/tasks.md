# Tasks for id-pipeline-changelog-models

## 1. Crear `.taskmaster/CHANGELOG.md`

- [ ] Escribir plantilla + entrada placeholder para el ciclo actual (#11)
- [ ] Backfill manual de los últimos 5 ciclos (6-10) copiando de `rd_journal.json`
- [ ] Mantenerlo append-only (regla explícita en cabecera)

## 2. Extender `.agents/skills/id-pipeline/SKILL.md`

- [ ] Añadir Sección 6 "Changelog obligatorio por pase" (MANDATORY)
  - Cuándo: al final del Paso 3, antes del retorno al Paso 1.
  - Dónde: `.taskmaster/CHANGELOG.md`.
  - Formato: plantilla fija (incluida en la skill).
- [ ] Añadir Sección 7 "Matriz de modelos consolidada"
  - Tabla: Paso × Área → Modelo recomendado.
  - Reglas de override (cuándo upgradear a `pro`, cuándo bajar a `flash`).
  - Default seguro: `inherit`.
- [ ] Hacer referencia cruzada `rd_journal.json` (machine) ↔ `CHANGELOG.md` (per-pass human) ↔ `STATUS.md` (dashboard).

## 3. Actualizar `AGENTS.md`

- [ ] Mini-sección en "Skills Disponibles" o nueva sub-sección "Motor de I+D" mencionando `CHANGELOG.md`.

## 4. Actualizar `llms.txt`

- [ ] Añadir link a `.taskmaster/CHANGELOG.md` en la sección de Orquestación de Tareas.

## 5. Extender `validate_docs.py`

- [ ] Check de existencia de `.taskmaster/CHANGELOG.md`.
- [ ] Check de formato mínimo: encabezado `# Changelog de pases — Motor id-pipeline` + ≥1 entrada `[CYCLE-NNN]`.
- [ ] Re-ejecutar y verificar todo OK.

## 6. No romper nada

- [ ] `python run_tests.py` (no tocamos `src/`, debería seguir pasando).
- [ ] `python verify_ui_syntax.py` (idem).

## 7. Archivar

- [ ] `git add openspec/changes/2026-09-29-id-pipeline-changelog-models/ .agents/skills/id-pipeline/SKILL.md .taskmaster/CHANGELOG.md AGENTS.md llms.txt validate_docs.py`
- [ ] `python .taskmaster/git_safe_commit.py "chore(id-pipeline): changelog obligatorio + matriz de modelos"`
- [ ] Mover `openspec/changes/2026-09-29-id-pipeline-changelog-models/` → `openspec/changes/archive/`
- [ ] Re-leer `AGENTS.md` (regla del usuario).
