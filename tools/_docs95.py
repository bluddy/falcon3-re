"""Docs for Finding 95 (orphan batch 1, 67 named). Idempotent."""
import io

# ---------- findings_log.md (LF) ----------
FL = "docs/findings_log.md"
raw = io.open(FL, encoding="utf-8", newline="").read()
if "## 2026-10-19 95" not in raw:
    foot2 = "\n\n(append new findings below)"
    assert raw.rstrip("\n").endswith(foot2), repr(raw[-60:])
    i = raw.rindex(foot2)
    assert raw[:i].rstrip("\n").endswith("---"), "footer must be preceded by ---"
    entry = (
        "\n\n## 2026-10-19 95 - Orphan batch 1 complete: 67 named\n"
        "(`named` 1,631 -> **1,698**; orphans 397 -> **330**)\n"
        "\n"
        "After the global queue hit 0 (F94), the remaining unnamed set is\n"
        "**397 orphans** (`dyn==0 AND in==0`, no static callers - reached\n"
        "via far-jump/vector, excluded from the queue by design). Batch 1\n"
        "named 67 of them (54 medium / 13 low conf):\n"
        "\n"
        "**`game_frame_far_entry`** (sub_3FFEF, 3685B, in=0, 42 callees):\n"
        "the multi-purpose game-frame far-entry thunk (pop ax; cmp\n"
        "ax,0FFFFh) dispatching farobj_table_snapshot, farobj_rect_state_\n"
        "setup, game_config_apply_init, game_state_load_apply, view_\n"
        "terrain_frame_step, far_mode_event_dispatch, hud_track_strip_\n"
        "pipeline, r32_hud_phase_dispatch, entity_record_table_ops - the\n"
        "main game far-entry dispatcher reached via vector.\n"
        "\n"
        "**`r48_mouse_event_entry`** (r48_e97, 931B, C): the r48 overlay\n"
        "mouse/event pipeline - mode_record_field_lookup + 30+ op_dispatch_\n"
        "far_entry calls across 602Eh/7894h record slots.\n"
        "\n"
        "**`r39_queue_drain_entry`** (r39_e147, 566B, C): farobj queue\n"
        "drain + 8x r39_farptr_call_gate batch (opcodes 1-8).\n"
        "\n"
        "**`distance_tier_classify_entry`** (sub_6DD12, 369B): abs dx/dy\n"
        "diff vs 0BB8h (3000) selects tier 45h/54h/4Eh for far_cb_2.\n"
        "\n"
        "**`ui_bounds_clip_entry`** (sub_2A248, 198B): copies 10h-stride\n"
        "rects, bounds-checks vs 4 cs:1F6xx words, ORs clip flags, calls\n"
        "uibounds_top_bottom_dispatch.\n"
        "\n"
        "Remaining 13 low-conf = `overlay_undecoded_body_*` markers (IDA\n"
        "cannot decode the body); 13 `tail_bridge_to_*` 8-byte stubs\n"
        "(call tail_bridge_overlay_load + jmp far named target).\n"
        "\n"
        "### Gates (all green)\n"
        "\n"
        "`naming.py check` **1,700** . `verify_rebuild` **faithful (2,237\n"
        "== 2,237)** . `verify_idb` **INTACT** . `name_readback`\n"
        "**1,698/1,698 function + 2/2 global**.\n"
    )
    new = raw[:i] + entry + "\n---" + foot2
    io.open(FL, "w", encoding="utf-8", newline="").write(new)
    print("findings_log: inserted Finding 95 entry")
else:
    print("findings_log: Finding 95 already present")

# ---------- time_log.yaml (CRLF) ----------
TL = "docs/time_log.yaml"
raw = io.open(TL, encoding="utf-8", newline="").read()
if "Finding 95:" not in raw:
    j = raw.index("Finding 94")
    eol = raw.index("\n", j) + 1
    row = (
        "| 2026-10-19 (session 48) | ~0.5 h | **Finding 95: orphan batch 1 "
        "complete -- 67 named, `named` 1,631 -> **1,698**, orphans 397 -> "
        "**330** (queue still 0).** Headlines: game_frame_far_entry "
        "(sub_3FFEF 3685B 42-callee far-entry dispatcher), r48_mouse_event_"
        "entry, r39_queue_drain_entry, distance_tier_classify_entry, "
        "ui_bounds_clip_entry; 13 low-conf overlay_undecoded_* markers, 13 "
        "tail_bridge_to_* stubs. **Gates green:** check 1,700, verify_rebuild "
        "faithful, verify_idb INTACT, read-back 1698/1698+2/2. |\r\n"
    )
    new = raw[:eol] + row + raw[eol:]
    io.open(TL, "w", encoding="utf-8", newline="").write(new)
    print("time_log: inserted Finding 95 row")
else:
    print("time_log: Finding 95 row already present")

# ---------- status.md ----------
ST = "status.md"
raw = io.open(ST, encoding="utf-8", newline="").read()
if "ORPHAN BATCH 1 (finding 95)" not in raw:
    marker = "**Still outstanding:**"
    i = raw.index(marker)
    para = (
        "**ORPHAN BATCH 1 (finding 95):** the first 67 of 397 orphans "
        "named (`named` 1,631 → **1,698 / 2,237**; orphans 397 → **330**). "
        "Headlines: **game_frame_far_entry** (sub_3FFEF, 3685B, 42 callees "
        "— the main game far-entry dispatcher); **r48_mouse_event_entry** "
        "(931B mouse/event pipeline); **r39_queue_drain_entry**; "
        "**distance_tier_classify_entry**; **ui_bounds_clip_entry**. 13 "
        "low-conf `overlay_undecoded_body_*` markers + 13 "
        "`tail_bridge_to_*` 8-byte stubs. **Gates green:** check "
        "**1,700**, verify_rebuild **faithful**, verify_idb **INTACT**, "
        "read-back **1,698/1,698 + 2/2**.\n\n"
    )
    new = raw[:i] + para + raw[i:]
    io.open(ST, "w", encoding="utf-8", newline="").write(new)
    print("status: inserted ORPHAN BATCH 1 paragraph")
else:
    print("status: ORPHAN BATCH 1 paragraph already present")

# ---------- open_items.md (CRLF, plain bullet) ----------
OI = "docs/open_items.md"
raw = io.open(OI, encoding="utf-8", newline="").read()
key = "Orphan batches 2-6"
if key not in raw:
    line = (
        "- Orphan batches 2-6 (330 orphans remaining of the 397; "
        "orphan_batches.json has 6 batches) -- continue one finding per "
        "batch; 5 batches x ~66 fns each.\r\n"
    )
    if not raw.endswith("\r\n"):
        raw += "\r\n"
    io.open(OI, "w", encoding="utf-8", newline="").write(raw + line)
    print("open_items: appended orphan-batches bullet")
else:
    print("open_items: orphan-batches bullet already present")
print("docs95 done")
