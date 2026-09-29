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

    if re.search(r"^## ", llms, re.MULTILINE):
        ok.append("llms.txt: tiene secciones H2 (formato v3)")
    else:
        errors.append("llms.txt: sin secciones H2")

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
            # proposal.md es obligatorio
            proposal = os.path.join(active_changes_dir, cid, "proposal.md")
            if os.path.exists(proposal):
                ok.append(f"openspec/changes/{cid}/proposal.md: existe ({os.path.getsize(proposal)} bytes)")
            else:
                errors.append(f"openspec/changes/{cid}/proposal.md: NO EXISTE")
            # tasks.md es opcional (per decision matrix del SDD: cambios triviales/pequeños pueden no tenerlo)
            tasks = os.path.join(active_changes_dir, cid, "tasks.md")
            if os.path.exists(tasks):
                ok.append(f"openspec/changes/{cid}/tasks.md: existe ({os.path.getsize(tasks)} bytes)")

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

    # 4. AGENTS.md estructura v3 (Stack + Invariantes + Skills Disponibles)
    with open(os.path.join(root, "AGENTS.md"), encoding="utf-8") as f:
        agents = f.read()
    v3_sections = ["Stack", "Invariantes", "Skills Disponibles"]
    missing_sections = [s for s in v3_sections if s not in agents]
    if not missing_sections:
        ok.append(f"AGENTS.md: secciones v3 presentes ({', '.join(v3_sections)})")
    else:
        errors.append(f"AGENTS.md: faltan secciones v3: {missing_sections}")
    if "CHANGELOG" in agents and "MANDATORY" in agents:
        ok.append("AGENTS.md: menciona CHANGELOG.md como obligatorio")
    else:
        errors.append("AGENTS.md: no menciona CHANGELOG.md como mandatory")

    # 5. .taskmaster/CHANGELOG.md existe y tiene formato valido (MANDATORY desde ciclo 11)
    changelog = os.path.join(root, ".taskmaster", "CHANGELOG.md")
    if not os.path.exists(changelog):
        errors.append(".taskmaster/CHANGELOG.md: NO EXISTE (MANDATORY desde ciclo #11)")
    else:
        with open(changelog, encoding="utf-8") as f:
            ch = f.read()
        size = os.path.getsize(changelog)
        if "Changelog de pases" not in ch:
            errors.append(".taskmaster/CHANGELOG.md: falta encabezado 'Changelog de pases'")
        else:
            ok.append(f".taskmaster/CHANGELOG.md: existe ({size} bytes) con encabezado correcto")
        cycle_count = len(re.findall(r"\[CYCLE-\d{3}\]", ch))
        if cycle_count == 0:
            errors.append(".taskmaster/CHANGELOG.md: ninguna entrada [CYCLE-NNN] encontrada")
        else:
            ok.append(f".taskmaster/CHANGELOG.md: {cycle_count} entradas [CYCLE-NNN]")
        if "MANDATORY" in ch:
            ok.append(".taskmaster/CHANGELOG.md: marca MANDATORY presente")
        else:
            errors.append(".taskmaster/CHANGELOG.md: no marca la convencion como MANDATORY")

    # 6. mkdocs.yml existe y tiene nav
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