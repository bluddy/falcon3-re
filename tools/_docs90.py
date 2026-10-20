"""Docs for Finding 90 (L19 Batch 4 of 6, 34 named). Idempotent per doc."""
import io, sys

# ---------- findings_log.md (LF) ----------
FL = "docs/findings_log.md"
raw = io.open(FL, encoding="utf-8", newline="").read()
if "## 2026-10-19 90" not in raw:
    foot2 = "\n\n(append new findings below)"
    assert raw.rstrip("\n").endswith(foot2), repr(raw[-60:])
    i = raw.rindex(foot2)
    assert raw[:i].rstrip("\n").endswith("---"), "footer must be preceded by ---"
    entry = (
        "\n\n## 2026-10-19 90 - L19 Batch 4 of 6: 34 named, L19 queue 102 -> 68\n"
        "(`named` 1,502 -> **1,536**)\n"
        "\n"
        "Fourth slice of the giant Level-19 SCC. 34 of 102 named from\n"
        "`level19_batch4.txt` (5,925 ln). Highlights:\n"
        "\n"
        "**`farobj_queue_drain_dispatch`** (sub_4C19E, 2500B, **in=9 - the\n"
        "batch-4 hub**): FAR queue drain. Class-range dispatch on bx (12h/13h,\n"
        "33h-37h), pops cs:word_2E10A records at 1Bh stride, inc 2E10E /\n"
        "dec 2E10C, tail-jumps into farobj_slot_update_driver bodies.\n"
        "**`hud_state_rowtable_step`** (sub_45057, 2142B, in=4 main loop):\n"
        "walks 72 (48h) 63FD:0A5h+ entries with entity_step_flags +\n"
        "hw_flag_bit2/3_22e ops per row.\n"
        "\n"
        "**`farobj_class_table_entry`** (sub_4111F, in=12): [si+75h] class\n"
        "selects the 263Bh or 2A01h table at 2Ah stride, returns [di+2],\n"
        "plus farobj_table_snapshot position read. **`hud_track_label_strip`**\n"
        "(sub_3A29C, in=8): copies [si+8Ch/86h/8Ah] -> [si+90h/92h/94h] with\n"
        "0AABh thresholds on [si+79h] bit0 + tile_strip_sample_draw at 47D6h\n"
        "(called by steerpoint_scan_update + the menu pipeline).\n"
        "**`ems_window_load_snapshot`** (sub_30882, in=6): ems_map_seg_10233\n"
        "then movsw 1770h words 5DC0h -> 2EE0h + slot2_map_window_load;\n"
        "callers span ems_slot_bootstrap_step and three F87-F89 hubs.\n"
        "\n"
        "**Input/transform core:** **`control_axes_record_write`**\n"
        "(sub_307A5, in=8): writes 47Bh x7 words + control_axes_read x2 +\n"
        "control_axis_value into the record; **`farobj_project_transform_write`**\n"
        "(sub_32453, in=7): fixed_matrix_mul + position add +\n"
        "angle_adjusted_copy (the shared project primitive); **`ui_gauge_panel_draw`**\n"
        "(sub_32393, in=5): draw_from_struct x2 + far_cb_gated x5 on the\n"
        "2A0h..2F5h panel structs; **`coord_window_bounds_test`**\n"
        "(sub_31EBF, in=5): idiv 4E06h/3031h then CF set/clear against the\n"
        "60h..E4h x 70h..C1h window. **`game_setup_staged_init`**\n"
        "(sub_45976, in=1): 6x game_setup_staged_step stage loop.\n"
        "\n"
        "### Gates (all green)\n"
        "\n"
        "`naming.py check` **1,538** . `verify_rebuild` **faithful (2,237 ==\n"
        "2,237)** . `verify_idb` **INTACT** . `name_readback` **1,536/1,536\n"
        "function + 2/2 global**.\n"
    )
    new = raw[:i] + entry + "\n---" + foot2
    io.open(FL, "w", encoding="utf-8", newline="").write(new)
    print("findings_log: inserted Finding 90 entry")
else:
    print("findings_log: Finding 90 already present")

