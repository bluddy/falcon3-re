"""Record finding 86 (Global Levels 15-18 COMPLETE: 11 named,
L15..18 queue 11 -> 0, named 1387 -> 1398) -- docs/findings_log.md (LF),
time_log.yaml (CRLF), status.md, docs/open_items.md (CRLF). Idempotent."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-19 86 — Global Levels 15–18 COMPLETE: 11 named, L15..18 queue 11 -> 0
(`named` 1,387 -> **1,398**)

Single batch, all 11 full-dumped across the four levels. Highlights:
**`aircraft_motion_step`** (L15, 248B, 4 callers — velocity accumulation
into the 65A7 record, altitude clamp, 1352/1356-scaled vertical rate,
depth/scale derivation, three angle deltas, then obj_fuel_exhaust_step)
paired with **`aircraft_record_load_step`** (L16, 100B — copies the
12-byte record into 65A7:3CDh, resolves the object farptr, invokes
aircraft_motion_step). The map/HUD render stack:
**`map_view_project_pipeline`** (L16, 272B, 5 callers — clipped rect
projection with shadowed view extents + object projection + farobj
sort/step + tile-base search), **`hud_map_overlay_frame`** (L17, 192B —
crosshair + box edges + strip draws + grid dispatches with the map
pipeline nested inside), **`map_overlay_clip_frame`** (L18, 223B — R12
farptr gate, clip-save rect pass wrapping hud_map_overlay_frame, clip
restore). Control input: **`key_range_wheel_handler`** (L15, 451B — full
102h/103h latch state machine for wheel steps -40/-20/+20/+40),
**`control_axis_store_step`** (L16, 201B — quantize + store-select range
key + 2558h table cache), **`range_cb_dispatch_loop`** (L15, 27B — walks
codes 85h..A4h through the range gate). Key/state leaves:
**`key_tick_clear_4fe`** (L15, 16B far — clears 54AF:4FE then
key_state_machine_tick), **`key_tick_set_178`** (L16, 12B far — sets
cs:2E178 request flag then the clear+tick wrapper), **`obj_timer_farptr_step`**
(L15, 93B — 6562E countdown per 2E112 rate, on expiry loads the object
farptr and returns the scaled slot index).

### MILESTONE

**Levels 0–18 are now all complete.** `named` = **1,398**; global
`naming_queue` = **233** across Levels 19..22 (L19=206 giant SCC next,
L20=25, L21=2); L15..18 residue = 0, **0 to_name** in L15..18.

### Gates (all green)

`naming.py check` **1,400** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,398/1,398
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-19 (session 42) | ~1 h | **Finding 86: Global Levels "
       "15-18 COMPLETE -- 11 named, `named` 1,387 -> **1,398**, L15..18 "
       "queue 11 -> 0** (all 11 full-dumped). Highlights: "
       "aircraft_motion_step + aircraft_record_load_step (65A7 record "
       "velocity/altitude/scale/fuel step), map_view_project_pipeline + "
       "hud_map_overlay_frame + map_overlay_clip_frame (map/HUD render "
       "stack with clip save/restore), key_range_wheel_handler "
       "(102h/103h latch state machine for wheel steps), "
       "control_axis_store_step (quantize + store-select range key), "
       "range_cb_dispatch_loop (codes 85h..A4h), key_tick_clear_4fe, "
       "key_tick_set_178, obj_timer_farptr_step. **Levels 0-18 all "
       "complete**; queue 244 -> 233 (L19=206 giant SCC next). "
       "**Gates green:** check 1,400, verify_rebuild faithful, verify_idb "
       "INTACT, read-back 1398/1398+2/2. |")

STATUS_PARA = (
    "**Global Levels 15–18 COMPLETE (finding 86):** 11 functions "
    "named (`named` 1,387 → **1,398**), **L15..18 `naming_queue` 11 → "
    "0** (all 11 full-dumped). Headlines: the aircraft motion pair "
    "**aircraft_motion_step / aircraft_record_load_step** (65A7 record "
    "velocity accumulation, altitude clamp, scaled vertical rate, angle "
    "deltas, fuel step); the map/HUD render stack "
    "**map_view_project_pipeline / hud_map_overlay_frame / "
    "map_overlay_clip_frame** (clipped rect projection, crosshair + box "
    "edges + strips + grids, R12 gate with clip save/restore); "
    "**key_range_wheel_handler** (102h/103h latch state machine for "
    "wheel steps -40/-20/+20/+40), **control_axis_store_step** "
    "(quantize + store-select range key + 2558h table cache), "
    "**range_cb_dispatch_loop** (codes 85h..A4h), "
    "**key_tick_clear_4fe / key_tick_set_178**, and "
    "**obj_timer_farptr_step** (6562E countdown -> scaled object slot). "
    "**Levels 0–18 are now all complete**; global naming_queue = "
    "**233** across Levels 19–22 (L19 = 206 giant SCC next, L20 = 25, "
    "L21 = 2). **Gates all green** (check 1,400, verify_rebuild "
    "faithful, verify_idb INTACT, read-back **1,398/1,398 + 2/2**)."
)

OPEN_NEW = [
    "- **GLOBAL LEVELS 15-18 COMPLETE (finding 86):** 11 named, `named`",
    "  **1387 -> 1398**, **L15..18 queue 11 -> 0** (all 11 full-dumped).",
    "  Highlights: aircraft_motion_step + aircraft_record_load_step",
    "  (65A7 record motion/fuel), map_view_project_pipeline +",
    "  hud_map_overlay_frame + map_overlay_clip_frame (map/HUD render",
    "  stack), key_range_wheel_handler (102h/103h latch state machine),",
    "  control_axis_store_step, range_cb_dispatch_loop,",
    "  key_tick_clear_4fe, key_tick_set_178, obj_timer_farptr_step.",
    "  All 4 gates green (check 1400, verify_rebuild faithful,",
    "  verify_idb INTACT, read-back 1398/1398+2/2).",
    "- **Next: Global Level 19** (206 unnamed in giant SCC, ~6 batches)",
    "  -- global queue 233 across L19..L22 (L19=206, L20=25, L21=2).",
    "- **Follow-ups carried:** class-c undecodable overlay spans (conf:low),",
    "  92 low-conf DATA fns, 24 trap-only thunks, 397 global orphans",
    "  excluded from bottom-up naming.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-19 86" in raw:
    print("findings_log: 86 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 86 before footer")

p = "docs/time_log.yaml"
raw = load(p)
if "session 42" in raw:
    print("time_log: 42 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 41" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 42 after line %d" % (idx + 1))

p = "status.md"
raw = load(p)
if "Global Levels 15–18 COMPLETE (finding 86)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f86 para")

p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVELS 15-18 COMPLETE (finding 86)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f86 status (%d bytes)" % len(block))
