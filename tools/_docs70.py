"""Record finding 70 (Batch 5: 36 named, fartrans blind spot + in>=5 closed)
in docs/findings_log.md (LF), time_log.yaml (CRLF), status.md and
docs/open_items.md (CRLF).  Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 70 — Global Batch 5 (36 named: `dyn>=10` + the last
hotspots + high-fan-in tail), `named` 397 -> 433, Level-0 queue 418 -> 382,
**`caller_dyn>=1000` and `in>=5` buckets now EMPTY**

Finding 69 left the Level-0 queue at 454 with 48 `dyn>=10`, 6
`caller_dyn>=1000` hotspots, and 11 `in>=5` high-fan-in leaves. This session
ran **Batch 5 (36)**: Slice A = top 18 `dyn>=10`; Slice B = the **last 6
`caller_dyn` hotspots** + 12 high-fan-in long-tail static leaves.

### Batch 5 (36)

Disassembled via `dump_batch5.py` -> `batch5_disasm.txt`/`batch5_context.json`.

**Slice A (top 18 `dyn>=10`)** — state/EMS/dispatch:
`overlay_seg_word_read` (66), `state_word_9a36_get` (65),
`fixed_repeat_sub_count` (64 — repeat-count loop), `farptr_7075_const_9c`
(63 — returns constant `7075:009C`), `dispatch_2211c_invoke_2arg` (61),
`dispatch_22178_then_27474_0` (59, cd=11,565), `event_mode_set_77c98` (53 —
switch 1/2/3/else -> `es:77C98`=2/3/4/0), `ems_map_pages_4` (44 — 4x INT 67h
AH=44h), `state_byte_2549f_set` (44), `state_byte_254a0_set` (44),
`state_7eab8_zero` (40), `state_word_77b32_get` (39, cd=133),
`state_word_77804_set` (39 — atomic cli store), `state_word_1f6e2_get` (36),
`state_byte_2549f_get` (36), `dispatch_2211c_stub` (34),
`dispatch_22178_invoke_3arg` (33), `state_byte_25488_set_arg` (32).

**Slice B (6 hotspots + 12 long-tail static)**:
*Hotspots (the last `caller_dyn>=1000`):* `farobj_batch_flush_2548c`
(**cd=8,606**, caller `sub_258B2` 8.6K — one-shot 4x far-dispatch flush),
`trig_table_lookup_83a5` (2,369 — near-twin trig lookup at `ES=83A5h`),
`dispatch_22188/2218c/22190/22194_stub` (2,019 each, all from `sub_27697`
2K). *Long-tail static (in>=4):* `flag_1f733_gate` (in=6),
`matrix_constants_copy_es3852` (in=6 — 12-word matrix scatter, twin of
`..._3820`), `farobj_index_range_check` (in=6 — index 1..15 bounds),
`flag_532_set_dispatch_4ab` (in=6 — one-shot flag merge + far dispatch),
`farobj_magic_feec_check` (in=6, low-conf undecodable),
`r17_farptr_dispatch`/`r17_farptr_dispatch2` (in=5, low-conf overlay),
`farobj_attr_table_lookup` (in=5 — byte/word table lookup),
`farobj_record_build_6b58` (in=5), `hw_config_copy_85061` (in=5),
`r06_farptr_dispatch` (in=5, low-conf overlay), `hw_flag_bit2_22e_set`
(in=4). Four low-confidence undecodable overlay/farobj routines flagged.

### Ledger + gates

`naming.yaml` **399 -> 435** (+36), `routines.yaml` **398 -> 434** ea (+36,
CRLF normalized). `naming.py apply` (36 fb_fields + 1 source text, 7 hits) +
`push-ida` (36 renamed in IDB).

Gates (all green): `naming.py check` **435** . `verify_rebuild` **faithful
(2,237==2,237, LOST 0, CHANGED 0)** . `verify_idb` **INTACT (0 span/name/
hole problems)** . `name_readback` **433/433 function + 2/2 global**.

### Effect + re-bucketed queue — two buckets hit ZERO

| metric | f69 | f70 |
|---|---|---|
| named (fb join) | 397 | **433 (+36)** |
| naming_queue | 1,234 | **1,198 (−36)** |
| Level-0 queue | 418 | **382 (−36)** |

`callgraph_bottomup` re-run: **all 36 removed** (0 remain). Re-bucketed
Level-0 (382): `dyn>=10` **30**, `1<=dyn<10` 31, **`dyn0,in>=5` 0**,
`dyn0,2-4` 129, `dyn0,in1` 192. **Two milestones:**
* **`caller_dyn>=1000` hotspots = 0** (was 24 at f68) — the fartrans blind
  spot is fully closed at Level 0.
* **`dyn0,in>=5` = 0** (was 45 at f67) — every high static fan-in Level-0
  leaf is now named.

Remaining Level-0 (382): 30 `dyn>=10` + 31 `dyn 1-9` + 321 static-only
(`2-4` 129, `in=1` 192) — the long tail.

---

"""

