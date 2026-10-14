Reversing a massive, hybrid 16-bit DOS flight sim like *Falcon 3.0*—especially with an agentic workflow—requires untangling the structural layers (linker overlays, compression, runtime libraries, and segmented memory) before letting your agents attempt semantic decompilation. If the agents try to reason about raw thunk tables or compressed overlay blocks as standard code, they will hallucinate wildly.

Here is a systematic architecture for breaking down the binary into clean, agent-digestible modules to achieve a fully functional, annotated codebase.

---

### 1. Defeating the `.RTLink` Overlay Manager

Pocket Soft’s `.RTLink` (and `.RTLink/Plus`) was notorious in the early 90s because, unlike Borland’s standard `TLINK` (VROOMM) which uses `INT 3Fh` traps for overlay swapping, `.RTLink` uses a custom, high-performance dynamic overlay manager that supports nested overlays, EMS/XMS caching, and fine-grained module extraction.

* **Locate the Thunk Table:** In an `.RTLink` executable, far calls (`9A xx xx yy yy`) to overlaid functions do not point directly to the target code; they point to a resident **stub/thunk segment** in low memory. Each stub typically loads an overlay ID or table offset into a register (or pushes it onto the stack) and jumps to the central `.RTLink` overlay dispatcher.
* **Map the Overlay Descriptor Table:** Find the central dispatcher routine. It reads a master table (often at the end of the root `MZ` image or the start of the appended overlay area) that maps **Overlay ID $\rightarrow$ File Offset, Compressed/Uncompressed Size, and Relocation Table**.
* **Reconstruct Flat Segments:** Write a custom pre-processing loader script (e.g., in Python or a Ghidra loader extension) that parses the `.RTLink` header, extracts every overlay chunk from the tail of the `.EXE` (or external `.OVL`/`.RTL` files), applies `.RTLink`'s internal segment fixups, and maps each overlay into its own synthetic, non-overlapping 16-bit segment in your disassembler (e.g., `ovr_01:0000`, `ovr_02:0000`).
* **Patch the Thunks for Static Analysis:** Once overlays are mapped to unique virtual segments, rewrite the far calls or patch the thunks in your database to jump directly to the resolved target address in `ovr_XX:YYYY`. This restores the true call graph for your agents.

---

### 2. Unpacking the Embedded PKWARE Data

those "opaque chunks" you are seeing are almost certainly compressed with **PKWARE Data Compression Library (`PKWARE DCL` / `implode`)** rather than standard `.ZIP` Deflate—or `.RTLink`'s built-in overlay compression.

* **Distinguish Code Overlays from Asset Blobs:**
* Check cross-references to file I/O (`INT 21h, AH=3Dh/3Fh/42h`). If the `.RTLink` manager is reading those offsets and running a fast decompression loop before fixing up segments, the linker compressed the code overlays.
* If game functions seek to hard-coded offsets inside `FALCON3.EXE` (or data files) and pass a buffer to a routine with a large switch/table lookup, it is likely **PKWARE DCL (`explode`)**.


* **Signature the `explode()` Routine:** Look for the telltale static tables of PKWARE DCL in the data segment: the **ChBits**, **ChCode**, **LenBits**, **LenCode**, and **ExLenBits** arrays (used for Shannon-Fano / Huffman tree decoding in `explode`).
* **Dynamic Extraction over Static Guessing:** Instead of reversing the decompression algorithm from scratch, hook DOSBox-X's debugger (or `dosbox-staging` with memory dump scripts). Put a breakpoint on the return of the decompression dispatcher or `INT 21h, AH=3Fh`, let the game load the mission/menu, and dump the decompressed buffers directly from RAM. You can also test carving the raw blobs and running them through open-source `blast` (Mark Adler's PKWARE DCL decompressor in `zlib/contrib/blast`) to see if they decompress cleanly.

---

### 3. Stripping Borland C++ 2.0 Runtime (`C0L.OBJ` / `CL.LIB`)

