"""Record finding 83 (Global Level-12 COMPLETE: 11 named,
L12 queue 11 -> 0, named 1350 -> 1361) -- docs/findings_log.md (LF),
time_log.yaml (CRLF), status.md, docs/open_items.md (CRLF). Idempotent."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-19 83 — Global Level-12 COMPLETE: 11 named, L12 queue 11 -> 0
(`named` 1,350 -> **1,361**)

Single batch, 3 of 11 full-dumped. Highlights: **`key_event_gated_process`**
(dyn=266 hottest L12: keys 100/101/102 gated by the 10E22/10E23 latches
from L11, forwarded to key_event_process) + **`key_code_resolve_entry`**
(far wrapper), the **tile/build layer** **`farobj_tile_stream_build`**
(11 callers: compressed tile stream or 59CB/598B pick tables -> shared
11BCC/11BCA vars -> farobj_batch_build_project) and
**`tile_base_batch_build`** (15B set-base-and-build),
**`fixed_matrix_proj_factor`** (8 callers: dual matrix transform +
dot-accum / divide -> record +88 scale/depth), the **5982 scanner
trio** viewobj_5982_scan100/scan10/scan40 (bit0/bit1/bit4 gated table
walks), **`terrain_vm_sweep_sample`** (309B VM + 90-degree rotation
sweep up to 280x140 terrain correlation), **`entity_move_project_step`**
(pos_move_angle_step + type-2 select), and **`viewobj_self_copy_project`**
(object 0 refresh).

### MILESTONE

**Levels 0–12 are all complete.** `named` = **1,361**; global
`naming_queue` = **270** across Levels 13..22 (L13=15 next, L19=206
giant SCC); L12 residue = 2 unnamed (0 queue), **0 to_name**.

### Gates (all green)

`naming.py check` **1,363** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,361/1,361
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-19 (session 39) | ~1 h | **Finding 83: Global Level-12 "
       "COMPLETE -- 11 named, `named` 1,350 -> **1,361**, L12 queue 11 -> "
       "0** (3 full-dumped). Highlights: key_event_gated_process "
       "(dyn=266, 10E22/10E23 latch gates), key_code_resolve_entry, "
       "farobj_tile_stream_build (11 callers stream/table driver) + "
       "tile_base_batch_build, fixed_matrix_proj_factor (8 callers +88 "
       "scalar), viewobj_5982_scan100/10/40 trio, "
       "terrain_vm_sweep_sample (90-deg rotation sweep), "
       "entity_move_project_step, viewobj_self_copy_project. **MILESTONE: "
       "Levels 0-12 all complete**; queue 281 -> 270 (L13=15, L19=206). "
       "**Gates green:** check 1,363, verify_rebuild faithful, verify_idb "
       "INTACT, read-back 1361/1361+2/2. |")

STATUS_PARA = (
    "**Global Level-12 COMPLETE (finding 83):** 11 Level-12 functions "
    "named (`named` 1,350 → **1,361**), **L12 `naming_queue` 11 → 0**. "
    "Headlines: **key_event_gated_process** (dyn 266, the 10E22/10E23 "
    "latch-gated key path), the tile/build driver "
    "**farobj_tile_stream_build** (11 callers) + tile_base_batch_build, "
    "**fixed_matrix_proj_factor** (dual-matrix dot-accum +88 scalar), the "
    "viewobj_5982_scan100/10/40 trio, terrain_vm_sweep_sample "
    "(90°-rotation terrain sweep), entity_move_project_step and "
    "viewobj_self_copy_project. **Levels 0–12 are now all complete**; "
    "global naming_queue = **270** across Levels 13–22 (L13 = 15 next, "
    "L19 = 206 giant SCC). **Gates all green** (check 1,363, "
    "verify_rebuild faithful, verify_idb INTACT, read-back "
    "**1,361/1,361 + 2/2**)."
)

OPEN_NEW = [
    "- **GLOBAL LEVEL 12 COMPLETE (finding 83):** 11 named, `named`",
    "  **1350 -> 1361**, **L12 queue 11 -> 0** (3 full-dumped).",
    "  Highlights: key_event_gated_process (dyn=266), key_code_resolve_entry,",
    "  farobj_tile_stream_build + tile_base_batch_build,",
    "  fixed_matrix_proj_factor, viewobj_5982_scan100/10/40,",
    "  terrain_vm_sweep_sample, entity_move_project_step,",
    "  viewobj_self_copy_project. All 4 gates green (check 1363,",
    "  verify_rebuild faithful, verify_idb INTACT, read-back",
    "  1361/1361+2/2).",
    "- **Next: Global Level-13** (15 targets) -- global queue 270 across",
    "  L13..L22 (L13=15, L14=11, ..., L19=206 giant SCC, L20=25, L21=2).",
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
if "## 2026-10-19 83" in raw:
    print("findings_log: 83 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 83 before footer")

p = "docs/time_log.yaml"
raw = load(p)
if "session 39" in raw:
    print("time_log: 39 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 38" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 39 after line %d" % (idx + 1))

p = "status.md"
raw = load(p)
if "Global Level-12 COMPLETE (finding 83)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f83 para")

p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVEL 12 COMPLETE (finding 83)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f83 status (%d bytes)" % len(block))
