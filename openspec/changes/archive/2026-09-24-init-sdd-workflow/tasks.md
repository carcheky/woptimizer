# Tasks for init-sdd-workflow

## 1. Crear estructura `openspec/`

- [x] Crear `openspec/specs/woptimizer/` y `openspec/changes/archive/`
- [x] Escribir `openspec/README.md` (cómo usamos OpenSpec)
- [x] Escribir `openspec/specs/woptimizer/spec.md` (formato SHALL)

## 2. Escribir propuesta de demo (este cambio)

- [x] Crear `openspec/changes/2026-09-24-init-sdd-workflow/proposal.md`
- [x] Crear `openspec/changes/2026-09-24-init-sdd-workflow/tasks.md` (este archivo)

## 3. Backfill del cambio v2.1.0 en archive

- [ ] Crear `openspec/changes/archive/2026-09-24-standalone-exe/proposal.md`
- [ ] Crear `openspec/changes/archive/2026-09-24-standalone-exe/tasks.md`

## 4. Carga selectiva con llms.txt

- [ ] Crear `llms.txt` en raíz (índice curado LLM-friendly)
- [ ] Crear `llms-full.txt` en raíz (texto completo)

## 5. Configurar mkdocs

- [ ] Crear `mkdocs.yml` con nav desde `docs/`
- [ ] Verificar `mkdocs build` (dry-run via `mkdocs build --strict`) — si hay warning, fix

## 6. Actualizar AGENTS.md

- [x] Spec rev 10 → 11
- [x] Añadir sección "📜 Spec-Driven Development (SDD) — flujo OBLIGATORIO"
- [x] Actualizar "📚 Documentación relacionada" con llms.txt, openspec/
- [x] Changelog del spec: entrada rev 11

## 7. Validar (Validate-Yourself)

- [ ] `python -c "import py_compile; py_compile.compile('process_manager.py', doraise=True)"` sigue OK (regression check)
- [ ] `python verify_app.py` — GUI sigue arrancando
- [ ] Listado de archivos `openspec/` y raíz cuadra con acceptance criteria
- [ ] Re-leer `AGENTS.md` (regla del usuario: spec al inicio Y al final)

## 8. Cerrar propuesta

- [ ] Commit con mensaje: `init-sdd-workflow: adopta OpenSpec + llms.txt`
- [ ] Mover `openspec/changes/2026-09-24-init-sdd-workflow/` → `openspec/changes/archive/`