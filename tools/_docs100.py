"""Docs for Finding 100 (orphan batch 6, 66 named - sweep complete). Idempotent."""
import io

# ---------- findings_log.md (LF) ----------
FL = "docs/findings_log.md"
raw = io.open(FL, encoding="utf-8", newline="").read()
if "## 2026-10-22 100" not in raw:
    foot2 = "\n\n(append new findings below)"
    assert raw.rstrip("\n").endswith(foot2), repr(raw[-60:])
    i = raw.rindex(foot2)
    assert raw[:i].rstrip("\n").endswith("---"), "footer must be preceded by ---"
    entry = (
        "\n\n## 2026-10-22 100 - Orphan sweep COMPLETE: batch 6 named 66\n"
        "(`named` 1,962 -> **2,028**; orphans 66 -> **0**)\n"
        "\n"
        "Final batch of the 397-orphan sweep named 66 (48 medium / 18 low\n"
        "conf). All 397 orphans (67/66/66/66/66/66 across six batches) are\n"
        "now named. Headlines:\n"
        "\n"
        "**`r22_slot_select_modal_loop`** (r22_e57, 936B C): the largest\n"
        "batch-6 function - the 6E45h DGROUP modal slot-select loop with\n"
        "its 11-way event jump table.\n"
        "\n"
        "The **r39 render quartet**: **`r39_rotational_render_entry`**\n"
        "(595B C) + **`r39_rotational_render_entry_b`** (566B C) +\n"
        "**`r39_dual_index_render_entry`** (423B C) +\n"
        "**`r39_variant_switch_render_entry`** (321B C) - each an\n"
        "unrolled sub_2C4FF draw chain closed by a distinct\n"
        "`r39_farptr_call_gate` arity.\n"
        "\n"
        "**`record_pool_admit_demote`** (218B - admit-by-demote quota\n"
        "allocator), **`r35_field_scale_op_step`** (181B),\n"
        "**`r36_record_grids_clear`** (160B), **`r35_mode8_state_init`**\n"
        "(132B - sets the r35_e100 guard byte),\n"
        "**`r36_slot_max_flag_pick`** (112B).\n"
        "\n"
        "Also: **`startup_entry_stack_swap`** (the `start` entry),\n"
        "**`fixed_vec3_cross`** (16:16 cross product),\n"
        "**`cs_bitfield_byte_extract`**, **`cs_byte_2e12b_store`**,\n"
        "`r07_angle_xy_norm_pair` / `r07_list_heads_init` /\n"
        "`r07_state_byte_skip_gate` / `r07_state_byte_toggle`, r12 stubs,\n"
        "`r33_record_field_range_check` / `r33_vec3_lowbyte_avg`, and\n"
        "eight `*_far_wrapper` 6-24B bridges (trig_table_lookup_83a5,\n"
        "far_cb_with_args, bda_417_mask_clear, state_byte_2549e,\n"
        "overlay_seg_word_set2_if3).\n"
        "\n"
        "Low-conf tail: 11 `overlay_undecoded_body_*` markers + 4\n"
        "garbage fragments (r33/r58/r61/r67) + `farobj_ems_behavior_init`\n"
        "(callees-only body) + `r52_indexed_pair_step` +\n"
        "`data_fragment_6ec14`; 14 medium-conf tail-bridge stubs (incl.\n"
        "loadout_enter h/i/j, state_init_all m/n, `tail_bridge_2d63a` raw\n"
        "target).\n"
        "\n"
        "### Gates (all green)\n"
        "\n"
        "`naming.py check` **2,030** . `verify_rebuild` **faithful (2,237\n"
        "== 2,237)** . `verify_idb` **INTACT** . `name_readback`\n"
        "**2,028/2,028 function + 2/2 global**.\n"
    )
    new = raw[:i] + entry + "\n---" + foot2
    io.open(FL, "w", encoding="utf-8", newline="").write(new)
    print("findings_log: inserted Finding 100 entry")
else:
    print("findings_log: Finding 100 already present")

