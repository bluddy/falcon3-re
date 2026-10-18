"""Record finding 67 (Level-0 value-cliff buckets + Batch 2: 30 named) in
docs/findings_log.md (LF), time_log.yaml (CRLF), status.md and
docs/open_items.md (CRLF).  Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 67 — The Level-0 Value Cliff + Global Batch 2 (30 named
across dyn & static fan-in), `named` 295 -> 325, queue 688 -> 658

Finding 66 left a 688-entry Level-0 queue with a sharp inflection: Rank #30
had 15,191 dynamic calls but Rank #31 drops to 162, while `r30_e66` sits at
`dyn==0` with `in_degree=39`. This session first **bucketed the queue to locate
the value cliff**, then ran **Batch 2 across both the dynamic and static
high-value buckets**.

### 1. The Value Cliff (688 Level-0 leaves bucketed)

| bucket | count | metric |
|---|---|---|
| **dyn >= 10** | **99** | 19,944 calls |
| 1 <= dyn < 10 | 31 | 176 calls |
| **dyn==0, in>=5 (high static fan-in)** | **45** | 450 in_edges |
| dyn==0, 2<=in<=4 | 142 | 365 in_edges |
| dyn==0, in==1 (single caller) | 203 | 203 in_edges |
| **dyn==0, in==0 (ORPHANS)** | **168** | 0 (excluded) |

**The cliff:** the top **99** `dyn>=10` functions capture **19,944** of the
~20,120 total dyn calls in Level-0 (top-15 alone = 11,717), whereas the entire
`1<=dyn<10` band (31 fns) yields only **176**. So after the 99 `dyn>=10` leaves,
dynamic value collapses ~100x. Cumulative: top-30 = 16,391; top-50 = 18,474;
top-100 = 19,953 (the last 30 dyn>0 fns add <170).

**168 orphans** (`dyn==0 AND in==0`) are **disconnected** — 0 callers and 0
callees — and must be **excluded from bottom-up naming** (they are not
reachable in the graph; class mix: ASM 106, C 26, LEAF 21, DATA 15). The
**effective nameable Level-0 queue is 688 − 168 = 520**.

**45 high static fan-in leaves** (`in>=5`) split **27 overlay + 18 resident** —
these are the static hubs (R05_1E10 / carved overlay leaves) the trace never
exercised.

### 2. Batch 2 (30 = Slice A 15 dyn>0 + Slice B 15 dyn==0 in>=5)

Rather than grinding through 130 low-dyn leaves first, Batch 2 took the two
highest-value buckets. Disassembled via `dump_batch2.py` ->
`batch2_disasm.txt`/`batch2_context.json`.

**Slice A (top 15 remaining dyn>0)** — mostly the `dispatch_220xx` gateway
family + hot state setters:
`dispatch_22088_invoke_4arg` (1,172), `dispatch_22090_invoke_4arg` (1,157),
`dispatch_22094_stub` (1,144), `dispatch_22144_via_834a` (1,105),
`dispatch_2208c_stub` (1,061), `xlat_mask_or_setbit` (860 — XLAT mask-table
bit-set), `state_byte_25488_get` (777), `dispatch_22134_stub` (688),
`dispatch_220e4_invoke_farptr` (636), `state_byte_1f743_set` (542),
`state_word_25499_set_clamp` (541), `state_byte_2549e_set` (540),
`state_byte_25489_shadow_save` (498), `state_byte_25488_shadow_restore` (498),
`fixed_vec3_transform_7e900` (498 — 3x3 fixed matrix transform with
saturated `0x8001/0x7FFF` clamp).

**Slice B (top 15 dyn==0, in>=5)** — the static hubs the trace missed:
`r30_state_init_all` (**in=39**, R30 overlay global init), `game_state_setup_multi`
(in=33), `farobj_table_snapshot` (in=33, near `retn`, snapshots 4 far-object
table groups), `r12_farptr_load_thunk` (in=19), `sbi_command_wait` (in=15 —
Sound-Blaster port 330h/331h handshake), `r08_farptr_load_thunk` (in=14),
`fixed_scale_clamp_or40` (in=13), `r69_farptr_dispatch_entry` (in=13),
`sbi_data_write` (in=12), `trig_table_lookup` (in=12 — ES=8364h trig table,
quadrant-fold via bits 12/13 -> sin/cos pair; hot caller `sub_23D2B` 108K),
`r39_farptr_call_gate` (in=12), `sprite_clip_bounds_check` (in=10),
`fixed_vec3_transform_es` (in=9, near twin of `..._7e900`),
`sprite_project_screen_y` (in=9), `r05_dgroup_save_reg` (in=9 — saves
DS/SI/BX to DGROUP 632A:0).

Four low-confidence overlay thunks (`r12`/`r08`/`r39`/`r69`) have undecodable
mid-instruction spans (class-c, finding 65) — named provisionally by caller
context, flagged `conf: low`.

### 3. Ledger + gates

`naming.yaml` **297 -> 327** (+30), `routines.yaml` **296 -> 326** ea (+30,
CRLF normalized). `naming.py apply` (30 fb_fields + 1 source text file, 4
hits) + `push-ida` (30 renamed in IDB).

Gates (all green): `naming.py check` **327** . `verify_rebuild` **faithful
(2,237==2,237, LOST 0, CHANGED 0)** . `verify_idb` **INTACT (0 span/name/
hole problems)** . `name_readback` **325/325 function + 2/2 global**.

### 4. Effect + re-bucketed queue

| metric | f66 | f67 |
|---|---|---|
| named (fb join) | 295 | **325 (+30)** |
| naming_queue | 1,646 | **1,616 (−30)** |
| Level-0 queue | 688 | **658 (−30)** |

`callgraph_bottomup` re-run: **all 30 removed** (0 remain). Re-bucketed Level-0
(658): `dyn>=10` 84 (8,227 calls), `1<=dyn<10` 31 (176), `dyn0,in>=5` 30,
`dyn0,2<=in<=4` 142, `dyn0,in1` 203, **orphans 168 (excluded)**. The
`dyn>=10` band is the remaining high-value dynamic target (84 leaves); after
that the queue is static fan-in + orphans.

---

"""

