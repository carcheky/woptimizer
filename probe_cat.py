import json
d = json.load(open("openspec/changes/2026-10-22-el-gate-distingue-o-falla/mutaciones.json", encoding="utf-8"))
print("claves:", list(d.keys()))
print({k: v for k, v in d.items() if k != "mutaciones"})
print("n mutantes:", len(d["mutaciones"]))
for m in d["mutaciones"][:2]:
    print(json.dumps(m, ensure_ascii=False, indent=2)[:2000])
print("---- M-121 ----")
for m in d["mutaciones"]:
    if m["id"] in ("M-121", "M-90", "M-92"):
        print(json.dumps(m, ensure_ascii=False, indent=2)[:2500])
