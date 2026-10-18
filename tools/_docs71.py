"""Record finding 71 (Global Level-0 FINISH: batches 6-16, +382 names,
Level-0 queue 382 -> 0) in docs/findings_log.md (LF), time_log.yaml (CRLF),
status.md and docs/open_items.md (CRLF).  Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 71 — Global Level-0 COMPLETE: batches 6-16 named 382 more
functions (`named` 433 -> 815), Level-0 `naming_queue` 382 -> 0

Finding 70 left the Level-0 queue at 382. This session ran the remaining
**11 batches** (10 x 36 + 1 x 22 = **382 functions**) with the established
cadence -- dump (`dump_batchNN.py`) -> derive (disasm + caller context ->
semantic name / `sig:` / conf) -> append both ledgers -> `naming.py apply` ->
`push-ida` -> re-run `callgraph_bottomup` for the next slice -- and finished
the level.

### Cadence (each batch: 36 named except the finale)

| batch | named after | L0 queue after | highlights |
|---|---|---|---|
| 6 | 469 | 346 | EMS alloc plan/execute (`int 67h AH=43h/44h`), `int15_joystick_detect`, far-ptr list copy `0xFFFF` |
| 7 | 505 | 310 | CPU-generation detect (EFLAGS bits 12-15), DOS `mem_block_move`, drive-path build, INT 8/9 vector unhook |
| 8 | 541 | 274 | SBI 0xAA port discovery, PIT mode-3 (`out 43h,36h`), keyboard scancode shift-table XLAT, `r14_stream_read_retf8` |
| 9 | 577 | 238 | **`farptr_slot0/1_handler` (real targets behind RTLink thunk slots #000/#001)**, DOS arena offset math, patch scanner `E8->0x58D` |
| 10 | 613 | 202 | terrain attr lookups (es:3840), `kbd_ctrl_wait_64` (port 64h), `drive_path_build`, coord-delta quartet |
| 11 | 649 | 166 | BCD->hex ASCII trick (`90h/daa`), module slot far-calls (`cs:2A662`), UI 4-edge bound presets, entity table find-free |
| 12 | 685 | 130 | AdLib/OPL register write with read-delay loops (`out DX`), `pcspk_tone_on_b6` (PIT ch2), 3 save/restore table pairs (65A7/69FF/6B58) |
| 13 | 721 | 94 | anim frame counters (`cs:27988/9/A`), INT8/INT9 vector restore, `bcd_hex_stosb`, line-raster diffs |
| 14 | 757 | 58 | view-bounds shadow quad, entity cursor step (63FDh), `nop_retf`, R05 state save/restore bundles |
| 15 | 793 | 22 | sprite blend/stride (`imul ds:0AD2D`), `r33_record_scan/walk_4e` (0x4E-stride record tables), 3 more save/restore pairs |
| 16 | **815** | **0** | finale: R06 scale-clamp, R15 flag gates, `r33_record_walk_4e` twin, `r53_record_walk_82` (0x82 stride), partial class-c entries |

### Two incidents, both fixed

1. **YAML backslash escape.** `drive_path_build`'s `sig` contained `X:\\`
   (a literal backslash inside a YAML double-quoted scalar) which broke
   `naming.yaml` (line 3144) and then `routines.yaml` -- `naming.py apply`
   crashed before updating `function_bytes` (batch-11 silently lost its
   `fb_fields` until re-run). The append templates
   (`_append_naming66/_routines66.py`, the source for every later batch)
   now escape **backslash first, then quote**
   (`replace(chr(92), chr(92)*2).replace('"', ...)`); both files patched and
   validated with `yaml.safe_load`.
2. **IDA `seg_` dummy-prefix trap (the `set_name` returns-True-but-reverts
   bug).** Two names would not stick in the IDB: `seg_change_debounce_cx`
   (`sub_112F6`) and `seg_bitfield_decode` (`sub_14152`). Empirical bisect
   proved the trigger is the **`seg_` prefix itself** -- IDA's naming kernel
   treats it as a dummy/autoname prefix: `set_name(...)` / even
   `ida_name.force_name(...)` returned `True` while the auto-name survived
   (force_name additionally mangled the result to `_seg_...`), whereas
   `bitfield_decode` / `debounce_cx` (no `seg_` prefix) stuck instantly at
   the same addresses. `push-ida`'s `OK` lines for these two were therefore
   lies (its check only tests the `set_name` return code). **Fix:** renamed
   both ledger entries to `segment_*` equivalents --
   `segment_change_debounce_cx` + `segment_bitfield_decode` -- across
   `naming.yaml`, `routines.yaml` (hypothesis), `batch9/10_names.json`,
   `function_bytes` (via apply) and the IDB (verified with immediate
   `get_ea_name` assertion). A nested-loop bug in the first routines.yaml
   patch briefly wrote the wrong hypothesis into the `ea=0x14152` entry;
   corrected deterministically by ea (`check` re-validated).

### MILESTONE: Level-0 naming_queue = 0

| metric | f70 | f71 |
|---|---|---|
| named (fb join) | 433 | **815 (+382)** |
| naming_queue (global) | 1,234 | **854** |
| **Level-0 queue** | **382** | **0** |

Level-0 residue = **204 orphans (dyn0 AND in0) + 148 thunk slots, 0 other**
-- every nameable Level-0 leaf is named. (Global `naming_queue` 854 remains:
Levels 1..22 + the long-tail in=1/in=2-4 bands above Level 0.)

### Gates (all green)

`naming.py check` **817** . `verify_rebuild` **faithful (2,237 == 2,237,
LOST 0, CHANGED 0)** . `verify_idb` **INTACT (0 span / 0 name / 0 data-hole
problems)** . `name_readback` **815/815 function + 2/2 global**.

---

"""

