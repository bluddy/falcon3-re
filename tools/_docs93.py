"""Docs for Finding 93 (L20 complete, 25 named - queue down to L21 only). Idempotent."""
import io

# ---------- findings_log.md (LF) ----------
FL = "docs/findings_log.md"
raw = io.open(FL, encoding="utf-8", newline="").read()
if "## 2026-10-19 93" not in raw:
    foot2 = "\n\n(append new findings below)"
    assert raw.rstrip("\n").endswith(foot2), repr(raw[-60:])
    i = raw.rindex(foot2)
    assert raw[:i].rstrip("\n").endswith("---"), "footer must be preceded by ---"
    entry = (
        "\n\n## 2026-10-19 93 - Level 20 complete: 25 named\n"
        "(`named` 1,604 -> **1,629**; L20 to_name 25 -> **0**)\n"
        "\n"
        "The entire Level-20 level (63 fns incl. overlay bodies, 25\n"
        "unnamed) is named in one pass from `level20_full.txt` (3,152 ln).\n"
        "Global naming queue 27 -> **2 (L21 only: sub_186ADC, sub_6E29E)**.\n"
        "Highlights:\n"
        "\n"
        "**`ui_loadout_menu_cmd_dispatch`** (r35_e127, in=12): the\n"
        "two-level jump-table hub of the 162C family - cs:off_162DAF[bx]\n"
        "12-entry table (cmd0..cmd10 + self slots) with nested\n"
        "jpt_162D0F/jpt_162D49; cases set 602Eh:60956=0 or 63989=8 then\n"
        "call ui_loadout_menu_enter. Named with its eleven case arms as\n"
        "**ui_loadout_cmd0_transition** / **cmd1_record_clear** /\n"
        "**cmd2_slot_scan** / **cmd3..cmd5_enter** / **cmd6_enter**\n"
        "(nested) / **cmd7..cmd10_enter**, plus outer frame\n"
        "**`ui_loadout_menu_frame_scan`** (sub_162A94: clears record\n"
        "[bx+4] marks, decodes the 79B52 control byte, 60964 bit40h gate\n"
        "-> 79BDA).\n"
        "\n"
        "**`hw_config_apply_chain`** (sub_30307): stores bx/ax:dx into\n"
        "word_2E135/dword_2E13F then chains view_block4287_angles +\n"
        "hw_cfg_scan_22158 + hw_config_copy_85061 + r37_farptr_store_gate\n"
        "+ mode_session_state_reset -> jmp game_config_apply_init.\n"
        "**`mode_frame_gate_floor_clamp`** (sub_39CAA): ds:4AC2h==4 ->\n"
        "mode_frame_step_core; ==2/3 -> retn; else ax+=ds:4AA1h clamped to\n"
        "ds:4AB9h via floor_store_4abb. **`mode_session_state_mirror_init`**\n"
        "(sub_66ABD, in=9): the 6DE8h state-word mirror chain\n"
        "(6E14D->6E119->6E10D->6E129) + 4 flag-byte clears + config block.\n"
        "**`display_palette_hud_refresh_step`** (sub_67781): cmd\n"
        "interpreter + dword_79E60->79E3A + flag_block_zero +\n"
        "terrain_vm_buffer_decay + vga_dac_palette_upload + HUD strips.\n"
        "**`overlay_teardown_restore_state`** (sub_4DF9D):\n"
        "handle_release_all + op_bitmap_sweep_clear + ems_seg_free_21_49\n"
        "exit path + cs:2E118..2E11C -> 2E104..2E120 state restore.\n"
        "\n"
        "Overlay bodies (low conf, mixed data/code in far segments):\n"
        "**r53_record_walk_dispatch** (sub_188DF2, 2272B),\n"
        "**r36_loadout_record_copy** (r36_e75, stride-4Eh copy),\n"
        "**r53_farobj_pipeline_body** (sub_187E94, mutual SCC with\n"
        "**r53_far_call_case_block** = r35_e51), **r53_sbi_stream_dispatch**\n"
        "(sub_1820C0), **menu_cmd_store_and_record_scan** (r34_e94),\n"
        "**cmd_terrain_decay_step** (r30_e98).\n"
        "\n"
        "### Gates (all green)\n"
        "\n"
        "`naming.py check` **1,631** . `verify_rebuild` **faithful (2,237\n"
        "== 2,237)** . `verify_idb` **INTACT** . `name_readback`\n"
        "**1,629/1,629 function + 2/2 global**.\n"
    )
    new = raw[:i] + entry + "\n---" + foot2
    io.open(FL, "w", encoding="utf-8", newline="").write(new)
    print("findings_log: inserted Finding 93 entry")
