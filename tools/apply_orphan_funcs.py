"""Register orphan code that is called but belongs to no function (finding 126, S1c-4).

Tier 1 only: a run of code heads that no function owns, entered by a call from code, that decodes from its
start to a terminator (ret/retf/iret or an unconditional jmp) without touching another function.  Runs that
end mid-flow (mov/add/popf ...) or look misdecoded are NOT registered; they are listed in finding 126.

Manifest registry/orphan_funcs_expected.json: {"add_funcs": [{"ea", "end", "last", "callers", "sha256"}]}
  OFMODE=plan   run on a COPY: registers every candidate in ADD (below) with an explicit end, checks each,
                records the result, never saves.
  (default)     replays the manifest: each [ea, end) must hold its recorded bytes and no function (or already be
                exactly the planned function); applies add_func(ea, end); post-check requires the old functions
                to be unchanged (start, end, name, chunks) and the new ones to be exactly the planned ones.
                A failure discards everything (DBFL_KILL).  Never runs auto_wait.
REBASE (finding 130) moves the start of an existing named function up to the call-reached entry in front of it (the
old start was a mid-instruction byte left by a misdecode): del_func, clear, recursive descent, add_func, same name and
far flag, DS range extended.  Manifest key "rebase_funcs".
OFLOG overrides the log path, OFDRY=1 applies and checks without saving.

Usage: idat -A -S"tools\\apply_orphan_funcs.py" <idb>
"""
import hashlib
import json
import os
import traceback
from pathlib import Path

import ida_bytes
import ida_funcs
import ida_loader
import ida_nalt
import ida_name
import ida_segment
import ida_segregs
import ida_ua
import idaapi
import idautils
import idc

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "registry/orphan_funcs_expected.json"
LOG = Path(os.environ.get("OFLOG") or ROOT / "analysis/ida_falconcd/apply_orphan_funcs.log")
PLAN = os.environ.get("OFMODE") == "plan"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}
# (ea, end): chosen from analysis/s1/orphan_t1*.json; every end is the address after a terminator
ADD = [(0x1617C, 0x162DF), (0x162DF, 0x163AD), (0x16284E, 0x162878), (0x12C970, 0x12C9D0),
       (0x12CA0D, 0x12CAEF), (0x12CAEF, 0x12CB27), (0x12C683, 0x12C7C6), (0x12C951, 0x12C970),
       (0x12CCE9, 0x12CE9D), (0x10931E, 0x1093A8), (0x109445, 0x109519), (0x129F7, 0x12B12), (0x12B12, 0x12B62),
       (0x100CA8, 0x100D00), (0x12C4F2, 0x12C504), (0x12C9D0, 0x12C9DF), (0x12CB27, 0x12CB2A), (0x22C89, 0x22C91)]
# finding 139: no-xref runs that end in a terminator (far stubs, wrappers, an ISR); scan analysis/s1/orphan_scan138.json
ADD += [(0x1002C, 0x1005A), (0x10473, 0x1047C), (0x105DC, 0x105E1), (0x10C7E, 0x10C83), (0x11B90, 0x11B96), (0x11D16, 0x11D2B), (0x13A53, 0x13A57), (0x205BA, 0x205BF), (0x20613, 0x2061B), (0x20889, 0x20897), (0x21ABA, 0x21ABE), (0x22564, 0x2256D), (0x229BB, 0x229C0), (0x229C8, 0x229D1), (0x229D1, 0x229DD), (0x22AEB, 0x22AFF), (0x23E25, 0x23E37), (0x23E37, 0x23E57), (0x23F5E, 0x23F62), (0x2408B, 0x2408F), (0x24963, 0x24970), (0x24970, 0x2497C), (0x2551C, 0x25522), (0x25562, 0x25567), (0x25893, 0x25899), (0x25899, 0x2589F), (0x2B131, 0x2B135), (0x2CA17, 0x2CA3F), (0x2CB72, 0x2CB76), (0x2CB76, 0x2CB7B), (0x12D15E, 0x12D16E)]
# finding 141: a switch function entered through an overlay stub that pushes its offset; its second chunk lies after the stub
ADD += [(0x100457, 0x1004BE)]
# finding 142: the real entry sits in a misdecoded stretch behind a word table (0x12BF96) or inside a table's last bytes (0x155F18)
ADD += [(0x12BF96, 0x12BFA8), (0x12BFA8, 0x12BFE1), (0x155F18, 0x155F2A), (0x155F2A, 0x155F4C)]
# finding 172 P6: 26 terminated orphan runs with callers (small gaps between P1-split functions)
ADD += [
    (0x2E98B, 0x2E992), (0x2F185, 0x2F188), (0x2F353, 0x2F35B), (0x34901, 0x34907),
    (0x37810, 0x37818), (0x38C81, 0x38C91), (0x3BEEB, 0x3BEFD), (0x3C004, 0x3C00C),
    (0x3D313, 0x3D319), (0x3FAA7, 0x3FAAE), (0x40F56, 0x40F5D), (0x42832, 0x42838),
    (0x42F08, 0x42F10), (0x492D8, 0x492E0), (0x496CB, 0x496D3), (0x49A19, 0x49A1F),
    (0x4A87F, 0x4A88F), (0x4B4C8, 0x4B4D0), (0x4B7B1, 0x4B7B9), (0x4B8E4, 0x4B8EC),
    (0x4BF52, 0x4BF5A), (0x4C3C2, 0x4C3C7), (0x4D352, 0x4D35A), (0x4FA33, 0x4FA3B),
    (0x6DC04, 0x6DC09), (0x6F8FF, 0x6F907),
]
# finding 173 P7: drain auto queue — 1 clean ADD entry (0x3FB20 R05).
# Overlay entries (R12/R18/R28/R29/R33/R49) need IDA's auto analysis (auto_wait) —
# deferred; they will be created when those overlay segments are analyzed.
ADD += [
    (0x3FB20, 0x3FB22),  # R05 — analyzed; 2B fall-through stub
]
# Deferred: 0x43BAC (add_func fails), 0x4DA3D (data bytes),
# 0x6E31D (R14), 0x434B2/0x13DBD8 (owned), 0x4E5xx (inside 0x4E520 — SPLIT deferred)
# Overlay auto-queue functions (R12/R18/R28/R29/R33/R49): need auto_wait, deferred
# ea -> (clear_lo, clear_hi, seeds): orphan run with a misdecoded stretch that must be cleared and redecoded first
ADD_CLEAR = {0x10931E: (0x109388, 0x1093A6, [0x10931E, 0x109388]), 0x109445: (0x109445, 0x109519, [0x109445]),
             0x129F7: (0x129F7, 0x12B12, [0x129F7]), 0x12B12: (0x12B12, 0x12B62, [0x12B12]), 0x100CA8: (0x100CA8, 0x100D00, [0x100CA8]),
             0x22C89: (0x22C89, 0x22C91, [0x22C89]), 0x100457: (0x100457, 0x1004BE, [0x100457]),
             0x12BF96: (0x12BF88, 0x12BF99, [0x12BF96]), 0x155F18: (0x155F18, 0x155F1A, [0x155F18])}
# functions that end by falling into the entry of the next function (0x155F4C is a shared `retn` stub)
FALL = {0x155F2A, 0x3FB20}
# ea -> (lo, hi): word table entries inside the ADD_CLEAR range, made words again before the code behind them is redecoded
ADD_WORDS = {0x12BF96: (0x12BF88, 0x12BF96)}
# ea -> (tail chunk, clear ranges, seeds, pad bytes): a function whose second chunk lies after a foreign function that sits
# inside its span (finding 131); pad bytes are single data bytes inside a chunk that no flow reaches
TAILS = {0x100CA8: ([(0x100D0E, 0x100DFA)], [(0x100CA8, 0x100D00), (0x100D0D, 0x100DFA)], [0x100CA8, 0x100D0E, 0x100DF4], [0x100DEC]),
         0x100457: ([(0x1004CC, 0x10059E)], [(0x100457, 0x1004BE), (0x1004CC, 0x10059E)],
                    [0x100457, 0x1004CC, 0x1004D3, 0x1004E4, 0x100502], [0x100501])}
# (old_start, new_start, end, clear_lo, ds_para[, clear_hi]): existing function whose real entry is new_start (finding 130).
# [clear_lo, clear_hi) (default end) is cleared and redecoded from new_start; ds_para (or None) extends the DS range
# down to new_start.  A narrow clear_hi (finding 132, an instruction boundary) leaves the rest of a long body alone.
REBASE = [(0x106EEC, 0x106EE2, 0x106F3A, 0x106EE2, 0x706E), (0x10843D, 0x108430, 0x1084A6, 0x10843C, None),
          (0x10CFA6, 0x10CE30, 0x10CFEC, 0x10CFA5, None),
          (0x4335A, 0x4334E, 0x43395, 0x4334E, None),
          (0x6EF31, 0x6EF30, 0x6F1CE, 0x6EF30, None, 0x6EF39), (0x69723, 0x69720, 0x69AC6, 0x69720, None, 0x6972B),
          (0x16F4B5, 0x16F4B1, 0x16F507, 0x16F4B1, None),
          # finding 178 P5a: r30_record_link real prologue `enter 6,0` at 0x6940B (3 bytes inside ui_loadout_menu_enter);
          # full body clear so the garbled instructions from offset 0x6940E are all redeoded from scratch
          (0x6940E, 0x6940B, 0x69462, 0x6940B, None),
          # finding 179 P5b: ui_loadout_menu_enter starts mid-instruction (0x683C5 = last byte of push es:[0x14FA]);
          # real start is 0x683C1; narrow clear_hi=0x683C6 to redecode only the 5-byte push prefix
          (0x683C5, 0x683C1, 0x6940B, 0x683C1, None, 0x683C6),
          # finding 205 P2 batch 1: 6 not_head misdecodes where calls land 1 byte into current function start
          # (all have 0x00 orphan byte before, no prior function ownership, xrefs point to prev byte)
          (0x407BF, 0x407BE, 0x40843, 0x407BE, None),  # sub_407BF: 2 xrefs to 0x407BE, 0 to current
          (0x40DDB, 0x40DDA, 0x40E35, 0x40DDA, None),  # sub_40DDB: 1 xref to 0x40DDA
          (0x40C69, 0x40C68, 0x40C73, 0x40C68, None),  # sub_40C69: 7 xrefs to 0x40C68
          (0x40045, 0x40044, 0x4005C, 0x40044, None),  # sub_40045: 2 xrefs to 0x40044
          (0x3FD66, 0x3FD65, 0x3FD89, 0x3FD65, None),  # sub_3FD66: 4 xrefs to 0x3FD65
          (0x404F1, 0x404F0, 0x404F6, 0x404F0, None),  # sub_404F1: 2 xrefs to 0x404F0
]
# finding 161 P2 type-1 misdecodes: DEFERRED — these have external callers to the old null-byte head
# (the REBASE stale-head check correctly flags them; they need sub-block fixup or individual analysis)
# finding 161 P2 type-2a misdecodes:
# of a multi-byte instruction that bleeds into the real code at head+1.  FIX_DECODE clears the
# misdecoded instruction and re-decodes from head+1 without changing the function structure.
# (fn_ea, head): t = head+1 for all off==1 cases; deferred: 5 off>1 cases.
FIX_DECODE = [(0x2E910, 0x2E91F), (0x2F043, 0x2F05E), (0x2F257, 0x2F293), (0x348AD, 0x348ED),
              # (0x356A7, 0x3592B): 66-prefix misdecode, deferred — fix interacts with plan-mode state
              (0x377CF, 0x377F3), (0x38778, 0x389AC), (0x38778, 0x38792),
              (0x38CF3, 0x38D2C), (0x3BB8F, 0x3BCEA), (0x3BB8F, 0x3BBDB), (0x3BEFD, 0x3BF4A),
              (0x3C8EB, 0x3C920), (0x3CF9D, 0x3D22A), (0x3EEDB, 0x3EFF2), (0x3F861, 0x3F8DC),
              (0x3FAAE, 0x3FB07), (0x40EA8, 0x40F12), (0x4113C, 0x4115D), (0x42731, 0x427B9),
              (0x42ECA, 0x42EF1), (0x47239, 0x4732D), (0x49235, 0x49275), (0x495DF, 0x49609),
              (0x49997, 0x499E1), (0x4A7E5, 0x4A802), (0x4AB06, 0x4AB23), (0x4B36A, 0x4B42A),
              (0x4B6BB, 0x4B715), (0x4B7B9, 0x4B890), (0x4BDD0, 0x4BEC6), (0x4C19E, 0x4C200),
              (0x4CD1D, 0x4CF2E), (0x4D230, 0x4D279), (0x4D9FC, 0x4DA3C), (0x4F8BC, 0x4F963),
              (0x4FD38, 0x4FD46), (0x4FD4A, 0x4FD5C), (0x4FD4A, 0x4FD74), (0x6B87A, 0x6BAF1),
              (0x6D5DF, 0x6D60B), (0x6DA34, 0x6DA95), (0x6E29E, 0x6E31C), (0x6E32A, 0x6E32F),
              (0x6E32A, 0x6E355), (0x6E376, 0x6E3B1), (0x6E3D0, 0x6E423), (0x6E3D0, 0x6E3E9),
              (0x6F6C0, 0x6F8F1)]
# (ea, fn_end, data_end): a "function" that is really the head of a word table (finding 134).  The function is deleted,
# [ea, data_end) is cleared and re-made as words; nothing may jump or call into it from outside.
REMOVE = [(0x6EC14, 0x6EC17, 0x6EC2C), (0x6EF1C, 0x6EF1F, 0x6EF30), (0x2E1C2, 0x2E1E8, 0x2E20A)]
# Table repair (finding 135): functions that are misread table words are deleted, the table and the text behind it are
# remade as data, and the two dispatch tables that caused the misread are rebuilt.  funcs: (ea, end) to delete;
# clear: [lo, hi) cleared to bytes; words: [lo, hi) remade as plain words; offwords: (lo, hi, base) words that are
# offsets from base; plain: (lo, hi) words that are not pointers.
TABLEFIX = [{"funcs": [(0x105D9D, 0x105DA7), (0x105DA7, 0x105DA9)], "clear": (0x105D90, 0x105EB5),
             "words": (0x105D90, 0x105DE6), "offwords": (0x1069B4, 0x1069BE, 0x105D90), "plain": (0x1069BE, 0x1069C8)}]
# Text fix (finding 136): the message text behind the 0x105D90 offset table becomes strings.  table: (lo, hi, base) offset
# words; text: (lo, hi) typed as C strings and single control bytes (1..0x1f, bare NUL); keep: bytes that are variables
# inside the text (0x10614A is the patched player digit of "PLAYER #2 HAS") and stay one-byte items.
TEXTFIX = [{"table": (0x105D90, 0x105DE6, 0x105D90), "text": (0x105DE6, 0x10626E), "keep": [0x10614A]}]
# (ea, old_end, new_end, clear_hi): a function whose tail is really data (finding 137).  The end moves up to new_end,
# [new_end, clear_hi) is cleared and the words in [new_end, words_hi) are made 2-byte data; whatever is left up to
# clear_hi is re-decoded by the ADD entry that follows (so an ADD_CLEAR item must cover [words_hi, clear_hi)).
TRIM = [(0x22C62, 0x22C8B, 0x22C71, 0x22C89, 0x22C91),
        # finding 178 P5a: trim ui_loadout_menu_enter tail to 0x6940B (retf at 0x6940A is last insn);
        # zero-width word range so trim_state stays "applied" after r30_record_link REBASE reclaims the bytes
        (0x683C5, 0x6940E, 0x6940B, 0x6940B, 0x6940E)]
