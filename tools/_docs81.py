"""Record finding 81 (Global Level-10 COMPLETE: 11 named,
L10 queue 11 -> 0, named 1324 -> 1335) -- docs/findings_log.md (LF),
time_log.yaml (CRLF), status.md, docs/open_items.md (CRLF). Idempotent."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-19 81 — Global Level-10 COMPLETE: 11 named, L10 queue 11 -> 0
(`named` 1,324 -> **1,335**)

Single batch, 6 of 11 full-dumped. Highlights: the **view-object
index pair** **`viewobj_project_advance`** (dyn=62,986, hottest L10: farptr
via 500C:[ax*4+34], +22 counter advance, projection; carry=invalid) +
**`viewobj_project_advance_mark`** (same, brackets projection with
+24 bit20h mark), **`key_action_execute_sbi`** (594B, cd=276 -- the SBI
key-action core: held/released state machine, PIT period bracketing,
mode-slot latch, MIDI (mode 4) vs group_register_main paths), the
**stream pair addition `stream_playback_start`** (ensures ADLIB, one-time
write path into 77C9C:E, INT8 hook, kicks stream_stop_reload_gate) with
**`sound_device_init_far`** (13B forwarder from the mode_slot trio),
**`viewmode3_vector_project`** (state==3 gated 6-byte vector list ->
54AF:20 VMT), **`viewvec3_project_track_max`** (11 callers: sampler +
transformer with running max extent at cs:2E3B1+1 self-mod word),
**`coord_point_group_project`** (up-to-10 bitmask points in quad/list
modes), **`viewlist_project_flagged`** (16x16B records, bit8000h gate),
**`view_block4287_entry`** (4 tiny far stubs around block 7B0E:4287), and
**`farobj_tile_align_project`** (sole callee of sub_1243B: record build +
tile align copy + projection).

### MILESTONE

**Levels 0–10 are all complete.** `named` = **1,335**; global
`naming_queue` = **296** across Levels 11..22 (L11=15 next, L19=206
giant SCC); L10 residue = 0 unnamed, **0 to_name**.

### Gates (all green)

`naming.py check` **1,337** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,335/1,335
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-19 (session 37) | ~1 h | **Finding 81: Global Level-10 "
       "COMPLETE -- 11 named, `named` 1,324 -> **1,335**, L10 queue 11 -> "
       "0** (6 full-dumped). Highlights: viewobj_project_advance "
       "(dyn=62986, hottest L10) + _mark pair, key_action_execute_sbi "
       "(594B cd=276 SBI key core), stream_playback_start + "
       "sound_device_init_far, viewmode3_vector_project, "
       "viewvec3_project_track_max (11 callers, self-mod max), "
       "coord_point_group_project, viewlist_project_flagged, "
       "view_block4287_entry, farobj_tile_align_project. **MILESTONE: "
       "Levels 0-10 all complete**; queue 307 -> 296 (L11=15, L19=206). "
       "**Gates green:** check 1,337, verify_rebuild faithful, verify_idb "
       "INTACT, read-back 1335/1335+2/2. |")

STATUS_PARA = (
    "**Global Level-10 COMPLETE (finding 81):** 11 Level-10 functions named "
    "(`named` 1,324 → **1,335**), **L10 `naming_queue` 11 → 0**. Headlines: "
    "the **viewobj_project_advance/_mark** index-projection pair (dyn "
    "62,986 hottest), **`key_action_execute_sbi`** (594B SBI key-action "
    "core: PIT bracketing, mode-slot latch, MIDI vs group paths), the "
    "**stream_playback_start** + **sound_device_init_far** sound/stream "
    "starts, and the projection family (viewmode3_vector_project, "
    "viewvec3_project_track_max, coord_point_group_project, "
    "viewlist_project_flagged, view_block4287_entry, "
    "farobj_tile_align_project). **Levels 0–10 are now all complete**; "
    "global naming_queue = **296** across Levels 11–22 (L11 = 15 next, "
    "L19 = 206 giant SCC). **Gates all green** (check 1,337, "
    "verify_rebuild faithful, verify_idb INTACT, read-back "
    "**1,335/1,335 + 2/2**)."
)

OPEN_NEW = [
    "- **GLOBAL LEVEL 10 COMPLETE (finding 81):** 11 named, `named`",
    "  **1324 -> 1335**, **L10 queue 11 -> 0** (6 full-dumped).",
    "  Highlights: viewobj_project_advance (dyn=62986) + _mark pair,",
    "  key_action_execute_sbi (594B cd=276), stream_playback_start +",
    "  sound_device_init_far, view projection family (viewmode3,",
    "  viewvec3 track_max, coord_point_group, viewlist_flagged,",
    "  block4287, farobj_tile_align). All 4 gates green (check 1337,",
    "  verify_rebuild faithful, verify_idb INTACT, read-back",
    "  1335/1335+2/2).",
    "- **Next: Global Level-11** (15 targets) -- global queue 296 across",
    "  L11..L22 (L11=15, L12=11, ..., L19=206 giant SCC, L20=25, L21=2).",
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
if "## 2026-10-19 81" in raw:
    print("findings_log: 81 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 81 before footer")

p = "docs/time_log.yaml"
raw = load(p)
if "session 37" in raw:
    print("time_log: 37 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 36" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 37 after line %d" % (idx + 1))

p = "status.md"
raw = load(p)
if "Global Level-10 COMPLETE (finding 81)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f81 para")

p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVEL 10 COMPLETE (finding 81)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f81 status (%d bytes)" % len(block))
