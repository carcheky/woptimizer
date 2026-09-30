import pathlib
p = pathlib.Path("README.md"); c = p.read_text(encoding="utf-8")
c = c.replace("ciclos-19-blue", "ciclos-20-blue").replace("tests-48%20verdes", "tests-57%20verdes")
p.write_text(c, encoding="utf-8")
p = pathlib.Path("STATUS.md"); c = p.read_text(encoding="utf-8")
c = c.replace("**48 tests**: 47 backend + 1 headless UI", "**57 tests**: 56 backend + 1 headless UI")
c = c.replace("#14 a #19 SIN COMMIT", "#14 a #20 SIN COMMIT").replace("los ciclos #14 a #19 est", "los ciclos #14 a #20 est").replace("ciclos #14 a #19:", "ciclos #14 a #20:")
c = c.replace("- **Ciclos Completados:** 19 (`rd_journal.json` actualizado).\n- **Ciclo Actual #20:** Paso 1 - la tarea activa es `TASK-027` (robustitud de UI).\n- **Ultima Accion:** Ciclo #19 TASK-031 - la rotacion de copias machacaba el `.bak` sano al arrancar. **48 tests en verde, Paso 4 = PASS tras 3 iteraciones, sin commit por bloqueo del entorno.**",
  "- **Ciclos Completados:** 20 (`rd_journal.json` actualizado).\n- **Ciclo Actual #21:** Paso 1 - la tarea activa es `TASK-028` (deuda tecnica).\n- **Ultima Accion:** Ciclo #20 TASK-027 - arranque de apps sin `shell`, orden de categorias real y favorites. **57 tests en verde, Paso 4 = PASS tras 3 iteraciones, sin commit por bloqueo del entorno.**")
c = c.replace("| 2 | Gaming & Telemetr", "| 2 | Gaming & Telemetr")
c = c.replace("**Tarea activa: `TASK-027`**. Backlog: `TASK-028`, `TASK-029`", "**Tarea activa: `TASK-028`**. Backlog: `TASK-029`")
c = c.replace("| 2 | Gaming & Telemetría UX | **#14** |", "| 2 | Gaming & Telemetría UX | **#20** |")
p.write_text(c, encoding="utf-8")
print("README y STATUS actualizados")
