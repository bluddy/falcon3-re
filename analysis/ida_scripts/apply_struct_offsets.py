"""
Apply structure offsets to function instructions in IDA.
Converts instructions like:
    mov ax, [di+0Ah]
into:
    mov ax, [di+AIContext.timer]

Follows docs/IDA_AUTOMATION_GUIDE.md:
- Pure Python
- Module-level execution
- Early idaapi.auto_wait()
- Explicit idc.qexit(0)
"""

import json
from pathlib import Path
import traceback

import idc
import idaapi
import idautils

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
CONFIG_FILE = SCRIPT_DIR / "struct_offset_targets.json"
REPORT_FILE = SCRIPT_DIR / "struct_offset_report.json"

print("=" * 80)
print("APPLYING STRUCTURE OFFSETS TO INSTRUCTIONS ('T' KEY EQUIVALENT)")
print("=" * 80)

print("Waiting for IDA auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete.")

report = {
    "total_targets": 0,
    "total_operands_converted": 0,
    "details": [],
    "errors": []
}

try:
    if not CONFIG_FILE.exists():
        # Default starter example: ai_context_batch_processor (0x495df) with AIContext on DI
        targets = [
            {
                "function": 0x495DF,
                "struct": "AIContext",
                "register": "di",
                "delta": 0,
                "notes": "DI points to current AIContext in batch loop"
            }
        ]
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(targets, f, indent=2)
    else:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            targets = json.load(f)

    report["total_targets"] = len(targets)

    for target in targets:
        func_spec = target.get("function")
        struct_name = target.get("struct")
        reg = target.get("register", "").lower()
        delta = target.get("delta", 0)

        # Resolve function EA
        if isinstance(func_spec, str):
            if func_spec.startswith("0x") or func_spec.startswith("0X"):
                func_ea = int(func_spec, 16)
            else:
                func_ea = idc.get_name_ea_simple(func_spec)
        else:
            func_ea = int(func_spec)

        func = idaapi.get_func(func_ea)
        if not func:
            msg = f"Function {func_spec} not found in IDA"
            print(f"  [!] {msg}")
            report["errors"].append(msg)
            continue

        sid = idc.get_struc_id(struct_name)
        if sid == idc.BADADDR:
            msg = f"Structure '{struct_name}' not found in IDA"
            print(f"  [!] {msg}")
            report["errors"].append(msg)
            continue

        func_name = idc.get_func_name(func_ea)
        print(f"\nProcessing function {func_name} ({func_ea:#x}) for struct {struct_name} on register [{reg}]...")

        converted_in_func = 0
        samples = []

        ea = func.start_ea
        while ea < func.end_ea:
            insn = idaapi.insn_t()
            length = idaapi.decode_insn(insn, ea)
            if length > 0:
                for op_idx in range(len(insn.ops)):
                    op = insn.ops[op_idx]
                    if op.type == idc.o_void:
                        break

                    # Check for displacement operand: [reg + offset]
                    if op.type == idc.o_displ:
                        op_str = idc.print_operand(ea, op_idx).lower()
                        # Verify register is mentioned in the operand string
                        if reg in op_str:
                            disp = op.addr
                            before_disasm = idc.generate_disasm_line(ea, 0)

                            # Apply structure offset ('T' key)
                            res = idc.op_stroff(ea, op_idx, sid, delta)
                            if res == 1 or res == 0:  # In IDA 9, op_stroff returns 1 on success
                                after_disasm = idc.generate_disasm_line(ea, 0)
                                if before_disasm != after_disasm:
                                    converted_in_func += 1
                                    samples.append({
                                        "ea": hex(ea),
                                        "offset": hex(disp),
                                        "before": before_disasm,
                                        "after": after_disasm
                                    })
                                    print(f"    {ea:#08x}: {before_disasm}  -->  {after_disasm}")

            ea = idc.next_head(ea, func.end_ea)

        report["total_operands_converted"] += converted_in_func
        report["details"].append({
            "function": func_name,
            "ea": hex(func_ea),
            "struct": struct_name,
            "register": reg,
            "converted_count": converted_in_func,
            "samples": samples
        })

    report["status"] = "success"

except Exception as ex:
    err_msg = f"Exception: {ex}\n{traceback.format_exc()}"
    print(err_msg)
    report["errors"].append(err_msg)
    report["status"] = "failed"

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(f"\nReport saved to: {REPORT_FILE}")
print("Exiting IDA...")
idc.qexit(0)