else:
    print("findings_log: Finding 93 already present")

# ---------- time_log.yaml (CRLF) ----------
TL = "docs/time_log.yaml"
raw = io.open(TL, encoding="utf-8", newline="").read()
if "Finding 93:" not in raw:
    j = raw.index("Finding 92")
    eol = raw.index("\n", j) + 1
    row = (
        "| 2026-10-19 (session 47) | ~1.5 h | **Finding 93: Level 20 complete "
        "-- 25 named, `named` 1,604 -> **1,629**, L20 to_name 25 -> 0.** "
        "Headlines: **ui_loadout_menu_cmd_dispatch** (two-level 12-entry jpt "
        "hub + 11 cmd cases), **hw_config_apply_chain**, "
        "**mode_frame_gate_floor_clamp**, **mode_session_state_mirror_init** "
        "(in=9), **display_palette_hud_refresh_step**, "
        "**overlay_teardown_restore_state**, plus 6 overlay bodies "
        "(r53/r36/r34/r30). Queue 27 -> **2 (L21 only)**. **Gates green:** "
        "check 1,631, verify_rebuild faithful, verify_idb INTACT, read-back "
        "1629/1629+2/2. |\r\n"
    )
    new = raw[:eol] + row + raw[eol:]
    io.open(TL, "w", encoding="utf-8", newline="").write(new)
    print("time_log: inserted Finding 93 row")
else:
    print("time_log: Finding 93 row already present")

# ---------- status.md ----------
ST = "status.md"
raw = io.open(ST, encoding="utf-8", newline="").read()
if "Level 20 complete (finding 93)" not in raw:
    marker = "**Still outstanding:**"
    i = raw.index(marker)
    para = (
        "**Level 20 complete (finding 93):** 25 functions named "
        "(`named` 1,604 → **1,629**), **L20 `to_name` 25 → 0**. "
        "Headlines: **ui_loadout_menu_cmd_dispatch** (r35_e127, in=12 — "
        "two-level jump-table hub with eleven named cmd cases from "
        "cmd0_transition through cmd10_enter); **hw_config_apply_chain** "
        "(sub_30307 — hw scan/copy → game_config_apply_init tail); "
        "**mode_frame_gate_floor_clamp** (sub_39CAA); "
        "**mode_session_state_mirror_init** (sub_66ABD, in=9 — 6DE8h "
        "state-word mirror chain); **display_palette_hud_refresh_step** "
        "(sub_67781 — DAC palette upload + HUD strips); "
        "**overlay_teardown_restore_state** (sub_4DF9D — handle release "
        "+ bitmap sweep + EMS free + state restore); 6 low-conf overlay "
        "bodies (r53/r36/r34/r30). **Gates green:** check **1,631**, "
        "verify_rebuild **faithful**, verify_idb **INTACT**, read-back "
        "**1,629/1,629 + 2/2**. Remaining: L21 (2) → queue 0.\n\n"
    )
    new = raw[:i] + para + raw[i:]
    io.open(ST, "w", encoding="utf-8", newline="").write(new)
    print("status: inserted Level 20 complete paragraph")
else:
    print("status: Level 20 paragraph already present")

# ---------- open_items.md (CRLF, plain bullet) ----------
OI = "docs/open_items.md"
raw = io.open(OI, encoding="utf-8", newline="").read()
key = "L21 (2 fns: sub_186ADC"
if key not in raw:
    line = (
        "- L21 (2 fns: sub_186ADC, sub_6E29E) \u2014 the final two; one "
        "finding hits the global naming queue 0.\r\n"
    )
    if not raw.endswith("\r\n"):
        raw += "\r\n"
    io.open(OI, "w", encoding="utf-8", newline="").write(raw + line)
    print("open_items: appended L21 bullet")
else:
    print("open_items: L21 bullet already present")
print("docs93 done")