# (owner, frag, clear_lo, clear_hi, new_end): finding 138.  frag is a bogus function made of fragments of owner's own body;
# it is deleted, [clear_lo, clear_hi) is redecoded from clear_lo, owner's tail chunks inside [main_end, new_end) are dropped
# and owner's main chunk is extended to new_end.
ABSORB = [(0x166F80, 0x167440, 0x16743E, 0x167450, 0x16781A)]
# (func, [(lo, hi, seeds)], [frag functions]): finding 144.  Pieces of a function's own body that were misdecoded and left orphan
# (or owned by a bogus fragment function, which is deleted and unnamed first): [lo, hi) is cleared, redecoded from the seeds and
# appended as a chunk of func (append_func_tail merges it with an adjacent chunk).
GLUE = [(0x2E20A, [(0x2E22F, 0x2E23D, [0x2E22F, 0x2E236]), (0x2E281, 0x2E28F, [0x2E281])], []),
        (0x166F80, [(0x16781A, 0x167827, [0x16781A])], [0x16781C])]
# (lo, hi, kind): orphan "code" that is really data (finding 143): jump-table words ('w', an odd last byte stays a byte) or
# key / record bytes ('b').  [lo, hi) is cleared and re-made as data; nothing may jump or call into it.
DATAFIX = [(0x1982F, 0x19843, "w"), (0x1277CC, 0x1277DA, "w"), (0x1B4E0, 0x1B4E8, "w"), (0x1F75F, 0x1F769, "b"),
           (0x2E190, 0x2E194, "w"), (0x5CDA8, 0x5CDB2, "b"), (0x5CDFA, 0x5CDFD, "w"), (0x5D1E6, 0x5D1ED, "b"),
           (0x5D2E5, 0x5D2E9, "b"), (0x5D5AB, 0x5D5B3, "b"), (0x5D91B, 0x5D925, "b"), (0x5DA68, 0x5DA75, "b"),
           (0x6EA3A, 0x6EA4A, "w")]
# (ea, end): existing functions whose body continues in orphan code (jcc/jmp into it) -> set_func_end
EXTEND = [(0x12C518, 0x12C66A), (0x12C7C6, 0x12C951)]
# (func, run_lo, run_hi): fl_F continuations (finding 129).  If run_lo is the main-chunk end the function is
# lengthened (set_func_end, which also swallows an adjacent tail chunk), else the run is appended as a tail chunk.
EXTEND_RUNS = [(0x10CC60, 0x10CC8E, 0x10CE05), (0x2D31A, 0x2D353, 0x2D375), (0x3F6A9, 0x3F6C7, 0x3F6D6),
               (0x2142E, 0x215FE, 0x21631), (0x2520B, 0x25220, 0x25224)]
