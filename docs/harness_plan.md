# Falcon 3.0 — C++20 Native Recompilation & Shadow-Verify Harness Plan

## Objective
Transition *Falcon 3.0* from a 16-bit DOS real-mode + `.RTLink` overlay binary into a clean, flat-memory **64-bit C++20** codebase (`src/port/`), verified function-by-function against the live 16-bit execution state inside our instrumented DOSBox runner before replacing the emulated CPU loop entirely with SDL3.

We are **not** chasing 16-bit byte-identical recompilation (`new_bytes == old_bytes`). We enforce **Bit-Exact Semantic State Identity (`new_fn(pre_state) == post_state`)** via an automated in-process Shadow-Verify Harness.

---

## Architectural Invariants

1. **Topological Bottom-Up Porting (`Level 0 -> Level 22`) = Zero Reverse Callbacks:**
   Because our 2,237-node call graph is topologically sorted (with `0` cross-SCC invariant violations), we port functions strictly from `Level 0` upward.
   - When a function `f` at `Level k` is ported to C++20, **100% of its callees (`Level < k`) are already native C++20 functions**.
   - Therefore, a native C++ function calls its callees as **direct C++ function calls** and **never** needs to re-enter the 16-bit x86 emulator mid-function.

2. **Zero-Copy Shared Arena (`g_mem_base`):**
   Both x86-64 and 80286 are little-endian. The C++20 port operates directly on a 1 MB linear pointer `uint8_t* g_mem_base` pointing to DOSBox's `MemBase` (and in `SHADOW_VERIFY` mode, to a 1 MB `g_scratch_ram` copy).
   - Resident `CS` globals (`0x10000..0x2CF60` in IDA), `DGROUP` (`0x6C27`), and `FAR_DATA` (`0x46A4`) are accessed in-place via `#pragma pack(1)` struct overlays and typed reference accessors.
   - Address conversion from IDA linear `ea` (in Resident) to physical offset in `g_mem_base`:
     `phys_addr(ida_ea) = (ida_ea - 0x10000) + (g_load_base_seg << 4)` (where `g_load_base_seg = 0x01F5` at runtime).

3. **Overlay Disambiguation via Relocation-Masked 8-Byte Prologue Fingerprints:**
   Because `.RTLink` swaps mutually exclusive overlays into the same runtime `CS:IP` arenas (e.g., `R05`, `R27`, `R28`, `R29` sharing `w0 = 0x1E10` at `0x2005`, or smaller overlays sharing dynamic pools `0x569F`/`0x5CD9`), raw `(CS, IP)` is not unique over time.
   - **Cross-Overlay Calls:** Intercepted at the fixed Resident `.RTLink` Thunk Table (`0x2BD9D..0x2C968`), where each slot maps 1-to-1 to a specific `(overlay_rec_id, record_offset)`.
   - **Intra-Overlay Calls / Direct `CS:IP` Hits:** Every `FunctionIntercept` carries an 8-byte `expected_prologue_8b` and `prologue_mask_8b` (generated from `function_bytes.json` + `.EXE`/`.RTLink` relocation records, setting `0x0000` on relocated segment words and `0xFFFF` on fixed opcode/immediate bytes). At runtime, the hook reads `live_8b = *(uint64_t*)(MemBase + (cs << 4) + ip)` and matches `(live_8b & mask) == (expected & mask)` in 2 CPU cycles.
   - **Constant Overlay Data Tables:** Ported overlay functions read constant `CS`-embedded tables from a static immutable array `g_overlay_rom[rec_id][offset]` extracted from `FALCONCD.EXE` so table reads succeed even when `.RTLink` has another overlay swapped into low RAM.

4. **Collapse Trivial Plumbing Leaves into Accessors:**
   Level-0 functions that are purely 1-to-3 instruction segment/offset getters, setters, or flag bit-twiddlers (`state_word_*_get/set`, `flag_*_clear/set`, `active_farptr_*`, and the 302 `.RTLink` thunk slots) are **inlined as C++ accessors/macros** rather than emitted as standalone C++ functions, unless directly called from unported 16-bit code.

---

