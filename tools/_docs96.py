"""Docs for Finding 96 (orphan batch 2, 66 named). Idempotent."""
import io

# ---------- findings_log.md (LF) ----------
FL = "docs/findings_log.md"
raw = io.open(FL, encoding="utf-8", newline="").read()
if "## 2026-10-22 96" not in raw:
    foot2 = "\n\n(append new findings below)"
    assert raw.rstrip("\n").endswith(foot2), repr(raw[-60:])
    i = raw.rindex(foot2)
    assert raw[:i].rstrip("\n").endswith("---"), "footer must be preceded by ---"
    entry = (
        "\n\n## 2026-10-22 96 - Orphan batch 2 complete: 66 named\n"
        "(`named` 1,698 -> **1,764**; orphans 330 -> **264**)\n"
        "\n"
        "Batch 2 of the 397-orphan sweep named 66 (47 medium / 19 low\n"
        "conf). Headlines:\n"
        "\n"
        "**`r53_opcode_decode_apply`** (r53_e88, 2736B, 10 callees): the\n"
        "largest batch-2 function - r53 overlay stream/opcode decode\n"
        "dispatching sbi_stream_dispatch, r53_script_opcode_interpreter,\n"
        "r53_record_walk_dispatch, key_event_mode_gate.\n"
        "\n"
        "**`sprite_step_clip_project_body`** (sub_4B36A, 459B, 8\n"
        "callees): sprite step + clip projection body.\n"
        "\n"
        "**`fixed_vec3_magnitude_gate`** (sub_2385D, 237B): abs /\n"
        "componentwise-max magnitude + range gate - copies 12 bytes or\n"
        "jumps to the neighbouring loc_238B9 path.\n"
        "\n"
        "**`stream_playback_resume_gate`** (sub_1BD64, 78B),\n"
        "**`cell_delta_key_search`** (sub_13276, 124B),\n"
        "**`kb_record_field22_clear_all`** (sub_1B631, 83B C, 6\n"
        "callees), **`device_port_cmd_poll`** (sub_17263),\n"
        "**`menu_index_step_dispatch`** (sub_67480),\n"
        "**`pending_session_step_chain`** (sub_6E558, 4 callees),\n"
        "**`r25_four_slot_menu_step`** / **`r26_two_view_menu_step`**,\n"
        "**`r27_coord_pair_select_entry`**, **`r64_record_field_read`**.\n"
        "\n"
        "Low-conf tail: 18 `overlay_undecoded_body_*` markers + 1 data\n"
        "fragment (r38_e131 -> `r38_data_fragment`); 15 medium-conf\n"
        "`tail_bridge_to_*` 8-byte stubs.\n"
        "\n"
        "### Gates (all green)\n"
        "\n"
        "`naming.py check` **1,766** . `verify_rebuild` **faithful (2,237\n"
        "== 2,237)** . `verify_idb` **INTACT** . `name_readback`\n"
        "**1,764/1,764 function + 2/2 global**.\n"
    )
    new = raw[:i] + entry + "\n---" + foot2
    io.open(FL, "w", encoding="utf-8", newline="").write(new)
    print("findings_log: inserted Finding 96 entry")
else:
    print("findings_log: Finding 96 already present")

# ---------- time_log.yaml (CRLF) ----------
TL = "docs/time_log.yaml"
raw = io.open(TL, encoding="utf-8", newline="").read()
if "Finding 96:" not in raw:
    j = raw.index("Finding 95")
    eol = raw.index("\n", j) + 1
    row = (
        "| 2026-10-22 (session 49) | ~1 h | **Finding 96: orphan batch 2 "
        "complete -- 66 named, `named` 1,698 -> **1,764**, orphans 330 -> "
        "**264** (queue still 0).** Headlines: r53_opcode_decode_apply "
        "(r53_e88 2736B 10-callee overlay opcode decode), "
        "sprite_step_clip_project_body (sub_4B36A 459B), "
        "fixed_vec3_magnitude_gate (sub_2385D), stream_playback_resume_"
        "gate, cell_delta_key_search, kb_record_field22_clear_all; "
        "47 medium / 19 low (18 overlay_undecoded_* + r38_data_fragment); "
        "15 tail_bridge_to_* stubs. **Gates green:** check 1,766, "
        "verify_rebuild faithful, verify_idb INTACT, read-back 1764/1764"
        "+2/2. |\r\n"
    )
    new = raw[:eol] + row + raw[eol:]
    io.open(TL, "w", encoding="utf-8", newline="").write(new)
    print("time_log: inserted Finding 96 row")
else:
    print("time_log: Finding 96 row already present")

# ---------- status.md ----------
ST = "status.md"
raw = io.open(ST, encoding="utf-8", newline="").read()
if "ORPHAN BATCH 2 (finding 96)" not in raw:
    marker = "**Still outstanding:**"
    i = raw.index(marker)
    para = (
        "**ORPHAN BATCH 2 (finding 96):** the next 66 of 397 orphans "
        "named (`named` 1,698 → **1,764 / 2,237**; orphans 330 → **264**). "
        "Headlines: **r53_opcode_decode_apply** (r53_e88, 2736B, 10 "
        "callees — r53 overlay stream/opcode decode); "
        "**sprite_step_clip_project_body** (sub_4B36A, 459B); "
        "**fixed_vec3_magnitude_gate** (sub_2385D, 237B); "
        "**stream_playback_resume_gate**; **cell_delta_key_search**; "
        "**kb_record_field22_clear_all**; r25/r26/r27 menu step entries. "
        "47 medium / 19 low (18 `overlay_undecoded_body_*` + "
        "r38_data_fragment) + 15 `tail_bridge_to_*` stubs. **Gates "
        "green:** check **1,766**, verify_rebuild **faithful**, "
        "verify_idb **INTACT**, read-back **1,764/1,764 + 2/2**.\n\n"
    )
    new = raw[:i] + para + raw[i:]
    io.open(ST, "w", encoding="utf-8", newline="").write(new)
    print("status: inserted ORPHAN BATCH 2 paragraph")
else:
    print("status: ORPHAN BATCH 2 paragraph already present")

# ---------- open_items.md (CRLF, update orphan bullet) ----------
OI = "docs/open_items.md"
raw = io.open(OI, encoding="utf-8", newline="").read()
old = "- Orphan batches 2-6 (330 orphans remaining of the 397; "
if old in raw:
    line_end = raw.index("\r\n", raw.index(old)) + 2
    line_start = raw.rindex("\n", 0, raw.index(old)) + 1
    new_line = (
        "- Orphan batches 3-6 (264 orphans remaining of the 397; "
        "orphan_batches.json has 6 batches) -- continue one finding per "
        "batch; 4 batches x ~66 fns each.\r\n"
    )
    raw = raw[:line_start] + new_line + raw[line_end:]
    io.open(OI, "w", encoding="utf-8", newline="").write(raw)
    print("open_items: updated orphan-batches bullet (2-6 -> 3-6)")
else:
    print("open_items: orphan bullet already at batch 3-6")
print("docs96 done")
