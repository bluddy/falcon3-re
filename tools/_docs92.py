"""Docs for Finding 92 (L19 Batch 6 of 6, 34 named - L19 SCC complete). Idempotent."""
import io

# ---------- findings_log.md (LF) ----------
FL = "docs/findings_log.md"
raw = io.open(FL, encoding="utf-8", newline="").read()
if "## 2026-10-19 92" not in raw:
    foot2 = "\n\n(append new findings below)"
    assert raw.rstrip("\n").endswith(foot2), repr(raw[-60:])
    i = raw.rindex(foot2)
    assert raw[:i].rstrip("\n").endswith("---"), "footer must be preceded by ---"
    entry = (
        "\n\n## 2026-10-19 92 - L19 Batch 6 of 6: 34 named, L19 COMPLETE\n"
        "(`named` 1,570 -> **1,604**; L19 to_name 34 -> **0**)\n"
        "\n"
        "**The giant Level-19 SCC is fully named (209/209, 292 total fns\n"
        "incl. joined sub-nodes).** Final 34 from `level19_batch6.txt`\n"
        "(5,600 ln). Global naming queue 61 -> **27** (L20=25, L21=2).\n"
        "Highlights:\n"
        "\n"
        "**`mode_phase_apply_core`** (sub_321DD, in=8): THE target of all\n"
        "four mode_phase_apply trampolines (sub_421F9/42206/42213/42220 -\n"
        "F89 + F90's stub/alt, F92's event/state). ds:491h!=0FFFFh routes\n"
        "to far_mode_event_dispatch body; else stores ds:23Bh mode +\n"
        "state_word_22d28_set_ax + the 24Fh..259h view-extent block with\n"
        "modes 0Ch/0Eh/0 selecting C7h/96h vs 63h/32h. Its sibling\n"
        "**`mode_extent_recompute`** (sub_322E5, in=7) forces full\n"
        "view_extent_init_0c + compute + get_quad into ds:78Eh..794h.\n"
        "\n"
        "**`farobj_altitude_scale_step`** (sub_3DC55, **in=16 - ties the\n"
        "batch's caller record**): funcs_4E5C0*(64h-[si+14h])>>5 scale ->\n"
        "farobj_record_bulk_copy, [di+60h]->[si+23h]. **`game_frame_update_chain`**\n"
        "(sub_2FEF2): the per-frame entity/HUD chain - farobj_slot_update_driver\n"
        "+ farobj_move_accumulate_step + tile_object_interpreter +\n"
        "farobj_slot_step_spawn + farobj_sweep_all + 3 hud_* steps +\n"
        "entity_proj_depth_class. **`hud_draw_chain_step`** (sub_35BCE): the\n"
        "7-call HUD draw pipeline (heading tape -> field14 -> value format\n"
        "-> field0c -> readout -> timer countdown -> sprite trail).\n"
        "\n"
        "**The burn pair:** **`farobj_thrust_burn_step`** (sub_4236B) -\n"
        "[di+0C3h]>>2 fuel sub + [si+5Ah] bits0/1 -> 1Eh/4Ch [di+5Eh] subs\n"
        "(two-bit one-shot); sibling of F90's farobj_fuel_burn_step.\n"
        "**`terrain_vm_buffer_decay`** (sub_4F3EC, **in=15**): 7A32h\n"
        "A754h->ABF8h copy + 46h-byte -2-clamped decay (the VM neighbor).\n"
        "**`ui_menu_transition_step`** (sub_67BAF, in=13, menu stub hub),\n"
        "**`ui_menu_page_args_setup`**, **`farobj_cfg_code_patch`**\n"
        "(self-mod 2FCE8/30C14/30C17/30C19 patcher), **`control_axes_record_store`**\n"
        "+ **`ems_axes_record_init`**, **`farobj_slot_table_load`** (mirror of\n"
        "F91's farobj_slot_table_copy), **`game_state_load_apply`**\n"
        "(1770h-word save-state restore), and the small trampolines\n"
        "**`mode_reset_far_tail`** / **`r30_vm_flag_set`** / **`farobj_behavior_far_tramp`**.\n"
        "\n"
        "### Gates (all green)\n"
        "\n"
        "`naming.py check` **1,606** . `verify_rebuild` **faithful (2,237 ==\n"
        "2,237)** . `verify_idb` **INTACT** . `name_readback` **1,604/1,604\n"
        "function + 2/2 global**.\n"
    )
    new = raw[:i] + entry + "\n---" + foot2
    io.open(FL, "w", encoding="utf-8", newline="").write(new)
    print("findings_log: inserted Finding 92 entry")