## Phase 1: Build the C++20 Skeleton & `falcon_globals.h` Generator (No Porting Yet)

### Step 1.1 — Create `src/port/` CMake/Build Target
Create a clean C++20 static library target (`falcon_port`) that links into our instrumented DOSBox runner (and also compiles standalone for fast unit-test execution):
- `src/port/include/falcon_types.h`:
  - Fixed-width types (`uint8_t`, `int16_t`, `uint16_t`, `int32_t`, `uint32_t`).
  - `FarPtr16 { uint16_t off; uint16_t seg; }` (`#pragma pack(1)`, 4 bytes) with helper `.linear()` returning `(uint32_t(seg) << 4) + off` and `template<typename T> T* as_ptr(uint8_t* base)`.
  - `CpuState16` struct holding `{ ax, bx, cx, dx, si, di, bp, sp, ds, es, ss, cs, ip, flags }` plus 8-bit sub-register views (`al`, `ah`, `bl`, `bh`, `cl`, `ch`, `dl`, `dh`) and flag helpers (`cf()`, `zf()`, `sf()`, `of()`, `set_zf(bool)`, `set_cf(bool)`).
- `src/port/include/falcon_memory.h`:
  - `extern uint8_t* g_mem_base;`
  - `extern uint16_t g_load_base_seg;`
  - `template<typename T> inline T& mem_phys(uint32_t phys) { return *reinterpret_cast<T*>(g_mem_base + (phys & 0xFFFFFu)); }`
  - `template<typename T> inline T& mem_seg_off(uint16_t seg, uint16_t off) { return mem_phys<T>((uint32_t(seg) << 4) + off); }`
  - `template<typename T> inline T& mem_ida_res(uint32_t ida_ea) { return mem_phys<T>((ida_ea - 0x10000u) + (uint32_t(g_load_base_seg) << 4)); }`

### Step 1.2 — Auto-Generate `src/port/include/falcon_globals.h` from IDA + `naming.yaml`
Write `tools/export_globals_header.py`:
- Scans `registry/naming.yaml` (`kind: global` entries + all `cs:XXXXX` / `ds:XXXXX` addresses referenced in `sig` and `notes`) and IDA data xrefs inside Resident (`0x10000..0x2CF60`) and `DGROUP`.
- Emits typed inline reference accessors (`inline uint16_t& g_word_2223e() { return mem_ida_res<uint16_t>(0x2223E); }`) and initial `#pragma pack(1)` structs for already-identified clusters (`FixedVec3State` @ `0x22C71`, `ViewClipLimits` @ `0x2547C`, `CallbackArgsBlock` @ `0x24BB8`).
- Emits `expected_prologue_8b` and `prologue_mask_8b` for all 2,237 functions from `function_bytes.json` + relocation maps.
- Add `static_assert(sizeof(...) == ...)` for every struct.

---

## Phase 2: The In-Process Two-Phase `SHADOW_VERIFY` & `NATIVE_REPLACE` Harness

### Step 2.1 — Two-Phase Execution Inside DOSBox CPU Loop
When the emulated CPU's `CS:IP` matches a registered `FunctionIntercept` (verified via `(live_8b & prologue_mask_8b) == (expected_prologue_8b & prologue_mask_8b)`):
1. **Phase 1 (Entry Hook at `CS:IP`):**
   - Save `entry_regs = live_regs` and copy 1 MB `MemBase` -> `g_scratch_ram` (~40 µs).
   - Point `g_mem_base = g_scratch_ram`, execute `intercept.wrapper(cpp_regs)`, and simulate `RETN` / `RETF` (popping `IP`/`CS` from `g_scratch_ram` at `SS:SP` and advancing `SP` by `2 + (is_far ? 2 : 0) + ret_pop_bytes`).
   - Record `(expected_ret_cs, expected_ret_ip, expected_ret_sp)` from `cpp_regs`.
   - Restore `g_mem_base = MemBase` and let DOSBox execute the original 16-bit instructions on `MemBase` (while suppressing nested `SHADOW_VERIFY` triggers on inner callees).
