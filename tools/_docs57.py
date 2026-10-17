"""Record finding 57 in docs/findings_log.md (LF), time_log.yaml (CRLF),
status.md and docs/open_items.md (CRLF).

Idempotent + line-ending preserving (same pattern as tools/_docs56.py).
"""
import io

FOOT = "(append new findings below)"

ENTRY = """## 2026-10-17 57 — The sub-block fixups are applied: 11,475 words corrected,
919 more call sites now hit a real function entry — and `static_unresolved`
rose because the targets finally tell the truth

Finding 56 verified `abs = (seg-w0)*16 + off` and deliberately did **not**
apply it ("12,118 fixups -> mass CHANGED -> needs a manifest"). This session
applied it with that manifest, and measured what actually moved.

### Step 1 — size the pass, freeze pass 1

`tools/_size57.py` over 38,001 candidate pairs, dropping the arena misses
(452), the pass-1 window repeat (681 — exactly pass 1's 321 failures: 177
mismatch + 144 out-of-bounds), non-paragraph offsets (5,458) and file-OOB
(0) leaves **31,410 word-ok**, of which **19,935 pass 1 had already applied**
and **11,475 are NEW**. 9,727 of the NEW sit outside any function; the rest
touch 59 functions. Pass 1's applied set was frozen to
`registry/fixups_pass1_applied.json` (25,543 entries / 67 rows) so
`validate_fixup_semantics.py` stays idempotent, and `fixups_to_apply.json`
regenerated twice to an identical hash: **36,697 entries over 68 records**
(25,222 reproduced + 11,475 NEW).

### Step 2 — the writer had to be made honest, and its first run was refused

`tools/apply_overlay_fixups.py` was rewritten: a **per-entry word guard**
(`applied` when the word still equals the recorded link value, `already_done`
when it already equals `+0x1000`, `mismatch` = never written) replaced the
blanket per-segment `RTFIX` skip, which would have blocked every record pass 1
had already touched. **Run 1 applied all 11,475 with 0 mismatches — and then
failed its own guard:** `sub_4DA46` grew `0x4DA46..0x4DA87` → `..0x4DA88`,
because re-decoding a byte IDA held as *data* let `create_insn` invent an
instruction and push the function end by one byte. NOT SAVED, IDB restored
from `.bak_f57_fixups`. **Run 2 re-decodes only heads that already had a
mnemonic** (5,359 pre-existing heads, 1,622 re-created) → **GUARD PASSED:
11,475 applied, 25,222 already present, 0 mismatch, 306 function spans
unchanged → SAVED.**

### Step 3 — exact-match manifest so the gate stays strict

`tools/make_subblock_manifest.py` → `registry/subblock_fixups_expected.json`
pins all 59 changed functions by `(key, ea, size)` **plus the sha256 of the
bytes before AND after**. Its first run refused `sub_3FD82`, which turned out
to be real: a fixup at `0x3FD81` writes a 2-byte word that *straddles* into
the function starting at `0x3FD82`, so attribution has to be by word overlap,
not owner-by-address. `verify_rebuild.py` gained a **PATCH** class — both
hashes must match exactly, so a rebuild that patches the wrong word still
fails as CHANGED. Result: **PATCH 59 / CHANGED 0 / LOST 0 / ADDED 0 →
faithful**.

### Measured effect

| metric | f56 | f57 |
|---|---|---|
| functions | 1,678 | 1,678 (0 lost, 0 added, 0 span change) |
| static edges | 2,493 | **2,730** |
| `static_unresolved` | 702 | **957** |
| overlay zero-indegree orphans | 228 | **224** |

Retargeted/new sites (`tools/measure_f57.py`): 1,369 sites moved, 103 new, 0
gone. **Exact function-entry hits 71 → 990** (resident 38 → 923, overlay 33
→ 67) — 72% of retargeted destinations now land on a registered entry instead
of somewhere inside one. Destinations that are data (outside every function):
**199 → 449**. Those 449 refs collapse to **233 distinct addresses**
(hottest: `0x28CAB` ×36, `0x15CCB` ×27, both resident). Functions with zero
indegree at HEAD: **719 → 138 now reached** (134 resident, 4 overlay);
pre-existing overlay orphans hit 7 times → **4 actually rescued** (the other 3
were self-edges, which the graph drops) → 228 → 224, 0 newly orphaned.

**Inside `sub_2E2F0` (0x2E2F0..0x3ACAC):** refs **985 → 1,053**, every one of
them **interior — 0 at a function start, 0 at `0x2F640`** — spread across
**13 distinct 4 KB blocks, i.e. 13 of that function's sub-block anchors**
(42..135 refs each), with 205 of them retargeted by this pass.

**Why `static_unresolved` rose 702 → 957: arithmetic, not a regression.**
Refs are only emitted from heads inside functions (0 sources ever fail to
resolve), so the count *is* "destination outside every function". The delta is
exact: 702 + 250 (retargeted dsts that moved onto data) + 5 (new sites) =
957; the remaining 503 are untouched pre-existing data destinations. Those
449 dsts used to be **interior** hits — resolved by luck, at the wrong address
— and now point at the true link-time targets, which for 449 sites are tables
and data with no registered function. The words themselves are certain: 0
mismatches in 36,697 guarded writes, and exact-entry hits 5% → 72%.

Gates: `naming.py check` OK (267) · `verify_rebuild` **PATCH 59 / CHANGED 0 /
LOST 0 → faithful** · `verify_idb` **INTACT (1,678, 0 span / 0 name
mismatch)** · read-back **265/265 + 2/2**. Classification unchanged
(ASM 1,370 / C 130 / LEAF 121 / DATA 46 / NEARTHUNK 11). Backup:
`FALCONCD.EXE.i64.bak_f57_fixups`.

Impact: the correction finding 56 staged is now **applied and allowlisted**,
and it bought ~919 provable call-to-entry edges — but it also *increased* the
unresolved backlog, because honest targets include tables. Two structural
items follow: register/classify the 233 data destinations (the residual is now
503 untouched + 449 new data dsts), and split `sub_2E2F0` along its 13 anchor
lines, since 1,053 call sites currently resolve into one 46 KB span.

---

"""

