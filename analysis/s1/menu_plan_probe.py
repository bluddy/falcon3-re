"""Plan probe (COPY, DBFL_KILL) for the two jmp-reached menu bodies 10B380 and 10B720.
Key/handler table offsets are read from the `mov bx, imm` before the lookup loop.  Handlers are decoded by
recursive descent (create_insn, follow jmp/jcc targets, stop at ret/jmp), then add_func(base, end).
Output: analysis/s1/menu_plan.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes, ida_ua
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\menu_plan.json"
# base, call-far fixup head, end of the body (after the final retf)
VARS = [(0x10B380, 0x10B4E8, 0x10B6DF), (0x10B720, 0x10B888, 0x10BA7B)]
RETS = {"retn", "retf", "iret"}
R = {"v": {}}


def words(ea, n):
    return [ida_bytes.get_word(ea + 2 * i) for i in range(n)]


def descend(seed, lo, hi, made):
    todo = [seed]
    while todo:
        ea = todo.pop()
        while lo <= ea < hi:
            fl = ida_bytes.get_flags(ea)
            if ida_bytes.is_code(fl) and ida_bytes.get_item_head(ea) == ea:
                if ea in made:
                    break
            else:
                ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, 1)
                if ida_ua.create_insn(ea) <= 0:
                    made[ea] = None
                    break
            n = ida_bytes.get_item_size(ea)
            m = idc.print_insn_mnem(ea)
            made[ea] = m
            if m in RETS:
                break
            if m.startswith("j") or m.startswith("loop"):
                for x in idautils.XrefsFrom(ea, 0):
                    if x.type in (18, 19) and lo <= x.to < hi:
                        todo.append(x.to)
                if m == "jmp":
                    break
            ea += n


try:
    for base, cf, end in VARS:
        r = {}
        mov = None
        a = base
        while a < base + 0x1C0 and mov is None:
            h = ida_bytes.get_item_head(a)
            if idc.print_insn_mnem(h) == "mov" and idc.get_operand_type(h, 0) == idc.o_reg and idc.print_operand(h, 0) == "bx" \
                    and idc.get_operand_type(h, 1) == idc.o_imm and idc.get_operand_value(h, 1) > 0x300:
                mov = h
            a = h + max(ida_bytes.get_item_size(h), 1)
        r["mov_bx"] = [hex(mov), idc.generate_disasm_line(mov, 0)]
        tab = idc.get_operand_value(mov, 1)
        cx = None
        h = mov
        while h > base and cx is None:
            h = idc.prev_head(h, base)
            if idc.print_insn_mnem(h) == "mov" and idc.print_operand(h, 0) == "cx" and idc.get_operand_type(h, 1) == idc.o_imm:
                cx = idc.get_operand_value(h, 1)
        r["cx"] = cx
        keys = words(base + tab, cx)
        hands = words(base + tab + 2 * cx, cx)
        r["tab"] = hex(tab)
        r["keys"] = [hex(k) for k in keys]
        r["handlers"] = [hex(h) for h in hands]
        r["bytes_774"] = [hex(b) for b in ida_bytes.get_bytes(0x10B760, 32)]
        r["dis_774"] = [idc.generate_disasm_line(x, 0) for x in range(0x10B76A, 0x10B77C)] if base == 0x10B720 else []
        ida_bytes.del_items(cf, ida_bytes.DELIT_SIMPLE, 5)
        r["cf_len"] = ida_ua.create_insn(cf)
        r["cf_after"] = idc.generate_disasm_line(cf, 0)
        made = {}
        descend(cf + 5, base, end, made)
        r["handler_ea"] = [hex(base + h) for h in hands]
        for t in sorted(set(base + h for h in hands)):
            descend(t, base, end, made)
        r["bad_decode"] = [hex(k) for k, v in made.items() if v is None]
        ok = ida_funcs.add_func(base, end)
        r["add_ok"] = bool(ok)
        if ok:
            f = ida_funcs.get_func(base)
            r["span"] = [hex(f.start_ea), hex(f.end_ea)]
            und, a = [], base
            while a < f.end_ea:
                h = ida_bytes.get_item_head(a)
                if not ida_bytes.is_code(ida_bytes.get_flags(h)):
                    und.append(h)
                a = h + max(ida_bytes.get_item_size(h), 1)
            runs = []
            for h in und:
                if runs and runs[-1][1] == h:
                    runs[-1][1] = h + 1
                else:
                    runs.append([h, h + 1])
            r["non_code_runs"] = [[hex(x), hex(y), y - x] for x, y in runs]
            it = ida_funcs.func_tail_iterator_t(f)
            ch, okk = [], it.main()
            while okk:
                ch.append([hex(it.chunk().start_ea), hex(it.chunk().end_ea)])
                okk = it.next()
            r["chunks"] = ch
            r["calls"] = sorted({idc.print_operand(h, 0) for h in made if made[h] and made[h].startswith("call")})
        R["v"]["%X" % base] = r
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
