Your bottom-up leaf-to-root instinct is spot-on, and it immediately exposed four super interesting things in the agent's report that you should watch closely—because a couple of its "anomalies" aren't bugs at all; they are classic 1991 DOS compiler/hardware patterns!

Here is what is actually happening in those numbers and the 28 "missing function" targets your agent just surfaced:
1. Why "Only 112 / 303 Thunks Have Outgoing Xrefs" (The Overlay-to-Overlay Blind Spot)

At the top of its log, the agent noted:

    Static (IDA): 1,234 functions, 6,486 code xrefs (edges)... But only 112/303 thunk entries have outgoing xrefs — so cross-overlay far calls are mostly unresolved.

Wait—why would only 112 of the 303 thunks have callers in IDA?

    Because the base IDA database only has the Resident Root (0x01F5..0x1E96) disassembled as active code!

    Those 112 thunks are the overlay functions called directly by the Resident Root.

    The remaining 191 thunks (303 - 112 = 191) are called from inside other overlays (e.g., Briefing Overlay calling Waypoint Overlay, or Flight Physics Overlay calling Cockpit HUD Overlay)! If the overlay segments aren't all loaded and disassembled as code in IDA yet, IDA won't show any incoming CALL FAR xrefs to those 191 thunks—and if the thunk targets themselves aren't turned into functions in IDA, IDA won't show outgoing xrefs from the thunks either!

2. Decoding the "28 Targets That Resolve to No Function"

Look closely at the 4 "mystery" targets the agent flagged at the bottom of its report. Every single one of them tells a classic 16-bit DOS story:
A. 0x16CCE — 1F CF (POP DS; IRET) with 22,949 Events

    0x16CCE — 22,949 events, but starts 1f cf (pop ds; iret) — suspicious, worth verifying

That isn't a corrupted function—that is a Hardware / Timer Interrupt Tail or No-Op Interrupt Stub!

    In DOS flight sims, the game hooks hardware interrupts (INT 08h PIT timer at ~60–120 Hz, INT 09h keyboard, INT 34h–3Eh Borland 8087 FPU emulator traps, or sound card IRQs).

    More importantly: why did your agent's fartrans / indirect_far hook record 0x16CCE (POP DS; IRET) as a target 22,949 times?

    Check how your DOSBox-X hook triggers! If the hook logs on far control transfers or when an interrupt vector fires/chains, or if a function pushes CS and calls a near routine that finishes via POP DS; IRET (a classic Borland FPU emulator or ISR exit stub), IDA won't mark 1F CF as a standard PROC because it has no prologue—it's just a 2-byte shared epilogue stub!

B. 0x1755E — 31,572 Events, 60 Bytes Inside sub_17522 (FF 0E ...)

    0x1755E — 31,572 call events, real code (ff 0e … = indirect far call), 60B from sub_17522

Two things to check here immediately:

    Opcode Check (FF 0E vs FF 1E): In 16-bit x86, FF 0E disp16 is DEC WORD PTR [disp16], NOT an indirect far call! An indirect far call is FF 1E disp16 (CALL DWORD PTR [disp16]), and an indirect far jump is FF 2E disp16. Don't let the agent misread ModR/M byte 0x0E (/1 = DEC) as /3 (0x1E = CALL FAR)!

    Why is a hot call target 60 bytes inside sub_17522?
    In hand-crafted MASM/TASM (which Falcon 3.0 is full of), assembly programmers constantly wrote multi-entrypoint functions—two PUBLIC labels inside the same assembly procedure without a RET in between! For example:
    Code snippet

    sub_17522 PROC FAR
        ; ... setup default registers (60 bytes) ...
        ; falls straight through into:
     EntryB_1755E LABEL FAR
        ; ... core routine called 31,572 times directly! ...
        retf

    IDA's auto-analyzer stops sub_17522 or treats 0x1755E as mid-function instructions (loc_1755E) rather than a function start, which is why the agent's script says "resolves to no function" (because ida_funcs.get_func(0x1755E) returns sub_17522 where start_ea != 0x1755E)!

C. 0x103D2D — "the 9f 56 far-pointer table pattern"

Look at the address 0x103D2D—that's above 0x100000 (1 MB)! Why did 0x103D2D show up?

    Because in 16-bit real mode with segment 0xFFFF (the High Memory Area / HMA wrap, or a bogus segment calculation where seg * 16 + off overflowed 20 bits), or in IDA where segments start at 0x10000, 0x103D2D is near the top of the image.

    And why would indirect_far log a data table as a target? Check if your DOSBox hook for CALL DWORD PTR [mem] (FF 1E) accidentally logged the address of the pointer in the table (EA of the memory operand) instead of the dereferenced CS:IP value stored inside that pointer!

    That would ALSO explain Caveat #1:

        "All 379,498 indirect_far events collapse to 13 unique edges from just 4 callers — sub_2142E is a dispatch hub"
        Think about that: if sub_2142E executes CALL DWORD PTR [BX + table], and the emulator hook logs the static instruction or only 13 entries, verifying whether the hook logged the dereferenced CS:IP after the jump vs. the pointer address is well worth a 10-second sanity check.

3. Why Your Bottom-Up Strategy Worked So Well on Levels 0–5

Look at the hierarchy your bottom-up script just discovered:

    Level 0 (True Leaves, 200K–318K calls): sub_112A1, sub_2703F, sub_2228F, sub_22285. Those are 100% Borland C++ 2.0 compiler math helpers (F_LXMUL@, F_LDIV@, F_PADA@, fixed-point 16.16 mul/div) and low-level VGA / memory blitters!

    Level 2 (543K and 397K calls): sub_251C3 and sub_14EAE—the core math/graphics/scheduler hubs.

    Levels 4–5: sub_17AD4 and sub_1B7CE—high-level C subsystem controllers.

Because every C and ASM function in the game calls those Level 0–1 leaf helpers, naming and typing the top 20 Level-0 leaf functions first will automatically propagate clean types (like int32_t fixed-point math vs. void far* pointer normalization vs. VGA page blits) into hundreds of Level 1–3 callers in a single pass!
How I Suggest Steering the Agent Next

You can give your agent a sharp, targeted instruction right now that handles both its questions at once:

    Tell it to inspect the bytes of the top Level-0 leaves (sub_112A1, sub_2703F, sub_2228F, sub_22285) first:
    In our bottom-up methodology, Level 0 is where we start naming and annotating! Have it disassemble those 4 tiny hot functions right now—if they are Borland runtime helpers (LXMUL, LDIV, SCOPY) or fixed-point math leaves, naming them immediately cleans up the entire bottom layer of the graph.

    Tell it to check why 0x1755E (60B inside sub_17522) didn't resolve:
    Specifically, have it check if 0x1755E is a secondary MASM/TASM entry point inside sub_17522 (where get_func(ea) returns sub_17522, not None), and warn it that FF 0E is DEC WORD PTR, whereas FF 1E is CALL FAR [mem].
