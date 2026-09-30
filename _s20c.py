import pathlib
p = pathlib.Path("STATUS.md")
c = p.read_text(encoding="utf-8")
c = c.replace("**Tarea activa: `TASK-027`**. Backlog: `TASK-028`, `TASK-029`", "**Tarea activa: `TASK-028`**. Backlog: `TASK-029`")
c = c.replace("| 2 | Gaming & Telemetr\u00eda UX | **#14** |", "| 2 | Gaming & Telemetr\u00eda UX | **#20** |")
c = c.replace("#14 a #19 SIN COMMIT", "#14 a #20 SIN COMMIT")
c = c.replace("los ciclos #14 a #19 est", "los ciclos #14 a #20 est")
p.write_text(c, encoding="utf-8")
ok = ["Ciclos Completados", "Ciclo Actual", "Tarea activa"]
for l in c.split("\n"):
    if any(k in l for k in ok) or ("| 2 |" in l):
        print(" ", l.strip()[:95])
