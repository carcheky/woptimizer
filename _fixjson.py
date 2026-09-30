import json
p = r".taskmaster/tasks.json"
raw = open(p, encoding="utf-8").read()
d = None
for end in range(len(raw), 0, -1):
    try:
        d = json.loads(raw[:end]); break
    except Exception:
        continue
if d is None:
    raise SystemExit("no se pudo recuperar el JSON")
print("recuperado con", len(d["tasks"]), "tareas")
for t in d["tasks"]:
    if t["id"] == "TASK-030":
        t["status"] = "completed"
d["active_task_id"] = "TASK-031"
d["tasks"] = [t for t in d["tasks"] if t["id"] != "TASK-031"]
d["tasks"].append({
  "id": "TASK-031",
  "title": "Ceguidad de la guarda de forma: las HOJAS de un pack no se validan (perdida silenciosa del .bak)",
  "description": "Encontrado por mutation-auditor al cerrar TASK-030 (veredicto PASS, pero hueco nuevo de severidad ALTA). La guarda de forma de load() valida el CONTENEDOR (isinstance(perfiles, dict) e isinstance(v, dict)) pero no las HOJAS. Un pack con keepers o target_categories mal formados (p.ej. keepers como string en vez de lista) pasa la guarda, la rama legacy nunca lee esos campos, y quedan [] sin clasificarse como corrupcion: el .bak sano NUNCA se consulta y un save() posterior machaca ese .bak. Perdida silenciosa e irreversible de la copia de seguridad. Pre-existente, NO es regresion de TASK-030, pero vive en la funcion que TASK-030 endurecio y ningun test lo ve. La solucion NO es anadir mas isinstance: es validar la FORMA completa contra el modelo Pydantic antes de clasificar, y decidir explicitamente que un pack con un campo mal formado es corrupcion (y por tanto recuperable desde el .bak) en vez de un no-op silencioso.",
  "complexity": 3,
  "priority": "critical",
  "status": "pending",
  "dependencies": ["TASK-030"],
  "module": "docs/ai/data-models.md"
})
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
d2 = json.load(open(p, encoding="utf-8"))
print("JSON OK | tareas:", len(d2["tasks"]), "| active:", d2["active_task_id"])
print("pending:", [t["id"] for t in d2["tasks"] if t["status"] == "pending"])
print("TASK-030:", [t["status"] for t in d2["tasks"] if t["id"] == "TASK-030"])
