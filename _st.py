import pathlib
p = pathlib.Path("STATUS.md")
c = p.read_text(encoding="utf-8")
reps = [
 ("**28 tests**: 27 backend + 1 headless UI", "**36 tests**: 35 backend + 1 headless UI"),
 ("#14, #15, #16 y #17 SIN COMMIT", "#14 a #18 SIN COMMIT"),
 ("los ciclos #14, #15, #16 y #17 est", "los ciclos #14 a #18 est"),
 ("Commits pendientes de los ciclos #14, #15, #16 y #17:", "Commits pendientes de los ciclos #14 a #18:"),
 ("**Abierto desde el ciclo #15, pendiente para el #17.**", "**Cerrado en el ciclo #18** (guarda de forma con `PerfilCorruptoError`)."),
 ("**Toca el ciclo #18.**", "Resuelto en el ciclo #18; la ceguidad de las HOJAS es `TASK-031`."),
 ("**Backlog activo por delante de la rotación:** `TASK-027`", "**Tarea activa: `TASK-031`** (critica). Backlog: `TASK-027`"),
 ("| 1 | Resiliencia & Robustez | **#15** |", "| 1 | Resiliencia & Robustez | **#18** |"),
]
for a, b in reps:
    if a not in c: print("NO ENCONTRADO:", a[:55])
    c = c.replace(a, b)
p.write_text(c, encoding="utf-8")
print("STATUS.md actualizado")
