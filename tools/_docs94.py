"""Docs for Finding 94 (L21 complete, 2 named - GLOBAL NAMING QUEUE = 0). Idempotent."""
import io

# ---------- findings_log.md (LF) ----------
FL = "docs/findings_log.md"
raw = io.open(FL, encoding="utf-8", newline="").read()
if "## 2026-10-19 94" not in raw:
    foot2 = "\n\n(append new findings below)"
    assert raw.rstrip("\n").endswith(foot2), repr(raw[-60:])
    i = raw.rindex(foot2)
    assert raw[:i].rstrip("\n").endswith("---"), "footer must be preceded by ---"
    entry = (
        "\n\n## 2026-10-19 94 - Level 21 complete: 2 named. GLOBAL NAMING QUEUE = 0\n"
        "(`named` 1,629 -> **1,631**; L21 to_name 2 -> **0**)\n"
        "\n"
        "The bottom-up naming campaign is **COMPLETE**: every level 0-21\n"
        "is fully named, the global naming queue (unnamed - thunks -\n"
        "orphans) is **0**, and the final two fns were the deepest SCCs\n"
        "(depth 21, 23 and 16 levels past the deepest previously-named\n"
        "L19 hub). Final 2 from `level21_full.txt`:\n"
        "\n"
        "**`r53_script_opcode_interpreter`** (sub_186ADC, 2312B, in=1\n"
        "r53_e88): the r53 overlay main script interpreter - 8-slot\n"
        "local-table init, 42h-stride record walk bucketing by [bx+41h]\n"
        "slot index (0FFh -> slot2_map_window_load + unk_5CA48 random\n"
        "tick), then farobj_store_32075 script fetch and byte&7 opcode\n"
        "dispatch via jpt_186DE1 (8 opcodes) with nested jpt_186EEA/\n"
        "jpt_187150/jpt_1872C8 sub-dispatchers.\n"
        "\n"
        "**`overlay_ems_farptr_setup`** (sub_6E29E, 139B, class=DATA,\n"
        "in=3 r22_e57/sub_2BF73/sub_2BF7D): 6E-segment stub whose real\n"
        "trampoline (0x6E2FF) sets cs:word_6E2AE=4A75h, calls\n"
        "overlay_teardown_restore_state, stores returned ax/bx/cx into\n"
        "cs:byte_6E0B0+2/4/6 far-pointer vector slot, += 7FC0h.\n"
        "\n"
        "### Campaign totals (Levels 0-21 COMPLETE)\n"
        "\n"
        "`named` 0 -> **1,631 / 2,237** (72.9% of all fns; 100% of the\n"
        "non-orphan, non-thunk queue). Levels 0-19 giant SCCs, L20 (25\n"
        "overlay fns + loadout-menu dispatch family), L21 (the final 2\n"
        "deepest overlay bodies) - all named bottom-up with callee\n"
        "context. Remaining unnamed: 302 thunk slots + 397 orphans\n"
        "(excluded by design).\n"
        "\n"
        "### Gates (all green)\n"
        "\n"
        "`naming.py check` **1,633** . `verify_rebuild` **faithful (2,237\n"
        "== 2,237)** . `verify_idb` **INTACT** . `name_readback`\n"
        "**1,631/1,631 function + 2/2 global**.\n"
    )
    new = raw[:i] + entry + "\n---" + foot2
    io.open(FL, "w", encoding="utf-8", newline="").write(new)
    print("findings_log: inserted Finding 94 entry")
else:
    print("findings_log: Finding 94 already present")

# ---------- time_log.yaml (CRLF) ----------
TL = "docs/time_log.yaml"
raw = io.open(TL, encoding="utf-8", newline="").read()
if "Finding 94:" not in raw:
    j = raw.index("Finding 93")
    eol = raw.index("\n", j) + 1
    row = (
        "| 2026-10-19 (session 47) | ~0.5 h | **Finding 94: Level 21 "
        "complete -- 2 named, `named` 1,629 -> **1,631**, L21 to_name 2 -> "
        "0, GLOBAL NAMING QUEUE = 0.** Headlines: r53_script_opcode_"
        "interpreter (sub_186ADC 2312B, byte&7 8-opcode script dispatch), "
        "overlay_ems_farptr_setup (sub_6E29E). **Campaign COMPLETE: Levels "
        "0-21 all named, 1,631/2,237 fns, queue 0.** **Gates green:** check "
        "1,633, verify_rebuild faithful, verify_idb INTACT, read-back "
        "1631/1631+2/2. |\r\n"
    )
    new = raw[:eol] + row + raw[eol:]
    io.open(TL, "w", encoding="utf-8", newline="").write(new)
    print("time_log: inserted Finding 94 row")
else:
    print("time_log: Finding 94 row already present")

# ---------- status.md ----------
ST = "status.md"
raw = io.open(ST, encoding="utf-8", newline="").read()
if "CAMPAIGN COMPLETE (finding 94)" not in raw:
    marker = "**Still outstanding:**"
    i = raw.index(marker)
    para = (
        "**CAMPAIGN COMPLETE (finding 94):** the final 2 Level-21 "
        "functions named (`named` 1,629 → **1,631 / 2,237**), **L21 "
        "`to_name` 2 → 0, global naming queue = 0**. Headlines: "
        "**r53_script_opcode_interpreter** (sub_186ADC, 2312B — the r53 "
        "overlay script interpreter: 8-slot record bucketing + byte&7 "
        "8-opcode dispatch with nested sub-dispatchers); "
        "**overlay_ems_farptr_setup** (sub_6E29E — EMS far-pointer "
        "vector install from the teardown-restore-state return). "
        "**Levels 0–21 fully named bottom-up.** Remaining unnamed: "
        "302 thunk slots + 397 orphans (excluded by design). "
        "**Gates green:** check **1,633**, verify_rebuild **faithful**, "
        "verify_idb **INTACT**, read-back **1,631/1,631 + 2/2**.\n\n"
    )
    new = raw[:i] + para + raw[i:]
    io.open(ST, "w", encoding="utf-8", newline="").write(new)
    print("status: inserted CAMPAIGN COMPLETE paragraph")
else:
    print("status: CAMPAIGN COMPLETE paragraph already present")

# ---------- open_items.md (CRLF, plain bullet) ----------
OI = "docs/open_items.md"
raw = io.open(OI, encoding="utf-8", newline="").read()
key = "Global naming queue = 0"
if key not in raw:
    line = (
        "- Global naming queue = 0 -- bottom-up naming campaign COMPLETE "
        "(Levels 0-21, 1,631/2,237 fns named). Remaining unnamed are 302 "
        "thunk slots + 397 orphans (excluded by design).\r\n"
    )
    if not raw.endswith("\r\n"):
        raw += "\r\n"
    io.open(OI, "w", encoding="utf-8", newline="").write(raw + line)
    print("open_items: appended queue-0 bullet")
else:
    print("open_items: queue-0 bullet already present")
print("docs94 done")
