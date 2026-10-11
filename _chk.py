import re
for ruta in ("run_tests.py", ".taskmaster/git_safe_commit.py", "docs/ai/sandbox-rules.md",
             "STATUS.md", "docs/ai/testing-guide.md", "CHANGELOG.md",
             ".taskmaster/CHANGELOG.md"):
    t = open(ruta, encoding="utf-8").read()
    raros = re.findall(r"[^\x00-\x7F]", t)
    from collections import Counter
    c = Counter(raros)
    print(ruta, "| no-ascii distintos:", len(c))
    if c:
        print("   ", [(hex(ord(k)), v) for k, v in c.most_common(8)])