DOS_EXIT = {0x2D353}  # run ends in `mov ax,4C00h / int 21h` (terminates the process)
# jmp-reached menu bodies (R20/R21): (base, damaged `call far` head, end).  The key table is `mov bx, tab` with
# `mov cx, n` before the lookup loop; the handler table follows the keys, offsets relative to base.
MENUS = [(0x10B380, 0x10B4E8, 0x10B6DF), (0x10B720, 0x10B888, 0x10BA7B)]
# (owner_ea, at): split the owner function at `at` -> owner becomes [owner_ea, at), new unnamed fn [at, end).
# One entry per batch per owner (use the lowest `at` per owner each batch; higher split points appear in
# the new function and are handled in a later batch).  finding 145 batch 1.
SPLIT = [
    (0x100AF, 0x100B5),   # bda_kb_flag_10000_get
    (0x100BB, 0x100C1),   # mouse_gate_far_entry (first of 2)
    (0x10D8C, 0x10D97),   # stub_bundle_10d8c (first of 2)
    (0x10E03, 0x10E0C),   # flag1084c_get
    (0x11A0C, 0x11A30),   # state_quad_11873_set (first of 2)
    (0x121C2, 0x122AE),   # entity_setup_step (first of 3)
    (0x127D4, 0x12884),   # param_table_init (first of 3)
    (0x128A1, 0x128AB),   # state_farptr_get (first of 3)
    (0x2234B, 0x2241E),   # control_axes_read (first of 5)
    (0x22841, 0x22846),   # state_word_2223e_set (first of 3)
    (0x228BF, 0x2295C),   # int32_to_ascii
    (0x22DDC, 0x22DE6),   # state_farptr_dxax_store (first of 3)
    (0x24DE6, 0x24DEC),   # dispatch_220dc_stub
    (0x24FB9, 0x2501A),   # flag_bits_dispatch
    (0x2533D, 0x253E4),   # sub_2533D
    (0x254C0, 0x254C5),   # flag254a1_set (first of 4)
    (0x25687, 0x2568C),   # view_block4287_entry (first of 3)
    (0x259B9, 0x259D8),   # dispatch_2210c_invoke_5arg
    (0x25E42, 0x25E4E),   # angle_quad_norm_far
    (0x26281, 0x2629A),   # trig_clip_project_entry
    (0x263F0, 0x263F6),   # dispatch_220d4_stub
    (0x26FF4, 0x2700E),   # farobj_copy_cond
    (0x274CF, 0x274D5),   # state_word_27470_set_ds
    (0x275D8, 0x27649),   # buffer_budget_entry_block (first of 2)
    (0x27697, 0x276B4),   # far_list_dispatch
    (0x2E2F0, 0x2E34A),   # farobj_slot_create
    (0x2E6C2, 0x2E6D5),   # farobj_cmd_interp
    (0x2FB5A, 0x2FBE9),   # mode_request_code_dispatch (first of 2)
    (0x305E4, 0x305F7),   # dgroup_state_cycle_step (first of 6)
    (0x3099C, 0x309A7),   # control_axes_record_store
    (0x30AA8, 0x30AE5),   # event_table_name_fill
    (0x30CB8, 0x30D4F),   # farobj_record_bulk_copy (first of 2)
    (0x327BE, 0x327C8),   # farobj_rect_state_setup
    (0x34416, 0x34469),   # handle_build_8f_block (first of 3)
    (0x345BA, 0x345FD),   # object_farptr_dispatch
    (0x3470D, 0x34770),   # range_key_event_dispatch (first of 2)
    (0x34954, 0x34A8E),   # mode_entity_select_apply
    (0x35EB5, 0x35FDF),   # rot_segment_strip_draw (first of 2)
    (0x36FAC, 0x36FE5),   # sprite_in_view_test
    (0x37051, 0x37056),   # mode_byte_dispatch
]
# finding 146 batch 2 (40 splits, early overlays R05)
SPLIT += [
    (0x100C1, 0x10108),   # sub_100C1 (tail of mouse_gate_far_entry, second split)
    (0x10D97, 0x10DA7),   # sub_10D97 (second split of stub_bundle_10d8c)
    (0x11A30, 0x11A44),   # sub_11A30 (second split of state_quad_11873_set)
    (0x122AE, 0x12320),   # sub_122AE (first of 2: entity_setup_step tail)
    (0x12884, 0x1288B),   # sub_12884 (first of 2: param_table_init tail)
    (0x128AB, 0x128CD),   # sub_128AB (first of 2: state_farptr_get tail)
    (0x2241E, 0x22436),   # sub_2241E (first of 4: control_axes_read tail)
    (0x22846, 0x2284B),   # sub_22846 (first of 2: state_word_2223e_set tail)
    (0x22DE6, 0x22DF0),   # sub_22DE6 (first of 2: state_farptr_dxax_store tail)
    (0x254C5, 0x254CA),   # sub_254C5 (first of 3: flag254a1_set tail)
    (0x2568C, 0x25693),   # sub_2568C (first of 2: view_block4287_entry tail)
    (0x27649, 0x2765D),   # sub_27649 (second split of buffer_budget_entry_block)
    (0x2FBE9, 0x2FBFD),   # sub_2FBE9 (second split of mode_request_code_dispatch)
    (0x305F7, 0x30610),   # sub_305F7 (first of 5: dgroup_state_cycle_step tail)
    (0x30D4F, 0x30D5F),   # sub_30D4F (second split of farobj_record_bulk_copy)
    (0x34469, 0x34474),   # sub_34469 (first of 2: handle_build_8f_block tail)
    (0x34770, 0x3480A),   # nullsub_35 (second split of range_key_event_dispatch)
    (0x35FDF, 0x36006),   # sub_35FDF (second split of rot_segment_strip_draw)
    (0x3772D, 0x377AB),   # sprite_project_screen_y (first of 2)
    (0x37818, 0x378A9),   # terrain_angle_time_step
    (0x386F2, 0x3875B),   # tile_sample_script_dispatch (first of 3)
    (0x38CAB, 0x38CB2),   # matrix_constants_copy_gate (first of 5)
    (0x395DF, 0x396D3),   # aircraft_motion_step
    (0x39AA9, 0x39AAF),   # state_word_2e12b_set
    (0x39BD3, 0x39C14),   # mode_quadrant_accum_step
    (0x39F1D, 0x3A003),   # steerpoint_scan_update
    (0x3A29C, 0x3A35E),   # hud_track_label_strip
    (0x3A88D, 0x3A8B1),   # map_view_project_pipeline
    (0x3AB59, 0x3AB7E),   # terrain_grid_cb_dispatch
    (0x3ADDA, 0x3AF9F),   # pos_move_angle_step (first of 3)
    (0x3B338, 0x3B503),   # pos_step_chain_engine (first of 7)
    (0x3B6BB, 0x3B6E2),   # tile_quad_classify (first of 6)
    (0x3BB8F, 0x3BEFD),   # farobj_record_ops_exec (first of 4)
    (0x3C1BD, 0x3C319),   # farobj_slot_update_driver (first of 4)
    (0x3C4F2, 0x3C57E),   # farobj_slot_project_step (first of 4)
    (0x3CE92, 0x3CEDD),   # farobj_behavior_dispatch_step (first of 5)
    (0x3DC55, 0x3DE4A),   # farobj_altitude_scale_step (first of 7)
    (0x3E16B, 0x3E170),   # farobj_cmd_accum_sweep (first of 5)
    (0x3E552, 0x3E878),   # farobj_cfg_scan_step (first of 2)
    (0x3E95E, 0x3E962),   # farobj_cfg_code_patch (first of 3)
]
# finding 147 batch 3 (40 splits, R05_2B83 through R05_33AE area)
SPLIT += [
    (0x12320, 0x1232E),   # sub_12320 (remaining entity_setup_step tail)
    (0x1288B, 0x12890),   # sub_1288B (remaining param_table_init tail)
    (0x128CD, 0x12910),   # sub_128CD (remaining state_farptr_get tail)
    (0x22436, 0x2243B),   # sub_22436 (first of 3: control_axes_read multi-split)
    (0x2284B, 0x22850),   # sub_2284B (remaining state_word_2223e_set tail)
    (0x22DF0, 0x22DF5),   # sub_22DF0 (remaining state_farptr_dxax_store tail)
    (0x254CA, 0x254D0),   # sub_254CA (first of 2: flag254a1_set tail)
    (0x25693, 0x256A3),   # sub_25693 (remaining view_block4287_entry tail)
    (0x30610, 0x3061B),   # sub_30610 (first of 4: dgroup_state_cycle_step tail)
    (0x34474, 0x3448A),   # sub_34474 (remaining handle_build_8f_block tail)
    (0x377AB, 0x377C0),   # sub_377AB (remaining sprite_project_screen_y tail)
    (0x3875B, 0x3876A),   # sub_3875B (first of 2: tile_sample_script_dispatch tail)
    (0x38CB2, 0x38CB7),   # sub_38CB2 (first of 4: matrix_constants_copy_gate tail)
    (0x3AF9F, 0x3B1B9),   # sub_3AF9F (first of 2: pos_move_angle_step tail)
    (0x3B503, 0x3B549),   # sub_3B503 (first of 6: pos_step_chain_engine tail)
    (0x3B6E2, 0x3B72C),   # sub_3B6E2 (first of 5: tile_quad_classify tail)
    (0x3BEFD, 0x3C00C),   # sub_3BEFD (first of 3: farobj_record_ops_exec tail)
    (0x3C319, 0x3C38D),   # sub_3C319 (first of 3: farobj_slot_update_driver tail)
    (0x3C57E, 0x3C5CA),   # sub_3C57E (first of 3: farobj_slot_project_step tail)
    (0x3CEDD, 0x3CEF4),   # sub_3CEDD (first of 4: farobj_behavior_dispatch_step tail)
    (0x3DE4A, 0x3DE6F),   # sub_3DE4A (first of 6: farobj_altitude_scale_step tail)
    (0x3E170, 0x3E1C2),   # sub_3E170 (first of 4: farobj_cmd_accum_sweep tail)
    (0x3E878, 0x3E8C5),   # sub_3E878 (remaining farobj_cfg_scan_step tail)
    (0x3E962, 0x3EB4E),   # sub_3E962 (first of 2: farobj_cfg_code_patch tail)
    (0x3EEDB, 0x3F274),   # farobj_view_project_step (first of 3)
    (0x3F861, 0x3FAAE),   # farobj_index_resolve_step
    (0x3FBCC, 0x3FC66),   # farobj_angle_distance_gate (first of 2)
    (0x3FCF1, 0x3FD32),   # range_scale_accum_clamp
    (0x40F77, 0x41075),   # hud_data_panel_slot_mgr (first of 2)
    (0x4111F, 0x41123),   # farobj_class_table_entry (first of 4)
    (0x415CE, 0x415FD),   # farobj_state_flag_set
    (0x41646, 0x416EC),   # farobj_range_slot_init
    (0x41784, 0x4179E),   # farobj_flag_or_set (first of 2)
    (0x41B4E, 0x41B68),   # farobj_index_state_swap (first of 5)
    (0x41D21, 0x41D23),   # hud_object_text_format
    (0x42025, 0x42139),   # farobj_selection_window_step
    (0x42220, 0x4222D),   # mode_phase_apply_state
    (0x4236B, 0x423A9),   # farobj_thrust_burn_step
    (0x4245B, 0x42503),   # farobj_fuel_apply_step
    (0x42553, 0x425A2),   # farobj_matrix_project_copy
]
# finding 148 batch 4 (40 splits, R05_33AE through R05_38DB area)
SPLIT += [
    (0x2243B, 0x22440),   # sub_2243B (first of 2: control_axes_read multi-split cont.)
    (0x254D0, 0x254DC),   # sub_254D0 (remaining flag254a1_set tail)
    (0x3061B, 0x30650),   # sub_3061B (first of 3: dgroup_state_cycle_step tail cont.)
    (0x3876A, 0x38778),   # sub_3876A (remaining tile_sample_script_dispatch tail)
    (0x38CB7, 0x38CBC),   # sub_38CB7 (first of 3: matrix_constants_copy_gate tail cont.)
    (0x3B1B9, 0x3B256),   # sub_3B1B9 (remaining pos_move_angle_step tail)
    (0x3B549, 0x3B57F),   # sub_3B549 (first of 3: pos_step_chain_engine tail cont.)
    (0x3B72C, 0x3B73C),   # sub_3B72C (first of 3: tile_quad_classify tail cont.)
    (0x3C00C, 0x3C09E),   # sub_3C00C (first of 2: farobj_record_ops_exec tail cont.)
    (0x3C38D, 0x3C3E1),   # sub_3C38D (first of 2: farobj_slot_update_driver tail cont.)
    (0x3C5CA, 0x3C62C),   # sub_3C5CA (first of 2: farobj_slot_project_step tail cont.)
    (0x3CEF4, 0x3CF9D),   # sub_3CEF4 (first of 3: farobj_behavior_dispatch_step tail cont.)
    (0x3DE6F, 0x3DED9),   # sub_3DE6F (first of 3: farobj_altitude_scale_step tail cont.)
    (0x3E1C2, 0x3E1F6),   # sub_3E1C2 (first of 3: farobj_cmd_accum_sweep tail cont.)
    (0x3EB4E, 0x3EBA5),   # sub_3EB4E (remaining farobj_cfg_code_patch tail)
    (0x3F274, 0x3F287),   # sub_3F274 (first of 2: farobj_view_project_step tail cont.)
    (0x3FC66, 0x3FCE1),   # sub_3FC66 (remaining farobj_angle_distance_gate tail)
    (0x41075, 0x410F6),   # sub_41075 (remaining hud_data_panel_slot_mgr tail)
    (0x41123, 0x4113C),   # sub_41123 (first of 3: farobj_class_table_entry tail cont.)
    (0x4179E, 0x417B2),   # sub_4179E (remaining farobj_flag_or_set tail)
    (0x41B68, 0x41BDF),   # sub_41B68 (first of 3: farobj_index_state_swap tail cont.)
    (0x426CC, 0x42731),   # hud_track_distance_draw (first of 2)
    (0x4289E, 0x428A1),   # ui_slot_filter_predicate (first of 5)
    (0x44352, 0x445A6),   # farobj_entity_attr_setup (first of 2)
    (0x446CB, 0x4478D),   # farobj_entity_step_near (first of 2)
    (0x45057, 0x45074),   # hud_state_rowtable_step (first of 5)
    (0x45976, 0x45C4B),   # game_setup_staged_init (first of 4)
    (0x45F2C, 0x45FB4),   # viewport_strip_row_draw (first of 8)
    (0x46999, 0x46AC0),   # hud_readout_timer_render (first of 6)
    (0x46D42, 0x46ECF),   # hud_track_strip_pipeline (first of 8)
    (0x47686, 0x47743),   # sprite_delta_project_47686
    (0x47A9B, 0x47B10),   # r32_hud_phase_dispatch (first of 3)
    (0x47BDE, 0x47DF5),   # hud_rowlist_timer_step (first of 5)
    (0x47F9E, 0x4812B),   # hud_panel_transform_step
    (0x484C1, 0x4853F),   # record_script_coord_entry (first of 7)
    (0x487B2, 0x487C3),   # viewport_bounds_setup (first of 3)
    (0x48B05, 0x48C20),   # target_cycle_scan
    (0x48EC7, 0x48F99),   # tile_grid_scan_step (first of 7)
    (0x493C4, 0x493FC),   # aircraft_record_load_step
    (0x495DF, 0x496D3),   # store_fall_sim_step (first of 6)
]
# finding 149 batch 5 (40 splits, R05_39AB through R05_3BDD area)
SPLIT += [
    (0x22440, 0x22445),   # sub_22440 (remaining control_axes_read chain)
    (0x30650, 0x306D1),   # sub_30650 (first of 2: dgroup_state_cycle_step tail cont.)
    (0x38CBC, 0x38CCF),   # sub_38CBC (first of 2: matrix_constants_copy_gate tail cont.)
    (0x3B57F, 0x3B5B0),   # sub_3B57F (first of 4: pos_step_chain_engine tail cont.)
    (0x3B73C, 0x3B7B2),   # sub_3B73C (first of 3: tile_quad_classify tail cont.)
    (0x3C09E, 0x3C0AE),   # sub_3C09E (remaining farobj_record_ops_exec tail)
    (0x3C3E1, 0x3C48F),   # sub_3C3E1 (remaining farobj_slot_update_driver tail)
    (0x3C62C, 0x3C8EB),   # sub_3C62C (remaining farobj_slot_project_step tail)
    (0x3CF9D, 0x3D319),   # sub_3CF9D (first of 2: farobj_behavior_dispatch_step tail cont.)
    (0x3DED9, 0x3DF1E),   # sub_3DED9 (first of 3: farobj_altitude_scale_step tail cont.)
    (0x3E1F6, 0x3E269),   # sub_3E1F6 (first of 2: farobj_cmd_accum_sweep tail cont.)
    (0x3F287, 0x3F3A8),   # sub_3F287 (remaining farobj_view_project_step tail)
    (0x4113C, 0x41466),   # sub_4113C (first of 2: farobj_class_table_entry tail cont.)
    (0x41BDF, 0x41BF1),   # sub_41BDF (first of 3: farobj_index_state_swap tail cont.)
    (0x42731, 0x42838),   # sub_42731 (remaining hud_track_distance_draw tail)
    (0x428A1, 0x428C1),   # sub_428A1 (first of 4: ui_slot_filter_predicate tail cont.)
    (0x445A6, 0x4460F),   # sub_445A6 (remaining farobj_entity_attr_setup tail)
    (0x4478D, 0x4486B),   # sub_4478D (remaining farobj_entity_step_near tail)
    (0x45074, 0x45270),   # sub_45074 (first of 4: hud_state_rowtable_step tail cont.)
    (0x45C4B, 0x45D13),   # sub_45C4B (first of 3: game_setup_staged_init tail cont.)
    (0x45FB4, 0x45FF1),   # sub_45FB4 (first of 7: viewport_strip_row_draw tail cont.)
    (0x46AC0, 0x46AF9),   # sub_46AC0 (first of 5: hud_readout_timer_render tail cont.)
    (0x46ECF, 0x46F46),   # sub_46ECF (first of 7: hud_track_strip_pipeline tail cont.)
    (0x47B10, 0x47B2A),   # sub_47B10 (first of 2: r32_hud_phase_dispatch tail cont.)
    (0x47DF5, 0x47E1C),   # sub_47DF5 (first of 4: hud_rowlist_timer_step tail cont.)
    (0x4853F, 0x48571),   # sub_4853F (first of 6: record_script_coord_entry tail cont.)
    (0x487C3, 0x48800),   # sub_487C3 (first of 2: viewport_bounds_setup tail cont.)
    (0x48F99, 0x490BA),   # sub_48F99 (first of 6: tile_grid_scan_step tail cont.)
    (0x496D3, 0x498ED),   # sub_496D3 (first of 5: store_fall_sim_step tail cont.)
    (0x49AB4, 0x49C03),   # entity_spawn_from_tile (first of 4)
    (0x4A7E5, 0x4A88F),   # mode_record_field_lookup (first of 12)
    (0x4AD30, 0x4AD88),   # ui_aircraft_slot_step (first of 6)
    (0x4AEC4, 0x4AFBD),   # farobj_pos_move_angle_step (first of 11)
    (0x4B36A, 0x4B4D0),   # sprite_step_clip_project_body (first of 2)
    (0x4B584, 0x4B5D5),   # pos_state_block_read
    (0x4B68D, 0x4B6BB),   # tile_object_interpreter (first of 6)
    (0x4BFB8, 0x4BFE0),   # farobj_tile_key_cache
    (0x4C0E4, 0x4C14F),   # farobj_table_init_69ff (first of 2)
    (0x4C19E, 0x4C3C7),   # farobj_queue_drain_dispatch (first of 3)
    (0x4CB62, 0x4CC50),   # farobj_record_flag_ops
]
# finding 150 batch 6 (40 splits, R05_3C0D through R05_3E52 area)
SPLIT += [
    (0x306D1, 0x30769),   # sub_306D1 (remaining dgroup_state_cycle_step tail)
    (0x38CCF, 0x38CE2),   # sub_38CCF (remaining matrix_constants_copy_gate tail)
    (0x3B5B0, 0x3B5BD),   # sub_3B5B0 (first of 3: pos_step_chain_engine tail cont.)
    (0x3B7B2, 0x3B7C3),   # sub_3B7B2 (first of 2: tile_quad_classify tail cont.)
    (0x3D319, 0x3D37F),   # sub_3D319 (remaining farobj_behavior_dispatch_step tail)
    (0x3DF1E, 0x3E01A),   # sub_3DF1E (first of 3: farobj_altitude_scale_step tail cont.)
    (0x3E269, 0x3E2D3),   # sub_3E269 (remaining farobj_cmd_accum_sweep tail)
    (0x41466, 0x41555),   # sub_41466 (remaining farobj_class_table_entry tail)
    (0x41BF1, 0x41C07),   # sub_41BF1 (first of 2: farobj_index_state_swap tail cont.)
    (0x428C1, 0x428D4),   # sub_428C1 (first of 3: ui_slot_filter_predicate tail cont.)
    (0x45270, 0x4540B),   # sub_45270 (first of 3: hud_state_rowtable_step tail cont.)
    (0x45D13, 0x45E29),   # sub_45D13 (first of 2: game_setup_staged_init tail cont.)
    (0x45FF1, 0x46000),   # sub_45FF1 (first of 6: viewport_strip_row_draw tail cont.)
    (0x46AF9, 0x46B2B),   # sub_46AF9 (first of 4: hud_readout_timer_render tail cont.)
    (0x46F46, 0x46FEA),   # sub_46F46 (first of 6: hud_track_strip_pipeline tail cont.)
    (0x47B2A, 0x47B68),   # sub_47B2A (remaining r32_hud_phase_dispatch tail)
    (0x47E1C, 0x47E43),   # sub_47E1C (first of 3: hud_rowlist_timer_step tail cont.)
    (0x48571, 0x485AC),   # sub_48571 (first of 5: record_script_coord_entry tail cont.)
    (0x48800, 0x48864),   # sub_48800 (remaining viewport_bounds_setup tail)
    (0x490BA, 0x490F4),   # sub_490BA (first of 5: tile_grid_scan_step tail cont.)
    (0x498ED, 0x49982),   # sub_498ED (first of 4: store_fall_sim_step tail cont.)
    (0x49C03, 0x49C2E),   # sub_49C03 (first of 3: entity_spawn_from_tile tail cont.)
    (0x4A88F, 0x4A8DE),   # sub_4A88F (first of 11: mode_record_field_lookup tail cont.)
    (0x4AD88, 0x4AE06),   # sub_4AD88 (first of 5: ui_aircraft_slot_step tail cont.)
    (0x4AFBD, 0x4B048),   # sub_4AFBD (first of 10: farobj_pos_move_angle_step tail cont.)
    (0x4B4D0, 0x4B505),   # sub_4B4D0 (remaining sprite_step_clip_project_body tail)
    (0x4B6BB, 0x4B7B9),   # sub_4B6BB (first of 5: tile_object_interpreter tail cont.)
    (0x4C14F, 0x4C15E),   # sub_4C14F (remaining farobj_table_init_69ff tail)
    (0x4C3C7, 0x4CAE2),   # sub_4C3C7 (first of 2: farobj_queue_drain_dispatch tail cont.)
    (0x4CD1D, 0x4D143),   # farobj_move_accumulate_step (first of 9)
    (0x4D3C7, 0x4D3EC),   # farobj_flag_dispatch_step
    (0x4D544, 0x4D55F),   # farobj_class16_record_ops (first of 2)
    (0x4D8A7, 0x4D9C3),   # farobj_slot_step_spawn (first of 2)
    (0x4DC16, 0x4DC63),   # view_wrap_projection_entry (first of 6)
    (0x4DE76, 0x4DF80),   # ems_opstream_buffer_append
    (0x4DF9D, 0x4DFEA),   # overlay_teardown_restore_state (first of 2)
    (0x4E14C, 0x4E18F),   # ems_stream_pointer_step (first of 6)
    (0x4E309, 0x4E314),   # farobj_slot_create_status
    (0x4E320, 0x4E32B),   # farobj_cfg_step_control (first of 2)
    (0x4E520, 0x4E803),   # store_cmd_interpreter (first of 2)
]
# finding 151 batch 7 (40 splits, R05_3E52/R05_3F25 and overlays)
SPLIT += [
    (0x3B5BD, 0x3B5D1),   # sub_3B5BD (first of 2: pos_step_chain_engine tail cont.)
    (0x3B7C3, 0x3B7F3),   # sub_3B7C3 (remaining tile_quad_classify tail)
    (0x3E01A, 0x3E02E),   # sub_3E01A (first of 2: farobj_altitude_scale_step tail cont.)
    (0x41C07, 0x41C2C),   # sub_41C07 (remaining farobj_index_state_swap tail)
    (0x428D4, 0x42939),   # sub_428D4 (first of 2: ui_slot_filter_predicate tail cont.)
    (0x4540B, 0x45472),   # sub_4540B (first of 2: hud_state_rowtable_step tail cont.)
    (0x45E29, 0x45ECB),   # sub_45E29 (remaining game_setup_staged_init tail)
    (0x46000, 0x4602C),   # sub_46000 (first of 5: viewport_strip_row_draw tail cont.)
    (0x46B2B, 0x46B66),   # sub_46B2B (first of 3: hud_readout_timer_render tail cont.)
    (0x46FEA, 0x4705F),   # sub_46FEA (first of 5: hud_track_strip_pipeline tail cont.)
    (0x47E43, 0x47E87),   # sub_47E43 (first of 2: hud_rowlist_timer_step tail cont.)
    (0x485AC, 0x485B3),   # sub_485AC (first of 4: record_script_coord_entry tail cont.)
    (0x490F4, 0x4915D),   # sub_490F4 (first of 4: tile_grid_scan_step tail cont.)
    (0x49982, 0x49997),   # sub_49982 (first of 3: store_fall_sim_step tail cont.)
    (0x49C2E, 0x49C40),   # sub_49C2E (first of 2: entity_spawn_from_tile tail cont.)
    (0x4A8DE, 0x4A94C),   # sub_4A8DE (first of 10: mode_record_field_lookup tail cont.)
    (0x4AE06, 0x4AE27),   # sub_4AE06 (first of 4: ui_aircraft_slot_step tail cont.)
    (0x4B048, 0x4B09F),   # sub_4B048 (first of 9: farobj_pos_move_angle_step tail cont.)
    (0x4B7B9, 0x4B8EC),   # sub_4B7B9 (first of 4: tile_object_interpreter tail cont.)
    (0x4CAE2, 0x4CB0A),   # sub_4CAE2 (remaining farobj_queue_drain_dispatch tail)
    (0x4D143, 0x4D160),   # sub_4D143 (first of 8: farobj_move_accumulate_step tail cont.)
    (0x4D55F, 0x4D75F),   # sub_4D55F (remaining farobj_class16_record_ops tail)
    (0x4D9C3, 0x4D9FC),   # sub_4D9C3 (remaining farobj_slot_step_spawn tail)
    (0x4DC63, 0x4DC97),   # sub_4DC63 (first of 5: view_wrap_projection_entry tail cont.)
    (0x4DFEA, 0x4E044),   # sub_4DFEA (remaining overlay_teardown_restore_state tail)
    (0x4E18F, 0x4E194),   # sub_4E18F (first of 5: ems_stream_pointer_step tail cont.)
    (0x4E32B, 0x4E361),   # sub_4E32B (remaining farobj_cfg_step_control tail)
    (0x4E803, 0x4E86E),   # sub_4E803 (remaining store_cmd_interpreter tail)
    (0x4E90E, 0x4E93A),   # ems_opstream_table_flush (first of 3)
    (0x4EAF8, 0x4EB82),   # ems_entity_slot_script (first of 8)
    (0x4EED3, 0x4EF01),   # ems_state_flags_709f (first of 2)
    (0x4EF1C, 0x4EF4E),   # entity_record_table_ops (first of 5)
    (0x4F271, 0x4F385),   # vga_dac_palette_upload (first of 2)
    (0x4F3A3, 0x4F3BA),   # farobj_cfg_gate_85059
    (0x4F4FE, 0x4F5CB),   # view_pos_cache_update
    (0x4F72B, 0x4F76A),   # sprite_blend_0ad2d (first of 2)
    (0x4F7B8, 0x4F7F0),   # terrain_vm_blend_apply
    (0x4FA8A, 0x4FB1C),   # palette_delta_blend
    (0x4FBC2, 0x4FC2D),   # hw_cfg_copy_a76f
    (0x4FCE4, 0x4FCF3),   # hw_flag_85052_set_ff
]
# finding 152 batch 8 (49 splits, R05_3F25 through R05_3DAD + all overlays remaining)
SPLIT += [
    (0x3B5D1, 0x3B618),   # sub_3B5D1 (remaining pos_step_chain_engine tail)
    (0x3E02E, 0x3E042),   # sub_3E02E (remaining farobj_altitude_scale_step tail)
    (0x42939, 0x42957),   # sub_42939 (remaining ui_slot_filter_predicate tail)
    (0x45472, 0x456A3),   # sub_45472 (remaining hud_state_rowtable_step tail)
    (0x4602C, 0x4611C),   # sub_4602C (first of 4: viewport_strip_row_draw tail cont.)
    (0x46B66, 0x46BD6),   # sub_46B66 (first of 2: hud_readout_timer_render tail cont.)
    (0x4705F, 0x47111),   # sub_4705F (first of 4: hud_track_strip_pipeline tail cont.)
    (0x47E87, 0x47EC6),   # sub_47E87 (remaining hud_rowlist_timer_step tail)
    (0x485B3, 0x48612),   # sub_485B3 (first of 3: record_script_coord_entry tail cont.)
    (0x4915D, 0x491F6),   # sub_4915D (first of 3: tile_grid_scan_step tail cont.)
    (0x49997, 0x49A1F),   # sub_49997 (first of 2: store_fall_sim_step tail cont.)
    (0x49C40, 0x49C67),   # sub_49C40 (remaining entity_spawn_from_tile tail)
    (0x4A94C, 0x4A9E9),   # sub_4A94C (first of 9: mode_record_field_lookup tail cont.)
    (0x4AE27, 0x4AE35),   # sub_4AE27 (first of 3: ui_aircraft_slot_step tail cont.)
    (0x4B09F, 0x4B0D8),   # sub_4B09F (first of 8: farobj_pos_move_angle_step tail cont.)
    (0x4B8EC, 0x4B94F),   # sub_4B8EC (first of 3: tile_object_interpreter tail cont.)
    (0x4D160, 0x4D17C),   # sub_4D160 (first of 7: farobj_move_accumulate_step tail cont.)
    (0x4DC97, 0x4DD0A),   # sub_4DC97 (first of 4: view_wrap_projection_entry tail cont.)
    (0x4E194, 0x4E199),   # sub_4E194 (first of 4: ems_stream_pointer_step tail cont.)
    (0x4E93A, 0x4E945),   # sub_4E93A (first of 2: ems_opstream_table_flush tail cont.)
    (0x4EB82, 0x4EC42),   # sub_4EB82 (first of 7: ems_entity_slot_script tail cont.)
    (0x4EF01, 0x4EF0C),   # sub_4EF01 (remaining ems_state_flags_709f tail)
    (0x4EF4E, 0x4EF7B),   # sub_4EF4E (first of 4: entity_record_table_ops tail cont.)
    (0x4F385, 0x4F394),   # sub_4F385 (remaining vga_dac_palette_upload tail)
    (0x4F76A, 0x4F7A0),   # sub_4F76A (remaining sprite_blend_0ad2d tail)
    (0x4FD80, 0x4FD82),   # pop_ds_retf
    (0x4FDAD, 0x4FDB3),   # state_word_0f0e_store
    (0x4FEB5, 0x4FECC),   # angle_fixed_rotate_apply (first of 3)
    # (0x683C5, 0x6940B) SKIPPED: ui_loadout_menu_enter is part of the deferred 0x6E696 handler cluster (P5)
    (0x6A050, 0x6A19F),   # r30_mode_set_637fc_c
    (0x6A5BD, 0x6A651),   # ui_menu_page_setup
    (0x6B53A, 0x6B669),   # ui_slot_count_tally (first of 3)
    (0x6CDA8, 0x6CDFA),   # r06_mode_step_dispatch
    (0x6CE4B, 0x6CE4C),   # r06_farptr_dispatch_gate
    (0x6D0C9, 0x6D126),   # r06_state_init_e56
    (0x6D13D, 0x6D145),   # r06_gate_4ac9
    (0x6D256, 0x6D29F),   # r06_ui_dispatch_block (first of 3)
    (0x6D4F4, 0x6D51A),   # r06_mode_gate_49a3 (first of 2)
    (0x6D68D, 0x6D6EC),   # r06_mode_state_update
    (0x6D838, 0x6D875),   # r06_mode_step_tick
    (0x6D8E6, 0x6D948),   # r06_mode_dispatch_bx8 (first of 4)
    (0x6DD12, 0x6DD8E),   # distance_tier_classify_entry (first of 2)
    # 0x6E32A r14_farptr_call_gate2 and 0x6E3D0 r14_farptr_call_gate SKIPPED: add_func fails at tails
    (0x106E66, 0x106E79), # r12_farptr_helper_c_record_wrap
    (0x107015, 0x10701D), # r12_ah0c_far_call_entry
    (0x166061, 0x166098), # r36_mod_slot_index_entry
    # (0x12C683, 0x12C764) SKIPPED: sub_12C683 is also in the ADD list (finding 128), conflict
    (0x12C7C6, 0x12C912), # sub_12C7C6 (safe: in EXTEND_RUNS not ADD, EXTEND runs before SPLIT)
]
# finding 153 batch 9 (22 splits, final tail chains + R30/R06 overlays)
SPLIT += [
    (0x4611C, 0x463DA),   # sub_4611C (first of 3: viewport_strip_row_draw tail cont.)
    (0x46BD6, 0x46C72),   # sub_46BD6 (remaining hud_readout_timer_render tail)
    (0x47111, 0x47162),   # sub_47111 (first of 3: hud_track_strip_pipeline tail cont.)
    (0x48612, 0x486A9),   # sub_48612 (first of 2: record_script_coord_entry tail cont.)
    (0x491F6, 0x49235),   # sub_491F6 (first of 2: tile_grid_scan_step tail cont.)
    (0x49A1F, 0x49A5B),   # sub_49A1F (remaining store_fall_sim_step tail)
    (0x4A9E9, 0x4AAA4),   # sub_4A9E9 (first of 8: mode_record_field_lookup deep chain)
    (0x4AE35, 0x4AE66),   # sub_4AE35 (first of 2: ui_aircraft_slot_step tail cont.)
    (0x4B0D8, 0x4B12C),   # sub_4B0D8 (first of 7: farobj_pos_move_angle_step deep chain)
    (0x4B94F, 0x4B9D0),   # sub_4B94F (first of 2: tile_object_interpreter tail cont.)
    (0x4D17C, 0x4D19C),   # sub_4D17C (first of 6: farobj_move_accumulate_step deep chain)
    (0x4DD0A, 0x4DD3B),   # sub_4DD0A (first of 3: view_wrap_projection_entry tail cont.)
    (0x4E199, 0x4E1A3),   # sub_4E199 (first of 3: ems_stream_pointer_step tail cont.)
    (0x4E945, 0x4EA53),   # sub_4E945 (remaining ems_opstream_table_flush tail)
    (0x4EC42, 0x4EC43),   # nullsub_36 (1-byte stub before the ems_entity_slot_script deep chain)
    (0x4EF7B, 0x4F0A9),   # sub_4EF7B (first of 3: entity_record_table_ops tail cont.)
    (0x4FECC, 0x4FF3C),   # sub_4FECC (first of 2: angle_fixed_rotate_apply tail cont.)
    (0x6B669, 0x6B709),   # sub_6B669 (first of 2: ui_slot_count_tally tail cont.)
    (0x6D29F, 0x6D3D5),   # sub_6D29F (first of 2: r06_ui_dispatch_block tail cont.)
    (0x6D51A, 0x6D575),   # sub_6D51A (remaining r06_mode_gate_49a3 tail)
    (0x6D948, 0x6D967),   # sub_6D948 (first of 3: r06_mode_dispatch_bx8 tail cont.)
    (0x6DD8E, 0x6DE07),   # sub_6DD8E (remaining distance_tier_classify_entry tail)
]
# finding 154 batch 10 (17 splits, final batch of pure splits)
SPLIT += [
    (0x463DA, 0x46439),   # sub_463DA (first of 2: viewport_strip_row_draw deep chain)
    (0x47162, 0x47239),   # sub_47162 (first of 2: hud_track_strip_pipeline deep chain)
    (0x486A9, 0x486D1),   # sub_486A9 (remaining record_script_coord_entry tail)
    (0x49235, 0x492E0),   # sub_49235 (remaining tile_grid_scan_step tail)
    (0x4AAA4, 0x4AABC),   # sub_4AAA4 (first of 7: mode_record_field_lookup deep chain)
    (0x4AE66, 0x4AEA6),   # sub_4AE66 (remaining ui_aircraft_slot_step tail)
    (0x4B12C, 0x4B16A),   # sub_4B12C (first of 6: farobj_pos_move_angle_step deep chain)
    (0x4B9D0, 0x4BBFD),   # sub_4B9D0 (remaining tile_object_interpreter tail)
    (0x4D19C, 0x4D1C6),   # sub_4D19C (first of 5: farobj_move_accumulate_step deep chain)
    (0x4DD3B, 0x4DDB4),   # sub_4DD3B (first of 2: view_wrap_projection_entry tail cont.)
    (0x4E1A3, 0x4E1EE),   # sub_4E1A3 (first of 2: ems_stream_pointer_step tail cont.)
    (0x4EC43, 0x4EC58),   # sub_4EC43 (first of 5: ems_entity_slot_script deep chain)
    (0x4F0A9, 0x4F0B6),   # sub_4F0A9 (first of 2: entity_record_table_ops tail cont.)
    (0x4FF3C, 0x50035),   # sub_4FF3C (remaining angle_fixed_rotate_apply tail)
    (0x6B709, 0x6B77F),   # sub_6B709 (remaining ui_slot_count_tally tail)
    (0x6D3D5, 0x6D3FB),   # sub_6D3D5 (remaining r06_ui_dispatch_block tail)
    (0x6D967, 0x6D988),   # sub_6D967 (first of 2: r06_mode_dispatch_bx8 tail cont.)
]
# finding 155 batch 11 (10 splits, final deep chains)
SPLIT += [
    (0x46439, 0x4649B),   # sub_46439 (remaining viewport_strip_row_draw tail)
    (0x47239, 0x4751E),   # sub_47239 (remaining hud_track_strip_pipeline tail)
    (0x4AABC, 0x4AAE2),   # sub_4AABC (first of 6: mode_record_field_lookup deep chain)
    (0x4B16A, 0x4B1E3),   # sub_4B16A (first of 5: farobj_pos_move_angle_step deep chain)
    (0x4D1C6, 0x4D1EC),   # sub_4D1C6 (first of 4: farobj_move_accumulate_step deep chain)
    (0x4DDB4, 0x4DE2F),   # sub_4DDB4 (remaining view_wrap_projection_entry tail)
    (0x4E1EE, 0x4E2C8),   # sub_4E1EE (remaining ems_stream_pointer_step tail)
    (0x4EC58, 0x4EC76),   # sub_4EC58 (first of 4: ems_entity_slot_script deep chain)
    (0x4F0B6, 0x4F128),   # sub_4F0B6 (remaining entity_record_table_ops tail)
    (0x6D988, 0x6D9DE),   # sub_6D988 (remaining r06_mode_dispatch_bx8 tail)
]
# finding 156 batch 12 (4 splits, one per remaining deep chain)
SPLIT += [
    (0x4AAE2, 0x4AB06),   # sub_4AAE2 (1 of 5: mode_record_field_lookup deep chain)
    (0x4B1E3, 0x4B251),   # sub_4B1E3 (1 of 4: farobj_pos_move_angle_step deep chain)
    (0x4D1EC, 0x4D230),   # sub_4D1EC (1 of 3: farobj_move_accumulate_step deep chain)
    (0x4EC76, 0x4ECAC),   # sub_4EC76 (1 of 3: ems_entity_slot_script deep chain)
]
# finding 157 batch 13 (4 splits, second level of remaining chains)
SPLIT += [
    (0x4AB06, 0x4AC1E),   # sub_4AB06 (2 of 5: mode_record_field_lookup chain)
    (0x4B251, 0x4B2BD),   # sub_4B251 (2 of 4: farobj_pos_move_angle_step chain)
    (0x4D230, 0x4D35A),   # sub_4D230 (2 of 3: farobj_move_accumulate_step chain)
    (0x4ECAC, 0x4EE65),   # sub_4ECAC (2 of 3: ems_entity_slot_script chain)
]
# finding 158 batch 14
SPLIT += [
    (0x4AC1E, 0x4AC5E),   # sub_4AC1E (3 of 5: mode_record_field_lookup chain)
    (0x4B2BD, 0x4B2EE),   # sub_4B2BD (3 of 4: farobj_pos_move_angle_step chain)
    (0x4D35A, 0x4D38C),   # sub_4D35A (3 of 3: farobj_move_accumulate_step - last)
    (0x4EE65, 0x4EEB3),   # sub_4EE65 (3 of 3: ems_entity_slot_script - last)
]
# finding 159 batch 15
SPLIT += [
    (0x4AC5E, 0x4AC80),   # sub_4AC5E (4 of 5: mode_record_field_lookup chain)
    (0x4B2EE, 0x4B327),   # sub_4B2EE (4 of 4: farobj_pos_move_angle_step - last)
]
# finding 160 batch 16 (1 split, final split of mode_record_field_lookup chain)
SPLIT += [
    (0x4AC80, 0x4ACC9),   # sub_4AC80 (5 of 5: mode_record_field_lookup - last)
]
# finding 162 P3 batch 1 (19 splits: prologue-bearing fall-in entries, one per owner)
# These are call targets inside a function body where the target has a push/mov/enter prologue
# AND a fall-through from before. Standard SPLIT creates two functions at the prologue boundary.
# NOTE: (0x1189E, 0x118D6) skipped — 0x118D2 (mov) is a non-call inner xref to 0x118D6
#   (shared tail / fall-through branch, not a pure prologue split); defer to P4.
# All entries here have inner xrefs of type fl_F (21, ordinary flow) or genuine branches because
# the predecessor instruction falls directly into the split point. These are added to SPLIT_RELAX
# so split_fn skips the strict "call-only" inner-xref check for them.
SPLIT += [
    (0x20AC1, 0x20B29),   # view_bounds_distribute
    (0x28CA1, 0x28CA4),   # sub_28CA1
    (0x33443, 0x3352A),   # far_mode_event_dispatch (1 of 6: at 0x3352A)
    (0x39CE0, 0x39D02),   # state_gate_4ac2_4a83
    (0x3C00C, 0x3C03D),   # sub_3C00C
    (0x3E8C5, 0x3E8D2),   # sub_3E8C5
    (0x3E962, 0x3E96F),   # sub_3E962
    (0x3F62C, 0x3F62F),   # sub_3F62C (3-byte stub before main body)
    (0x3FD89, 0x3FD9A),   # farobj_attr_apply_step
    (0x42AFA, 0x42C31),   # sub_42AFA
    (0x42E31, 0x42E37),   # sub_42E31
    (0x49C67, 0x49C80),   # sub_49C67
    (0x4A4F6, 0x4A505),   # hud_map_overlay_step
    (0x4D3EC, 0x4D459),   # sub_4D3EC
    (0x4EE65, 0x4EE82),   # sub_4EE65
    (0x4F7F0, 0x4F84B),   # sub_4F7F0
    (0x6E32A, 0x6E343),   # r14_farptr_call_gate2
    (0x13DB5D, 0x13DB5E), # sub_13DB5D (1-byte stub)
    (0x13DC09, 0x13DC0A), # sub_13DC09 (1-byte stub)
]
# SPLIT_RELAX: at_ea values for P3 entries where non-call inner xrefs are expected.
# The predecessor instruction falls directly into the split point (fl_F flow xref),
# and in some cases there are also genuine internal branches to the entry (which
# become cross-function references after the split, handled by IDA as tail calls).
# Append new P3 at values here whenever a new P3 finding is added.
SPLIT_RELAX = {
    # finding 162 P3 batch 1
    0x20B29, 0x28CA4, 0x3352A, 0x39D02, 0x3C03D, 0x3E8D2, 0x3E96F,
    0x3F62F, 0x3FD9A, 0x42C31, 0x42E37, 0x49C80, 0x4A505, 0x4D459,
    0x4EE82, 0x4F84B, 0x6E343, 0x13DB5E, 0x13DC0A,
}
# finding 163 P3 cont (2 splits: far_mode_event_dispatch chain steps 2 & 4)
# A: split owner 0x33443 (now ends at 0x3352A from f162) at 0x33468 (inside stub)
# C: split owner 0x3352A (the second half from f162) at 0x339B2
# B, D, E need owners created by A and C → deferred to finding 164+
SPLIT += [
    (0x33443, 0x33468),   # far_mode_event_dispatch stub split (2 of 6)
    (0x3352A, 0x339B2),   # far_mode_event_dispatch second-half split (4 of 6)
]
SPLIT_RELAX |= {0x33468, 0x339B2}  # P3 fall-through entries
# finding 164 P3 cont (2 splits: far_mode_event_dispatch chain steps 3 & 5)
# B: split owner 0x33468 (created by f163) at 0x334C2
# D: split owner 0x339B2 (created by f163) at 0x33C1B
SPLIT += [
    (0x33468, 0x334C2),   # far_mode_event_dispatch (3 of 6)
    (0x339B2, 0x33C1B),   # far_mode_event_dispatch (5 of 6)
]
SPLIT_RELAX |= {0x334C2, 0x33C1B}  # P3 fall-through entries
# finding 165 P3 cont (1 split: far_mode_event_dispatch chain step 6, final)
# E: split owner 0x33C1B (created by f164) at 0x33D83
SPLIT += [
    (0x33C1B, 0x33D83),   # far_mode_event_dispatch (6 of 6, final)
]
SPLIT_RELAX |= {0x33D83}  # P3 fall-through entry
# finding 166 P4 batch 1: 5 pure-split merged_fn entries (no internal jmps, no tail chunks)
# These are `after_ret_or_jmp(merged_fn)` entries that were missed in P1 (created later by P1/P3
# splits or deferred due to ADD conflict), confirmed no internal jumps from owner, no tail chunks.
SPLIT += [
    (0x3FAAE, 0x3FB08),   # sub_3FAAE: retn before 0x3FB08, 1 caller
    (0x4F84B, 0x4F870),   # sub_4F84B (from P3 f162): retn before 0x4F870, 1 caller
    (0x4F8BC, 0x4F964),   # terrain_vm_flag_gate: retf before 0x4F964, 1 caller
    (0x6E3D0, 0x6E404),   # r14_farptr_call_gate: retf before 0x6E404 (step 1 of 2)
    (0x12C683, 0x12C764), # sub_12C683: retn before 0x12C764 (deferred from P1: ADD conflict resolved)
]
log = []
# SPLIT_OWNERS: owner ea values for all SPLIT entries.  Used by state() to recognise
# add_func items that were later split (their end changes after the split is applied,
# so a plain end-equality check would return "mismatch" and try to re-add them).
SPLIT_OWNERS = {ea for ea, at in SPLIT}
# SPLIT_TAILS: owner_ea values whose function has IDA tail chunks (unusual).
# Standard split_fn checks chunks(ea)==[[ea,end]] which fails for these.
# set_func_end still works; the tail chunk is retained by the stub after the split.
SPLIT_TAILS = set()
# finding 171 P4: segment_clip_test split (has tail chunk at 0x25F8F..0x25F93)
# set_func_end(0x25F93, 0x26099) works (confirmed on probe); tail stays with stub.
SPLIT += [
    (0x25F93, 0x26099),   # segment_clip_test: 32 callers, prev=jmp, no inner xrefs
]
SPLIT_TAILS.add(0x25F93)
# finding 167 P4 cont: r14_farptr_call_gate second split (needs 0x6E404 from f166)
SPLIT += [
    (0x6E404, 0x6E43B),   # r14_farptr_call_gate: retf before 0x6E43B (step 2 of 2)
]
SPLIT_OWNERS |= {0x6E404}  # update owners set
# finding 168 P4 shared tails batch 1 (9 splits)
# These all have non-call inner xrefs (jz/jmp/loop) from the owner → added to SPLIT_RELAX.
# Entries 32D22+33074, 3B5DB+3B5E9, 475A1+4760F are chains: first half only here, second in f169.
SPLIT += [
    (0x3352A, 0x3396E),   # sub_3352A: jz from 0x33934 to 0x3396E (2 callers)
    (0x3B618, 0x3B645),   # sub_3B618: jz from 0x3B61C to 0x3B645 (1 caller)
    (0x48F99, 0x49078),   # sub_48F99: jmp from 0x49091 to 0x49078 (2 callers)
    (0x4F0B6, 0x4F0CB),   # sub_4F0B6: jmp from 0x4F126 to 0x4F0CB (4 callers)
    (0x6D4F4, 0x6D4FC),   # r06_mode_gate_49a3: jz from 0x6D4F9 (1 caller)
    # (0x4113C, 0x41167) DEFERRED — add_func fails at 0x41167, bytes not valid code head for IDA
    (0x32C62, 0x32D22),   # mode_session_state_reset chain step 1 (jnz from 0x32CD4, 2 callers)
    (0x3B5D1, 0x3B5DB),   # sub_3B5D1 chain step 1 (jz from 0x3B5D7, 2 callers)
    (0x4751E, 0x475A1),   # sub_4751E chain step 1 (loop×2 from 0x47603/0x4760C, 1 caller)
]
SPLIT_RELAX |= {0x3396E, 0x3B645, 0x49078, 0x4F0CB, 0x6D4FC, 0x32D22, 0x3B5DB, 0x475A1}
# finding 169 P4 shared tails chain continuations
# After finding 168: sub_32D22 (0x32D22..0x33116), sub_3B5DB (0x3B5DB..0x3B618), sub_475A1 (0x475A1..0x47686)
SPLIT += [
    (0x32D22, 0x33074),   # mode_session_state_reset chain step 2 (jz from 0x33071, 2 callers)
    (0x3B5DB, 0x3B5E9),   # sub_3B5D1 chain step 2 (jmp from 0x3B5D9, 2 callers)
    (0x475A1, 0x4760F),   # sub_4751E chain step 2 (loop×2 from 0x4767A/0x47683, 1 caller)
]
SPLIT_RELAX |= {0x33074, 0x3B5E9, 0x4760F}
# finding 170 P4 'other' batch: 3 pure splits with no inner xrefs (classified 'other' not 'fallthrough')
# These have no fall-through and no internal jumps from owner → standard split, no SPLIT_RELAX needed.
# Owner code is not fully decoded before the target (prev_mnem=''), typical for ds-setup prologues.
SPLIT += [
    (0x11A5E, 0x11A7D),   # cb_args_invoke: 'mov' at 0x11A7D, 8 callers
    (0x14BD7, 0x14BE0),   # farobj_pos_wrap_update: 'mov' at 0x14BE0, 1 caller
    (0x24DEC, 0x24E46),   # sub_24DEC: 'push' at 0x24E46, 6 callers
]


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
                    raise RuntimeError("cannot decode 0x%X" % ea)
            made.add(ea)
            m = idc.print_insn_mnem(ea)
            if m in RETS:
                break
            if m.startswith("j") or m.startswith("loop"):
                for x in idautils.XrefsFrom(ea, 0):
                    if x.type in (18, 19) and lo <= x.to < hi:
                        todo.append(x.to)
                if m == "jmp":
                    break
            ea += ida_bytes.get_item_size(ea)