ROW = ("| 2026-10-18 (session 23) | ~3 h | **Finding 67: Level-0 value-cliff "
       "buckets + Batch 2 -- 30 named, `named` 295 -> 325, queue 688 -> 658.** "
       "Buckets (688 L0): **dyn>=10 = 99 fns / 19,944 calls** (cliff: the "
       "31-fn `1<=dyn<10` band adds only 176; top-15=11,717, top-100=19,953), "
       "**dyn0,in>=5 = 45 (27 overlay+18 resident)**, 2<=in<=4=142, in=1=203, "
       "**orphans (dyn0 AND in0) = 168 EXCLUDED** (0 callers/0 callees) -> "
       "effective nameable L0 = 520. Batch 2 = **Slice A (15 dyn>0)**: "
       "dispatch_22088/22090/22094/22144/2208c/22134/220e4 gateway stubs, "
       "xlat_mask_or_setbit, state_byte_25488_get, state_byte_1f743_set, "
       "state_word_25499_set_clamp, state_byte_2549e_set, "
       "25489_shadow_save/25488_shadow_restore, fixed_vec3_transform_7e900; "
       "**Slice B (15 dyn0 in>=5)**: r30_state_init_all(in=39), "
       "game_state_setup_multi(33), farobj_table_snapshot(33), "
       "r12_farptr_load_thunk(19), sbi_command_wait(15, port 330h/331h), "
       "r08_farptr_load_thunk(14), fixed_scale_clamp_or40(13), "
       "r69_farptr_dispatch_entry(13), sbi_data_write(12), "
       "trig_table_lookup(12, ES=8364h sin/cos), r39_farptr_call_gate(12), "
       "sprite_clip_bounds_check(10), fixed_vec3_transform_es(9), "
       "sprite_project_screen_y(9), r05_dgroup_save_reg(9). 4 low-conf overlay "
       "thunks (r12/r08/r39/r69) flagged. Ledgers 297->**327** / 296->**326**, "
       "apply+push-ida. **Gates green:** check 327, verify_rebuild faithful, "
       "verify_idb INTACT, read-back **325/325+2/2**. Re-bucketed L0 (658): "
       "dyn>=10=84 (8,227 calls), orphans 168 excluded. |")

STATUS_PARA = (
    "**Level-0 value cliff + Batch 2 (finding 67):** bucketed the 688 Level-0 "
    "leaves — **99 `dyn>=10` fns capture 19,944 calls** (the 31-fn `1<=dyn<10` "
    "band adds only 176 → the cliff), **45 high static fan-in** (`in>=5`, 27 "
    "overlay + 18 resident), and **168 orphans** (`dyn==0 AND in==0`, 0 "
    "callers/callees) **excluded** from bottom-up naming → effective nameable "
    "queue **520**. Ran **Batch 2 across both high-value buckets**: Slice A "
    "(15 dyn>0) = the `dispatch_220xx` gateway stubs + hot state setters + "
    "`fixed_vec3_transform_7e900`; Slice B (15 dyn==0 `in>=5`) = the static "
    "hubs `r30_state_init_all` (in=39), `farobj_table_snapshot` (in=33), "
    "`sbi_command_wait`/`sbi_data_write` (Sound-Blaster ports 330h/331h), "
    "`trig_table_lookup` (ES=8364h sin/cos), and 4 R-overlay farptr thunks "
    "(low-conf, flagged). Ledgers 297→**327** / 296→**326**, applied + pushed. "
    "**Gates all green** (check 327, verify_rebuild faithful, verify_idb "
    "INTACT, read-back **325/325+2/2**). Re-ran the call graph: **named "
    "295→325, Level-0 queue 688→658**; re-bucketed, the `dyn>=10` band is down "
    "to 84 leaves (8,227 calls) — the remaining high-value dynamic target."
)

OPEN_NEW = [
    "- **Level-0 value cliff mapped + Batch 2 done (finding 67):** 30 named,",
    "  `named` **295 -> 325**, Level-0 queue **688 -> 658**. Buckets: dyn>=10",
    "  = 99 fns/19,944 calls (cliff after), dyn0,in>=5 = 45, **orphans = 168",
    "  excluded** (effective nameable L0 = 520). All 4 gates green (check 327,",
    "  verify_rebuild faithful, verify_idb INTACT, read-back 325/325+2/2).",
    "- **Next (Batch 3):** the remaining **84 `dyn>=10` Level-0 leaves**",
    "  (8,227 calls) are the last high-value dynamic band; then the static",
    "  fan-in hubs (`dyn0,in>=5` now 30 left). The 168 orphans stay excluded",
    "  (0 callers/0 callees -- not reachable bottom-up).",
    "- **Follow-ups:** 4 low-conf R-overlay farptr thunks (r12/r08/r39/r69)",
    "  have undecodable mid-instruction spans (class-c) -- reclassify when the",
    "  epilogue window / span repair lands; 92 low-conf DATA fns still queued;",
    "  24 trap-only thunk far-targets point at word_*/unk_* data.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 67" in raw:
    print("findings_log: 67 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 67 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 23" in raw:
    print("time_log: 23 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 22" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 23 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Level-0 value cliff + Batch 2 (finding 67)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f67 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "Level-0 value cliff mapped + Batch 2 done (finding 67)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f67 status (%d bytes)" % len(block))