Since the game uses a **far memory model** (almost certainly the **Large** model—multiple code segments, multiple data segments, single default `DGROUP`—or **Huge** for massive terrain/flight arrays), a significant percentage of the root executable is standard Borland runtime boilerplate.

* **Generate Exact FLIRT / Function ID Signatures:** Do not let your agents waste tokens analyzing `printf`, `farmalloc`, or 32-bit `long` division helpers. Grab an archive copy of **Borland C++ 2.0 (1991)**, extract `CL.LIB`, `MATHL.LIB`, and `EMU.LIB` (important for Falcon 3, which heavily used 8087/287/387 FPU instructions and software emulation traps `INT 34h`–`INT 3Eh`), and generate signature files for your disassembler.
* **Anchor at `C0L.ASM`:** The entry point of a BC++ 2.0 binary follows a strict startup sequence in `C0L.OBJ`. Identifying the exact byte offset where `C0L` calls `_main(argc, argv, envp)` immediately gives you:
* The exact segment value of `DGROUP` (`DS`).
* The heap pointers, stack limits, and interrupt vectors hooked by the CRT (`INT 00h` divide-by-zero, `INT 23h` Ctrl-Break).


* **Identify Long/Far Pointer Helpers:** In BC++ 2.0 Large model, 32-bit math and far pointer normalization use internal compiler helpers that take arguments in `DX:AX` and `CX:BX` rather than the stack:
* `N_LXMUL@` / `F_LXMUL@` (32-bit multiply)
* `F_LDIV@` / `F_LMOD@` (32-bit signed divide/modulo)
* `F_PADA@` / `F_PSBA@` (Huge pointer addition/subtraction with segment normalization)
Flagging these immediately turns messy register juggling back into clean `int32_t` arithmetic.



---

### 4. Taming the Far Memory Model & Hand-Crafted ASM

In a Large/Huge model DOS game, the biggest point of failure for automated decompilers and LLM agents is **segment register tracking (`DS`, `ES`)**.

* **Enforce `DGROUP` vs. Far Data Discipline:**
* In Borland C++ 2.0 functions, `DS` is normally assumed to point to `DGROUP` upon entry. Make sure your disassembler's default `DS` register value is locked to the `DGROUP` segment across all C code segments so static globals resolve properly.
* Far data accesses in C will follow the pattern `LES BX, [BP+arg]` or `LDS SI, [DGROUP:global_ptr]` followed by `ES:[BX+offset]`. If `LDS` clobbers `DS`, Borland C++ will push `DS` in the prologue and pop it in the epilogue.


* **Isolating Hand-Crafted Assembly:** Falcon 3's 3D polygon engine, flight physics math, and VGA hardware routines are written in hand-tuned MASM/TASM. Tell your pipeline to classify a function as hand-crafted ASM if it violates Borland C++ 2.0 calling conventions:
* Missing standard stack frame (`PUSH BP` / `MOV BP, SP` / `PUSH SI` / `PUSH DI`).
* Passing arguments in registers (`AX`, `BX`, `CX`, `DX`, `SI`, `DI`) rather than pushing right-to-left on the stack.
* Direct segment arithmetic, self-modifying code (common in fast line/polygon rasterizers), or custom `DS`/`ES` juggling without saving `DS`.
* Direct hardware port I/O (`IN`/`OUT` to `3DAh` VGA status, `3C4h`/`3CEh` Sequencer/Graphics Controller, `40h`–`43h` PIT timer, or `201h` Joystick).


* **Synthesize Pseudo-C Signatures for ASM:** Once an ASM routine is identified, have a specialized agent determine its **register contract** (Inputs, Outputs, Clobbered Registers, and Flags) and apply a custom storage/calling convention signature in the disassembler so C callers decompile cleanly.

---

### 5. Structuring the Agentic Reversing Pipeline

To get **fully functional, annotated code**, avoid asking an agent to reverse the binary top-down. Build a multi-stage, bottom-up DAG (Directed Acyclic Graph) pipeline:

1. **Dynamic Trace Harvesting (Ground Truth):**
Run *Falcon 3.0* inside an instrumented emulator (like a modified DOSBox-X or QEMU/Unicorn script) that logs:
* Every `.RTLink` overlay load (File Offset $\rightarrow$ RAM Segment).
* Every `INT 21h` file open/read (mapping filenames like `F3.DAT` or theater files to the exact functions that parse them).
* Actual runtime values of `DS` and `ES` at the entry of every function call. Feeding ground-truth segment values into your static database eliminates 90% of far-pointer ambiguity.


2. **Call-Graph Leaf-to-Root Traversal:**
Sort the call graph topologically (breaking recursion cycles) and have your agents work strictly **from leaf functions upward**:
* **Pass 1 (Leaf Nodes):** Low-level math (fixed-point 16.16 trig tables, matrix transforms), VGA blitters, string utilities, and file readers. Once an agent names a function (e.g., `FixedMul16_16` or `Matrix3x3_Rotate`) and defines its struct offsets, lock those symbols in the database.
* **Pass 2 (Struct Reconstruction):** Before decompiling mid-level systems (avionics, radar, AI, flight model), have a dedicated agent pass scan all functions that share the same far pointer base and aggregate every `[BX + disp]` access (along with operand sizes: byte, word, dword, or 80-bit `tbyte` float) to synthesize C `struct` definitions.
* **Pass 3 (Subsystem Annotation):** With structs and leaf helpers named, agents working on high-level overlay modules will see semantic calls (`UpdatePitchRoll(&AircraftState, delta_t)`) instead of raw segment:offset math.


3. **Byte-Exact / Behavioral Equivalence Verification:**
To ensure the resulting code is genuinely **functional**:
* **Compile-and-Compare (Decomp.me style):** For the Borland C++ 2.0 modules, spin up a headless toolchain running the actual `BCC.EXE` 2.0 compiler inside a minimal DOS emulator (`dosemu2` or a fast 16-bit CPU emulator wrapper). Have the agent iterate on the C code until `BCC -ml -O` produces matching (or instruction-equivalent) `.OBJ` bytes.
* **Micro-Execution Harness:** For hand-crafted ASM or stubborn C functions, use a 16-bit CPU emulator (like Unicorn Engine in `UC_MODE_16`) to run the original binary's function bytes against randomized/traced register and memory states, and assert that your re-implemented C/ASM function produces identical memory and register side effects.


Dumping `DS` and `ES` on every single modification sounds tempting, but in a 16-bit Large-model DOS game, it will quickly flood your logs and introduce a massive address-randomization problem.

Here is why raw change-logging gets messy in *Falcon 3.0*, and how to structure your segment trace so it becomes clean, deterministic metadata for your agents.

---

### 1. The Two Traps of Raw `DS`/`ES` Logging

* **The `ES` Scratchpad Explosion:** In Borland C++ 2.0's Large memory model (`-ml`), `DS` stays anchored to `DGROUP` almost all the time, while `ES` is treated as a volatile scratch register. Every single time C code dereferences a far pointer, the compiler emits `LES BX, [BP+06h]` followed by `MOV AX, ES:[BX]`. Furthermore, inside tight 3D polygon or flight-math loops, `REP MOVSW` and `LES`/`LDS` instructions fire tens of thousands of times per frame. Logging every `ES` change will generate gigabytes of noise in seconds.
* **Raw Paragraphs Are Meaningless Statically:** If DOS loads the executable at segment `0x1234`, and `farmalloc()` hands out a heap block at `0x45A0`, logging `ES = 0x45A0` at instruction `CS:0105` doesn't immediately help a static disassembler—because `0x45A0` doesn't exist in the static `.EXE` file. Moreover, because `.RTLink` dynamically swaps overlays into a pool of memory segments, the exact numerical value of `CS`, `DS`, or `ES` can change depending on mission load order.

---

### 2. What to Log Instead: Aggregated Instruction Profiles