def menu_seeds(base, cf):
    mov = cx = None
    a = base
    while a < base + 0x1C0 and mov is None:
        h = ida_bytes.get_item_head(a)
        if (idc.print_insn_mnem(h) == "mov" and idc.print_operand(h, 0) == "bx" and idc.get_operand_type(h, 1) == idc.o_imm
                and idc.get_operand_value(h, 1) > 0x300):
            mov = h
        a = h + max(ida_bytes.get_item_size(h), 1)
    must(mov is not None, "table load in 0x%X" % base)
    h = mov
    while h > base and cx is None:
        h = idc.prev_head(h, base)
        if idc.print_insn_mnem(h) == "mov" and idc.print_operand(h, 0) == "cx" and idc.get_operand_type(h, 1) == idc.o_imm:
            cx = idc.get_operand_value(h, 1)
    must(cx, "loop count in 0x%X" % base)
    tab = idc.get_operand_value(mov, 1)
    hands = [ida_bytes.get_word(base + tab + 2 * cx + 2 * i) for i in range(cx)]
    return sorted({base + x for x in hands} | {cf + 5})


def decode_menu(item):
    lo, hi = item["ea"], item["end"]
    if "clear" in item or "clears" in item:
        regs = regions(item)
        orig = set()
        for clo, chi in item.get("clears") or [item["clear"]]:
            a = clo
            while a < chi:
                h = ida_bytes.get_item_head(a)
                if ida_bytes.is_code(ida_bytes.get_flags(h)):
                    orig.add(h)
                a = h + max(ida_bytes.get_item_size(h), 1)
            ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, chi - clo)
        if "words" in item:
            for a in range(item["words"][0], item["words"][1], 2):
                must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
        for sd in item["seeds"]:
            rlo, rhi = next((x, y) for x, y in regs if x <= sd < y)
            descend(sd, rlo, rhi, set())
        for h in sorted(orig):
            if not (ida_bytes.is_code(ida_bytes.get_flags(h)) and ida_bytes.get_item_head(h) == h):
                bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not any(x <= r.frm < y for x, y in regs)]
                must(not bad, "jump/call into stale head 0x%X from %s" % (h, [hex(b) for b in bad]))
        return
    else:
        cf = item["redecode"]
        ida_bytes.del_items(cf, ida_bytes.DELIT_SIMPLE, 5)
        must(ida_ua.create_insn(cf) == 5, "re-decode call far at 0x%X" % cf)
    made = set()
    for sd in item["seeds"]:
        descend(sd, lo, hi, made)