ROW = ("| 2026-10-18 (session 27) | ~4 h | **Finding 71: Global Level-0 "
       "COMPLETE -- batches 6-16 named 382 fns, `named` 433 -> 815, L0 queue "
       "**382 -> 0**.** 11-batch cadence (10x36+22): EMS alloc/int15 joystick, "
       "CPU-486 detect + INT8/9 unhook, SBI 0xAA discovery + PC-speaker B6 + "
       "PIT mode3, **farptr_slot0/1_handler (real targets behind RTLink thunk "
       "slots #000/#001)**, DOS arena/patch-scan E8->0x58D, terrain es:3840 + "
       "kbd port-64h + drive-path + coord-delta quartet, BCD-hex 90h/daa + "
       "module slot calls + UI 4-edge presets, AdLib out-DX delay loops + 3 "
       "save/restore table pairs (65A7/69FF/6B58), anim counters 27988/9/A + "
       "entity cursor, sprite blend imul 0AD2D + r33/r53 record walks (0x4E/"
       "0x82 stride), finale R06/R15 gates. **Two incidents fixed:** (1) YAML "
       "backslash escape (drive_path_build X:\\ sig broke naming+routines "
       "yaml, crashed apply; templates now escape backslash-then-quote); (2) "
       "**IDA `seg_` dummy-prefix trap** -- set_name/force_name return True "
       "but the auto-name survives (force mangles to `_seg_..`); bisect proved "
       "the `seg_` prefix is the trigger (`bitfield_decode` stuck at the same "
       "ea); both entries renamed to `segment_change_debounce_cx` / "
       "`segment_bitfield_decode` across all ledgers + IDB (a nested-loop "
       "patch briefly corrupted the ea=0x14152 hypothesis -- fixed by ea). "
       "**Gates green:** check 817, verify_rebuild faithful, verify_idb INTACT, "
       "read-back **815/815+2/2**. L0 residue = 204 orphans + 148 thunks, 0 "
       "other. Global queue remains 854 (Levels 1-22). |")

STATUS_PARA = (
    "**Global Level-0 COMPLETE (finding 71):** 11 batches named **382 more "
    "functions** (`named` 433 → **815**), driving the **Level-0 "
    "`naming_queue` from 382 to 0** — every nameable Level-0 leaf is named "
    "(residue = 204 orphans + 148 thunk slots, 0 other). Notable tail finds: "
    "**`farptr_slot0/1_handler`** (the real targets behind RTLink thunk slots "
    "#000/#001), the AdLib/OPL read-delay write loop, PC-speaker `B6` PIT "
    "setup, three state save/restore table pairs (65A7/69FF/6B58), and the "
    "`r33`/`r53` 0x4E/0x82-stride record walks. **Two tooling traps fixed:** "
    "(1) a YAML backslash in a `sig:` (`X:\\` in `drive_path_build`) broke "
    "`naming.yaml`/`routines.yaml` and crashed `apply` — append templates now "
    "escape backslash-then-quote; (2) the **IDA `seg_` dummy-prefix trap** — "
    "`set_name`/`force_name` return `True` but the auto-name survives "
    "(force mangles to `_seg_…`), proven by bisect (`bitfield_decode` stuck "
    "at the same ea) — both affected entries renamed to `segment_*` across "
    "all ledgers + IDB. **Gates all green** (check 817, verify_rebuild "
    "faithful, verify_idb INTACT, read-back **815/815+2/2**). Global "
    "naming_queue remains 854 (Levels 1–22)."
)

OPEN_NEW = [
    "- **GLOBAL LEVEL 0 COMPLETE (finding 71):** batches 6-16 named 382 fns,",
    "  `named` **433 -> 815**, **L0 naming_queue 382 -> 0** (residue: 204",
    "  orphans + 148 thunks, 0 other). Two tooling traps fixed: YAML",
    "  backslash escaping in append templates; the IDA `seg_` dummy-prefix",
    "  trap (set_name True-but-reverts; renamed 2 entries to `segment_*`).",
    "  All 4 gates green (check 817, verify_rebuild faithful, verify_idb",
    "  INTACT, read-back 815/815+2/2).",
    "- **Next: Global Level-1 naming.** The SCC-condensed call graph says",
    "  Level-1 callees are all at Level 0 (now 100% named), so Level 1 can",
    "  be named with full callee context. Global `naming_queue` = 854",
    "  (Levels 1..22 + in=1/in=2-4 static bands).",
    "- **Follow-ups carried:** class-c / undecodable overlay spans (r06/r14/",
    "  r17/r30 entry partials now named `conf:low` pending span repair); 92",
    "  low-conf DATA fns; 24 trap-only thunk far-targets; 688 -> 0 verified",
    "  but 168-Level0-orphan + global 397 orphans stay excluded from",
    "  bottom-up naming.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 71" in raw:
    print("findings_log: 71 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 71 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 27" in raw:
    print("time_log: 27 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 26" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 27 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Global Level-0 COMPLETE (finding 71)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f71 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVEL 0 COMPLETE (finding 71)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f71 status (%d bytes)" % len(block))