"""
validate_docs.py — valida que llms.txt cumple el formato Answer.AI v2
y que la estructura openspec/ esta completa. Sin dependencias externas.
"""
import os
import re
import sys


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    errors = []
    ok = []

    # 1. llms.txt format
    with open(os.path.join(root, "llms.txt"), encoding="utf-8") as f:
        llms = f.read()

    if re.search(r"^# .+", llms, re.MULTILINE):
        ok.append("llms.txt: H1 project name presente")
    else:
        errors.append("llms.txt: falta H1 project name")

    if "> " in llms:
        ok.append("llms.txt: blockquote summary presente")
    else:
        errors.append("llms.txt: falta blockquote summary")

    if re.search(r"^## Specs", llms, re.MULTILINE):
        ok.append("llms.txt: seccion ## Specs presente")
    else:
        errors.append("llms.txt: falta seccion ## Specs")

    if re.search(r"^## Docs", llms, re.MULTILINE):
        ok.append("llms.txt: seccion ## Docs presente")
    else:
        errors.append("llms.txt: falta seccion ## Docs")

    # 2. llms-full.txt debe existir y concatenar todos los docs/*.md
    full_path = os.path.join(root, "llms-full.txt")
    if not os.path.exists(full_path):
        errors.append("llms-full.txt: no existe")
    else:
        with open(full_path, encoding="utf-8") as f:
            full = f.read()
        full_size = os.path.getsize(full_path)
        docs_dir = os.path.join(root, "docs")
        docs_files = sorted(f for f in os.listdir(docs_dir) if f.endswith(".md"))
        missing = [d for d in docs_files if d not in full]
        if missing:
            errors.append(f"llms-full.txt: faltan secciones: {missing}")
        else:
            ok.append(f"llms-full.txt: incluye todos los {len(docs_files)} docs/*.md ({full_size} bytes)")

    # 3. OpenSpec structure (dinamico: detecta proposal id actual)
    openspec = os.path.join(root, "openspec")

    # Estructura base siempre requerida
    base_required = [
        "README.md",
        "specs/woptimizer/spec.md",
    ]
    for rel in base_required:
        full = os.path.join(openspec, rel)
        if os.path.exists(full):
            ok.append(f"openspec/{rel}: existe ({os.path.getsize(full)} bytes)")
        else:
            errors.append(f"openspec/{rel}: NO EXISTE")

    # Cambios activos en changes/ (excluyendo archive/)
    active_changes_dir = os.path.join(openspec, "changes")
    if os.path.isdir(active_changes_dir):
        active = [
            d for d in os.listdir(active_changes_dir)
            if os.path.isdir(os.path.join(active_changes_dir, d))
            and d not in ("archive",)
        ]
        for cid in active:
            for fn in ("proposal.md", "tasks.md"):
                full = os.path.join(active_changes_dir, cid, fn)
                if os.path.exists(full):
                    ok.append(f"openspec/changes/{cid}/{fn}: existe ({os.path.getsize(full)} bytes)")
                else:
                    errors.append(f"openspec/changes/{cid}/{fn}: NO EXISTE")

    # Archive debe existir y tener al menos un cambio
    archive_dir = os.path.join(openspec, "changes", "archive")
    if os.path.isdir(archive_dir):
        archived = [
            d for d in os.listdir(archive_dir)
            if os.path.isdir(os.path.join(archive_dir, d))
        ]
        if archived:
            ok.append(f"openspec/changes/archive/: {len(archived)} cambio(s) cerrado(s)")
            for cid in archived:
                for fn in ("proposal.md", "tasks.md"):
                    full = os.path.join(archive_dir, cid, fn)
                    if not os.path.exists(full):
                        errors.append(f"openspec/changes/archive/{cid}/{fn}: NO EXISTE")
        else:
            ok.append("openspec/changes/archive/: existe (vacio)")
    else:
        errors.append("openspec/changes/archive/: NO EXISTE")

    # 4. AGENTS.md menciona la seccion SDD y refinamientos
    with open(os.path.join(root, "AGENTS.md"), encoding="utf-8") as f:
        agents = f.read()
    if "Spec-Driven Development" in agents and "OBLIGATORIO" in agents:
        ok.append("AGENTS.md: seccion SDD OBLIGATORIO presente")
    else:
        errors.append("AGENTS.md: falta seccion SDD obligatoria")
    if "Decision matrix" in agents and "Anti-burocracia" in agents:
        ok.append("AGENTS.md: decision matrix + anti-burocracia presentes (rev 12)")
    else:
        errors.append("AGENTS.md: faltan refinamientos de rev 12 (decision matrix / anti-burocracia)")
    if "Spec delta" in agents and "ADDED Requirements" in agents:
        ok.append("AGENTS.md: spec delta documentado (ADDED/MODIFIED/REMOVED)")
    else:
        errors.append("AGENTS.md: falta documentacion de spec delta")
    if "todowrite" in agents and "tasks.md" in agents and "sincronizaci" in agents:
        ok.append("AGENTS.md: todowrite <-> tasks.md binding documentado")
    else:
        errors.append("AGENTS.md: falta binding todowrite <-> tasks.md")
    if re.search(r"Spec rev:\*\*\s*12\b", agents):
        ok.append("AGENTS.md: spec rev 12")
    else:
        errors.append("AGENTS.md: spec rev != 12")

    # 5. mkdocs.yml existe y tiene nav
    if os.path.exists(os.path.join(root, "mkdocs.yml")):
        with open(os.path.join(root, "mkdocs.yml"), encoding="utf-8") as f:
            mk = f.read()
        # Debe tener bloque nav: con al menos 3 entries
        nav_block = re.search(r"^nav:\s*\n((?:  - .+\n)+)", mk, re.MULTILINE)
        if nav_block and nav_block.group(1).count("  - ") >= 3:
            ok.append(f"mkdocs.yml: nav configurada ({nav_block.group(1).count('  - ')} entries)")
        else:
            errors.append("mkdocs.yml: nav incompleta")
    else:
        errors.append("mkdocs.yml: NO EXISTE")

    # Reporte
    print("=" * 60)
    print(" validate_docs.py — woptimizer SDD + llms.txt")
    print("=" * 60)
    print()
    for line in ok:
        print(f"  [OK]   {line}")
    if errors:
        print()
        for line in errors:
            print(f"  [FAIL] {line}")
    print()
    print(f"Resumen: {len(ok)} OK, {len(errors)} FAIL")
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()