def chunks(ea):
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea:
        return None
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append([it.chunk().start_ea, it.chunk().end_ea])
        ok = it.next()
    return sorted(out)


def snapshot():
    return {fs: (idaapi.get_name(fs), chunks(fs)) for fs in idautils.Functions()}


def sha(ea, end):
    return hashlib.sha256(ida_bytes.get_bytes(ea, end - ea)).hexdigest()


def must(ok, what):
    if not ok:
        raise RuntimeError(what + " failed")


def terminated(ea, end):
    last = idc.prev_head(end, ea)
    m = idc.print_insn_mnem(last)
    return m in RETS or (m == "jmp" and idc.get_operand_type(last, 0) in (idc.o_near, idc.o_far))


def callers(ea):
    return sorted(x.frm for x in idautils.XrefsTo(ea, 0)
                  if x.iscode and idc.print_insn_mnem(x.frm).startswith("call") and ida_funcs.get_func(x.frm))


def regions(item):
    return [[item["ea"], item["end"]]] + [list(t) for t in item.get("tails", [])]


def state(item):
    f = ida_funcs.get_func(item["ea"])
    if f and f.start_ea == item["ea"] and f.end_ea == item["end"] and (not item.get("tails") or chunks(item["ea"]) == sorted(regions(item))):
        return "applied"
    # If this function was later split (ea is in SPLIT_OWNERS), its end changed from item["end"].
    # The function still starts at item["ea"] and was successfully created; return "applied".
    if f and f.start_ea == item["ea"] and item["ea"] in SPLIT_OWNERS:
        return "applied"
    if (not any(ida_funcs.get_func(a) for lo, hi in regions(item) for a in range(lo, hi))
            and sha(item["ea"], item["end"]) == item["sha256"]
            and all(sha(lo, hi) == t for (lo, hi), t in zip(item.get("tails", []), item.get("tails_sha256", [])))):
        return "fresh"
    return "mismatch"


def uname(ea):
    return idaapi.get_name(ea) if ida_bytes.has_user_name(ida_bytes.get_flags(ea)) else None


def norm(x):
    """Fill the fields the finding-128 entries lack (they were a single contiguous run appended to a one-chunk function)."""
    x.setdefault("run", [x["before_end"], x["end"]])
    x.setdefault("run_sha256", x["sha256"])
    x.setdefault("chunks_before", [[x["ea"], x["before_end"]]])
    x.setdefault("chunks_after", [[x["ea"], x["end"]]])
    return x


def ext_state(x):
    """Entry: ea, run [lo, hi) of orphan code, run_sha256, chunks_before/after (sorted chunk lists), before_end/end
    (main-chunk end, which is what function_bytes.json sees) and sha256 of the bytes appended to the main chunk."""
    f = ida_funcs.get_func(x["ea"])
    if not f or f.start_ea != x["ea"]:
        return "mismatch"
    if chunks(x["ea"]) == x["chunks_after"] and f.end_ea == x["end"]:
        return "applied"
    # Also "applied" if the extension occurred (end moved past before_end = run[0]) but
    # the function was subsequently split further: bytes of the extended run are unchanged.
    lo, hi = x["run"]
    if sha(lo, hi) == x["run_sha256"] and f.end_ea > lo:
        return "applied"
    if (chunks(x["ea"]) == x["chunks_before"] and f.end_ea == lo
            and not any(ida_funcs.get_func(a) for a in range(lo, hi)) and sha(lo, hi) == x["run_sha256"]):
        return "fresh"
    return "mismatch"