else:
    print("findings_log: Finding 92 already present")

# ---------- time_log.yaml (CRLF) ----------
TL = "docs/time_log.yaml"
raw = io.open(TL, encoding="utf-8", newline="").read()
if "Finding 92:" not in raw:
    j = raw.index("Finding 91")
    eol = raw.index("\n", j) + 1
    row = (
        "| 2026-10-19 (session 46) | ~2 h | **Finding 92: L19 Batch 6 of 6 -- "
        "34 named, `named` 1,570 -> **1,604**, L19 to_name 34 -> 0 (SCC "
        "COMPLETE: 209/209).** Headlines: **mode_phase_apply_core** (target "
        "of all four phase trampolines), **farobj_altitude_scale_step** "
        "(in=16), **game_frame_update_chain**, **hud_draw_chain_step**, "
        "**farobj_thrust_burn_step**, **terrain_vm_buffer_decay** (in=15). "
        "Queue 61 -> 27 (L20=25, L21=2). **Gates green:** check 1,606, "
        "verify_rebuild faithful, verify_idb INTACT, read-back 1604/1604+2/2. |\r\n"
    )
    new = raw[:eol] + row + raw[eol:]
    io.open(TL, "w", encoding="utf-8", newline="").write(new)
    print("time_log: inserted Finding 92 row")
else:
    print("time_log: Finding 92 row already present")

# ---------- status.md ----------
ST = "status.md"
raw = io.open(ST, encoding="utf-8", newline="").read()
if "L19 Batch 6/6 (finding 92)" not in raw:
    marker = "**Still outstanding:**"
    i = raw.index(marker)
    para = (
        "**L19 Batch 6/6 (finding 92) - L19 SCC COMPLETE:** 34 functions "
        "named (`named` 1,570 → **1,604**), **L19 `to_name` 34 → 0 "
        "(209/209 of the giant SCC)**. Headlines: **mode_phase_apply_core** "
        "(sub_321DD — THE target of all four mode_phase_apply trampolines; "
        "stores the mode + view-extent block); **mode_extent_recompute** "
        "(forced view_extent_init/compute/get_quad sibling); "
        "**farobj_altitude_scale_step** (sub_3DC55, in=16); "
        "**game_frame_update_chain** (the per-frame entity/HUD update "
        "chain); **hud_draw_chain_step** (7-call HUD draw pipeline); "
        "**farobj_thrust_burn_step** + **farobj_fuel_burn_step** pair "
        "context; **terrain_vm_buffer_decay** (in=15); "
        "**ui_menu_transition_step** (in=13 menu stub hub). "
        "**Gates green:** check **1,606**, verify_rebuild **faithful**, "
        "verify_idb **INTACT**, read-back **1,604/1,604 + 2/2**. "
        "Remaining: L20 (25), L21 (2) → queue 0.\n\n"
    )
    new = raw[:i] + para + raw[i:]
    io.open(ST, "w", encoding="utf-8", newline="").write(new)
    print("status: inserted L19 Batch 6/6 paragraph")
else:
    print("status: Batch 6/6 paragraph already present")

# ---------- open_items.md (CRLF, plain bullet) ----------
OI = "docs/open_items.md"
raw = io.open(OI, encoding="utf-8", newline="").read()
key = "L20 (25 fns"
if key not in raw:
    line = (
        "- L20 (25 fns) + L21 (2 fns) \u2014 the final two global levels; "
        "one finding each hits naming queue 0.\r\n"
    )
    if not raw.endswith("\r\n"):
        raw += "\r\n"
    io.open(OI, "w", encoding="utf-8", newline="").write(raw + line)
    print("open_items: appended L20/L21 bullet")
else:
    print("open_items: L20/L21 bullet already present")
print("docs92 done")
