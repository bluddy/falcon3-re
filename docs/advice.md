I've patched both tools and regenerated the overlay JSONs, and the coast-edge extractor is written and has been run. I couldn't regenerate the .i64 here: IDA Free 9.1 has no idat.exe and no IDAPython, so that has to run on your IDA Pro machine.

Cluster-B base fix

The cluster-B records (rows 50–69) start at 0x100000 + w2*16, not 0xFFFA0 + w2*16. Every one of those records, row 69 included, has its fixup table first, with data after it. The old base put them 0x60 bytes early, so fixups were patched into the middle of instructions. That is where your stuck "0x26" bytes came from.

- tools/prep_overlay_placement.py: base changed to 0x100000. Row 69 no longer has its own "code-first" case; it is handled like rows 50–68, with length w8*16 clipped at end of file.
- tools/validate_fixup_semantics.py: table_pos() uses the new base for rows 50–69.
- Regenerated JSONs:
  - overlay_placement.json: rows 50–68 moved by exactly +0x60. Row 69's data moved from 0x13ABA0 to 0x13AC60.
  - overlay_entries.json: unchanged.
  - fixups_to_apply.json: 37,324 pairs. Rows 50–68 each gain the 24 real pairs the old base missed, and row 53 gains 195. All 25,222 pass-1 fixups are still in the corrected tables.
- Backups of the old JSONs are in %TEMP%\f3bak\.

Coast edges

tools/extract_isldat_coast_edges.py writes analysis/isldat_coast_edges/<THEATER>.json and .svg (one small panel per record).
- Coastline = edges used by only one ring, minus edges lying on the tile's clip box. Lakes keep every such edge.
- For example, ISR 0x1542 comes out as (-4388,1703)→(-3340,1506)→(851,2947)→(4388,327).
- Output is in each record's local coordinates. Converting to world coordinates is still unsolved: matching line endpoints across neighbouring tiles found no consistent scale or orientation. The best source for it is the live es:441E line table in an in-flight memory dump.

Docs

- New finding 118 in docs/findings_log.md. It says findings 20, 108 and 110 are wrong where they depend on the old base.
- docs/structures.md: corrected the record layout and added an ISLDAT geometry section.
- docs/current_state.md: count updated to 1–118.

What you need to run at home (IDA Pro 9.1)

1. Back up the existing .i64 (runbook rule 6). git status shows it as modified, and I didn't touch it; maybe IDA Free opened it.
2. Run steps 0–7 of docs/workflow/idb_regeneration.md on a fresh .i64. A fresh run is better than reusing the old one, which already has the wrong-offset fixups baked in.
3. Step V will fail, and that's expected. Every function in rows 50–69 changes address, size and bytes, so verify_rebuild.py will report CHANGED/LOST/ADDED. make_subblock_manifest.py won't fix this because it refuses size or address changes. You'll need to decide how to accept it: either commit the new function_bytes.json as the new baseline, or add a manifest for this one-time shift. I didn't change the gate itself.
4. After the rebuild, re-derive the r53 interpreter jump tables and handler addresses (findings 108/110). Run naming.py push-ida; names for those rows will show up as MISSING.

Five old one-off diagnostic scripts (map_sub2e2f0.py, _hyp56.py, _join55.py, _segrel56.py, _size57.py) still use 0xFFFA0. I left them alone as history.
