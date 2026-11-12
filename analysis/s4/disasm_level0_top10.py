#!/usr/bin/env python3
"""Disassemble top 10 Level-0 functions from function_bytes.json."""
import json
from pathlib import Path
from capstone import *

ROOT = Path(__file__).resolve().parent.parent.parent
IDA = ROOT / "analysis" / "ida_falconcd"

# Load data
fb = json.loads((IDA / "function_bytes.json").read_text())
cg = json.loads((ROOT / "analysis" / "traces" / "callgraph_partial.json").read_text())

TARGETS = [
    "sub_263F6",   # 122B
    "sub_12890",   # 5B tiny
    "sub_2295C",   # 2B tiny
    "sub_22436",   # 5B tiny
    "sub_2243B",   # 5B tiny
    "sub_2284B",   # 5B tiny
    "sub_230D8",   # 92B
    "sub_22846",   # 5B tiny
    "sub_23134",   # 88B
    "sub_22850",   # 5B tiny
]

def disasm_16bit(bytecode_hex, ea):
    """Disassemble 16-bit x86 bytecode."""
    md = Cs(CS_ARCH_X86, CS_MODE_16)
    bytecode = bytes.fromhex(bytecode_hex)
    result = []
    for insn in md.disasm(bytecode, ea):
        result.append("  {:05X}  {}  {}".format(insn.address, insn.mnemonic, insn.op_str))
    return result

def main():
    print("=== Disassembling top 10 Level-0 functions ===\n")
    result = {}
    
    for key in TARGETS:
        fb_entry = fb.get(key, {})
        if not fb_entry or not fb_entry.get("bytes"):
            print(f"{key}: NO BYTECODE")
            result[key] = {"error": "No bytecode in function_bytes.json"}
            continue
        
        ea = fb_entry["ea"]
        bytecode = fb_entry["bytes"]
        size = len(bytecode) // 2
        
        # Disassemble
        disasm = disasm_16bit(bytecode, ea)
        
        # Get caller info
        callers = [edge[0] for edge in cg["edges"] if edge[1] == key]
        dyn = cg["dyn_target_calls"].get(key, 0)
        
        result[key] = {
            "ea": hex(ea),
            "size": size,
            "bytecode": bytecode,
            "disasm": disasm,
            "callers": callers,
            "dyn_calls": dyn,
        }
        
        # Print
        print(f"{key}  (0x{ea:05X}, {size}B, dyn={dyn}, {len(callers)} callers)")
        for line in disasm:
            print(line)
        print(f"  Callers: {', '.join(callers[:5])}{' ...' if len(callers) > 5 else ''}")
        print()
    
    out_path = ROOT / "analysis" / "s4" / "level0_top10_disasm.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
