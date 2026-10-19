"""Record finding 79 (Global Level-8 COMPLETE: 13 named,
L8 queue 13 -> 0, named 1304 -> 1317) in docs/findings_log.md (LF),
time_log.yaml (CRLF), status.md and docs/open_items.md (CRLF).
Idempotent + line-ending preserving."""

import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-19 79 — Global Level-8 COMPLETE: 13 named, L8 queue 13 -> 0
(`named` 1,304 -> **1,317**)

Finding 78 closed Level 7. Level 8 was a single clean batch (13 fns,
**0 truncated**). Highlights: **`kb_record_key_event`** (692B class-C
per-key brain behind `key_event_process`: kb record fetch/commit +
`state_block_77720` clamp/select/commit chain + 0x4A/0x13 key special
cases), **`stream_command_interpret`** (475B class-C stream opcode
interpreter: '/' terminator, 'Q' 3-byte quantize accum vs 77B66, 0x7F ->
`channel_mode_cmd_dispatch`, default record-skip), the **five-member
`param454_apply_*` family** (ds:454h param-block writers dispatched by
sub_32C62: `_thresholds` writes 0x5DC0/0x9088/0xC738 constants,
`_tableinit` gates on param_table_init + 478h bit0/bit1, and
`_single`/`_double`/`_triple` count their repeated ch=1 field pairs with
field index si=2/4/6), **`farobj_record_lookup_step`** (72B slot-table
indirection front end into `farobj_record_step`, cd=338,048),
**`slot3_window_scroll_up`** (fourth slot3 direction: vertical edge at
Y-2, tail into `slot3_window_reload_col1`), **`worldmap_state_apply`**
(71C1 state table -> map window + 3x3 tile refresh), `adlib_device_init`
(OPL probe + `adlib_synth_init`), `channel_voice_register_setup`
(volume/pitch field compute + `channel_list_register_batch`), and
`view_delta_ratio_compute` (delta normalize -> angle matrix -> signed
ratio pair ds:5C6/5C8).

### MILESTONE

**Levels 0–8 are all complete.** `named` = **1,317**; global
`naming_queue` = **314** across Levels 9..22 (L9=7 next, then L19=206
giant SCC); L8 residue = 2 unnamed (0 queue), **0 to_name**.

### Gates (all green)

`naming.py check` **1,319** . `verify_rebuild` **faithful (2,237 ==
2,237)** . `verify_idb` **INTACT** . `name_readback` **1,317/1,317
function + 2/2 global**.

---

"""

ROW = ("| 2026-10-19 (session 35) | ~1 h | **Finding 79: Global Level-8 "
       "COMPLETE -- 13 named, `named` 1,304 -> **1,317**, L8 queue 13 -> "
       "0** (0 truncated). Highlights: kb_record_key_event (692B per-key "
       "record/state brain), stream_command_interpret (475B stream opcode "
       "interpreter), the 5-member param454_apply_* family (thresholds/"
       "tableinit/single/double/triple), farobj_record_lookup_step, "
       "slot3_window_scroll_up (4th direction), worldmap_state_apply, "
       "adlib_device_init, channel_voice_register_setup, "
       "view_delta_ratio_compute. **MILESTONE: Levels 0-8 all complete**; "
       "queue 327 -> 314 (L9=7, L19=206). **Gates green:** check 1,319, "
       "verify_rebuild faithful, verify_idb INTACT, read-back "
       "1317/1317+2/2. |")

STATUS_PARA = (
    "**Global Level-8 COMPLETE (finding 79):** 13 Level-8 functions named "
    "(`named` 1,304 → **1,317**), **L8 `naming_queue` 13 → 0**. Headlines: "
    "**`kb_record_key_event`** (692-byte class-C keyboard record handler "
    "behind `key_event_process`), **`stream_command_interpret`** "
    "(475-byte stream opcode interpreter feeding `channel_mode_cmd_"
    "dispatch`), the **five-variant `param454_apply_*` family** (ds:454h "
    "param-block writers dispatched by sub_32C62), **`farobj_record_"
    "lookup_step`** (slot-table entry into `farobj_record_step`), "
    "**`slot3_window_scroll_up`** (completes the four slot3 window "
    "directions), `worldmap_state_apply`, `adlib_device_init`, "
    "`channel_voice_register_setup`, `view_delta_ratio_compute`. "
    "**Levels 0–8 are now all complete**; global naming_queue = **314** "
    "across Levels 9–22 (L9 = 7 next, L19 = 206 giant SCC). **Gates all "
    "green** (check 1,319, verify_rebuild faithful, verify_idb INTACT, "
    "read-back **1,317/1,317 + 2/2**)."
)

OPEN_NEW = [
    "- **GLOBAL LEVEL 8 COMPLETE (finding 79):** 13 named, `named`",
    "  **1304 -> 1317**, **L8 queue 13 -> 0** (0 truncated). Highlights:",
    "  kb_record_key_event (692B), stream_command_interpret (475B),",
    "  param454_apply_* family (thresholds/tableinit/single/double/triple),",
    "  farobj_record_lookup_step, slot3_window_scroll_up (4th direction),",
    "  worldmap_state_apply, adlib_device_init, channel_voice_register_setup,",
    "  view_delta_ratio_compute. All 4 gates green (check 1319,",
    "  verify_rebuild faithful, verify_idb INTACT, read-back",
    "  1317/1317+2/2).",
    "- **Next: Global Level-9** (7 targets) -- global queue 314 across",
    "  L9..L22 (L9=7, L10=11, L11=15, ..., L19=206 giant SCC, L20=25, L21=2).",
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
if "## 2026-10-19 79" in raw:
    print("findings_log: 79 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 79 before footer (LF preserved)")

p = "docs/time_log.yaml"
raw = load(p)
if "session 35" in raw:
    print("time_log: 35 already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 34" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 35 after line %d" % (idx + 1))

p = "status.md"
raw = load(p)
if "Global Level-8 COMPLETE (finding 79)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    print("status: inserted f79 para")

p = "docs/open_items.md"
raw = load(p)
if "GLOBAL LEVEL 8 COMPLETE (finding 79)" in raw:
    print("open_items: already updated")
else:
    block = "\r\n\r\n" + "\r\n".join(OPEN_NEW)
    save(p, raw + block)
    print("open_items: appended the f79 status (%d bytes)" % len(block))
