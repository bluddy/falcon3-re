def edit(p, fn):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    s = fn(s)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("ok", p, crlf)


ROOT = r"C:\Users\ybarnoy\projects\falcon3"
PLAN = ROOT + r"\docs\workflow\idb_stabilisation_plan.md"
ST = ROOT + r"\status.md"
RB = ROOT + r"\docs\workflow\idb_regeneration.md"
NS = ROOT + r"\docs\workflow\next_steps_for_future_agents.md"
TL = ROOT + r"\docs\time_log.yaml"
OI = ROOT + r"\docs\open_items.md"
LINK = "[IDB stabilisation plan](docs/workflow/idb_stabilisation_plan.md)"


def plan(s):
    a = "| 64 / 125 (was 257 sites before 138-144) |"
    assert s.count(a) == 1
    s = s.replace(a, "| 64 / 125 |")
    # the file is new: make it CRLF like its siblings
    return s


def status(s):
    a = "**Last updated**: 2026-11-10 (session 55"
    assert s.count(a) == 1
    s = s.replace(a, "**Last updated**: 2026-11-11 (session 55 cont.")
    a = "   - **Now:** 524 mid-body targets / 1,409 sites, mostly R05/resident.\n"
    assert s.count(a) == 1
    i = s.index(a)
    j = s.index("\n", s.index("drain the auto queue under a manifest.", i)) + 1
    new = (
        "   - **Now (after finding 144, measured 2026-11-11):** 3,590 functions, ledger 2,034; 529 mid-body targets / 1,299 sites\n"
        "     (407 merged functions, 64 misdecodes, 26 + 23 fall-in entries, 9 other); 96 orphan code runs / 221 B, of which\n"
        "     92 are 1-2 B padding left on purpose.  Of the 407 merged targets, 394 are pure splits (978 sites), 12 are shared\n"
        "     tails (21 sites) and 1 is multi-chunk.\n"
        "   - **Next:** the full work queue, procedure, mode table and pitfalls are in the " + LINK + ".  In order:\n"
        "     - P0 commit S1c-4r / S1c-4s (findings 143, 144; applied and gated, not committed);\n"
        "     - P1 split the 394 pure-split merged functions (new `SPLIT` mode, batches of ~40);\n"
        "     - P2 the 64 `not_head` misdecodes; P3 the 49 fall-in entries; P4 the 9 `other` targets and 12 shared tails;\n"
        "     - P5 the 0x6E696..0x6E8B7 handler cluster / R30 menu state machine (needs a function-merge mode);\n"
        "     - P6 the small leftover orphans (0x6E16E ...); P7 drain the auto queue (~94 functions) under a manifest;\n"
        "     - P8 housekeeping; then S2 VGRAPH (P9), S3 trace edges (P10), S4 deep dive (P11).\n"
    )
    s = s[:i] + new + s[j:]
    a = "**Plan, each step gated before the next:**\n"
    assert s.count(a) == 1
    return s.replace(a, "**Plan, each step gated before the next** (working procedure and queue: " + LINK + "):\n")


def rb(s):
    a = "## Step V — VERIFY"
    assert s.count(a) == 1
    return s.replace(
        a,
        "> **Adding a finding to the orphan manifest** (S1c-4: plan, dry replay, apply, idempotent replay, extract, gates, docs) and the\n"
        "> queue of remaining IDB work are described in [idb_stabilisation_plan.md](idb_stabilisation_plan.md).\n\n" + a)


NEXT = """# Next Steps for Future Agents

> **Superseded 2026-11-11.**  The list below dates from session 17 (Track C scaffolding).  The live work is IDB stabilisation
> (S1-S4) followed by the function-by-function deep dive and the Track E parser.  Start from
> [idb_stabilisation_plan.md](idb_stabilisation_plan.md) (state, procedure, prioritised queue) and `status.md`.

## Session-17 list (kept for Track C, not current)
"""


def nxt(s):
    a = "# Next Steps for Future Agents\n## Next Steps for Future Agents\n"
    assert s.count(a) == 1
    return s.replace(a, NEXT)


ROW = ("| 2026-11-11 (session 55 cont.) | ~1 day | **Findings 126-144: S1c-4 orphan code and misdecode cleanup.** Orphan code runs "
       "registered, extended, rebased, trimmed, glued or remade as data through `tools/apply_orphan_funcs.py` and "
       "`registry/orphan_funcs_expected.json` (new modes REMOVE, TABLEFIX, TEXTFIX, TRIM, ABSORB, DATAFIX, GLUE); functions "
       "3,541 -> 3,590, ledger 2,038 -> 2,034, orphan code 142 runs / 1,020 B -> 96 runs / 221 B (92 are 1-2 B padding). "
       "Findings 143 and 144 applied and gated, uncommitted. Mid-body call targets 529 / 1,299 sites (407 merged, 394 of them pure splits). "
       "Wrote `docs/workflow/idb_stabilisation_plan.md` (state, per-finding cycle, mode table, prioritised queue P0-P11). |\r\n")


def tl(s):
    # time_log rows are separated by \n after normalisation; append after the last table row
    s = s.rstrip("\n") + "\n"
    return s + ROW.replace("\r\n", "\n") + "\n"


def oi(s):
    s = s.rstrip("\n") + "\n"
    return s + ("- **IDB stabilisation (S1-S4) is the active work item** (2026-11-11): remaining function-boundary, misdecode, auto-queue, "
                "VGRAPH and trace-edge work is queued as P0-P11 in docs/workflow/idb_stabilisation_plan.md.\n")


edit(PLAN, plan)
edit(ST, status)
edit(RB, rb)
edit(NS, nxt)
edit(TL, tl)
edit(OI, oi)
