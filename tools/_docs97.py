"""Docs for Finding 97 (orphan batch 3, 66 named). Idempotent."""
import io

# ---------- findings_log.md (LF) ----------
FL = "docs/findings_log.md"
raw = io.open(FL, encoding="utf-8", newline="").read()
if "## 2026-10-22 97" not in raw:
    foot2 = "\n\n(append new findings below)"
    assert raw.rstrip("\n").endswith(foot2), repr(raw[-60:])
    i = raw.rindex(foot2)
    assert raw[:i].rstrip("\n").endswith("---"), "footer must be preceded by ---"
    entry = (
        "\n\n## 2026-10-22 97 - Orphan batch 3 complete: 66 named\n"
        "(`named` 1,764 -> **1,830**; orphans 264 -> **198**)\n"
        "\n"
        "Batch 3 of the 397-orphan sweep named 66 (48 medium / 18 low\n"
        "conf). Headlines:\n"
        "\n"
        "**`r32_track_menu_step_entry`** (r32_e83, 1572B, 10 callees):\n"
        "the largest batch-3 function - jpt_156DD4 jump table over\n"
        "7894h mode words, 300-unit threshold gates on 79E80, scroll\n"
        "counters, hud_track_distance_draw + ui_menu_transition_step.\n"
        "\n"
        "**`r37_hud_strip_render_entry`** (r37_e137, 788B, 9 callees):\n"
        "8x box_edge_strip_draw + 5x hud_track_label_strip HUD panel\n"
        "renderer.\n"
        "\n"
        "**`r23_menu_key_dispatch_loop`** (r23_e61, 570B C): 6E45h\n"
        "DGROUP modal loop - dispatch_22100, key scan at cs:23Ah ->\n"
        "10-way jmp table, pane state 6E8D6.\n"
        "\n"
        "**`record_span_build_and_dispatch`** (sub_29917),\n"
        "**`r29_yesno_confirm_loop`** (r29_e06, 166B),\n"
        "**`ems_sample_stream_tick`** (sub_16CE5 - EMS + AdLib 388h\n"
        "sample tick), **`r36_slot_char_flag_scan`**, **`r15_op_init_`\n"
        "`sequence`**, and the r39 three-render family (`r39_four_slot_`\n"
        "`render_entry` / `r39_angular_slot_render_entry` /\n"
        "`r39_queue_slot_render_entry`).\n"
        "\n"
        "Low-conf tail: 10 `overlay_undecoded_body_*` markers + 8\n"
        "fragments (r33/r35/r52/r54/r59/r60/r64 x2); 15 medium-conf\n"
        "`tail_bridge_to_*` 8-byte stubs.\n"
        "\n"
        "### Gates (all green)\n"
        "\n"
        "`naming.py check` **1,832** . `verify_rebuild` **faithful (2,237\n"
        "== 2,237)** . `verify_idb` **INTACT** . `name_readback`\n"
        "**1,830/1,830 function + 2/2 global**.\n"
    )
    new = raw[:i] + entry + "\n---" + foot2
    io.open(FL, "w", encoding="utf-8", newline="").write(new)
    print("findings_log: inserted Finding 97 entry")
else:
    print("findings_log: Finding 97 already present")

# ---------- time_log.yaml (CRLF) ----------
TL = "docs/time_log.yaml"
raw = io.open(TL, encoding="utf-8", newline="").read()
if "Finding 97:" not in raw:
    j = raw.index("Finding 96")
    eol = raw.index("\n", j) + 1
    row = (
        "| 2026-10-22 (session 50) | ~1 h | **Finding 97: orphan batch 3 "
        "complete -- 66 named, `named` 1,764 -> **1,830**, orphans 264 -> "
        "**198** (queue still 0).** Headlines: r32_track_menu_step_entry "
        "(r32_e83 1572B 10-callee), r37_hud_strip_render_entry (788B), "
        "r23_menu_key_dispatch_loop (570B C), record_span_build_and_"
        "dispatch, r29_yesno_confirm_loop, ems_sample_stream_tick, "
        "r36_slot_char_flag_scan + r39 render family; 48 medium / 18 low "
        "(10 overlay_undecoded_* + 8 fragments); 15 tail_bridge_to_* "
        "stubs. **Gates green:** check 1,832, verify_rebuild faithful, "
        "verify_idb INTACT, read-back 1830/1830+2/2. |\r\n"
    )
    new = raw[:eol] + row + raw[eol:]
    io.open(TL, "w", encoding="utf-8", newline="").write(new)
    print("time_log: inserted Finding 97 row")
else:
    print("time_log: Finding 97 row already present")

# ---------- status.md ----------
ST = "status.md"
raw = io.open(ST, encoding="utf-8", newline="").read()
if "ORPHAN BATCH 3 (finding 97)" not in raw:
    marker = "**Still outstanding:**"
    i = raw.index(marker)
    para = (
        "**ORPHAN BATCH 3 (finding 97):** the next 66 of 397 orphans "
        "named (`named` 1,764 → **1,830 / 2,237**; orphans 264 → **198**). "
        "Headlines: **r32_track_menu_step_entry** (r32_e83, 1572B, 10 "
        "callees — jpt_156DD4 mode dispatch); **r37_hud_strip_render_"
        "entry** (788B); **r23_menu_key_dispatch_loop** (570B C modal "
        "loop); **record_span_build_and_dispatch**; **r29_yesno_confirm_"
        "loop**; **ems_sample_stream_tick** (EMS + AdLib 388h); r39 "
        "three-render family. 48 medium / 18 low (10 "
        "`overlay_undecoded_body_*` + 8 fragments) + 15 "
        "`tail_bridge_to_*` stubs. **Gates green:** check **1,832**, "
        "verify_rebuild **faithful**, verify_idb **INTACT**, read-back "
        "**1,830/1,830 + 2/2**.\n\n"
    )
    new = raw[:i] + para + raw[i:]
    io.open(ST, "w", encoding="utf-8", newline="").write(new)
    print("status: inserted ORPHAN BATCH 3 paragraph")
else:
    print("status: ORPHAN BATCH 3 paragraph already present")

# ---------- open_items.md (CRLF, update orphan bullet) ----------
OI = "docs/open_items.md"
raw = io.open(OI, encoding="utf-8", newline="").read()
old = "- Orphan batches 3-6 (264 orphans remaining of the 397; "
if old in raw:
    line_end = raw.index("\r\n", raw.index(old)) + 2
    line_start = raw.rindex("\n", 0, raw.index(old)) + 1
    new_line = (
        "- Orphan batches 4-6 (198 orphans remaining of the 397; "
        "orphan_batches.json has 6 batches) -- continue one finding per "
        "batch; 3 batches x ~66 fns each.\r\n"
    )
    raw = raw[:line_start] + new_line + raw[line_end:]
    io.open(OI, "w", encoding="utf-8", newline="").write(raw)
    print("open_items: updated orphan-batches bullet (3-6 -> 4-6)")
else:
    print("open_items: orphan bullet already at batch 4-6")
print("docs97 done")
