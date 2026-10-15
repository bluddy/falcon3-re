# Code Coverage
## Code Coverage (fresh)

| Region | Functions | Notes |
|--------|-----------|-------|
| Resident image | 888 | entry, overlay mgr, video, input, sim core, keyboard unit (complete) + 59 gap-sweep |
| Overlay (rebuilt IDB) | 192 | via 184 thunk entries + analysis; cluster-B included |
| IDA-missed registered | 207 | kb-unit gap fns (findings 26/28) + 59 gap-sweep + **135 trace-verified (finding 33)** |
| **Total** | **1,215** | C-class 108 → 43 ported (+1 known-diff), **~65 remaining queue** |

Remaining tail: ~1.2 MB = RTLink record data + undecoded bulk — **compression
format of the tail is UNKNOWN, nothing extracted by us** (finding 31);
`game/` assets came from the game install.