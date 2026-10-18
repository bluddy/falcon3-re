"""Record finding 74 (Global Level-3 COMPLETE: 2 batches = 52 named,
L3 queue 52 -> 0, named 1057 -> 1109; tools/dump_full.py added) in
docs/findings_log.md (LF), time_log.yaml (CRLF), status.md and
docs/open_items.md (CRLF). Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-18 74 — Global Level-3 COMPLETE: 2 batches named all 52
Level-3 functions (`named` 1,057 -> **1,109**), L3 queue 52 -> 0

Level-3 queue had 52 entries (full callee context: L0-L2 fully named, so
every L3 dump shows its callees' semantic names). Two batches:
**36 + 16 = 52**, both derived from the `dump_level1.py` disasm +
`full_dump` completions.

### New tool: tools/dump_full.py

`dump_level1.py` breaks at the FIRST terminator (retn/retf/iret), which
shows e.g. sub_14CC6's 12-byte early-exit but hides its other 384 bytes.
`dump_full.py` walks the whole function (no break, 4000-insn cap) reading
`full_dump_targets.json` (`{"A": [keys]}`) -> `full_dump_disasm.txt`.
Used for sub_100BB/14CC6/1EA58/257E5/14956/27A20/37B1E/14E52/6D68D
(batch 1) and sub_6D256/3804B/6D7FF (batch 2). Also learned (again):
`FALCON_L1_TARGETS` must be a FILE PATH with `{"A": [...]}`, not inline
JSON.

### Batches

| batch | named after | L3 queue after | highlights |
|---|---|---|---|
| l3a | 1,093 | 16 | **`sbi_note_state_machine`** (cd=42,313, 1548B 22-case OPL voice lifecycle), **`angle_quad_norm_scale`** (cd=165,686 -- hottest of batch, shared angle primitive of angle_xy/angle_aux), `farobj_rect_ratio_build` (in=28, 2 projection ratios), `channel_note_seq_write` + `channel_seq_word_store` (seq siblings), **`sbi_pit_period_enable`/`_disable`** (the critical-section bracket mode_slot_enter wraps around `sbi_mode_slot_store`), `view_extent_shadow_save`/`_restore` (pair), `tile_quad_sample` (in=19, fills the 11C5E..61 quad for avg_pair_dispatch), `view_proj_preset_apply` (callers = view_proj_default + presets 1..7 exactly), `mouse_driver_init`/`mouse_gate_far_entry`/`mouse_delta_scale_far_entry`/`mouse_buttons_test_far` (mouse entry family), `anim_line_object_draw` (sole caller of line_raster_diff_281), `farobj_slot_create`, `game_setup_staged_step`, `sbi_stream_stop_load` |
| l3b | **1,109** | **0** | **`sbi_request_dispatch`** (731B, THE 20-op SBI mailbox processor -- pair of state_block_77720_store8: config triples / EMS pages / PIT period / driver callbacks, writes the 77722 result), **`overlay_file_open`** (open/cache front end delegating to overlay_loader_main), **`line_record_draw_loop`** (parent loop of line_flag_dispatch_28ed8 + line_table_scan_dispatch), **`farobj_entity_accum_sweep`** (slot-aging sweep pair of farobj_entity_accum_copy: clears mode bit4 when no slots remain), `farobj_slot_cycle` (timer-driven farptr repoint, sibling of farobj_slot_create), `terrain_attr_block_scan_inc`/`_axdec`/`_dec` (the 3 remaining direction twins -- with batch 1's terrain_attr_block_scan the 4 sign-combination family is complete), `game_setup_toggle_step` + `game_setup_entity_step` (staged-step siblings of game_setup_staged_step: counters 1078..107A alongside 107B..107E form ONE 7-phase sequence run by sub_37A0A), `r06_ui_dispatch_block` (5-entry R06 UI/HUD block incl. the ASCII position readout), `r06_mode_param_dispatch`, `view_limits_pair_apply`, `stream_record_point_find`, `farobj_step_terrain_clamp`, `bcd_hex_ch_store` |

### Milestone + gates

**Levels 0, 1, 2 AND 3 are all complete.** `named` = **1,109**; global
`naming_queue` = **522** across Levels 4..21 (L19 = 206 -- the giant
SCC); L3 residue = 4 orphans + 7 thunks, **0 other**.

`naming.py check` **1,111** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,109/1,109
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-18 (session 30) | ~5 h | **Finding 74: Global Level-3 "
       "COMPLETE -- 2 batches named all 52 L3 fns, `named` 1,057 -> "
       "**1,109**, L3 queue 52 -> 0 (4 orphans + 7 thunks, 0 other).** "
       "New tool `dump_full.py` (dump_level1 stops at first terminator -- "
       "hid 384 of sub_14CC6's 396B); FALCON_L1_TARGETS = file path with "
       "{\"A\":[keys]}. l3a (1,093): sbi_note_state_machine (cd=42,313, "
       "22-case OPL voice lifecycle), angle_quad_norm_scale (cd=165,686 "
       "hottest), farobj_rect_ratio_build (in=28), sbi_pit_period_"
       "enable/disable (the bracket mode_slot_enter wraps around "
       "sbi_mode_slot_store), view_extent_shadow save/restore pair, "
       "tile_quad_sample (in=19), view_proj_preset_apply (callers = "
       "default + presets 1..7), mouse entry family, channel_note_seq_"
       "write, anim_line_object_draw. l3b (1,109): **sbi_request_dispatch** "
       "(731B 20-op mailbox processor), **overlay_file_open** (front end "
       "of overlay_loader_main), **line_record_draw_loop** (parent of "
       "line_flag_dispatch_28ed8), **farobj_entity_accum_sweep** ( slot-"
       "aging pair of farobj_entity_accum_copy), farobj_slot_cycle, "
       "terrain_attr_block_scan _inc/_axdec/_dec (4-sign family "
       "complete), game_setup_toggle_step + game_setup_entity_step "
       "(counters 1078-107A join 107B-107E = one 7-phase sequence), "
       "r06_ui_dispatch_block (5-entry HUD/dispatch block). **Levels "
       "0-3 all complete**; global queue 574 -> 522 (L4..L21, L19=206). "
       "**Gates green:** check 1,111, verify_rebuild faithful, verify_idb "
       "INTACT, read-back 1109/1109+2/2. |")

STATUS_PARA = (
    "**Global Level-3 COMPLETE (finding 74):** 2 batches named **all 52 L3 "
    "functions** (`named` 1,057 → **1,109**), **L3 `naming_queue` 52 → 0** "
    "(residue = 4 orphans + 7 thunks, 0 other). New tool `tools/dump_full.py` "
    "walks whole function bodies (dump_level1 stops at the first terminator "
    "— it had shown only 12 of sub_14CC6's 396 bytes). Structural wins: "
    "**`sbi_request_dispatch`** (the 731-byte 20-op SBI mailbox processor: "
    "config triples, EMS pages, PIT periods, driver callbacks — pair of "
    "`state_block_77720_store8`), **`overlay_file_open`** (open/cache front "
    "end delegating to `overlay_loader_main`), **`line_record_draw_loop`** "
    "(parent loop of `line_flag_dispatch_28ed8` + `line_table_scan_"
    "dispatch`), **`farobj_entity_accum_sweep`** (slot-aging sweep pair of "
    "`farobj_entity_accum_copy`), the `sbi_pit_period_enable`/`_disable` "
    "bracket around `sbi_mode_slot_store` in `mode_slot_enter`, the "
    "4-direction `terrain_attr_block_scan*` family, and the 7-phase "
    "`game_setup_*_step` sequence (counters ds:1078..107E across three "
    "siblings). **Levels 0–3 are now all complete**; global naming_queue = "
    "522 across Levels 4–21 (L19 = 206, the giant SCC). **Gates all green** "
    "(check 1,111, verify_rebuild faithful, verify_idb INTACT, read-back "
    "**1,109/1,109 + 2/2**)."
)

OPEN_NEW = [
    "- **GLOBAL LEVEL 3 COMPLETE (finding 74):** 2 batches named all 52 L3",
    "  fns, `named` **1057 -> 1109**, **L3 queue 52 -> 0** (4 orphans + 7",
    "  thunks, 0 other). New `tools/dump_full.py` (full bodies past the",
    "  first terminator). Highlights: sbi_request_dispatch (731B mailbox",
    "  processor), overlay_file_open, line_record_draw_loop,",
    "  farobj_entity_accum_sweep, 4-sign terrain_attr_block_scan family,",
    "  7-phase game_setup_*_step sequence. All 4 gates green (check 1111,",
    "  verify_rebuild faithful, verify_idb INTACT, read-back 1109/1109+2/2).",
    "- **Next: Global Level-4 naming** (queue 522 across Levels 4..21:",
    "  L4=54, L5=60, L6=60, L7=21, L8=13, L9=7, L10=11, L11=15, L12=11,",
    "  L13=15, L14=11, L15=5, L16=4, L17=1, L18=1, L19=206, L20=25, L21=2).",
    "  L4-L6 (174) are the next well-shaped batches; L19 (206-node giant",
    "  SCC) needs its own strategy.",
    "- **Follow-ups carried:** class-c undecodable overlay spans (conf:low),",
    "  92 low-conf DATA fns, 24 trap-only thunks, 397 global orphans",
    "  excluded from bottom-up naming.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-18 74" in raw:
    print("findings_log: 74 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 74 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 30" in raw:
    print("time_log: 30 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 29" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 30 after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Global Level-3 COMPLETE (finding 74)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f74 para")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVEL 3 COMPLETE (finding 74)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f74 status (%d bytes)" % len(block))