ROW = ("| 2026-10-18 (session 26) | ~3 h | **Finding 70: Batch 5 -- 36 named; "
       "`named` 397 -> 433, L0 queue 418 -> 382; caller_dyn>=1000 AND in>=5 "
       "buckets now EMPTY.** Slice A (18 dyn>=10): overlay_seg_word_read, "
       "state_word_9a36/77b32/1f6e2_get, state_byte_2549f/254a0_set/get, "
       "state_word_77804_set (cli atomic), state_7eab8_zero, "
       "state_byte_25488_set_arg, fixed_repeat_sub_count, "
       "farptr_7075_const_9c (7075:009C), event_mode_set_77c98 (switch->77C98), "
       "ems_map_pages_4 (4x INT 67h), dispatch_2211c/22178 x2. Slice B (6 "
       "hotspots + 12 tail): farobj_batch_flush_2548c (cd=8,606, 4x far "
       "flush), trig_table_lookup_83a5 (2,369), dispatch_22188/8c/90/94_stub "
       "(2,019 each); tail: flag_1f733_gate, matrix_constants_copy_es3852, "
       "farobj_index_range_check, flag_532_set_dispatch_4ab, "
       "farobj_attr_table_lookup, farobj_record_build_6b58, "
       "hw_config_copy_85061, hw_flag_bit2_22e_set, + 4 low-conf overlay "
       "dispatch (r06/r17 x2/farobj_magic). Ledgers 399->**435** / "
       "398->**434**, apply+push-ida. **Gates green:** check 435, "
       "verify_rebuild faithful, verify_idb INTACT, read-back **433/433+2/2**. "
       "Re-bucketed L0 (382): dyn>=10=30, dyn 1-9=31, **in>=5=0**, "
       "**caller_dyn>=1000=0** -- both target buckets emptied. |")

STATUS_PARA = (
    "**Batch 5 (finding 70):** named 36 — Slice A (18 `dyn≥10`: state "
    "getters/setters, EMS page-map, `event_mode_set_77c98`, dispatch gateways) "
    "and Slice B (**the last 6 `caller_dyn≥1000` hotspots** — "
    "`farobj_batch_flush_2548c` cd=8.6K, `trig_table_lookup_83a5`, 4 dispatch "
    "stubs — plus 12 high-fan-in long-tail static leaves: `flag_1f733_gate`, "
    "`matrix_constants_copy_es3852`, `farobj_index_range_check`, "
    "`farobj_attr_table_lookup`, `hw_config_copy_85061`, + 4 low-conf overlay "
    "dispatch). Ledgers 399→**435** / 398→**434**, applied + pushed. **Gates "
    "all green** (check 435, verify_rebuild faithful, verify_idb INTACT, "
    "read-back **433/433+2/2**). Re-ran the call graph: **named 397→433, "
    "Level-0 queue 418→382**. **Two milestones: `caller_dyn≥1000` hotspots = 0 "
    "(was 24) and `dyn0,in≥5` = 0 (was 45)** — the fartrans blind spot and "
    "every high static fan-in Level-0 leaf are now named. Remaining Level-0 "
    "(382): 30 `dyn≥10` + 31 `dyn 1-9` + 321 static-only long tail."
)

OPEN_NEW = [
    "- **Batch 5 done (finding 70):** 36 named, `named` **397 -> 433**,",
    "  Level-0 queue **418 -> 382**. **Two buckets emptied: caller_dyn>=1000",
    "  hotspots = 0 (was 24) and dyn0,in>=5 = 0 (was 45).** All 4 gates green",
    "  (check 435, verify_rebuild faithful, verify_idb INTACT, read-back",
    "  433/433+2/2).",
    "- **Next (Batch 6):** the long tail of Level-0 (382): **30 dyn>=10** +",
    "  31 dyn 1-9 + 321 static-only (129 in 2-4, 192 in=1). With the hot",
    "  buckets empty, rank by (dyn DESC, in DESC) across the whole set; use",
    "  caller_dyn_sum only as tie-break (max now <1000).",
    "- **Follow-ups:** 4 low-conf undecodable overlay dispatch routines this",
    "  batch (r06/r17 x2/farobj_magic) join the class-c repair list; 92",
    "  low-conf DATA fns; 24 trap-only thunks; consider advancing to Level 1",
    "  once Level 0 nears exhaustion.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 70" in raw:
    print("findings_log: 70 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 70 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 26" in raw:
    print("time_log: 26 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 25" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 26 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Batch 5 (finding 70)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f70 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "Batch 5 done (finding 70)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f70 status (%d bytes)" % len(block))