ROW = ("| 2026-10-17 (session 17w) | ~3 h | **Finding 57: applied the "
       "paragraph-anchor sub-block fixups (11,475 words) behind an exact-match "
       "manifest.** Sized to 38,001 candidate pairs -> 31,410 word-ok, 19,935 "
       "already done by pass 1, **11,475 NEW** (pass-1 set frozen to "
       "`registry/fixups_pass1_applied.json` so validate stays idempotent); "
       "`fixups_to_apply.json` = 36,697 entries / 68 records, regenerated "
       "identically. Applier rewritten to a per-entry word guard "
       "(applied/already_done/mismatch) and the blanket `RTFIX` skip removed; "
       "**run 1 applied 11,475 with 0 mismatches but its span guard caught "
       "`sub_4DA46` growing 1 byte** (re-decode invented an instruction over "
       "data) -> not saved, backup restored, re-decode narrowed to "
       "pre-existing mnemonic heads -> **run 2 GUARD PASSED: 11,475 applied, "
       "25,222 already present, 0 mismatch, 306 spans unchanged, SAVED**. "
       "Manifest `registry/subblock_fixups_expected.json` pins the **59** "
       "changed fns by (key,ea,size) + old/new sha256 (attribution by word "
       "OVERLAP - a fixup at 0x3FD81 straddles into sub_3FD82); "
       "`verify_rebuild` gained a **PATCH** class so anything unlisted or "
       "mis-hashed still fails. Measured: static **2,493 -> 2,730**, orphans "
       "**228 -> 224**, exact-entry hits **71 -> 990** (resident 38 -> 923), "
       "zero-indegree fns reached **719 -> 138 left** (134 resident + 4 "
       "overlay), data dsts **199 -> 449** over 233 distinct addrs. "
       "**`static_unresolved` 702 -> 957 is arithmetic, not regression**: "
       "702 + 250 moved-onto-data + 5 new = 957, and those dsts used to be "
       "interior hits. `sub_2E2F0` now holds **1,053 interior refs across 13 "
       "sub-block anchors, 0 at a function start, 0 at 0x2F640**. Gates: "
       "check 267, verify_rebuild PATCH 59/CHANGED 0, verify_idb INTACT "
       "1678, read-back 265/265+2/2. |")

STATUS_PARA = (
    "**Sub-block fixups applied (finding 57):** the correction finding 56 "
    "verified but staged is now executed — `abs = (seg-w0)*16 + off`, "
    "**11,475 NEW words written, 25,222 already correct, 0 mismatch, 306 "
    "function spans unchanged**. The first run was refused by its own span "
    "guard (`sub_4DA46` grew 1 byte while re-decoding data) and rerun with "
    "re-decode limited to pre-existing instruction heads. Because a bulk byte "
    "change would otherwise be indistinguishable from drift, "
    "`registry/subblock_fixups_expected.json` pins the **59 changed functions "
    "by (key, ea, size) and the sha256 of their bytes before *and* after**, "
    "and `verify_rebuild.py` learned a **PATCH** class that matches on both "
    "hashes — an unlisted or mis-hashed change still fails. Effect: static "
    "edges **2,493 -> 2,730**, overlay orphans **228 -> 224**, and **71 -> "
    "990 retargeted call sites now land exactly on a registered function "
    "entry** (resident 38 -> 923); 719 functions had zero indegree at HEAD, "
    "**138 now have an incoming edge** (134 resident, 4 overlay). "
    "`static_unresolved` went **702 -> 957** — arithmetic, not regression: "
    "449 retargeted destinations are now honest *data* (233 distinct "
    "addresses, hottest `0x28CAB` x36) that used to be interior hits, and 5 "
    "brand-new sites do the same (702 + 250 + 5 = 957). Inside `sub_2E2F0` "
    "there are now **1,053 interior refs across 13 sub-block anchors, none at "
    "a function start** — the next structural win is splitting that span."
)

