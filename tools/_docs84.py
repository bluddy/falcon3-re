"""Record finding 84 (Global Level-13 COMPLETE: 15 named,
L13 queue 15 -> 0, named 1361 -> 1376) -- docs/findings_log.md (LF),
time_log.yaml (CRLF), status.md, docs/open_items.md (CRLF). Idempotent."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-19 84 — Global Level-13 COMPLETE: 15 named, L13 queue 15 -> 0
(`named` 1,361 -> **1,376**)

Single batch, 9 of 15 full-dumped. Highlights: **`tile_base_opcode_interpreter`**
(dyn=**11,155** -- THE hottest function in the binary: walks the 0x31-entry
command stream at cs:11C8C, decoding per-entry opcode bits to direct
tile_base_batch_build or farobj_flag_record_push pair gates -- the core
per-frame terrain base emit loop), **`viewobj_5982_scan_all`** (16B
fan-out running the L12 scan100/scan10/scan40 trio), the **key/input
layer** **`key_event_gate_check`** (54AF:44FEE/44F4E latch pair forward),
**`key_code_pending_drain`** (4893/4894 deferred latches -> codes 4/3),
**`irq_state_init_entry`**, **`mode_slot_masks_entry`** and
**`range_key_event_dispatch`** (2940h ceiling / 64h tight gate with
half-step attract), the **view/HUD cluster** **`view_extent_default_reset`**
(zero view state + default 320x199 rect + quad republish),
**`terrain_stream_pos_update`** (82Ch/41Bh -> ds:674 cursor),
**`hud_metric_rows_draw`** (4 numeric fields -> fixed panel rects),
**`viewobj_batch_project_test`** (15-object double angle+range gate,
fires key 4Dh on match), and the **range-slot pair**
**`obj_range_slot_init`/`obj_range_slot_activate`** (65A7:0C+(idx-301h)*18h
records: init seeds clamped angles, activate fires projection or releases
with the 40h far-object flag).

Note: push-ida key-missed `sub_3470D` (live IDA name was `nullsub_24` for
the leading `retf` at 0x3470D); renamed by address via `_fix_3470D.py`,
read-back clean afterwards.

### MILESTONE

**Levels 0–13 are all complete.** `named` = **1,376**; global
`naming_queue` = **255** across Levels 14..22 (L14=11 next, L19=206
giant SCC); L13 residue = 0, **0 to_name**.

### Gates (all green)

`naming.py check` **1,378** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,376/1,376
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-19 (session 40) | ~1 h | **Finding 84: Global Level-13 "
       "COMPLETE -- 15 named, `named` 1,361 -> **1,376**, L13 queue 15 -> "
       "0** (9 full-dumped). Highlights: tile_base_opcode_interpreter "
       "(dyn=11155, hottest overall -- 11C8C command stream), "
       "viewobj_5982_scan_all (scan trio fan-out), key_event_gate_check, "
       "key_code_pending_drain, irq_state_init_entry, "
       "mode_slot_masks_entry, range_key_event_dispatch, "
       "view_extent_default_reset, terrain_stream_pos_update, "
       "hud_metric_rows_draw, viewobj_batch_project_test, "
       "obj_range_slot_init/activate pair. Fixed push-ida key-miss on "
       "sub_3470D (live name nullsub_24) via direct rename. **Levels "
       "0-13 all complete**; queue 270 -> 255 (L14=11, L19=206). "
       "**Gates green:** check 1,378, verify_rebuild faithful, verify_idb "
       "INTACT, read-back 1376/1376+2/2. |")

STATUS_PARA = (
    "**Global Level-13 COMPLETE (finding 84):** 15 Level-13 functions "
    "named (`named` 1,361 → **1,376**), **L13 `naming_queue` 15 → 0**. "
    "Headlines: **tile_base_opcode_interpreter** (dyn **11,155**, the "
    "hottest function overall -- 11C8C opcode stream driving "
    "tile_base_batch_build / flag-record gates), the 5982 scan-all "
    "fan-out, key_event_gate_check + key_code_pending_drain "
    "(44FEE/44F4E and 4893/4894 latches), range_key_event_dispatch, "
    "view_extent_default_reset, terrain_stream_pos_update, "
    "hud_metric_rows_draw, viewobj_batch_project_test, and the "
    "obj_range_slot_init/activate pair (65A7 store-slot records). "
    "Fixed a push-ida key-miss on sub_3470D (live IDA name "
    "`nullsub_24`), re-verified clean. **Levels 0–13 are now all "
    "complete**; global naming_queue = **255** across Levels 14–22 "
    "(L14 = 11 next, L19 = 206 giant SCC). **Gates all green** (check "
    "1,378, verify_rebuild faithful, verify_idb INTACT, read-back "
    "**1,376/1,376 + 2/2**)."
)

OPEN_NEW = [
    "- **GLOBAL LEVEL 13 COMPLETE (finding 84):** 15 named, `named`",
    "  **1361 -> 1376**, **L13 queue 15 -> 0** (9 full-dumped).",
    "  Highlights: tile_base_opcode_interpreter (dyn=11155, hottest",
    "  overall), viewobj_5982_scan_all, key_event_gate_check,",
    "  key_code_pending_drain, irq_state_init_entry,",
    "  mode_slot_masks_entry, range_key_event_dispatch,",
    "  view_extent_default_reset, terrain_stream_pos_update,",
    "  hud_metric_rows_draw, viewobj_batch_project_test,",
    "  obj_range_slot_init/activate. push-ida key-miss on sub_3470D",
    "  (live name nullsub_24) fixed by address rename. All 4 gates green",
    "  (check 1378, verify_rebuild faithful, verify_idb INTACT,",
    "  read-back 1376/1376+2/2).",
    "- **Next: Global Level-14** (11 targets) -- global queue 255 across",
    "  L14..L22 (L14=11, L15=5, L16=4, L17=1, L18=1, L19=206 giant SCC,",
    "  L20=25, L21=2).",
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
if "## 2026-10-19 84" in raw:
    print("findings_log: 84 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 84 before footer")

p = "docs/time_log.yaml"
raw = load(p)
if "session 40" in raw:
    print("time_log: 40 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 39" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 40 after line %d" % (idx + 1))

p = "status.md"
raw = load(p)
if "Global Level-13 COMPLETE (finding 84)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f84 para")

p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVEL 13 COMPLETE (finding 84)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f84 status (%d bytes)" % len(block))
