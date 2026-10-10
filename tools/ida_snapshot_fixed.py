"""IDAPython snapshot script for FALCONCD.EXE with fixup application.

Adds RTLink overlay record groups as segments at their runtime addresses,
applies fixups to relocate segment values, then runs auto-analysis.
"""
import json
import os
import struct

import ida_auto
import ida_bytes
import ida_funcs
import ida_ida
import ida_nalt
import ida_segment
import idaapi
import idautils
import idc

OUT = os.environ.get("FALCON_OUT", r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd")
MZF = os.path.join(os.path.dirname(ida_nalt.get_input_file_path()), "FALCONCD.EXE")
FIXUP_JSON = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\fixup_tables_complete.json"


def parse_rtlink(data):
    """Return {id: record} parsed from the overlay directory in the image."""
    nreloc, hdrparas = struct.unpack_from("<HH", data, 6)
    hdr = hdrparas * 16
    pages, lastpage = struct.unpack_from("<HH", data, 4)
    imagesize = (pages - 1) * 512 + lastpage - hdr
    tail = hdr + imagesize
    base = hdr + 0x1AA3 * 16 + 0x0C1F
    recs = []
    for i in range(512):
        o = base + i * 18
        if o + 18 > len(data):
            break
        w = struct.unpack_from("<9H", data, o)
        if not (0x100 <= w[0] <= 0x9000):
            break
        recs.append(dict(id=w[7], seg=w[0], off=w[2], size=w[4], B=w[5], C=w[6]))
    return recs, tail


def map_overlays(data, recs, tail):
    from collections import defaultdict
    base_para = ida_ida.inf_get_min_ea() >> 4
    groups = defaultdict(list)
    for r in recs:
        if r["size"]:
            groups[(r["C"], r["seg"])].append(r)
    made = []
    for (c, seg), rs in sorted(groups.items()):
        start = min(r["off"] for r in rs)
        end = max(r["off"] + r["size"] for r in rs)
        name = "OVL_%04X" % seg
        ea_start = (base_para + seg) * 16 + start
        ea_end = ea_start + (end - start)
        if ida_segment.add_segm(0, ea_start, ea_end, name, "CODE"):
            blob = bytearray(end - start)
            for r in rs:
                fo = tail + r["off"]
                blob[r["off"] - start:r["off"] - start + r["size"]] = data[fo:fo + r["size"]]
            ida_bytes.put_bytes(ea_start, bytes(blob))
            made.append(dict(name=name, seg=seg, c=c, file_off=tail + start,
                             size=end - start, records=[r["id"] for r in rs]))
    return made


def apply_fixups_to_segments(recs, tail, base_para, data):
    """Apply RTLink fixups to overlay segments."""
    with open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\fixup_tables_complete.json", 'r') as f:
        fixups = json.load(f)
    
    total_applied = 0
    for rec_id_str, rec in fixups.items():
        rec_id = int(rec_id_str)
        seg = rec['seg']
        code_size = rec['code_size']
        fixups_by_type = rec['fixups_by_type']
        
        runtime_para = (ida_ida.inf_get_min_ea() >> 4) + seg
        runtime_base = runtime_para * 16
        
        applied = 0
        for typ, offsets in rec['fixups_by_type'].items():
            for offset in offsets:
                if offset >= code_size:
                    continue
                ea = runtime_base + offset
                word = ida_bytes.get_word(runtime_base + offset)
                if word is None:
                    continue
                relocated = (word + runtime_para) & 0xFFFF
                ida_bytes.patch_word(runtime_base + offset, relocated)
                total_applied += 1
    
    print(f"Applied {total_applied} fixups")


def analyze_overlay_segments():
    """Force analysis of all OVL_* segments."""
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        seg_name = idc.get_segm_name(s.start_ea)
        if seg_name.startswith("OVL_"):
            print(f"Analyzing segment {seg_name} [{hex(s.start_ea)}-{hex(s.end_ea)}] size={s.end_ea - s.start_ea}")
            
            # Make sure it's marked as code
            ida_segment.set_segm_class(s, "CODE")
            
            # Try to create functions at likely entry points
            ea = s.start_ea
            while ea < s.end_ea:
                b = ida_bytes.get_bytes(ea, 2)
                if b == b'\x55\x8b':  # push bp; mov bp, sp
                    if not ida_funcs.get_func(ea):
                        ida_funcs.add_func(ea)
                        print(f"  Created function at {hex(ea)}")
                elif b and b[0] == 0xC8:  # ENTER
                    if not ida_funcs.get_func(ea):
                        ida_funcs.add_func(ea)
                        print(f"  Created function at {hex(ea)} (ENTER)")
                elif b and b[0] == 0x55:
                    b2 = ida_bytes.get_bytes(ea+1, 1)
                    if b2 and b2[0] in (0x8b, 0x89):
                        if not ida_funcs.get_func(ea):
                            ida_funcs.add_func(ea)
                            print(f"  Created function at {hex(ea)} (push bp; mov)")
                ea += 1
            
            print(f"  Running autoanalysis on {seg_name}...")
            ida_auto.auto_mark_range(s.start_ea, s.end_ea, ida_auto.AU_CODE)


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(MZF, "rb") as f:
        data = f.read()
    recs, tail = parse_rtlink(data)
    made = map_overlays(data, recs, tail)
    
    # Apply fixups BEFORE autoanalysis
    apply_fixups_to_segments(recs, tail, ida_ida.inf_get_min_ea() >> 4, data)
    
    # Force analysis of overlay segments
    analyze_overlay_segments()
    
    ida_auto.auto_wait()

    segs = []
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        try:
            segclass = idc.get_segm_attr(s.start_ea, ida_segment.SEGATTR_CLASS)
        except Exception:
            segclass = ""
        segs.append(dict(name=idc.get_segm_name(s.start_ea), start=s.start_ea, end=s.end_ea,
                         size=s.end_ea - s.start_ea, perm=int(s.perm),
                         bitness=s.bitness, segclass=segclass))

    entries = []
    try:
        import ida_entry
        for i in range(ida_entry.get_entry_qty()):
            ordinal = ida_entry.get_entry_ordinal(i)
            ea = ida_entry.get_entry(ordinal)
            entries.append(dict(ordinal=ordinal, ea=ea,
                                name=ida_entry.get_entry_name(ea) or ""))
    except Exception as e:
        entries.append(dict(error=str(e)))

    flirt = []
    try:
        n = idaapi.get_idasgn_qty()
        for i in range(n):
            nm, desc = idaapi.get_idasgn_desc(i)
            flirt.append(dict(name=nm, desc=desc))
    except Exception as e:
        flirt.append(dict(error=str(e)))

    funcs = []
    for ea in idautils.Functions():
        f = ida_funcs.get_func(ea)
        name = ida_funcs.get_func_name(ea) or ""
        flags = 0
        try:
            flags = int(idc.get_func_attr(ea, idc.FUNCATTR_FLAGS))
        except Exception:
            pass
        rets = 0
        retfs = 0
        b = ida_bytes.get_bytes(ea, f.size() if f else 16) or b""
        rets = b.count(0xC3)
        retfs = b.count(0xCB)
        funcs.append(dict(ea=ea, end=f.end_ea if f else ea, size=f.size() if f else 0,
                          name=name, flags=flags, is_thunk=bool(flags & ida_funcs.FUNC_THUNK),
                          is_far=bool(flags & ida_funcs.FUNC_FAR), nret=rets, nretf=retfs))

    imports = []
    try:
        nimps = ida_nalt.get_import_module_qty()
        for mi in range(nimps):
            imports.append(ida_nalt.get_import_module_name(mi))
    except Exception:
        pass

    strings = []
    for s in idautils.Strings():
        strings.append(dict(ea=s.ea, length=s.length, str=str(s)[:120]))

    survey = dict(
        input=ida_nalt.get_input_file_path(),
        imagebase=idaapi.get_imagebase(),
        min_ea=ida_ida.inf_get_min_ea(),
        max_ea=ida_ida.inf_get_max_ea(),
        processor=idc.get_processor_name(),
        overlays=made,
        rtlink_records=len(recs),
        segments=segs,
        entries=entries,
        flirt=flirt,
        import_modules=imports,
        function_count=len(funcs),
        functions=funcs,
        string_count=len(strings),
        strings=strings[:400],
    )
    with open(os.path.join(OUT, "survey.json"), "w", encoding="utf-8") as f:
        json.dump(survey, f, indent=1, default=lambda o: hex(o) if isinstance(o, int) and o > 0xFFFFFF else o)

    with open(os.path.join(OUT, "functions.tsv"), "w", encoding="utf-8") as f:
        f.write("ea\tend\tsize\tname\tfar\tthunk\tnret\tnretf\n")
        for fn in funcs:
            f.write("%08x\t%08x\t%d\t%s\t%d\t%d\t%d\t%d\n" % (
                fn["ea"], fn["end"], fn["size"], fn["name"],
                int(fn["is_far"]), int(fn["is_thunk"]), fn["nret"], fn["nretf"]))

    with open(os.path.join(OUT, "overlays.json"), "w", encoding="utf-8") as f:
        json.dump(dict(records=recs, tail=tail, groups=made), f, indent=1)

    print("snapshot done: %d functions, %d segments, %d overlays" % (
        len(funcs), len(segs), len(made)))
    idc.qexit(0)


main()