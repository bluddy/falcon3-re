"""Record finding 85 (Global Level-14 COMPLETE: 11 named,
L14 queue 11 -> 0, named 1376 -> 1387) -- docs/findings_log.md (LF),
time_log.yaml (CRLF), status.md, docs/open_items.md (CRLF). Idempotent."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-19 85 — Global Level-14 COMPLETE: 11 named, L14 queue 11 -> 0
(`named` 1,376 -> **1,387**)

Single batch, 4 of 11 full-dumped. Highlights: **`terrain_frame_update_driver`**
(dyn=**11,155**, ties tile_base_opcode_interpreter as hottest: the main
frame update driver -- neighbor norm scan, lite/quad/main script exec,
bracketed opcode interpreter, conditional 11C88-scrubbed attr walk), the
**key state machine** **`key_state_machine_tick`** (8 callers: services
2E17A/2E17C pending latches with 102h/103h, parks ds:0 at 101h) +
**`key_state_idle_enter`** (parks at 100h) + **`key_input_state_reset`**
(44FEA/49382-4 zero + irq re-init), **`key_103_range_step_gate`** and
**`range_scale_step_handler`** (493AA record delta -> key 3 + sbi_range_step),
**`obj_fuel_exhaust_step`** (flag-scaled 0Ch<<n cost vs record +8 budget,
fires key 10Ch on 0-crossing), **`terrain_stream_counter_step`** (41Bh
row counter wrap at 7), **`ui_session_tables_init`** (500C seed + 2500-word
copy + 75h/8Fh handle blocks), and the **mode trampolines**
mode_slot_masks_far_enter/far_reset (cx=0 reset variant).

### MILESTONE

**Levels 0–14 are all complete.** `named` = **1,387**; global
`naming_queue` = **244** across Levels 15..22 (L15=5 next, L19=206
giant SCC); L14 residue = 0, **0 to_name**.

### Gates (all green)

`naming.py check` **1,389** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,387/1,387
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-19 (session 41) | ~1 h | **Finding 85: Global Level-14 "
       "COMPLETE -- 11 named, `named` 1,376 -> **1,387**, L14 queue 11 -> "
       "0** (4 full-dumped). Highlights: terrain_frame_update_driver "
       "(dyn=11155, main frame driver: scripts + attr walk + opcode "
       "interpreter), key_state_machine_tick/idle_enter/input_reset "
       "(100h/101h/102h/103h state machine), key_103_range_step_gate, "
       "range_scale_step_handler, obj_fuel_exhaust_step (key 10Ch on "
       "budget 0-crossing), terrain_stream_counter_step, "
       "ui_session_tables_init, mode_slot_masks_far_enter/reset. "
       "**Levels 0-14 all complete**; queue 255 -> 244 (L15=5, L19=206). "
       "**Gates green:** check 1,389, verify_rebuild faithful, verify_idb "
       "INTACT, read-back 1387/1387+2/2. |")

STATUS_PARA = (
    "**Global Level-14 COMPLETE (finding 85):** 11 Level-14 functions "
    "named (`named` 1,376 → **1,387**), **L14 `naming_queue` 11 → 0**. "
    "Headlines: **terrain_frame_update_driver** (dyn **11,155**, the main "
    "frame update driver: neighbor scan + script exec + attr walk + "
    "opcode interpreter), the key state-machine trio "
    "**key_state_machine_tick / key_state_idle_enter / "
    "key_input_state_reset** (100h/101h/102h/103h latch parking), "
    "key_103_range_step_gate + range_scale_step_handler (sbi_range_step "
    "delta path), obj_fuel_exhaust_step (key 10Ch on budget "
    "0-crossing), terrain_stream_counter_step, ui_session_tables_init, "
    "and the mode_slot_masks far trampolines. **Levels 0–14 are now all "
    "complete**; global naming_queue = **244** across Levels 15–22 "
    "(L15 = 5 next, L19 = 206 giant SCC). **Gates all green** (check "
    "1,389, verify_rebuild faithful, verify_idb INTACT, read-back "
    "**1,387/1,387 + 2/2**)."
)

OPEN_NEW = [
    "- **GLOBAL LEVEL 14 COMPLETE (finding 85):** 11 named, `named`",
    "  **1376 -> 1387**, **L14 queue 11 -> 0** (4 full-dumped).",
    "  Highlights: terrain_frame_update_driver (dyn=11155, main frame",
    "  driver), key_state_machine_tick / key_state_idle_enter /",
    "  key_input_state_reset (100h/101h/102h/103h state machine),",
    "  key_103_range_step_gate, range_scale_step_handler,",
    "  obj_fuel_exhaust_step, terrain_stream_counter_step,",
    "  ui_session_tables_init, mode_slot_masks_far_enter/reset.",
    "  All 4 gates green (check 1389, verify_rebuild faithful,",
    "  verify_idb INTACT, read-back 1387/1387+2/2).",
    "- **Next: Global Levels 15-18** (5+4+1+1 = 11 targets) -- global queue",
    "  244 across L15..L22 (L15=5, L16=4, L17=1, L18=1, L19=206 giant SCC,",
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
if "## 2026-10-19 85" in raw:
    print("findings_log: 85 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 85 before footer")

p = "docs/time_log.yaml"
raw = load(p)
if "session 41" in raw:
    print("time_log: 41 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 40" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 41 after line %d" % (idx + 1))

p = "status.md"
raw = load(p)
if "Global Level-14 COMPLETE (finding 85)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f85 para")

p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVEL 14 COMPLETE (finding 85)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f85 status (%d bytes)" % len(block))
