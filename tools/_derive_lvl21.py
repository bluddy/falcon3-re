"""Validate and emit L21 names (2 fns) -> level21_batch_names.json."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMING = ROOT / "registry" / "naming.yaml"
OUT = ROOT / "analysis" / "ida_falconcd" / "level21_batch_names.json"

NAMES = {
    "sub_186ADC": ("r53_script_opcode_interpreter", "medium",
        "2312B, in=1 (r53_e88). r53 overlay script interpreter: enter 0B0h; slot2_map_window_load + farobj_index_resolve_step + tile_sample_script_dispatch prologue; 8-slot local-table init (bp-70h/-80h/-90h/-0A0h/-0B0h word arrays + bp-20h/-28h/-38h/-40h byte arrays); walks 42h-stride records at 6894h:dword_69E3A+3Dh, bucketing by [bx+41h] slot index (0FFh -> slot2_map_window_load loc_12C89 + unk_5CA48 random tick on [bx+25h] clamped to 64h); second pass incs [bx+27h] of selected records + word_69E3A+0Fh/word_69B52+0Ch counters; then farobj_store_32075 script fetch, byte&7 opcode dispatch via jpt_186DE1 (8 cases) with nested jpt_186EEA/jpt_187150/jpt_1872C8 sub-dispatchers updating record fields and calling farobj/tile helpers - the r53 main script interpreter."),
    "sub_6E29E": ("r22_farptr_vector_setup", "low",
        "139B, class=DATA, in=3 (r22_e57, sub_2BF73, sub_2BF7D). Mostly a data/far-pointer table (garbage decode at start); real trampoline at 0x6E2FF: sub ax,ax -> cs:word_6E2B0=0, cs:word_6E2AE=4A75h, call loc_4E044 (overlay_teardown_restore_state), stores returned ax/bx/cx into cs:byte_6E0B0+2/4/6 far-pointer vector slot, then cs:word_6E2AE += 7FC0h - installs a far vector from the teardown-restore-state return."),
}

def main():
    keys = list(NAMES)
    assert len(keys) == 2, len(keys)
    names = [NAMES[k][0] for k in keys]
    assert len(set(names)) == 2, "duplicate names"
    for n in names:
        assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", n), n
        assert not n.startswith(("sub_", "loc_", "off_", "byte_", "word_", "dword_", "unk_", "seg_")), n
        assert n.isascii(), n
    existing = set(re.findall(r"^\s+name: (\S+)", NAMING.read_text(encoding="utf-8"), re.M))
    coll = [n for n in names if n in existing]
    if coll:
        print("COLLISION:", coll)
        sys.exit(1)
    out = {}
    for k in keys:
        name, conf, notes = NAMES[k]
        out[k] = [name, notes, notes + " conf: " + conf, conf]
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
    from collections import Counter
    print("wrote", OUT, len(out))
    print("confidence:", dict(Counter(v[3] for v in out.values())))
    for k in keys:
        print(f"  {k:12s} -> {out[k][0]}")

if __name__ == "__main__":
    main()
