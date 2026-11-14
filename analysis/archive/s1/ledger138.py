import re


def cut(p, start_pat):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    lines = s.split("\n")
    idx = [i for i, l in enumerate(lines) if l == start_pat]
    assert len(idx) == 1, (p, start_pat, idx)
    i = idx[0]
    j = i + 1
    while j < len(lines) and not lines[j].startswith("- "):
        j += 1
    print(p, "removing lines", i + 1, "..", j, "\n  " + "\n  ".join(lines[i:j])[:600])
    del lines[i:j]
    out = "\n".join(lines)
    open(p, "w", newline="", encoding="utf-8").write(out.replace("\n", "\r\n") if crlf else out)


cut(r"C:\Users\ybarnoy\projects\falcon3\registry\naming.yaml", "- ida: r38_e131")
cut(r"C:\Users\ybarnoy\projects\falcon3\registry\routines.yaml", "- ea: 1471552")
