"""farobj_fields_probe.py — map FarObj struct fields 0x2E..0x73 via ES:[DI+N] access patterns.

Scans all code segments for:
  - 26 <op> <ModRM> <disp8>  where ModRM indicates [DI+disp8] and disp8 in [0x2E..0x73]
  
Common patterns:
  - 26 8B xx NN  → mov reg, es:[di+NN]
  - 26 8A xx NN  → mov reg8, es:[di+NN]
  - 26 89 xx NN  → mov es:[di+NN], reg
  - 26 88 xx NN  → mov es:[di+NN], reg8
  - 26 C6 45 NN  → mov byte ptr es:[di+NN], imm8
  - 26 C7 45 NN  → mov word ptr es:[di+NN], imm16
"""
import idc, ida_funcs, ida_bytes, ida_segment, idautils, idaapi
import json
from pathlib import Path
from collections import defaultdict

_idb = Path(idc.get_idb_path()).parent
LOG = _idb / "farobj_fields.log"
OUT = _idb / "farobj_fields.json"

log = []
field_map = defaultdict(list)  # offset → list of {ea, fn, disasm, access_type}

try:
    log.append("=== FarObj struct field scan: ES:[DI+N] for N in [0x2E..0x73] ===\n")
    
    total_hits = 0
    
    # Scan all code segments
    for seg_ea in idautils.Segments():
        seg = ida_segment.getseg(seg_ea)
        if seg is None or seg.sclass != idc.SEG_CODE:
            continue
        
        seg_name = idc.get_segm_name(seg_ea)
        ea = seg_ea
        end = seg.end_ea - 5
        
        while ea < end:
            b0 = ida_bytes.get_byte(ea)
            
            # Look for ES: override prefix (0x26)
            if b0 != 0x26:
                ea += 1
                continue
            
            b1 = ida_bytes.get_byte(ea + 1)
            b2 = ida_bytes.get_byte(ea + 2)
            b3 = ida_bytes.get_byte(ea + 3)
            
            # Decode ModRM: mod=01 (8-bit disp), any rm
            # ModRM byte: bits 7-6=mod, 5-3=reg, 2-0=rm
            # mod=01 (0x40) = 8-bit displacement
            # Accept ANY base register (BX, BP, SI, DI)
            
            modrm_mod = (b2 >> 6) & 0x3
            modrm_rm = b2 & 0x7
            
            disp = None
            access_type = None
            base_reg = None
            
            # Only proceed if mod=01 (8-bit displacement)
            if modrm_mod == 0x01:
                disp = b3
                
                # Decode base register
                base_map = {0: "BX+SI", 1: "BX+DI", 2: "BP+SI", 3: "BP+DI", 
                           4: "SI", 5: "DI", 6: "BP", 7: "BX"}
                base_reg = base_map.get(modrm_rm, "?")
                
                # Decode operation
                if b1 == 0x8B:
                    access_type = "read_word"
                elif b1 == 0x8A:
                    access_type = "read_byte"
                elif b1 == 0x89:
                    access_type = "write_word"
                elif b1 == 0x88:
                    access_type = "write_byte"
                elif b1 == 0xC6:
                    access_type = "write_imm_byte"
                elif b1 == 0xC7:
                    access_type = "write_imm_word"
                elif b1 in (0x85, 0x3B, 0x03, 0x2B, 0x23, 0x0B, 0x33, 0x84, 0x3A, 0x02, 0x2A, 0x22, 0x0A, 0x32):
                    access_type = "alu_op"
                else:
                    disp = None  # Unsupported opcode
            
            # Check if disp is in target range
            if disp is not None and 0x2E <= disp <= 0x73:
                fn = ida_funcs.get_func(ea)
                fn_name = idc.get_func_name(fn.start_ea) if fn else "<?>"
                dis = idc.generate_disasm_line(ea, 0)
                
                field_map[disp].append({
                    "ea": "0x%X" % ea,
                    "fn": fn_name,
                    "type": access_type,
                    "base": base_reg,
                    "dis": dis[:80]
                })
                total_hits += 1
            
            ea += 1
    
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
        
        log.append("[DI+0x%02X]: %d accesses, types=%s, funcs=%d" % (
            off, len(accesses), dict(types), len(funcs)
        ))
        # Show top 3 functions
        top_funcs = list(funcs)[:3]
        log.append("  → %s" % ", ".join(top_funcs))
        log.append("")
    
    # Write full JSON output
    results = {
        "total_hits": total_hits,
        "field_count": len(field_map),
        "fields": {
            "0x%02X" % k: v for k, v in sorted(field_map.items())
        }
    }
    
    OUT.write_text(json.dumps(results, indent=1), encoding='utf-8')
    LOG.write_text("\n".join(log), encoding='utf-8')
    
    log.append("Success: wrote %s and %s" % (OUT.name, LOG.name))

except Exception as e:
    import traceback
    LOG.write_text("\n".join(log) + "\n\nERROR:\n" + traceback.format_exc(), encoding='utf-8')

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
