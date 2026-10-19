"""Record finding 82 (Global Level-11 COMPLETE: 15 named,
L11 queue 15 -> 0, named 1335 -> 1350) -- docs/findings_log.md (LF),
time_log.yaml (CRLF), status.md, docs/open_items.md (CRLF). Idempotent."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-19 82 — Global Level-11 COMPLETE: 15 named, L11 queue 15 -> 0
(`named` 1,335 -> **1,350**)

Single batch, 6 of 15 full-dumped. Highlights: the **farobj build
pair** **`farobj_batch_build_project`** (346B/10 callers: view-centered
deltas, 10-byte record stream -> 2Ah slots, align+project, then
farobj_sort_and_step) + **`farobj_single_build_project`** (9 callers,
tail-call), **`vga_dac_palette_upload`** (306B one-shot DAC upload from
7A32:8505B latch across 5 palette tables via ports 3C8/3C9), the
**HUD cluster** **`hud_readout_render`** (908B: signed readouts, heading
XXX/degrees, 'A ' altitude, rotation matrix, view cursor sprite), +
**`hud_terrain_strip_render`** (988B terrain clamp + clipped quad
strips) + **`hud_heading_tape_draw`** (FD1/FCC/FD6 heading ribbon), the
**viewobj gates** **`viewobj_project_select`** (dyn=59,038 hottest L11,
11C88 route between the L10 pair) + **`viewobj_project_if_moved`**
(7BC0 bound diff gate) + three **`viewobj_table*_*_project`** scanners
(64/72/32 records at 63FD), **`key_action_100_apply`/`_102_apply`**
(mode_flags_apply -> key_action_execute latches), and
**`view_block4287_angles`** (mode-selected 500h+44D3D*12 config ->
44AF6/44AF8) + **`vec_transform_scale_norm`** (/165 transform).

### MILESTONE

**Levels 0–11 are all complete.** `named` = **1,350**; global
`naming_queue` = **281** across Levels 12..22 (L12=11 next, L19=206
giant SCC); L11 residue = 2 unnamed (0 queue), **0 to_name**.

### Gates (all green)

`naming.py check` **1,352** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,350/1,350
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-19 (session 38) | ~1 h | **Finding 82: Global Level-11 "
       "COMPLETE -- 15 named, `named` 1,335 -> **1,350**, L11 queue 15 -> "
       "0** (6 full-dumped). Highlights: farobj_batch/single_build_project "
       "pair, vga_dac_palette_upload (5 tables -> ports 3C8/3C9), HUD "
       "cluster (hud_readout_render 908B + hud_terrain_strip_render 988B + "
       "hud_heading_tape_draw), viewobj_project_select (dyn=59038) + "
       "if_moved + 3 table scanners, key_action_100/102_apply, "
       "view_block4287_angles, vec_transform_scale_norm. **MILESTONE: "
       "Levels 0-11 all complete**; queue 296 -> 281 (L12=11, L19=206). "
       "**Gates green:** check 1,352, verify_rebuild faithful, verify_idb "
       "INTACT, read-back 1350/1350+2/2. |")

STATUS_PARA = (
    "**Global Level-11 COMPLETE (finding 82):** 15 Level-11 functions "
    "named (`named` 1,335 → **1,350**), **L11 `naming_queue` 15 → 0**. "
    "Headlines: the **farobj_batch/single_build_project** build pair, "
    "**`vga_dac_palette_upload`** (one-shot DAC table streaming), the HUD "
    "cluster (**hud_readout_render** / **hud_terrain_strip_render** / "
    "**hud_heading_tape_draw**), the viewobj gates "
    "(**viewobj_project_select** dyn 59,038 + if_moved + 3 table "
    "scanners), **key_action_100/102_apply**, view_block4287_angles and "
    "vec_transform_scale_norm. **Levels 0–11 are now all complete**; "
    "global naming_queue = **281** across Levels 12–22 (L12 = 11 next, "
    "L19 = 206 giant SCC). **Gates all green** (check 1,352, "
    "verify_rebuild faithful, verify_idb INTACT, read-back "
    "**1,350/1,350 + 2/2**)."
)

OPEN_NEW = [
    "- **GLOBAL LEVEL 11 COMPLETE (finding 82):** 15 named, `named`",
    "  **1335 -> 1350**, **L11 queue 15 -> 0** (6 full-dumped).",
    "  Highlights: farobj_batch/single_build_project, "
    "vga_dac_palette_upload,",
    "  HUD cluster (hud_readout_render, hud_terrain_strip_render,",
    "  hud_heading_tape_draw), viewobj_project_select (dyn=59038) +",
    "  if_moved + table64/72/32 scanners, key_action_100/102_apply,",
    "  view_block4287_angles, vec_transform_scale_norm. All 4 gates",
    "  green (check 1352, verify_rebuild faithful, verify_idb INTACT,",
    "  read-back 1350/1350+2/2).",
    "- **Next: Global Level-12** (11 targets) -- global queue 281 across",
    "  L12..L22 (L12=11, L13=15, ..., L19=206 giant SCC, L20=25, L21=2).",
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
if "## 2026-10-19 82" in raw:
    print("findings_log: 82 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 82 before footer")

p = "docs/time_log.yaml"
raw = load(p)
if "session 38" in raw:
    print("time_log: 38 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 37" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 38 after line %d" % (idx + 1))

p = "status.md"
raw = load(p)
if "Global Level-11 COMPLETE (finding 82)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f82 para")

p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVEL 11 COMPLETE (finding 82)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f82 status (%d bytes)" % len(block))