Instead of writing a chronological trace stream to disk, have your emulator (e.g., a custom hook in DOSBox-X's CPU core) maintain an **in-memory hash map** keyed by the static instruction identity, and dump the aggregated profile when you exit the emulator.

#### Step A: Normalize the Instruction Key (`Overlay_ID:Offset` instead of `CS:IP`)

Before recording anything at `CS:IP`, translate the runtime `CS` into either:

* `Root_Segment_Index : IP` (by subtracting the DOS `PSP` + load segment base), or
* `RTLink_Overlay_ID : IP` (by tracking which overlay was most recently loaded into that runtime `CS` paragraph).

#### Step B: Classify the Segment Value into a "Symbolic Origin"

Rather than recording the raw 16-bit hex value of `DS` or `ES`, have the emulator classify *what* that segment points to at the moment it is loaded:

| Runtime Segment Range | Symbolic Classification | Static Disassembler / Agent Meaning |
| --- | --- | --- |
| Matches `DGROUP` | `SEG_DGROUP` | Standard static globals / CRT data segment. |
| Inside Root `.EXE` image | `SEG_STATIC + (Seg - Base)` | Fixed far data segment compiled into the binary (e.g., `FAR_DATA`). |
| `0xA000` (or `0xB800`) | `SEG_VGA_VRAM` | Direct hardware screen/buffer access. |
| Inside `.RTLink` buffer pool | `SEG_OVERLAY_ID(n)` | Code/data access into a specific loaded overlay. |
| Inside DOS/Far Heap | `SEG_HEAP_ALLOC(CallSite_CS:IP)` | Dynamic struct/buffer! Tag it with the `CS:IP` of the `farmalloc` or `INT 21h, AH=48h` call that created it. |

Tagging heap segments by their **allocation call-site** is a superpower for your agents. If an instruction at `ovr_12:0450` loads `ES` with a segment that was allocated by `InitFlightModel()` at `ovr_02:0110`, your agent immediately knows *which* subsystem owns the struct being accessed, even across completely separate overlays.

---

### 3. The 3 Hook Points You Actually Need

Instead of hooking `MOV DS/ES`, `POP DS/ES`, `LDS`, and `LES` everywhere, only record state at three boundaries:

1. **Function Entry (`CALL FAR`, `CALL NEAR`, and `.RTLink` Thunk Jumps):**
Record the symbolic `DS` and `ES` values at the target entrypoint.
* *Why:* If 100% of calls to `sub_2450` enter with `DS == SEG_DGROUP`, you can programmatically lock `DS = DGROUP` across that entire function in your disassembler. If a hand-crafted ASM routine always enters with `DS == SEG_STATIC + 0x0400` (say, the 3D trig/polygon table segment) and `ES == 0xA000`, your disassembler can immediately resolve every `[SI+disp]` to the trig table and every `ES:[DI]` to VGA RAM.


2. **Memory Dereferences (`EA` Calculation with `DS:` or `ES:`):**
When an instruction actually *reads or writes memory* via `DS` or `ES` (ignoring stack-relative `[BP+x]` which uses `SS`), update a small per-instruction set of seen symbolic segments (capping at ~4 unique targets per `CS:IP`).
* *Why:* In Borland C++, `LES BX, [BP+6]` is almost always followed immediately by `ES:[BX+offset]`. Recording the resolved segment + offset range (`min_offset`, `max_offset`, and `stride`) at the dereference site tells your struct-reconstruction agent the exact size and layout of the pointed-to object.


3. **Self-Modifying / Far Jump Targets (`JMP DWORD PTR [bx]`, `CALL DWORD PTR [bx]`):**
*Falcon 3.0* uses function pointers for UI callbacks, AI state machines, and graphics drivers. Logging the resolved `(Overlay_ID, Offset)` pairs at every indirect `CALL`/`JMP` gives your static call-graph builder complete visibility into virtual/callback dispatch tables.

---

### 4. Minimal Data Schema to Feed Your Agents

If you export a JSON map from your emulator run and inject it into your disassembler's comments or database metadata before the agent runs, each function header can look like this:

```json
{
  "func_id": "ovr_08:01A4",
  "entry_ds": ["DGROUP (100%)"],
  "entry_es": ["HEAP_ALLOC_from_ovr_01:08C2 (85%)", "DGROUP (15%)"],
  "memory_accesses": [
    {
      "ip": "0x01B2",
      "insn": "mov ax, es:[bx+0x14]",
      "seg_target": "HEAP_ALLOC_from_ovr_01:08C2",
      "observed_bx_bases": ["0x0000"],
      "comment": "Field +0x14 of struct allocated in InitMission()"
    }
  ]
}

```

With that single annotation block, an LLM agent doesn't have to guess what `es:[bx+0x14]` is—it sees that it's offset `0x14` of the struct allocated at `ovr_01:08C2` and can cross-reference every other function touching that same heap allocation to build a single, unified C `struct`.

Dumping the raw 1MB conventional memory image during the menu and in-flight sim is one of the smartest shortcuts you can take—it bypasses `.RTLink`'s relocation math, unpacks the PKWARE DCL buffers for free, and gives you already-initialized `DGROUP` and heap structures.

The reason disassemblers choke on a raw 1MB real-mode dump is the **Segment Aliasing Problem**. If you load a flat `0x100000`-byte blob at `0000:0000`, the disassembler has no segment boundaries. An instruction like `CALL NEAR 0x0450` or `MOV AX, [0x1234]` inside code located at linear address `0x2A400` requires the disassembler to know whether `CS` (or `DS`) is `2A40` (making the offset `0x0000`) or `2A00` (making the offset `0x0400`). If the segment base is off by even a single paragraph, every near jump, switch table, and offset reference resolves to garbage.

To turn your "Menu Dump" and "Sim Dump" into a single, clean, disassembler-ready image, use a **Snapshot Splicing & Segment Carve** pipeline.

---

### 1. Don't Load the Full 1MB as One Block—Carve by Segment Base

When an `MZ` executable loads, both the root Borland C++ modules and the `.RTLink` overlays are aligned to exact paragraph boundaries (`segment:0000`). Before feeding the 1MB dump to your disassembler, run a Python script over the raw binary to discover the exact list of active `CS` and `DS` paragraphs:

* **Harvest Active Segments from Far Calls (`9A`) and Vectors:**
Scan the 1MB dump (between the end of the DOS kernel/drivers, usually around `0x08000`–`0x10000`, and `0xA0000`) for:
1. Interrupt Vector Table (`0000:0000` to `0000:03FF`) entries that point into the game's memory range.
2. Every `CALL FAR seg:off` (`9A xx xx yy yy`) and `JMP FAR seg:off` (`EA xx xx yy yy`) instruction in the dump where `seg` falls within conventional RAM (`0x1000`–`0x9FFF`).
3. The `.RTLink` thunk table in low memory—each active overlay currently resident in the dump will have its live RAM segment patched right into the thunk or master table.


* **Walk the DOS MCB (Memory Control Block) Chain:**
In your 1MB dump, walk the DOS MCB chain (starting from the "List of Lists" pointer or scanning for `'M'`/`'Z'` MCB headers at `seg:0000`). This immediately separates the main `FALCON3.EXE` image from subsequent `INT 21h, AH=48h` far-heap allocations and `.RTLink` overlay pool blocks.

Once you have the sorted list of true segment bases (`Seg_0 < Seg_1 < Seg_2 ...`), slice the 1MB binary at each `(Seg_i << 4)` linear boundary and create distinct memory blocks at `Seg_i:0000` with length `(Seg_{i+1} - Seg_i) << 4`. Now every near call (`E8`), near jump (`E9`), and local offset starts from `:0000` exactly as `BCC` and `TASM` assembled it.

---

### 2. Reconciling the "Menu Dump" vs. "Sim Dump" (Overlay Collisions)

In *Falcon 3.0*, the Main Menu/Campaign UI and the 3D Flight Sim live in mutually exclusive `.RTLink` overlays that swap into the **exact same physical RAM pool** (e.g., segments `0x5000`–`0x8FFF`).

If you load both 1MB dumps into the same address space, the Sim code will overwrite the Menu code at `5000:0000`. Here is how to merge both dumps into a **single unified project**:

1. **Diff the Resident Root:**
Compare the two 1MB dumps paragraph-by-paragraph (`16` bytes at a time) starting from the game's load segment (`PSP + 0x10`).
* **Identical Paragraphs = Resident Code (`ROOT_CS`).** All non-overlaid code, the `.RTLink` manager, and Borland's CRT (`C0L`, `CL.LIB`) will be byte-for-byte identical between the Menu and Sim dumps (except for a few dynamic thunk bytes).
* **Modified Paragraphs in `DGROUP` / Far Data = Initialized Globals.** Keep both snapshots available as reference data, or use the Sim dump as the primary state since flight structs are populated.


2. **Mount Colliding Overlays as "Overlay Blocks" or Synthetic High Segments:**
For segments in the `.RTLink` overlay pool (`0x5000`–`0x8FFF`) where the Menu dump and Sim dump differ:
* **Option A (True Overlay Memory Blocks):** In tools like Ghidra, `createMemoryBlock()` accepts an `overlay=True` boolean. This creates a named overlay space (e.g., `MENU_5420:0000` and `SIM_5420:0000`) where internal offsets remain anchored at `:0000` without colliding in flat physical memory.
* **Option B (Synthetic High Segments):** If your agent scripts prefer flat `seg:off` coordinates without overlay-space namespaces, map the Resident + Sim dump at their native segments (`1000:0000`–`9FFF:0000`), and relocate the colliding Menu-only segments into unused upper segment numbers (e.g., `B000:0000`, `C000:0000`, `D000:0000`—above VGA RAM). Since 16-bit x86 code uses relative near jumps (`E8`/`E9`) within a segment, moving a segment from `5420:0000` to `C420:0000` does not break a single internal instruction! You only have to rewrite the `.RTLink` thunk jump in the root segment to point to `C420:xxxx`.



---

### 3. Fixing the "Live Thunk" Trap in a RAM Dump

When you dump RAM while the game is running in the 3D Sim:

* Overlays that are **currently loaded** in RAM have their `.RTLink` thunks patched to jump directly to the live RAM segment (or hold a live table index).
* Overlays that were **swapped out** (like the Menu, Briefing, or Debriefing screens) still point to the `.RTLink` disk-loader trap!

By combining the Menu dump and Sim dump (plus a quick dump at the Briefing and Debriefing screens), you can run a tiny script across the `.RTLink` thunk segment across all 3–4 dumps:

* Whenever Thunk `#k` is in its "loaded/resolved" state in *any* of the snapshots, grab its target `(Snapshot_ID, CS, IP)`.
* Patch Thunk `#k` in your master database to `JMP FAR` directly to the corresponding carved segment.

---

### 4. Extracting the Decompressed PKWARE Assets from the Dump

Because you captured the 1MB state *after* the menu and sim initialized, those mystery PKWARE-compressed chunks from `FALCON3.EXE` are now sitting uncompressed inside the DOS/Far Heap segments of your dumps.

To link the uncompressed RAM buffers back to the mystery blocks in `FALCON3.EXE`:

1. Take every carved heap segment from your Menu and Sim dumps (discovered via the DOS MCB chain or `DGROUP` far pointers).
2. Scan `DGROUP` for 32-bit far pointers (`off:seg`) whose `seg` matches one of those heap blocks.
3. Any function in the Menu or Sim that reads from that `DGROUP` far pointer is now directly inspecting the unpacked structure (whether it's cockpit bitmap data, 3D object polygon vertices, or flight envelope tables)—meaning your agents can reverse the data format straight from the consumer functions without ever touching the decompression math.

If you want to automate carving your existing 1MB Menu and Sim dumps right now, I can write a Python script that scans both 1MB files, walks the DOS MCBs, diffs the code segments vs. overlay pools, and outputs a clean segment map (or Ghidra/radare2 loader script). What disassembler or framework are your agents currently interfacing with to read the instructions?

For a visual walkthrough on extracting unpacked segments from RAM and configuring them in your tools, check out [Ghidra + IDA - How to load unpacked segments from memory](https://www.youtube.com/watch?v=gb0f2PWGuCc).

