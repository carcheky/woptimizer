import pathlib, re
p = pathlib.Path("CHANGELOG.md")
lines = p.read_text(encoding="utf-8").split("\n")
# localizar el encabezado huerfano de 018
for i, l in enumerate(lines):
    if l.startswith("**Resiliencia & Robustez**") and "TASK-030" in l:
        # insertar el encabezado 2 lineas antes del separador
        j = i - 1
        while j >= 0 and lines[j].strip() == "":
            j -= 1
        k = j
        while k >= 0 and lines[k].strip() == "---":
            k -= 1
        lines.insert(k + 1, "## CYCLE-018 — 2026-09-30")
        lines.insert(k + 2, "")
        break
p.write_text("\n".join(lines), encoding="utf-8")
txt = p.read_text(encoding="utf-8")
print("encabezados:", re.findall(r"^## (CYCLE-\d+)", txt, re.M))