OPEN_NEW = [
    "   (d) **DONE — finding 57 applied the correction** with the exact-match",
    "   manifest it needed: 11,475 NEW words (25,222 already correct), 0",
    "   mismatch, 306 spans unchanged, **59 changed functions pinned by",
    "   (key, ea, size) + before/after sha256** in",
    "   `registry/subblock_fixups_expected.json` (a fixup at `0x3FD81`",
    "   straddles into `sub_3FD82`, so attribution is by word overlap).",
    "   **Now:** (e) `static_unresolved` **702 -> 957** because 449 retargeted",
    "   destinations are honest *data* — 233 distinct addresses (hottest",
    "   `0x28CAB` x36) that used to be *interior* hits — plus 5 new sites;",
    "   register or classify those, or accept them as tables; (f) `sub_2E2F0`",
    "   now holds **1,053 interior refs across 13 of its sub-block anchors,",
    "   0 at a function start, 0 at `0x2F640`** — split it on anchor lines to",
    "   turn those into real edges; (g) 138 functions had zero indegree at",
    "   HEAD and now have an edge (134 resident, 4 overlay), while the 224",
    "   remaining overlay orphans are still never called by anything static.",
]


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


# ---- docs/findings_log.md (LF) ----
p = "docs/findings_log.md"
raw = load(p)
if "## 2026-10-17 57" in raw:
    print("findings_log: 57 already present")
else:
    i = raw.rindex(FOOT)
    assert raw[:i].endswith("---\n\n"), repr(raw[i - 40:i])
    save(p, raw[:i] + ENTRY + raw[i:])
    print("findings_log: inserted 57 before footer (LF preserved)")

# ---- docs/time_log.yaml (CRLF) ----
p = "docs/time_log.yaml"
raw = load(p)
if "session 17w" in raw:
    print("time_log: 17w already present")
else:
    lines = raw.split("\n")
    idx = max(i for i, l in enumerate(lines) if "session 17" in l)
    assert lines[idx].rstrip("\r\n").endswith("|"), lines[idx][:50]
    cr = "\r" if lines[idx].endswith("\r") else ""
    lines.insert(idx + 1, ROW + cr)
    save(p, "\n".join(lines))
    print("time_log: inserted 17w after line %d" % (idx + 1))

# ---- status.md (CRLF) ----
p = "status.md"
raw = load(p)
if "Sub-block fixups applied (finding 57)" in raw:
    print("status: already updated")
else:
    a = "**Still outstanding:**"
    i = raw.index(a)
    save(p, raw[:i] + STATUS_PARA.replace("\n", "\r\n") + "\r\n\r\n" + raw[i:])
    raw = load(p)
    # the finding-56 paragraph said the correction was not applied; point at 57
    old = ("is **verified but deliberately not applied** (it would mass-CHANGE "
           "overlay bytes and needs a manifest).")
    assert old in raw, "f56 sentence not found"
    save(p, raw.replace(old, old + " **(now applied — finding 57.)**"))
    print("status: inserted f57 para + patched the f56 sentence")

# ---- docs/open_items.md (CRLF) ----
p = "docs/open_items.md"
raw = load(p)
if "DONE — finding 57 applied the correction" in raw:
    print("open_items: already updated")
else:
    lines = raw.split("\n")
    start = next(i for i, l in enumerate(lines) if "(d) **staged, not run:**" in l)
    end = next(i for i in range(start, len(lines))
               if "exact-match manifest and its own backup/gate cycle." in lines[i])
    cr = "\r" if lines[start].endswith("\r") else ""
    lines[start:end + 1] = [x + cr for x in OPEN_NEW]
    save(p, "\n".join(lines))
    raw = load(p)
    raw = raw.replace("the residual `static_unresolved = 702` is now a",
                      "the residual `static_unresolved` (702 after f56, **957 after f57**) is now a")
    save(p, raw)
    print("open_items: replaced (d) with %d lines + refreshed the 702 figure"
          % len(OPEN_NEW))
