import json
d = json.load(open(".taskmaster/rd_journal.json", encoding="utf-8"))
ent = d if isinstance(d, list) else d.get("entradas", d)
print(type(d), len(ent))
for e in ent:
    if isinstance(e, dict):
        print(e.get("cycle"), "|", e.get("change"), "|", list(e.keys())[:12])
