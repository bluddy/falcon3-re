"""Record the post-finding-59 plan for the R05 upper half in
docs/open_items.md (CRLF, idempotent, no line-ending damage)."""

import io

BULLET = """- **Upper half `0x3ACAC..0x669F0` plan (after finding 59):** 179,524 B with
  only **38 functions / 4,304 B (2.4%)** registered, so this is *registration*,
  not a split: 251 unresolved destinations (445 `CALL` + 1 `JMP`; 211 frameless
  code, 40 anomalies, 126 terminator-preceded, 0 already functions, 0 thunk
  targets), 17 of the 24 anchors -> **18 blocks**, evidence heavily skewed
  (`0x3B830..0x43AE0` 33,456 B with 89 dsts/163 refs and `0x43AE0..0x48DB0`
  21,200 B with 50/93 carry the bulk; `0x500C0..0x54AF0` 18,992 B has **zero**
  call evidence; `0x54AF0..0x669F0` 73,472 B holds `*** PAUSED ***` /
  `SPEED = KNOTS` and only 1 strong entry). 8 RTLink `entry_ea`s land here, and
  unlike `0x2F640` these anchors are **code-led**, so holes are few (string
  runs in the UI block + `0x4FD80`). Ordered plan: **P0** per-anchor-block
  inventory (bytes/strings/entries/coverage -> `upper_map.json`); **P1** widen
  the dynamic CS->record map past the 16 covered segments (finding 51's gap)
  so `indirect_far` events into R05 resolve -- the only plausible evidence for
  the zero-dst blocks; **P2** chain-sweep entries (terminator before + a
  forward chain from a verified entry must reach it, and never contradict the
  existing decode; confidence A chain-verified / B ref-dst + terminator /
  C ref-dst only) instead of seed-carving, because ref density here is ~8x
  lower than the blob's; **P3** register block by block, highest-evidence
  first, under a manifest with **parentless entries** -> a new `verify_rebuild`
  `REGISTER` class (exact tiling of the stated range by `new_fns` + sha256
  holes) so a wave of ADDED never becomes a free pass the way loose
  registration did in finding 54; **P4** measure (`static_unresolved`
  957 -> ~511, +251 functions that are by construction called) and record as
  finding 60. Explicitly not doing: reusing the finding-59 mutator as-is (no
  parent function exists to delete here), or registering the 40 class-(c)
  anomalies without a chain."""


def load(p):
    return io.open(p, encoding="utf-8", newline="").read()


def save(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


p = "docs/open_items.md"
raw = load(p)
if "Upper half `0x3ACAC..0x669F0` plan" in raw:
    print("open_items: upper-half plan already recorded")
else:
    block = "\r\n\r\n" + "\r\n".join(BULLET.split("\n"))
    save(p, raw + block)
    print("open_items: appended the upper-half plan (%d bytes)"
          % len(block))
