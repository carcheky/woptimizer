import pathlib
p = pathlib.Path("STATUS.md")
c = p.read_text(encoding="utf-8")
reps = [
 ("**36 tests**: 35 backend + 1 headless UI", "**48 tests**: 47 backend + 1 headless UI"),
 ("#14 a #18 SIN COMMIT", "#14 a #19 SIN COMMIT"),
 ("los ciclos #14 a #18 est", "los ciclos #14 a #19 est"),
 ("Commits pendientes de los ciclos #14 a #18:", "Commits pendientes de los ciclos #14 a #19:"),
 ("- **Ciclos Completados:** 18 (`rd_journal.json` actualizado).\n- **Ciclo Actual #19:** Paso 1 — la tarea activa es `TASK-031`.\n- **Última Acción:** Ciclo #18 TASK-030 — cerrados los 3 supervivientes de mutación del #17. **36 tests en verde, Paso 4 = PASS, sin commit por bloqueo del entorno.**",
  "- **Ciclos Completados:** 19 (`rd_journal.json` actualizado).\n- **Ciclo Actual #20:** Paso 1 — la tarea activa es `TASK-027` (robustidad de UI).\n- **Última Acción:** Ciclo #19 TASK-031 — la rotación de copias machacaba el `.bak` sano al arrancar. **48 tests en verde, Paso 4 = PASS tras 3 iteraciones, sin commit por bloqueo del entorno.**"),
 ("| 1 | Resiliencia & Robustez | **#18** |", "| 1 | Resiliencia & Robustez | **#19** |"),
 ("**Tarea activa: `TASK-031`** (critica). Backlog: `TASK-027`", "**Tarea activa: `TASK-027`**. Backlog: `TASK-028`, `TASK-029`"),
]
for a, b in reps:
    if a not in c: print("NO ENCONTRADO:", a[:60])
    c = c.replace(a, b)
p.write_text(c, encoding="utf-8")
print("ok")
