"""farobj_fields_si_probe.py — map FarObj struct fields 0x2E..0x73 via DS:[SI+N] access.

FarObj pointers use SI register with DS segment (no ES: override).
Scan for ModRM with mod=01 (8-bit disp), rm=100 (SI).
"""
import idc, ida_funcs, ida_bytes, ida_segment, idautils, idaapi
import json
from pathlib import Path
from collections import defaultdict

_idb = Path(idc.get_idb_path()).parent
LOG = _idb / "farobj_si_fields.log"
OUT = _idb / "farobj_si_fields.json"

log = []
field_map = defaultdict(list)

try:
    log.append("=== FarObj struct field scan: DS:[SI+N] for ALL N ===\n")
    
    seg_count = 0
    total_hits = 0
    
    for seg_ea in idautils.Segments():
        seg = ida_segment.getseg(seg_ea)
        if seg is None:
            continue
        # Skip non-code segments (sclass=1 is CODE, sclass=2 is DATA)
        if seg.sclass != 1:
            continue
        
        seg_count += 1
        seg_name = idc.get_segm_name(seg_ea)
        ea = seg_ea
        end = seg.end_ea - 4
        
        scanned = 0
        while ea < end:
            b0 = ida_bytes.get_byte(ea)
            b1 = ida_bytes.get_byte(ea + 1)
            b2 = ida_bytes.get_byte(ea + 2)
            
            # Look for instructions with ModRM: mod=01, rm=100 (SI)
            # ModRM & 0xC7 == 0x44  (mod=01, rm=100)
            
            disp = None
            access_type = None
            
            # mov reg, [si+disp8] → 8B 44 NN (no segment prefix)
            if b0 == 0x8B and (b1 & 0xC7) == 0x44:
                disp = b2
                access_type = "read_word"
            # mov reg8, [si+disp8] → 8A 44 NN
            elif b0 == 0x8A and (b1 & 0xC7) == 0x44:
                disp = b2
                access_type = "read_byte"
            # mov [si+disp8], reg → 89 44 NN
            elif b0 == 0x89 and (b1 & 0xC7) == 0x44:
                disp = b2
                access_type = "write_word"
            # mov [si+disp8], reg8 → 88 44 NN
            elif b0 == 0x88 and (b1 & 0xC7) == 0x44:
                disp = b2
                access_type = "write_byte"
            # mov byte ptr [si+disp8], imm8 → C6 44 NN
            elif b0 == 0xC6 and (b1 & 0xC7) == 0x44:
                disp = b2
                access_type = "write_imm_byte"
            # mov word ptr [si+disp8], imm16 → C7 44 NN
            elif b0 == 0xC7 and (b1 & 0xC7) == 0x44:
                disp = b2
                access_type = "write_imm_word"
            # test/cmp/add/sub/and/or/xor → <op> 44 NN
            elif b0 in (0x85, 0x3B, 0x03, 0x2B, 0x23, 0x0B, 0x33, 0x84, 0x3A, 0x02, 0x2A, 0x22, 0x0A, 0x32, 0xF6, 0xF7) and (b1 & 0xC7) == 0x44:
                disp = b2
                access_type = "alu_op"
            # inc/dec word [si+disp8] → FF 44 NN or FE 44 NN
            elif b0 in (0xFF, 0xFE) and (b1 & 0xC7) == 0x44:
                disp = b2
                access_type = "inc_dec"
            
            if disp is not None:  # Accept ALL offsets
                if disp not in field_map:
                    field_map[disp] = []
                fn = ida_funcs.get_func(ea)
                fn_name = idc.get_func_name(fn.start_ea) if fn else "<?>"
                dis = idc.generate_disasm_line(ea, 0)
                
                field_map[disp].append({
                    "ea": "0x%X" % ea,
                    "fn": fn_name,
                    "type": access_type,
                    "dis": dis[:80]
                })
                total_hits += 1
            
            scanned += 1
            ea += 1
        
        if scanned > 0:
            log.append("Scanned %s: %d bytes" % (seg_name, scanned))
    
    log.append("\nTotal segments scanned: %d" % seg_count)
    log.append("Total accesses found: %d\n" % total_hits)
    log.append("Fields accessed: %d\n" % len(field_map))
    
    # Summarize by offset
    log.append("=== Field access summary ===\n")
    for off in sorted(field_map.keys()):
        accesses = field_map[off]
        types = defaultdict(int)
        funcs = set()
        for a in accesses:
            types[a["type"]] += 1
            funcs.add(a["fn"])
        
        log.append("[SI+0x%02X]: %d accesses, types=%s, funcs=%d" % (
            off, len(accesses), dict(types), len(funcs)
        ))
        # Show sample functions (first 5)
        sample_funcs = list(funcs)[:5]
        log.append("  funcs: %s%s" % (
            ", ".join(sample_funcs),
            " ..." if len(funcs) > 5 else ""
        ))
        
        # Show first 3 accesses
        for a in accesses[:3]:
            log.append("    0x%s in %s: %s" % (a["ea"], a["fn"], a["dis"][:60]))
        if len(accesses) > 3:
            log.append("    ... (%d more)" % (len(accesses) - 3))
        log.append("")
    
    # Write full JSON
    results = {
        "total_hits": total_hits,
        "field_count": len(field_map),
        "fields": {
            "0x%02X" % k: v for k, v in sorted(field_map.items())
        }
    }
    
    OUT.write_text(json.dumps(results, indent=1), encoding='utf-8')
    LOG.write_text("\n".join(log), encoding='utf-8')
    
    log.append("\nSuccess!")

except Exception as e:
    import traceback
    LOG.write_text("\n".join(log) + "\n\nERROR:\n" + traceback.format_exc(), encoding='utf-8')

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