# ---------- time_log.yaml (CRLF) ----------
TL = "docs/time_log.yaml"
raw = io.open(TL, encoding="utf-8", newline="").read()
if "Finding 100:" not in raw:
    j = raw.index("Finding 99")
    eol = raw.index("\n", j) + 1
    row = (
        "| 2026-10-22 (session 51) | ~1 h | **Finding 100: orphan sweep "
        "COMPLETE -- batch 6 named 66, `named` 1,962 -> **2,028**, orphans 66 "
        "-> **0** (397/397 orphans named across 6 batches; queue still 0).** "
        "Headlines: r22_slot_select_modal_loop (936B C), r39 render quartet "
        "(595+566+423+321B), record_pool_admit_demote (218B), "
        "r35_field_scale_op_step (181B), r36_record_grids_clear (160B), "
        "startup_entry_stack_swap (start), fixed_vec3_cross, "
        "cs_bitfield_byte_extract, eight *_far_wrapper bridges; 48 medium / "
        "18 low (11 overlay_undecoded_* + 4 fragments + 3 semantic); 14 "
        "tail-bridge stubs. **Gates green:** check 2,030, verify_rebuild "
        "faithful, verify_idb INTACT, read-back 2028/2028+2/2. |\r\n"
    )
    new = raw[:eol] + row + raw[eol:]
    io.open(TL, "w", encoding="utf-8", newline="").write(new)
    print("time_log: inserted Finding 100 row")
else:
    print("time_log: Finding 100 row already present")

# ---------- status.md ----------
ST = "status.md"
raw = io.open(ST, encoding="utf-8", newline="").read()
if "ORPHAN SWEEP COMPLETE (finding 100)" not in raw:
    marker = "**Still outstanding:**"
    i = raw.index(marker)
    para = (
        "**ORPHAN SWEEP COMPLETE (finding 100):** final batch named the "
        "last 66 of 397 orphans (`named` 1,962 → **2,028 / 2,237**; orphans "
        "66 → **0**). Headlines: **r22_slot_select_modal_loop** (936B C); "
        "**r39 render quartet** (595/566/423/321B C); "
        "**record_pool_admit_demote**; **r35_field_scale_op_step**; "
        "**r36_record_grids_clear**; **startup_entry_stack_swap** (the "
        "`start` entry); **fixed_vec3_cross**; eight `*_far_wrapper` "
        "bridges. 48 medium / 18 low (11 `overlay_undecoded_body_*` + 4 "
        "fragments + 3 semantic) + 14 tail-bridge stubs. **Gates green:** "
        "check **2,030**, verify_rebuild **faithful**, verify_idb "
        "**INTACT**, read-back **2,028/2,028 + 2/2**.\n\n"
    )
    new = raw[:i] + para + raw[i:]
    io.open(ST, "w", encoding="utf-8", newline="").write(new)
    print("status: inserted ORPHAN SWEEP COMPLETE paragraph")
else:
    print("status: ORPHAN SWEEP COMPLETE paragraph already present")

# ---------- open_items.md (CRLF, replace final orphan bullet) ----------
OI = "docs/open_items.md"
raw = io.open(OI, encoding="utf-8", newline="").read()
old = "- Orphan batch 6 (66 orphans remaining of the 397; "
if old in raw:
    line_end = raw.index("\r\n", raw.index(old)) + 2
    line_start = raw.rindex("\n", 0, raw.index(old)) + 1
    new_line = (
        "- Orphan sweep COMPLETE (finding 100): all 397/397 orphans named "
        "across 6 batches (67/66/66/66/66/66); `orphans` 397 -> 0, named "
        "1,962 -> 2,028/2,237, queue 0. Remaining unnamed: 209, all "
        "excluded by design (thunk slots/undecodable). Next-phase "
        "candidates: 302 thunk slots, multi-entry range repairs, "
        "sub_22DFF undecoded region.\r\n"
    )
    raw = raw[:line_start] + new_line + raw[line_end:]
    io.open(OI, "w", encoding="utf-8", newline="").write(raw)
    print("open_items: replaced orphan-batch bullet with sweep-complete note")
else:
    print("open_items: orphan bullet already at completion note")
print("docs100 done")
