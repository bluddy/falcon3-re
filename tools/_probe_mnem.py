import json
import ida_idp, ida_ua, ida_lines, idc, idautils
out = []
out.append("ida_idp: " + str([x for x in dir(ida_idp) if "insn" in x.lower() or "mnem" in x.lower() or "instruc" in x.lower()]))
out.append("ida_ua: " + str([x for x in dir(ida_ua) if "render" in x.lower() or "mnem" in x.lower() or "disasm" in x.lower() or "name" in x.lower()]))
out.append("ida_lines: " + str([x for x in dir(ida_lines) if "disasm" in x.lower() or "generate" in x.lower()]))
out.append("idc doc: " + str(idc.print_insn_mnem.__doc__))
# does generate_disasm_line work on an address with NO item?
ea = 0x28CAB
ins = ida_ua.insn_t()
n = ida_ua.decode_insn(ins, ea)
out.append("decode at 0x28CAB: n=%d itype=%d" % (n, ins.itype))
try:
    out.append("generate_disasm_line: " + str(ida_lines.generate_disasm_line(ea, 0)))
except Exception as e:
    out.append("generate_disasm_line failed: %r" % (e,))
try:
    out.append("print_insn_mnem: " + str(idc.print_insn_mnem(ea)))
except Exception as e:
    out.append("print_insn_mnem failed: %r" % (e,))
# insn_t fields that might carry a canonical mnemonic
out.append("insn_t fields: " + str([f for f in dir(ins) if not f.startswith("_")][:30]))
open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\probe_mnem.json", "w").write("\n".join(out))
import idaapi
idaapi.qexit(0)