2. **Phase 2 (Return Hook at `CS == expected_ret_cs && IP == expected_ret_ip && SP == expected_ret_sp`):**
   - Compare all non-clobbered registers (`AX, BX, CX, DX, SI, DI, BP, SP, DS, ES`) and contract flags (`CF, ZF` per `clobber_mask`).
   - Compare `g_scratch_ram` vs `MemBase` in 64-bit chunks across all 1 MB (ignoring stack scratch bytes below `entry_regs.sp`).
   - On any mismatch, append a structured JSON diff to `analysis/port_diffs.jsonl` and increment `intercept.mismatches`.

### Step 2.2 — 16-Seed Directed Fuzz Harness (`FALCON_PORT_TEST=sub_XXXXX`)
For functions with `dyn == 0` in the standard gameplay trace (such as `R05_1E10` ordnance/flight functions):
- Boot-time test runner loads the target overlay record into RAM, seeds 16 deterministic register + stack + struct states covering zero, positive, negative, and boundary values, runs both the 64-bit C++20 wrapper and the 16-bit DOS reference implementation on all 16 seeds, and asserts `0` diffs.

---

## Phase 3: Dual-Layer C++ Function Design (Clean C++ + Thin Register Wrapper)

Every ported function in `src/port/` is written in two layers:
1. **Clean C++20 Function:** Takes native typed arguments and struct references, called directly by other ported C++20 functions.
2. **Thin 16-Bit Intercept Wrapper (`wrap_<name>`):** Translates `CpuState16` registers and stack arguments into the clean C++20 function call when invoked by unported 16-bit callers.

---

## Phase 4: The Verification Gates (`tools/verify_port.py`)

No ported batch may be committed unless all 4 gates pass:
1. **Build Gate:** `cmake --build build --target falcon_port` compiles with zero warnings (`-Wall -Wextra -Werror`).
2. **Registry & Topological Gate (`tools/verify_port.py --check-registry`):**
   Every function in `registry/routines.yaml` marked `port_status: verified` has a registered entry in `falcon_intercepts.cpp` and has **100% of its callees already `verified`**.
3. **Differential Execution Gate (`tools/verify_port.py --run-shadow`):**
   Requires **`calls_tested >= 16` AND `reg_mismatches == 0` AND `mem_mismatches == 0`**.
4. **Flip to `NATIVE_REPLACE`:**
   Flip verified functions to `NATIVE_REPLACE` and re-run the smoke test to confirm live execution with 16-bit ASM bypassed.

---

## Phase 5: Complete Reference Implementation (`src/port/falcon_shadow_harness.cpp`)