def extend(x):
    lo, hi = x["run"]
    f = ida_funcs.get_func(x["ea"])
    if f.end_ea == lo:
        must(ida_funcs.set_func_end(x["ea"], hi), "set_func_end 0x%X -> 0x%X" % (x["ea"], hi))
    else:
        must(ida_funcs.append_func_tail(f, lo, hi), "append_func_tail 0x%X 0x%X..0x%X" % (x["ea"], lo, hi))
    if x["chunks_after"] is None:
        f = ida_funcs.get_func(x["ea"])
        x["end"], x["chunks_after"] = f.end_ea, chunks(x["ea"])
        x["sha256"] = sha(x["before_end"], x["end"]) if x["end"] > x["before_end"] else ""
    must(ext_state(x) == "applied", "extend 0x%X (state %s, chunks %s)" % (x["ea"], ext_state(x), chunks(x["ea"])))


def is_far(ea):
    return bool(ida_funcs.get_func(ea).flags & ida_funcs.FUNC_FAR)


def rb_state(x):
    old, new, end = x["old_ea"], x["ea"], x["end"]
    f = ida_funcs.get_func(new)
    if f and f.start_ea == new and f.end_ea == end and chunks(new) == [[new, end]] and uname(new) == x["name"]:
        return "applied"
    f = ida_funcs.get_func(old)
    if (f and f.start_ea == old and f.end_ea == end and chunks(old) == [[old, end]] and uname(old) == x["name"]
            and sha(new, end) == x["sha256"] and not any(ida_funcs.get_func(a) for a in range(new, old))):
        return "fresh"
    return "mismatch"


def rebase(x):
    old, new, end, clo = x["old_ea"], x["ea"], x["end"], x["clear_lo"]
    chi = x.get("clear_hi") or end
    far = is_far(old)
    must(far == x["far"], "far flag of 0x%X" % old)
    a, orig = clo, set()
    while a < chi:
        h = ida_bytes.get_item_head(a)
        if ida_bytes.is_code(ida_bytes.get_flags(h)):
            orig.add(h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    must(ida_funcs.del_func(old), "del_func 0x%X" % old)
    ida_name.set_name(old, "", ida_name.SN_NOWARN)
    ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, chi - clo)
    if x.get("ds") is not None:
        s = ida_segment.setup_selector(x["ds"])
        must(ida_segment.sel2para(s) == x["ds"], "selector for para 0x%X" % x["ds"])
        must(ida_segregs.split_sreg_range(new, idaapi.str2reg("ds"), s, ida_segregs.SR_user), "DS split at 0x%X" % new)
    made = set()
    descend(new, new, chi, made)
    a = new
    while a < chi:
        must(ida_bytes.is_code(ida_bytes.get_flags(a)) and ida_bytes.get_item_head(a) == a, "non-code head 0x%X in rebased 0x%X" % (a, new))
        a += ida_bytes.get_item_size(a)
    lost = sorted(h for h in orig if not (ida_bytes.is_code(ida_bytes.get_flags(h)) and ida_bytes.get_item_head(h) == h))
    for h in lost:
        bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (new <= r.frm < end)]
        must(not bad, "jump/call into stale head 0x%X from %s" % (h, [hex(b) for b in bad]))
    must(ida_funcs.add_func(new, end), "add_func 0x%X..0x%X" % (new, end))
    f = ida_funcs.get_func(new)
    must(f.start_ea == new and f.end_ea == end and chunks(new) == [[new, end]], "span of rebased 0x%X" % new)
    if far:
        f.flags |= ida_funcs.FUNC_FAR
        must(ida_funcs.update_func(f), "update_func 0x%X" % new)
    if x["name"]:
        must(ida_name.set_name(new, x["name"], ida_name.SN_NOWARN), "name of 0x%X" % new)
    must(is_far(new) == far, "far flag of rebased 0x%X" % new)
    if x.get("lost_heads") is None:
        x["lost_heads"] = lost
    must(x["lost_heads"] == lost, "stale code heads of 0x%X differ from the manifest: %s" % (new, [hex(h) for h in lost]))
    must(rb_state(x) == "applied", "rebase 0x%X" % new)


def rm_state(x):
    ea, fe, end = x["ea"], x["fn_end"], x["end"]
    f = ida_funcs.get_func(ea)
    if sha(ea, end) != x["data_sha256"]:
        return "mismatch"
    if not any(ida_funcs.get_func(a) for a in range(ea, end)):
        a = ea
        while a < end:
            if not (ida_bytes.is_data(ida_bytes.get_flags(a)) and ida_bytes.get_item_size(a) == 2):
                return "mismatch"
            a += 2
        return "applied"
    if (f and f.start_ea == ea and f.end_ea == fe and chunks(ea) == [[ea, fe]] and uname(ea) == x["name"]
            and not any(ida_funcs.get_func(a) for a in range(fe, end))):
        return "fresh"
    return "mismatch"


