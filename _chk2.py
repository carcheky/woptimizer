t = open(".taskmaster/git_safe_commit.py", encoding="utf-8").read().splitlines()
for i, l in enumerate(t):
    if any(ord(ch) > 127 for ch in l):
        print(i + 1, "|", l.encode("ascii", "replace").decode())
