"""IDAPython snapshot script for FALCONCD.EXE (run headless via idat.exe).

Adds RTLink overlay record groups as segments at their runtime addresses so
auto-analysis covers game code, then dumps a survey (segments, functions,
FLIRT, entry points) to analysis/ida_falconcd/.
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


def parse_rtlink(data):
    """Return {id: record} parsed from the overlay directory in the image."""
    nreloc, hdrparas = struct.unpack_from("<HH", data, 6)
    hdr = hdrparas * 16
    # last page: bytes in last page
    pages, lastpage = struct.unpack_from("<HH", data, 4)
    imagesize = (pages - 1) * 512 + lastpage - hdr
    tail = hdr + imagesize
    # overlay manager table: segment 0x1aa3 offset 0x0c1f (from entry thunk)
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


def _force_add_segm(start, end, name, sclass, para):
    """Create a segment with explicit base paragraph (16-bit mode).

    Falcon3 overlays and DS aliases overlap at runtime. In IDA's 16-bit
    model, segments with different base paragraphs (para) can occupy the
    same linear range. Use the runtime segment value as para.
    """
    if ida_segment.add_segm(para, start, end, name, sclass):
        s = ida_segment.getseg(start)
        if s and s.start_ea == start and s.end_ea == end:
            return True
    return False


def map_overlays(data, recs, tail):
    from collections import defaultdict
    # the MZ loader placed the image at inf_get_min_ea(); runtime seg values
    # in the overlay directory are relative to that load base
    base_para = ida_ida.inf_get_min_ea() >> 4
    image_end = ida_ida.inf_get_max_ea()
    # drop the empty placeholder segments the MZ loader made for relocated
    # paragraphs past the image; we replace them with real overlay content
    for s in list(_iter_segs()):
        if s.start_ea >= image_end and not idc.get_segm_name(s.start_ea).startswith("OVL_"):
            ida_segment.del_segm(s.start_ea, 0)
    groups = defaultdict(list)
    for r in recs:
        if r["size"]:
            groups[(r["C"], r["seg"])].append(r)
    made = []
    for (c, seg), rs in sorted(groups.items()):
        name = "OVL_%04X" % seg
        para = base_para + seg
        ea_base = para * 16
        # each record has its own off/size within the segment
        # create one segment covering the full span, place each record at its offset
        start = min(r["off"] for r in rs)
        end = max(r["off"] + r["size"] for r in rs)
        ea_start = ea_base + start
        ea_end = ea_base + end
        if _force_add_segm(ea_start, ea_end, name, "CODE", para):
            # zero-fill the segment, then write each record at its offset
            blob = bytearray(end - start)
            for r in rs:
                fo = tail + r["off"]
                blob[r["off"] - start:r["off"] - start + r["size"]] = data[fo:fo + r["size"]]
            ida_bytes.put_bytes(ea_start, bytes(blob))
            made.append(dict(name=name, seg=seg, c=c, file_off=tail + start,
                             size=end - start, records=[r["id"] for r in rs]))
        else:
            made.append(dict(name=name, seg=seg, c=c, error="add_segm failed"))
    return made


def _iter_segs():
    for i in range(ida_segment.get_segm_qty()):
        yield ida_segment.getnseg(i)


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(MZF, "rb") as f:
        data = f.read()
    recs, tail = parse_rtlink(data)
    made = map_overlays(data, recs, tail)
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
        # count ret / retf in the function body for near/far classification
        rets = retfs = 0
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

    # human-readable function list for the registry
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