def remove(x):
    ea, fe, end = x["ea"], x["fn_end"], x["end"]
    must((end - ea) % 2 == 0, "word table length 0x%X" % ea)
    a, orig = ea, set()
    while a < end:
        h = ida_bytes.get_item_head(a)
        if ida_bytes.is_code(ida_bytes.get_flags(h)):
            orig.add(h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    for h in sorted(orig):
        bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (ea <= r.frm < end)]
        must(not bad, "jump/call into table head 0x%X from %s" % (h, [hex(b) for b in bad]))
    must(ida_funcs.del_func(ea), "del_func 0x%X" % ea)
    ida_name.set_name(ea, "", ida_name.SN_NOWARN)
    ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, end - ea)
    for a in range(ea, end, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
    must(rm_state(x) == "applied", "removal of 0x%X" % ea)


def tf_outside(x):
    lo, hi = x["clear"]
    return sorted((r.frm, t) for t in range(lo, hi) for r in idautils.XrefsTo(t, 0)
                  if r.type in (1, 16, 17, 18, 19) and not (lo <= r.frm < hi))


def tf_state(x):
    lo, hi = x["clear"]
    olo, ohi, base = x["offwords"]
    plo, phi = x["plain"]
    if (sha(lo, hi) != x["clear_sha256"] or sha(olo, ohi) != x["offwords_sha256"]
            or sha(plo, phi) != x["plain_sha256"]):
        return "mismatch"
    if all(ida_funcs.get_func(f["ea"]) and ida_funcs.get_func(f["ea"]).start_ea == f["ea"]
           and ida_funcs.get_func(f["ea"]).end_ea == f["fn_end"] and uname(f["ea"]) == f["name"] for f in x["funcs"]):
        return "fresh"
    if any(ida_funcs.get_func(a) for a in range(lo, hi)):
        return "mismatch"
    wlo, whi = x["words"]
    for a in list(range(wlo, whi, 2)) + list(range(olo, phi, 2)):
        fl = ida_bytes.get_flags(a)
        if not (ida_bytes.is_data(fl) and ida_bytes.get_item_size(a) == 2):
            return "mismatch"
    if any(ida_bytes.is_code(ida_bytes.get_flags(a)) for a in range(lo, hi)) or tf_outside(x):
        return "mismatch"
    return "applied"


def tablefix(x):
    lo, hi = x["clear"]
    olo, ohi, base = x["offwords"]
    plo, phi = x["plain"]
    for f in x["funcs"]:
        must(ida_funcs.del_func(f["ea"]), "del_func 0x%X" % f["ea"])
        ida_name.set_name(f["ea"], "", ida_name.SN_NOWARN)
    ida_bytes.del_items(olo, ida_bytes.DELIT_SIMPLE, phi - olo)
    for a in range(olo, ohi, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
        must(idc.op_plain_offset(a, 0, base), "offset 0x%X" % a)
    for a in range(plo, phi, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
    ida_bytes.del_items(lo, ida_bytes.DELIT_SIMPLE, hi - lo)
    wlo, whi = x["words"]
    for a in range(wlo, whi, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
    for a in range(whi, hi):
        must(ida_bytes.create_byte(a, 1), "create_byte 0x%X" % a)
    for frm, t in tf_outside(x):
        ida_xref.del_cref(frm, t, 0)
    left = tf_outside(x)
    must(not left, "references into the table remain %s" % [(hex(a), hex(b), ) for a, b in left][:6])
    must(tf_state(x) == "applied", "table fix 0x%X" % lo)


def text_segments(x):
    lo, hi = x["text"]
    keep = set(x["keep"])
    bs = ida_bytes.get_bytes(lo, hi - lo)
    out, a = [], lo
    while a < hi:
        b = bs[a - lo]
        if a in keep or b < 0x20:
            out.append((a, 1, "b"))
            a += 1
            continue
        e = a
        while e < hi and bs[e - lo] >= 0x20 and e not in keep:
            e += 1
        if e < hi and bs[e - lo] == 0 and e not in keep:
            e += 1
        out.append((a, e - a, "s"))
        a = e
    return out


def xt_state(x):
    lo, hi = x["text"]
    tlo, thi, base = x["table"]
    if sha(lo, hi) != x["text_sha256"] or sha(tlo, thi) != x["table_sha256"]:
        return "mismatch"
    if any(ida_funcs.get_func(a) for a in range(tlo, hi)):
        return "mismatch"
    ok = all(ida_bytes.is_off0(ida_bytes.get_flags(a)) for a in range(tlo, thi, 2))
    for a, n, k in text_segments(x):
        fl = ida_bytes.get_flags(a)
        ok = ok and ida_bytes.get_item_size(a) == n and ida_bytes.is_head(fl) and (
            ida_bytes.is_strlit(fl) if k == "s" else ida_bytes.is_byte(fl))
    return "applied" if ok else "fresh"


def textfix(x):
    lo, hi = x["text"]
    tlo, thi, base = x["table"]
    for a in range(tlo, thi, 2):
        must(idc.op_plain_offset(a, 0, base), "offset 0x%X" % a)
    for a, n, k in text_segments(x):
        ida_bytes.del_items(a, ida_bytes.DELIT_SIMPLE, n)
        if k == "b":
            must(ida_bytes.create_byte(a, 1), "create_byte 0x%X" % a)
        else:
            must(ida_bytes.create_strlit(a, n, ida_nalt.STRTYPE_C), "create_strlit 0x%X" % a)
    must(xt_state(x) == "applied", "text fix 0x%X" % lo)


def trim_state(x):
    ea, oe, ne, wh, ch = x["ea"], x["old_end"], x["end"], x["words_hi"], x["clear_hi"]
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea or uname(ea) != x["name"] or sha(ea, ch) != x["sha256"]:
        return "mismatch"
    if f.end_ea == oe and chunks(ea) == [[ea, oe]]:
        return "fresh"
    if f.end_ea == ne and chunks(ea) == [[ea, ne]]:
        for a in range(ne, wh, 2):
            if not (ida_bytes.is_data(ida_bytes.get_flags(a)) and ida_bytes.get_item_size(a) == 2):
                return "mismatch"
        return "applied"
    return "mismatch"


def trim(x):
    ea, oe, ne, wh, ch = x["ea"], x["old_end"], x["end"], x["words_hi"], x["clear_hi"]
    must((wh - ne) % 2 == 0, "word run of 0x%X" % ea)
    a, orig = ne, set()
    while a < ch:
        h = ida_bytes.get_item_head(a)
        if ida_bytes.is_code(ida_bytes.get_flags(h)):
            orig.add(h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    for h in sorted(orig):
        bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (ne <= r.frm < ch) and h != wh]
        must(not bad, "jump/call into trimmed head 0x%X from %s" % (h, [hex(b) for b in bad][:5]))
    must(ida_funcs.set_func_end(ea, ne), "set_func_end 0x%X" % ea)
    ida_bytes.del_items(ne, ida_bytes.DELIT_SIMPLE, ch - ne)
    for a in range(ne, wh, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
    must(trim_state(x) == "applied", "trim of 0x%X" % ea)


def ab_state(x):
    ea, fr, be, ne = x["ea"], x["frag"], x["before_end"], x["end"]
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea or sha(be, ne) != x["sha256"]:
        return "mismatch"
    g = ida_funcs.get_func(fr)
    if (f.end_ea >= ne and not (g and g.start_ea == fr)
            and all(any(c[0] <= lo and hi <= c[1] for c in chunks(ea)) for lo, hi in x["chunks_after"])):   # a later glue may merge chunks
        return "applied"
    if (f.end_ea == be and chunks(ea) == x["chunks_before"] and g and g.start_ea == fr and uname(fr) == x["frag_name"]
            and chunks(fr) == x["frag_chunks"] and sha(fr, x["frag_end"]) == x["frag_sha256"]):
        return "fresh"
    return "mismatch"


def absorb(x):
    ea, fr, be, ne = x["ea"], x["frag"], x["before_end"], x["end"]
    clo, chi = x["clear"]
    far = is_far(ea)
    must(not is_far(fr) or far, "far flag of 0x%X" % fr)
    a, orig = clo, set()
    while a < chi:
        h = ida_bytes.get_item_head(a)
        if ida_bytes.is_code(ida_bytes.get_flags(h)):
            orig.add(h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    must(ida_funcs.del_func(fr), "del_func 0x%X" % fr)
    ida_name.set_name(fr, "", ida_name.SN_NOWARN)
    ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, chi - clo)
    a = clo
    while a < chi:
        n = ida_ua.create_insn(a)
        must(n > 0, "create_insn 0x%X" % a)
        a += n
    must(a == chi, "redecode of 0x%X..0x%X ends at 0x%X" % (clo, chi, a))
    lost = sorted(h for h in orig if not (ida_bytes.is_code(ida_bytes.get_flags(h)) and ida_bytes.get_item_head(h) == h))
    for h in lost:
        bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (clo <= r.frm < chi)]
        must(not bad, "jump/call into stale head 0x%X from %s" % (h, [hex(b) for b in bad]))
    f = ida_funcs.get_func(ea)
    for lo, hi in chunks(ea)[1:]:
        if be <= lo < ne:
            must(ida_funcs.remove_func_tail(ida_funcs.get_func(ea), lo), "remove_func_tail 0x%X" % lo)
    must(ida_funcs.set_func_end(ea, ne), "set_func_end 0x%X -> 0x%X" % (ea, ne))
    must(is_far(ea) == far, "far flag of 0x%X" % ea)
    if x["chunks_after"] is None:
        x["chunks_after"] = chunks(ea)
    must(ab_state(x) == "applied", "absorb into 0x%X (state %s, chunks %s)" % (ea, ab_state(x), chunks(ea)))


def df_items(x):
    lo, hi, k = x["lo"], x["hi"], x["kind"]
    if k == "b":
        return [(a, 1) for a in range(lo, hi)]
    n = (hi - lo) // 2
    return [(lo + 2 * i, 2) for i in range(n)] + ([(hi - 1, 1)] if (hi - lo) % 2 else [])


def df_state(x):
    lo, hi = x["lo"], x["hi"]
    if sha(lo, hi) != x["sha256"] or any(ida_funcs.get_func(a) for a in range(lo, hi)):
        return "mismatch"
    if all(ida_bytes.is_data(ida_bytes.get_flags(a)) and ida_bytes.get_item_size(a) == n for a, n in df_items(x)):
        return "applied"
    return "fresh"


def datafix(x):
    lo, hi = x["lo"], x["hi"]
    must(ida_bytes.get_item_head(lo) == lo and ida_bytes.get_item_head(hi) == hi, "range 0x%X..0x%X cuts an item" % (lo, hi))
    bad = [(hex(r.frm), hex(t)) for t in range(lo, hi) for r in idautils.XrefsTo(t, 0)
           if r.type in (16, 17, 18, 19) and not (lo <= r.frm < hi)]
    must(not bad, "jump/call into data fix 0x%X from %s" % (lo, bad[:5]))
    ida_bytes.del_items(lo, ida_bytes.DELIT_SIMPLE, hi - lo)
    for a, n in df_items(x):
        must(ida_bytes.create_word(a, 2) if n == 2 else ida_bytes.create_byte(a, 1), "create data 0x%X" % a)
    must(df_state(x) == "applied", "data fix 0x%X" % lo)


def gl_state(x):
    ea = x["ea"]
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea:
        return "mismatch"
    if chunks(ea) == x["chunks_after"] and f.end_ea == x["end"] and not any(ida_funcs.get_func(g) and ida_funcs.get_func(g).start_ea == g
                                                                          for g in x["frags"]):
        return "applied"
    if (chunks(ea) == x["chunks_before"] and f.end_ea == x["before_end"]
            and all(not any(ida_funcs.get_func(a) and ida_funcs.get_func(a).start_ea not in x["frags"] for a in range(lo, hi))
                    and sha(lo, hi) == h for (lo, hi), h in zip(x["runs"], x["runs_sha256"]))
            and all(ida_funcs.get_func(g) and ida_funcs.get_func(g).start_ea == g and uname(g) == x["frag_names"][str(g)]
                    for g in x["frags"])):
        return "fresh"
    return "mismatch"


def glue(x):
    ea = x["ea"]
    runs = [list(r) for r in x["runs"]]
    orig = set()
    for g in x["frags"]:
        must(ida_funcs.del_func(g), "del_func 0x%X" % g)
        ida_name.set_name(g, "", ida_name.SN_NOWARN)
    for lo, hi in runs:
        a = lo
        while a < hi:
            h = ida_bytes.get_item_head(a)
            if ida_bytes.is_code(ida_bytes.get_flags(h)):
                orig.add(h)
            a = h + max(ida_bytes.get_item_size(h), 1)
        ida_bytes.del_items(lo, ida_bytes.DELIT_SIMPLE, hi - lo)
    for sd in x["seeds"]:
        rlo, rhi = next((lo, hi) for lo, hi in runs if lo <= sd < hi)
        descend(sd, rlo, rhi, set())
    for h in sorted(orig):
        if not (ida_bytes.is_code(ida_bytes.get_flags(h)) and ida_bytes.get_item_head(h) == h):
            bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not any(lo <= r.frm < hi for lo, hi in runs)]
            must(not bad, "jump/call into stale head 0x%X from %s" % (h, [hex(b) for b in bad]))
    for lo, hi in runs:
        a = lo
        while a < hi:
            must(ida_bytes.is_code(ida_bytes.get_flags(a)), "non-code head 0x%X in glue run 0x%X" % (a, lo))
            a += ida_bytes.get_item_size(a)
        must(a == hi, "glue run 0x%X..0x%X ends at 0x%X" % (lo, hi, a))
        must(ida_funcs.append_func_tail(ida_funcs.get_func(ea), lo, hi), "append_func_tail 0x%X 0x%X..0x%X" % (ea, lo, hi))
    if x["chunks_after"] is None:
        f = ida_funcs.get_func(ea)
        x["end"], x["chunks_after"] = f.end_ea, chunks(ea)
        x["sha256"] = sha(x["before_end"], x["end"])
    must(gl_state(x) == "applied", "glue of 0x%X (state %s, chunks %s)" % (ea, gl_state(x), chunks(ea)))


def fix_descend(seed, lo, hi, made):
    """Like descend but pre-clears min(8, hi-ea) bytes before create_insn to handle
    long prefix instructions while NOT overwriting bytes beyond the valid range."""
    todo = [seed]
    while todo:
        ea = todo.pop()
        while lo <= ea < hi:
            fl = ida_bytes.get_flags(ea)
            if ida_bytes.is_code(fl) and ida_bytes.get_item_head(ea) == ea:
                if ea in made:
                    break
            else:
                ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, min(8, hi - ea))
                if ida_ua.create_insn(ea) <= 0:
                    raise RuntimeError("cannot decode 0x%X" % ea)
            made.add(ea)
            m = idc.print_insn_mnem(ea)
            if m in RETS:
                break
            if m.startswith("j") or m.startswith("loop"):
                for x in idautils.XrefsFrom(ea, 0):
                    if x.type in (18, 19) and lo <= x.to < hi:
                        todo.append(x.to)
                if m == "jmp":
                    break
            ea += ida_bytes.get_item_size(ea)


def fd_state(x):
    """State of a FIX_DECODE entry: 'applied' if t is a code head; 'fresh' if t is not a code head;
    'applied' (treated as done) if the function doesn't exist at fn_ea or bytes changed."""
    fn_ea, head, t = x["fn_ea"], x["head"], x["t"]
    if ida_bytes.is_code(ida_bytes.get_flags(t)) and ida_bytes.get_item_head(t) == t:
        return "applied"
    f = ida_funcs.get_func(fn_ea)
    if f and f.start_ea == fn_ea and sha(head, t) == x["head_sha256"]:
        return "fresh"
    # Function moved, no longer exists at fn_ea, or bytes changed: treat as already applied
    return "applied"


def fix_decode(x):
    """Clear the misdecoded instruction at [head, min(head+N, fn_end)) and re-decode from t=head+1.
    Uses fix_descend with per-step clearing. Clamped to fn_end to avoid clearing adjacent functions."""
    fn_ea, head, t, insn_size = x["fn_ea"], x["head"], x["t"], x["insn_size"]
    f = ida_funcs.get_func(fn_ea)
    if not f or f.start_ea != fn_ea:
        if fd_state(x) == "applied":
            return
        must(False, "fix_decode 0x%X: fn 0x%X no longer exists or moved" % (head, fn_ea))
    # Clamp clear range to fn_end to avoid clearing bytes in adjacent functions
    clear_len = max(insn_size, 1) + 7
    clear_to = min(head + clear_len, f.end_ea)
    ida_bytes.del_items(head, ida_bytes.DELIT_SIMPLE, clear_to - head)
    fix_descend(t, t, f.end_ea, set())
    must(fd_state(x) == "applied", "fix_decode 0x%X t=0x%X" % (head, t))
    must(fd_state(x) == "applied", "fix_decode 0x%X t=0x%X" % (head, t))


def sp_state(x):
    """State of a split: 'applied' if owner is [ea,at) and a function starts at `at`;
    'fresh' if owner is still [ea,end); 'mismatch' otherwise.  Both halves are
    sha256-pinned so an unexpected byte change is caught as mismatch.
    Note: the tail [at,end) may have been further split by a later batch, so we
    only require that some function starts at `at` (not that it ends at `end`).
    Also: IDA auto-analysis on IDB load may shorten fo.end_ea slightly below `at`;
    if the split happened (function at `at` exists) we still return "applied"."""
    ea, at, end = x["ea"], x["at"], x["end"]
    if sha(ea, at) != x["sha256_head"] or sha(at, end) != x["sha256_tail"]:
        return "mismatch"
    fo = ida_funcs.get_func(ea)
    if not fo or fo.start_ea != ea:
        return "mismatch"
    if fo.end_ea <= at and chunks(ea) is not None and all(c[1] <= at for c in chunks(ea)):
        # Owner ends at or before `at`; check if a function starts at `at`
        ft = ida_funcs.get_func(at)
        if ft and ft.start_ea == at:
            return "applied"
    if fo.end_ea == end and (chunks(ea) == [[ea, end]] or ea in SPLIT_TAILS):
        return "fresh"
    return "mismatch"


def split_fn(x):
    """Split the owner function [ea, end) at `at`: owner becomes [ea, at),
    a new unnamed function [at, end) is registered with the same far flag."""
    ea, at, end, far = x["ea"], x["at"], x["end"], x["far"]
    if at not in SPLIT_RELAX:
        for xr in idautils.XrefsTo(at, 0):
            if not xr.iscode:
                continue
            f2 = ida_funcs.get_func(xr.frm)
            if f2 and f2.start_ea == ea:
                m = idc.print_insn_mnem(xr.frm)
                must(m in ("call", "callf"), "non-call inner xref to 0x%X from 0x%X (%s)" % (at, xr.frm, m))
    must(ida_funcs.set_func_end(ea, at), "set_func_end 0x%X -> 0x%X" % (ea, at))
    must(ida_funcs.add_func(at, end), "add_func 0x%X..0x%X" % (at, end))
    if far:
        f = ida_funcs.get_func(at)
        f.flags |= ida_funcs.FUNC_FAR
        must(ida_funcs.update_func(f), "update_func far 0x%X" % at)
    must(sp_state(x) == "applied", "split of 0x%X at 0x%X" % (ea, at))


def add_all(items, exts=(), rebs=(), rms=(), tfs=(), xts=(), trs=(), abs_=(), dfs=(), gls=(), spls=(), fds=()):
    before = snapshot()
    for x in dfs:
        if df_state(x) != "applied":
            datafix(x)
    for x in abs_:
        if ab_state(x) != "applied":
            absorb(x)
    for x in gls:
        if gl_state(x) != "applied":
            glue(x)
    for x in trs:
        if trim_state(x) != "applied":
            trim(x)
    for x in xts:
        if xt_state(x) != "applied":
            textfix(x)
    for x in tfs:
        if tf_state(x) != "applied":
            tablefix(x)
    for x in rms:
        if rm_state(x) != "applied":
            remove(x)
    for x in exts:
        if ext_state(x) == "applied":
            continue
        extend(x)
    for x in spls:
        if sp_state(x) != "applied":
            split_fn(x)
    for x in fds:
        if fd_state(x) != "applied":
            try:
                fix_decode(x)
            except Exception as e:
                log.append("SKIP fix_decode 0x%X t=0x%X: %s" % (x["head"], x["t"], str(e)[:80]))
    for x in rebs:
        if rb_state(x) != "applied":
            rebase(x)
    for it in items:
        if state(it) == "applied":
            continue
        if "seeds" in it:
            decode_menu(it)
        must(ida_funcs.add_func(it["ea"], it["end"]), "add_func 0x%X..0x%X" % (it["ea"], it["end"]))
        f = ida_funcs.get_func(it["ea"])
        must(f.start_ea == it["ea"] and f.end_ea == it["end"], "span of 0x%X" % it["ea"])
        for lo, hi in it.get("tails", []):
            must(ida_funcs.append_func_tail(f, lo, hi), "append_func_tail 0x%X 0x%X..0x%X" % (it["ea"], lo, hi))
            f = ida_funcs.get_func(it["ea"])
        must(chunks(it["ea"]) == sorted(regions(it)), "chunks of 0x%X" % it["ea"])
        if "clear" in it or "clears" in it:
            for lo, hi in regions(it):
                must(terminated(lo, hi), "0x%X..0x%X does not end in a terminator" % (lo, hi))
            it["last"] = idc.generate_disasm_line(idc.prev_head(it["end"], it["ea"]), 0)
        if "seeds" in it:
            for lo, hi in regions(it):
                a = lo
                while a < hi:
                    if a in it.get("pad", []):
                        a += 1
                        continue
                    must(ida_bytes.is_code(ida_bytes.get_flags(a)), "non-code head 0x%X in 0x%X" % (a, it["ea"]))
                    a += ida_bytes.get_item_size(a)
    after = snapshot()
    new = {it["ea"] for it in items} | {x["ea"] for x in rebs} | {x["at"] for x in spls}
    fd_eas = {x["fn_ea"] for x in fds}
    changed = sorted(ea for ea in set(before) if before[ea] != after.get(ea))
    changed_non_fd = [ea for ea in changed if ea not in fd_eas]
    must(set(changed_non_fd) <= {x["ea"] for x in exts} | {x["old_ea"] for x in rebs} | {x["ea"] for x in rms} | {f["ea"] for x in tfs for f in x["funcs"]} | {x["ea"] for x in trs} | {x["ea"] for x in abs_} | {x["frag"] for x in abs_} | {x["ea"] for x in gls} | {g for x in gls for g in x["frags"]} | {x["ea"] for x in spls},
         "unplanned existing functions changed %s" % [hex(c) for c in changed_non_fd[:10]])
    for x in exts:
        must(after[x["ea"]][0] == before[x["ea"]][0], "name of 0x%X changed" % x["ea"])
    for x in rebs:
        must(x["old_ea"] not in after and (x["name"] is None or after[x["ea"]][0] == x["name"]), "rebase of 0x%X" % x["old_ea"])
    must(not any(x["frag"] in after for x in abs_), "absorbed function still present")
    must(not any(x["ea"] in after for x in rms) and not any(f["ea"] in after for x in tfs for f in x["funcs"]),
         "removed function still present")
    must(set(after) - set(before) <= new, "unplanned new functions %s" % [hex(c) for c in sorted(set(after) - set(before) - new)][:10])
    log.append("functions added: %s; extended: %s; rebased: %s; table %d -> %d, other existing functions unchanged" % (
        ["0x%X..0x%X" % (it["ea"], it["end"]) for it in items],
        ["0x%X -> 0x%X" % (x["ea"], x["end"]) for x in exts],
        ["0x%X -> 0x%X %s" % (x["old_ea"], x["ea"], x["name"]) for x in rebs], len(before), len(after)))
    must(not any(g in after for x in gls for g in x["frags"]), "glued fragment function still present")
    if gls:
        log.append("glued: %s" % ["0x%X + %s" % (x["ea"], ["0x%X..0x%X" % tuple(r) for r in x["runs"]]) for x in gls])
    if spls:
        log.append("split: %s" % ["0x%X at 0x%X (-> 0x%X..0x%X + 0x%X..0x%X)" % (x["ea"], x["at"], x["ea"], x["at"], x["at"], x["end"]) for x in spls])
    if fds:
        log.append("fix_decode: %s" % ["0x%X+1 in fn 0x%X" % (x["head"], x["fn_ea"]) for x in fds])
    if dfs:
        log.append("data fix: %s" % ["0x%X..0x%X %s" % (x["lo"], x["hi"], x["kind"]) for x in dfs])
    if abs_:
        log.append("absorbed: %s" % ["0x%X into 0x%X (end 0x%X)" % (x["frag"], x["ea"], x["end"]) for x in abs_])
    if trs:
        log.append("trimmed: %s" % ["0x%X end 0x%X -> 0x%X" % (x["ea"], x["old_end"], x["end"]) for x in trs])
    if xts:
        log.append("text fix: %s" % ["0x%X..0x%X (%d items)" % (x["text"][0], x["text"][1], len(text_segments(x))) for x in xts])
    if tfs:
        log.append("table fix: %s" % ["0x%X..0x%X (%d functions deleted)" % (x["clear"][0], x["clear"][1], len(x["funcs"])) for x in tfs])
    if rms:
        log.append("removed (word tables): %s" % ["0x%X..0x%X %s" % (x["ea"], x["end"], x["name"]) for x in rms])


def main():
    if PLAN:
        items = []
        old = {x["ea"]: x for x in json.loads(MANIFEST.read_text())["add_funcs"]} if MANIFEST.exists() else {}
        for ea, end in ADD:
            if state({"ea": ea, "end": end, "sha256": ""}) == "applied" and ea in old:
                items.append(old[ea])
                continue
            tails = TAILS[ea][0] if ea in TAILS else []
            freed = {a for (tea, toe, tne, twh, tch) in TRIM for a in range(tne, toe)}
            must(not any(ida_funcs.get_func(a) for lo, hi in [(ea, end)] + tails for a in range(lo, hi) if a not in freed), "0x%X..0x%X already owned" % (ea, end))
            must(ea in ADD_CLEAR or ea in FALL or terminated(ea, end), "0x%X..0x%X does not end in a terminator" % (ea, end))
            it = {"ea": ea, "end": end, "last": None, "callers": callers(ea), "sha256": sha(ea, end)}
            if ea in ADD_CLEAR:
                it["clear"], it["seeds"] = list(ADD_CLEAR[ea][:2]), ADD_CLEAR[ea][2]
                if ea in ADD_WORDS:
                    it["words"] = list(ADD_WORDS[ea])
            if ea in TAILS:
                it["tails"], it["tails_sha256"] = [list(t) for t in tails], [sha(lo, hi) for lo, hi in tails]
                it["clears"], it["seeds"], it["pad"] = [list(c) for c in TAILS[ea][1]], TAILS[ea][2], TAILS[ea][3]
                del it["clear"]
            items.append(it)
        for base, cf, end in MENUS:
            if state({"ea": base, "end": end, "sha256": ""}) == "applied" and base in old:
                items.append(old[base])
                continue
            must(not any(ida_funcs.get_func(a) for a in range(base, end)), "0x%X..0x%X already owned" % (base, end))
            must(terminated(base, end), "0x%X..0x%X does not end in a terminator" % (base, end))
            items.append({"ea": base, "end": end, "last": idc.generate_disasm_line(idc.prev_head(end, base), 0),
                          "callers": sorted(x.frm for x in idautils.XrefsTo(base, 0) if x.iscode),
                          "redecode": cf, "seeds": menu_seeds(base, cf), "sha256": sha(base, end)})
        oldx = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("extend_funcs", [])} if MANIFEST.exists() else {}
        exts = []
        for ea, end in EXTEND:
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea, "0x%X is not a function start" % ea)
            if ea in oldx:
                # always re-use the existing manifest entry: a later SPLIT may have changed
                # f.end_ea without undoing the extension (bytes of the extended run unchanged)
                exts.append(norm(oldx[ea]))
                continue
            must(terminated(f.end_ea, end), "0x%X..0x%X does not end in a terminator" % (f.end_ea, end))
            exts.append(norm({"ea": ea, "before_end": f.end_ea, "end": end, "sha256": sha(f.end_ea, end)}))
        for ea, lo, hi in EXTEND_RUNS:
            if ea in oldx and "run" in oldx[ea]:
                exts.append(oldx[ea])
                continue
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea, "0x%X is not a function start" % ea)
            must(not any(ida_funcs.get_func(a) for a in range(lo, hi)), "run 0x%X..0x%X already owned" % (lo, hi))
            must(terminated(lo, hi) or lo in DOS_EXIT, "run 0x%X..0x%X not terminated" % (lo, hi))
            exts.append({"ea": ea, "run": [lo, hi], "run_sha256": sha(lo, hi), "before_end": f.end_ea,
                         "chunks_before": chunks(ea), "end": None, "sha256": None, "chunks_after": None})
        oldr = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("rebase_funcs", [])} if MANIFEST.exists() else {}
        rebs = []
        for old, new, end, clo, ds, *chi in REBASE:
            if new in oldr:
                rebs.append(oldr[new])
                continue
            f = ida_funcs.get_func(old)
            must(f and f.start_ea == old and f.end_ea == end, "0x%X is not the planned function" % old)
            rebs.append({"ea": new, "old_ea": old, "end": end, "clear_lo": clo, "ds": ds, "name": uname(old),
                         "far": is_far(old), "sha256": sha(new, end), "old_sha256": sha(old, end),
                         "prefix_sha256": sha(new, old) if old > new else "", "lost_heads": None, **({"clear_hi": chi[0]} if chi else {})})
        oldm = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("remove_funcs", [])} if MANIFEST.exists() else {}
        rms = []
        for ea, fe, end in REMOVE:
            if ea in oldm:
                rms.append(oldm[ea])
                continue
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea and f.end_ea == fe, "0x%X is not the planned function" % ea)
            rms.append({"ea": ea, "fn_end": fe, "end": end, "name": uname(ea), "far": is_far(ea),
                        "fn_sha256": sha(ea, fe), "data_sha256": sha(ea, end)})
        oldt = {x["clear"][0]: x for x in json.loads(MANIFEST.read_text()).get("table_fix", [])} if MANIFEST.exists() else {}
        tfs = []
        for t in TABLEFIX:
            if t["clear"][0] in oldt:
                tfs.append(oldt[t["clear"][0]])
                continue
            fl = []
            for ea, fe in t["funcs"]:
                f = ida_funcs.get_func(ea)
                must(f and f.start_ea == ea and f.end_ea == fe, "0x%X is not the planned function" % ea)
                fl.append({"ea": ea, "fn_end": fe, "end": t["words"][1], "name": uname(ea), "far": is_far(ea),
                           "fn_sha256": sha(ea, fe)})
            tfs.append({"funcs": fl, "clear": list(t["clear"]), "clear_sha256": sha(*t["clear"]), "words": list(t["words"]),
                        "offwords": list(t["offwords"]), "offwords_sha256": sha(t["offwords"][0], t["offwords"][1]),
                        "plain": list(t["plain"]), "plain_sha256": sha(*t["plain"])})
        oldx2 = {x["text"][0]: x for x in json.loads(MANIFEST.read_text()).get("text_fix", [])} if MANIFEST.exists() else {}
        xts = []
        for t in TEXTFIX:
            if t["text"][0] in oldx2:
                xts.append(oldx2[t["text"][0]])
                continue
            xts.append({"table": list(t["table"]), "table_sha256": sha(t["table"][0], t["table"][1]), "text": list(t["text"]),
                        "text_sha256": sha(*t["text"]), "keep": list(t["keep"])})
        oldtr = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("trim_funcs", [])} if MANIFEST.exists() else {}
        trs = []
        for ea, oe, ne, wh, ch in TRIM:
            if ea in oldtr:
                trs.append(oldtr[ea])
                continue
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea and f.end_ea == oe, "0x%X is not the planned function" % ea)
            trs.append({"ea": ea, "old_end": oe, "end": ne, "words_hi": wh, "clear_hi": ch, "name": uname(ea), "far": is_far(ea),
                        "sha256": sha(ea, ch), "kept_sha256": sha(ea, ne)})
        olda = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("absorb_funcs", [])} if MANIFEST.exists() else {}
        abs_ = []
        for ea, fr, clo, chi, ne in ABSORB:
            if ea in olda:
                abs_.append(olda[ea])
                continue
            f, g = ida_funcs.get_func(ea), ida_funcs.get_func(fr)
            must(f and f.start_ea == ea and g and g.start_ea == fr, "0x%X / 0x%X are not the planned functions" % (ea, fr))
            abs_.append({"ea": ea, "frag": fr, "frag_end": g.end_ea, "frag_name": uname(fr), "frag_far": is_far(fr),
                         "frag_chunks": chunks(fr), "frag_sha256": sha(fr, g.end_ea), "clear": [clo, chi],
                         "before_end": f.end_ea, "end": ne, "sha256": sha(f.end_ea, ne), "chunks_before": chunks(ea),
                         "chunks_after": None})
        oldg = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("glue_funcs", [])} if MANIFEST.exists() else {}
        gls = []
        for ea, runs, frags in GLUE:
            if ea in oldg:
                gls.append(oldg[ea])
                continue
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea, "0x%X is not a function start" % ea)
            gls.append({"ea": ea, "runs": [[lo, hi] for lo, hi, sd in runs], "seeds": [q for lo, hi, sd in runs for q in sd],
                        "runs_sha256": [sha(lo, hi) for lo, hi, sd in runs], "frags": frags,
                        "frag_names": {str(g): uname(g) for g in frags},
                        "frag_ends": [ida_funcs.get_func(g).end_ea for g in frags],
                        "frag_sha256": {str(g): sha(g, ida_funcs.get_func(g).end_ea) for g in frags}, "before_end": f.end_ea, "chunks_before": chunks(ea),
                        "end": None, "sha256": None, "chunks_after": None})
        oldd = {x["lo"]: x for x in json.loads(MANIFEST.read_text()).get("data_fix", [])} if MANIFEST.exists() else {}
        dfs = []
        for lo, hi, k in DATAFIX:
            if lo in oldd:
                dfs.append(oldd[lo])
                continue
            must(not any(ida_funcs.get_func(a) for a in range(lo, hi)), "data fix 0x%X..0x%X is owned by a function" % (lo, hi))
            dfs.append({"lo": lo, "hi": hi, "kind": k, "sha256": sha(lo, hi)})
        oldspl = {(x["ea"], x["at"]): x for x in json.loads(MANIFEST.read_text()).get("split_funcs", [])} if MANIFEST.exists() else {}
        spls = []
        for ea, at in SPLIT:
            if (ea, at) in oldspl:
                spls.append(oldspl[(ea, at)])
                continue
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea, "0x%X is not a function start (split at 0x%X)" % (ea, at))
            must(f.end_ea > at > ea, "0x%X: at=0x%X not inside [ea, end=0x%X)" % (ea, at, f.end_ea))
            must(chunks(ea) == [[ea, f.end_ea]] or ea in SPLIT_TAILS, "0x%X has tail chunks, cannot split" % ea)
            end = f.end_ea
            spls.append({"ea": ea, "at": at, "end": end, "name": uname(ea) or "", "far": is_far(ea),
                         "sha256_head": sha(ea, at), "sha256_tail": sha(at, end)})
        oldfd = {(x["fn_ea"], x["head"]): x for x in json.loads(MANIFEST.read_text()).get("fix_decode_funcs", [])} if MANIFEST.exists() else {}
        fds = []
        for fn_ea, head in FIX_DECODE:
            t = head + 1  # all off==1 cases
            if (fn_ea, head) in oldfd:
                fds.append(oldfd[(fn_ea, head)])
                continue
            # If t is already a code head, the misdecode was fixed by a prior operation
            if ida_bytes.is_code(ida_bytes.get_flags(t)) and ida_bytes.get_item_head(t) == t:
                insn_size = ida_bytes.get_item_size(head)  # may be 1 (already cleared)
                fds.append({"fn_ea": fn_ea, "head": head, "t": t, "insn_size": max(1, insn_size),
                            "head_sha256": sha(head, t)})
                continue
            f = ida_funcs.get_func(fn_ea)
            must(f and f.start_ea == fn_ea, "0x%X is not a function start (fix_decode head=0x%X)" % (fn_ea, head))
            must(f.start_ea <= head < f.end_ea, "head 0x%X not inside fn 0x%X" % (head, fn_ea))
            insn_size = ida_bytes.get_item_size(head)
            # insn_size may be 1 if head was already cleared by a prior operation
            fds.append({"fn_ea": fn_ea, "head": head, "t": t, "insn_size": insn_size,
                        "head_sha256": sha(head, t)})
        add_all(items, exts, rebs, rms, tfs, xts, trs, abs_, dfs, gls, spls)  # fds verified in apply mode
        MANIFEST.write_bytes(json.dumps({"finding": 174, "step": "S1c-4..P8 (findings 145-174): P8 secondary entries documented",
                                        "extend_funcs": exts, "rebase_funcs": rebs, "remove_funcs": rms, "table_fix": tfs, "text_fix": xts, "trim_funcs": trs, "absorb_funcs": abs_, "data_fix": dfs, "glue_funcs": gls, "split_funcs": spls, "fix_decode_funcs": fds, "add_funcs": items},
                                       indent=1).replace("\n", "\r\n").encode("utf-8"))
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        log.append("plan written: %s (not saved)" % MANIFEST.name)
        return
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    exts = [norm(x) for x in doc.get("extend_funcs", [])]
    rebs = doc.get("rebase_funcs", [])
    rms = doc.get("remove_funcs", [])
    tfs = doc.get("table_fix", [])
    xts = doc.get("text_fix", [])
    trs = doc.get("trim_funcs", [])
    abs_ = doc.get("absorb_funcs", [])
    dfs = doc.get("data_fix", [])
    gls = doc.get("glue_funcs", [])
    spls = doc.get("split_funcs", [])
    fds = doc.get("fix_decode_funcs", [])
    states = ([state(it) for it in doc["add_funcs"]] + [ext_state(x) for x in exts] + [rb_state(x) for x in rebs]
              + [rm_state(x) for x in rms] + [tf_state(x) for x in tfs] + [xt_state(x) for x in xts] + [trim_state(x) for x in trs]
              + [ab_state(x) for x in abs_] + [df_state(x) for x in dfs] + [gl_state(x) for x in gls] + [sp_state(x) for x in spls]
              + [fd_state(x) for x in fds])
    fresh_trims = [x for x in trs if trim_state(x) == "fresh"]
    for i, it in enumerate(doc["add_funcs"]):
        if states[i] == "mismatch" and any(x["end"] <= it["ea"] < x["old_end"] for x in fresh_trims):
            states[i] = "fresh"
    # REBASE entries whose new_ea falls in a fresh TRIM's freed tail are also valid pre-TRIM
    n_adds_exts = len(doc["add_funcs"]) + len(exts)
    for i, rb in enumerate(rebs):
        si = n_adds_exts + i
        if states[si] == "mismatch" and any(x["end"] <= rb["ea"] < x["old_end"] for x in fresh_trims):
            states[si] = "fresh"
    log.append("manifest: %d entries (add + extend); live: %d fresh, %d applied, %d mismatched" % (
        len(states), states.count("fresh"), states.count("applied"), states.count("mismatch")))
    if all(s == "applied" for s in states):
        log.append("already applied: nothing to do")
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        return
    if "mismatch" in states:
        log.append("ABORT: live IDB does not match the manifest; nothing changed")
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        return
    add_all(doc["add_funcs"], exts, rebs, rms, tfs, xts, trs, abs_, dfs, gls, spls, fds)
    if os.environ.get("OFDRY"):
        ida_loader.set_database_flag(ida_loader.DBFL_KILL)
        log.append("dry run (OFDRY): not saved")
        return
    ida_loader.save_database(idaapi.get_path(idaapi.PATH_TYPE_IDB), 0)
    log.append("database saved")


try:
    main()
except Exception:
    ida_loader.set_database_flag(ida_loader.DBFL_KILL)
    log.append("ERROR (not saved):\n" + traceback.format_exc())
LOG.write_text("\n".join(log))
idaapi.qexit(0)