```cpp
/**
 * @file falcon_shadow_harness.cpp
 * @brief Production-ready C++20 implementation of the Two-Phase DOSBox Shadow-Verify
 *        Hook, Relocation-Masked 8-Byte Overlay Prologue Disambiguator, and
 *        16-Seed Directed Fuzz Harness.
 */

#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>

// ============================================================================
// 1. Core 16-Bit CPU & Memory Types
// ============================================================================

#pragma pack(push, 1)
struct FarPtr16 {
    uint16_t off;
    uint16_t seg;

    constexpr uint32_t linear() const { return (uint32_t(seg) << 4) + off; }
    template <typename T>
    T* as_ptr(uint8_t* base) const {
        return reinterpret_cast<T*>(base + (linear() & 0xFFFFFu));
    }
};
#pragma pack(pop)
static_assert(sizeof(FarPtr16) == 4, "FarPtr16 must be 4 bytes");

struct CpuState16 {
    uint16_t ax, bx, cx, dx, si, di, bp, sp;
    uint16_t ds, es, ss, cs, ip;
    uint16_t flags;

    uint8_t al() const { return static_cast<uint8_t>(ax & 0xFFu); }
    uint8_t ah() const { return static_cast<uint8_t>((ax >> 8) & 0xFFu); }
    void set_al(uint8_t v) { ax = static_cast<uint16_t>((ax & 0xFF00u) | v); }
    void set_ah(uint8_t v) { ax = static_cast<uint16_t>((ax & 0x00FFu) | (uint16_t(v) << 8)); }

    static constexpr uint16_t FLAG_CF = 0x0001u;
    static constexpr uint16_t FLAG_ZF = 0x0040u;
    static constexpr uint16_t FLAG_SF = 0x0080u;
    static constexpr uint16_t FLAG_OF = 0x0800u;

    bool cf() const { return (flags & FLAG_CF) != 0; }
    bool zf() const { return (flags & FLAG_ZF) != 0; }
    void set_cf(bool v) { flags = v ? (flags | FLAG_CF) : (flags & ~FLAG_CF); }
    void set_zf(bool v) { flags = v ? (flags | FLAG_ZF) : (flags & ~FLAG_ZF); }
};

enum RegClobberMask : uint16_t {
    CLOBBER_NONE  = 0,
    CLOBBER_AX    = 1u << 0,
    CLOBBER_BX    = 1u << 1,
    CLOBBER_CX    = 1u << 2,
    CLOBBER_DX    = 1u << 3,
    CLOBBER_SI    = 1u << 4,
    CLOBBER_DI    = 1u << 5,
    CLOBBER_BP    = 1u << 6,
    CLOBBER_DS    = 1u << 7,
    CLOBBER_ES    = 1u << 8,
    CHECK_FLAG_CF = 1u << 12,
    CHECK_FLAG_ZF = 1u << 13,
    CLOBBER_CDECL_16BIT_RET = CLOBBER_BX | CLOBBER_CX | CLOBBER_DX | CLOBBER_ES,
    CLOBBER_CDECL_32BIT_RET = CLOBBER_BX | CLOBBER_CX | CLOBBER_ES
};

enum class InterceptMode : uint8_t {
    DISABLED = 0,
    SHADOW_VERIFY = 1,
    NATIVE_REPLACE = 2
};

using NativeWrapperFn = void(*)(CpuState16& regs);

struct FunctionIntercept {
    uint32_t ida_ea;               // Canonical IDA EA (unique across all 2,237 fns)
    int16_t  overlay_rec_id;       // -1 for Resident; 0..69 for R00..R69
    uint16_t thunk_slot_ea;        // Optional Resident .RTLink thunk EA (0 if none)
    uint32_t record_offset;        // Offset from segment/record start (matches IP in overlays)
    uint64_t expected_prologue_8b; // First 8 bytes from function_bytes.json
    uint64_t prologue_mask_8b;     // 0x0000 on relocated words, 0xFFFF on invariant bytes
    const char* name;              // Semantic name from naming.yaml
    bool     is_far;               // true = RETF, false = RETN
    uint16_t ret_pop_bytes;        // N for RETF N / RETN N (0 for plain RET)
    uint16_t clobber_mask;         // RegClobberMask bitfield
    InterceptMode mode;
    NativeWrapperFn wrapper;
    uint32_t calls_tested = 0;
    uint32_t mismatches   = 0;
};

// ============================================================================
// 2. Shared Memory Pointers & Helpers
// ============================================================================

extern uint8_t* MemBase;                  // Live 1MB DOS RAM pointer owned by DOSBox
uint8_t*        g_mem_base = nullptr;     // Active arena pointer (MemBase or g_scratch_ram)
uint16_t        g_load_base_seg = 0x01F5; // Runtime load paragraph of Resident root

static uint8_t  g_scratch_ram[0x100000];  // 1MB scratch copy for C++ Shadow-Verify run
static int16_t  g_active_overlay_at_seg[0x10000]; // Optional runtime seg -> R## tracker

template <typename T>
inline T& mem_phys(uint32_t phys) {
    return *reinterpret_cast<T*>(g_mem_base + (phys & 0xFFFFFu));
}

template <typename T>
inline T& mem_seg_off(uint16_t seg, uint16_t off) {
    return mem_phys<T>((uint32_t(seg) << 4) + off);
}

template <typename T>
inline T& mem_ida_res(uint32_t ida_ea) {
    return mem_phys<T>((ida_ea - 0x10000u) + (uint32_t(g_load_base_seg) << 4));
}

template <typename T>
inline T stack_arg(const CpuState16& r, bool is_far, uint16_t arg_byte_offset) {
    const uint16_t ret_addr_size = is_far ? 4u : 2u;
    return mem_seg_off<T>(r.ss, static_cast<uint16_t>(r.sp + ret_addr_size + arg_byte_offset));
}

inline void simulate_16bit_return(CpuState16& r, bool is_far, uint16_t ret_pop_bytes) {
    r.ip = mem_seg_off<uint16_t>(r.ss, r.sp);
    r.sp = static_cast<uint16_t>(r.sp + 2u);
    if (is_far) {
        r.cs = mem_seg_off<uint16_t>(r.ss, r.sp);
        r.sp = static_cast<uint16_t>(r.sp + 2u);
    }
    r.sp = static_cast<uint16_t>(r.sp + ret_pop_bytes);
}

// ============================================================================
// 3. Overlay-Aware Lookup by IP Bucket + 8-Byte Relocation-Masked Fingerprint
// ============================================================================

static std::vector<FunctionIntercept*> g_ip_buckets[0x10000];
static std::unordered_map<uint32_t, FunctionIntercept*> g_res_phys_map;

void register_function_intercept(FunctionIntercept* fn) {
    if (fn->overlay_rec_id < 0) {
        // Resident function: physical address is fixed once g_load_base_seg is known
        const uint32_t phys = (fn->ida_ea - 0x10000u) + (uint32_t(g_load_base_seg) << 4);
        g_res_phys_map[phys] = fn;
    } else {
        // Overlay function: index by IP (record_offset) and disambiguate via 8-byte prologue
        if (fn->record_offset < 0x10000u) {
            g_ip_buckets[fn->record_offset].push_back(fn);
        }
        // If it also has a dedicated Resident .RTLink thunk slot, index the thunk in NATIVE_REPLACE
        if (fn->thunk_slot_ea != 0 && fn->mode == InterceptMode::NATIVE_REPLACE) {
            const uint32_t thunk_phys = (fn->thunk_slot_ea - 0x10000u) + (uint32_t(g_load_base_seg) << 4);
            g_res_phys_map[thunk_phys] = fn;
        }
    }
}

inline FunctionIntercept* find_matching_intercept(uint16_t cs, uint16_t ip) {
    const uint32_t phys = ((uint32_t(cs) << 4) + ip) & 0xFFFFFu;

    // 1. Check fixed Resident map first
    auto it = g_res_phys_map.find(phys);
    if (it != g_res_phys_map.end()) {
        return it->second;
    }

    // 2. Check overlay candidates sharing this IP offset using 8-byte masked prologue
    const auto& bucket = g_ip_buckets[ip];
    if (bucket.empty() || phys > 0x100000u - 8u) {
        return nullptr;
    }

    const uint64_t live_8b = *reinterpret_cast<const uint64_t*>(MemBase + phys);
    for (FunctionIntercept* cand : bucket) {
        if ((live_8b & cand->prologue_mask_8b) ==
            (cand->expected_prologue_8b & cand->prologue_mask_8b)) {
            return cand;
        }
    }
    return nullptr;
}

// ============================================================================
// 4. Two-Phase Shadow-Verify State Machine (Entry Hook + Return Hook)
// ============================================================================

struct ActiveShadowSession {
    bool               active = false;
    FunctionIntercept* intercept = nullptr;
    CpuState16         entry_regs{};
    CpuState16         cpp_exit_regs{};
    uint16_t           expected_ret_cs = 0;
    uint16_t           expected_ret_ip = 0;
    uint16_t           expected_ret_sp = 0;
};

static ActiveShadowSession g_shadow;

struct MemDiffEntry {
    uint32_t phys_addr;
    uint8_t  asm_byte;
    uint8_t  cpp_byte;
};

bool shadow_harness_on_instruction(CpuState16& live_regs) {
    // 1. If a SHADOW_VERIFY reference run is active, check if it reached its return site
    if (g_shadow.active) {
        if (live_regs.cs == g_shadow.expected_ret_cs &&
            live_regs.ip == g_shadow.expected_ret_ip &&
            live_regs.sp == g_shadow.expected_ret_sp) {
            g_shadow.active = false;
            FunctionIntercept& fn = *g_shadow.intercept;
            fn.calls_tested++;

            const CpuState16& cpp_r = g_shadow.cpp_exit_regs;
            const CpuState16& asm_r = live_regs;
            const uint16_t mask = fn.clobber_mask;

            bool reg_diff = false;
            auto check_reg = [&](uint16_t c_val, uint16_t a_val, uint16_t clobber_bit) {
                if (!(mask & clobber_bit) && (c_val != a_val)) reg_diff = true;
            };

            check_reg(cpp_r.ax, asm_r.ax, CLOBBER_AX);
            check_reg(cpp_r.bx, asm_r.bx, CLOBBER_BX);
            check_reg(cpp_r.cx, asm_r.cx, CLOBBER_CX);
            check_reg(cpp_r.dx, asm_r.dx, CLOBBER_DX);
            check_reg(cpp_r.si, asm_r.si, CLOBBER_SI);
            check_reg(cpp_r.di, asm_r.di, CLOBBER_DI);
            check_reg(cpp_r.bp, asm_r.bp, CLOBBER_BP);
            check_reg(cpp_r.ds, asm_r.ds, CLOBBER_DS);
            check_reg(cpp_r.es, asm_r.es, CLOBBER_ES);
            if (cpp_r.sp != asm_r.sp) reg_diff = true;
            if ((mask & CHECK_FLAG_CF) && (cpp_r.cf() != asm_r.cf())) reg_diff = true;
            if ((mask & CHECK_FLAG_ZF) && (cpp_r.zf() != asm_r.zf())) reg_diff = true;

            const uint32_t stack_ignore_hi = (uint32_t(g_shadow.entry_regs.ss) << 4) + g_shadow.entry_regs.sp;
            const uint32_t stack_ignore_lo = (stack_ignore_hi >= 512u) ? (stack_ignore_hi - 512u) : 0u;

            std::vector<MemDiffEntry> mem_diffs;
            const uint64_t* scratch64 = reinterpret_cast<const uint64_t*>(g_scratch_ram);
            const uint64_t* live64    = reinterpret_cast<const uint64_t*>(MemBase);

            for (uint32_t q = 0; q < (0x100000u / 8u); ++q) {
                if (scratch64[q] != live64[q]) {
                    const uint32_t base_addr = q * 8u;
                    for (uint32_t b = 0; b < 8u; ++b) {
                        const uint32_t addr = base_addr + b;
                        if (addr >= stack_ignore_lo && addr < stack_ignore_hi) continue;
                        if (g_scratch_ram[addr] != MemBase[addr]) {
                            mem_diffs.push_back({ addr, MemBase[addr], g_scratch_ram[addr] });
                            if (mem_diffs.size() >= 32) break;
                        }
                    }
                    if (mem_diffs.size() >= 32) break;
                }
            }

            if (reg_diff || !mem_diffs.empty()) {
                fn.mismatches++;
                std::ofstream log("analysis/port_diffs.jsonl", std::ios::app);
                log << "{\"fn\":\"" << fn.name
                    << "\",\"ea\":\"0x" << std::hex << fn.ida_ea
                    << "\",\"call\":" << std::dec << fn.calls_tested
                    << ",\"reg_diff\":" << (reg_diff ? "true" : "false")
                    << ",\"mem_diffs\":" << mem_diffs.size()
                    << ",\"ax_asm\":\"0x" << std::hex << asm_r.ax
                    << "\",\"ax_cpp\":\"0x" << cpp_r.ax
                    << "\",\"dx_asm\":\"0x" << asm_r.dx
                    << "\",\"dx_cpp\":\"0x" << cpp_r.dx << "\"}\n";
            }
        }
        return false;
    }

    FunctionIntercept* intercept = find_matching_intercept(live_regs.cs, live_regs.ip);
    if (!intercept || intercept->mode == InterceptMode::DISABLED) {
        return false;
    }

    // 2. NATIVE_REPLACE Mode: Execute C++ directly on live MemBase and pop return address
    if (intercept->mode == InterceptMode::NATIVE_REPLACE) {
        g_mem_base = MemBase;
        intercept->wrapper(live_regs);
        simulate_16bit_return(live_regs, intercept->is_far, intercept->ret_pop_bytes);
        intercept->calls_tested++;
        return true;
    }

    // 3. SHADOW_VERIFY Mode: Snapshot -> Run C++ on g_scratch_ram -> Let 16-bit ASM run on MemBase
    std::memcpy(g_scratch_ram, MemBase, 0x100000);

    g_shadow.active      = true;
    g_shadow.intercept   = intercept;
    g_shadow.entry_regs  = live_regs;

    g_mem_base = g_scratch_ram;
    CpuState16 cpp_regs = live_regs;
    intercept->wrapper(cpp_regs);
    simulate_16bit_return(cpp_regs, intercept->is_far, intercept->ret_pop_bytes);
    g_shadow.cpp_exit_regs   = cpp_regs;
    g_shadow.expected_ret_cs = cpp_regs.cs;
    g_shadow.expected_ret_ip = cpp_regs.ip;
    g_shadow.expected_ret_sp = cpp_regs.sp;

    g_mem_base = MemBase;
    return false;
}

// ============================================================================
// 5. 16-Seed Directed Fuzz Harness for Offline / dyn==0 Functions
// ============================================================================

extern "C" void dosbox_run_until_cs_ip_sp(uint16_t target_cs, uint16_t target_ip, uint16_t target_sp);

bool run_directed_fuzz_16(FunctionIntercept& intercept, uint16_t target_cs, uint16_t target_ip) {
    static constexpr uint16_t kSeeds[16] = {
        0x0000u, 0x0001u, 0x7FFFu, 0x8000u, 0xFFFFu, 0x0020u, 0x0100u, 0x7FFEu,
        0x1234u, 0xABCDu, 0x000Au, 0x0064u, 0x3FFFu, 0xC000u, 0x5555u, 0xAAAAu
    };

    std::vector<uint8_t> baseline_ram(MemBase, MemBase + 0x100000);

    for (int i = 0; i < 16; ++i) {
        std::memcpy(MemBase, baseline_ram.data(), 0x100000);

        CpuState16 regs{};
        regs.ax = kSeeds[i];
        regs.bx = kSeeds[(i + 3) & 15];
        regs.cx = kSeeds[(i + 7) & 15];
        regs.dx = kSeeds[(i + 11) & 15];
        regs.si = 0x0200u;
        regs.di = 0x0400u;
        regs.bp = 0xFF00u;
        regs.ds = g_load_base_seg;
        regs.es = g_load_base_seg;
        regs.ss = 0x9000u;
        regs.sp = 0xFF00u;
        regs.cs = target_cs;
        regs.ip = target_ip;

        g_mem_base = MemBase;
        const uint16_t sentinel_ip = 0xFFF0u;
        const uint16_t sentinel_cs = 0xF000u;
        mem_seg_off<uint16_t>(regs.ss, regs.sp) = sentinel_ip;
        if (intercept.is_far) {
            mem_seg_off<uint16_t>(regs.ss, static_cast<uint16_t>(regs.sp + 2u)) = sentinel_cs;
        }
        for (uint16_t arg_idx = 0; arg_idx < 8; ++arg_idx) {
            const uint16_t off = static_cast<uint16_t>((intercept.is_far ? 4u : 2u) + arg_idx * 2u);
            mem_seg_off<uint16_t>(regs.ss, static_cast<uint16_t>(regs.sp + off)) =
                kSeeds[(i + arg_idx) & 15];
        }

        InterceptMode saved_mode = intercept.mode;
        intercept.mode = InterceptMode::SHADOW_VERIFY;
        shadow_harness_on_instruction(regs);

        dosbox_run_until_cs_ip_sp(
            g_shadow.expected_ret_cs,
            g_shadow.expected_ret_ip,
            g_shadow.expected_ret_sp
        );

        CpuState16 exit_regs = regs;
        exit_regs.cs = g_shadow.expected_ret_cs;
        exit_regs.ip = g_shadow.expected_ret_ip;
        exit_regs.sp = g_shadow.expected_ret_sp;
        shadow_harness_on_instruction(exit_regs);
        intercept.mode = saved_mode;
    }

    std::memcpy(MemBase, baseline_ram.data(), 0x100000);
    return intercept.mismatches == 0;
}
```