# ---------- time_log.yaml (CRLF) ----------
TL = "docs/time_log.yaml"
raw = io.open(TL, encoding="utf-8", newline="").read()
if "Finding 90:" not in raw:
    j = raw.index("Finding 89")
    eol = raw.index("\n", j) + 1
    row = (
        "| 2026-10-19 (session 45) | ~2 h | **Finding 90: L19 Batch 4 of 6 -- "
        "34 named, `named` 1,502 -> **1,536**, L19 queue 102 -> 68**. "
        "Headlines: **farobj_queue_drain_dispatch** (sub_4C19E, in=9 queue-drain "
        "hub), **hud_state_rowtable_step** (2142B 72-row walk), "
        "**farobj_class_table_entry** (in=12 class-table selector), "
        "**ems_window_load_snapshot** (1770h-word EMS copy), "
        "**control_axes_record_write** (in=8), **farobj_project_transform_write** "
        "(in=7 shared fixed_matrix_mul primitive), **ui_gauge_panel_draw** "
        "(in=5). Queue 129 -> 95. **Gates green:** check 1,538, verify_rebuild "
        "faithful, verify_idb INTACT, read-back 1536/1536+2/2. |\r\n"
    )
    new = raw[:eol] + row + raw[eol:]
    io.open(TL, "w", encoding="utf-8", newline="").write(new)
    print("time_log: inserted Finding 90 row")
else:
    print("time_log: Finding 90 row already present")

# ---------- status.md ----------
ST = "status.md"
raw = io.open(ST, encoding="utf-8", newline="").read()
if "L19 Batch 4/6 (finding 90)" not in raw:
    marker = "**Still outstanding:**"
    i = raw.index(marker)
    para = (
        "**L19 Batch 4/6 (finding 90):** 34 functions named "
        "(`named` 1,502 → **1,536**), **L19 `naming_queue` 102 → 68**. "
        "Headlines: **farobj_queue_drain_dispatch** (sub_4C19E, in=9 — FAR "
        "queue drain: class-range dispatch on bx, 1Bh-stride record pop, "
        "tail-jumps into farobj_slot_update_driver bodies); "
        "**hud_state_rowtable_step** (sub_45057, 72-row entity_step_flags "
        "walk); **farobj_class_table_entry** (sub_4111F, in=12 — [si+75h] "
        "class → 263Bh/2A01h 2Ah-stride table); **ems_window_load_snapshot** "
        "(sub_30882, ems_map_seg_10233 + 1770h-word copy); "
        "**control_axes_record_write** (sub_307A5, in=8) + "
        "**farobj_project_transform_write** (sub_32453, in=7) + "
        "**ui_gauge_panel_draw** (sub_32393, in=5); **game_setup_staged_init** "
        "(sub_45976); **coord_window_bounds_test** (sub_31EBF). "
        "**Gates green:** check **1,538**, verify_rebuild **faithful**, "
        "verify_idb **INTACT**, read-back **1,536/1,536 + 2/2**. "
        "Remaining: L19 batches 5–6 (68), then L20 (25), L21 (2).\n\n"
    )
    new = raw[:i] + para + raw[i:]
    io.open(ST, "w", encoding="utf-8", newline="").write(new)
    print("status: inserted L19 Batch 4/6 paragraph")
else:
    print("status: Batch 4/6 paragraph already present")

# ---------- open_items.md (CRLF, plain bullet) ----------
OI = "docs/open_items.md"
raw = io.open(OI, encoding="utf-8", newline="").read()
key = "L19 batches 5\u20136"
if key not in raw:
    line = (
        "- L19 batches 5\u20136 (68 fns remaining of the giant SCC; "
        "`level19_batch5.txt`..`batch6.txt` ready) \u2014 continue one "
        "finding per batch; then L20 (25) + L21 (2) to hit queue 0.\r\n"
    )
    if not raw.endswith("\r\n"):
        raw += "\r\n"
    io.open(OI, "w", encoding="utf-8", newline="").write(raw + line)
    print("open_items: appended batches 5-6 bullet")
else:
    print("open_items: batches 5-6 bullet already present")
print("docs90 done")
