# IDA Renaming Plan - View System

## Critical Renamings (MUST DO)

### Variables
```
0x79F16  : word_79F16               -> current_view_index
0x107762 : r15_external_view_flag   -> view_pipeline_mode  (or acmi_playback_mode?)
0x79B66  : input_flag_pending_2     -> input_scan_code_queue
```

### Functions
```
0x156945 : overlay_r45_logic                   -> view_rendering_dispatcher
0x12DB63 : r29_tactical_screen_coordinator     -> tactical_screen_coordinator  
0x182390 : game_mode_r53_main_coordinator      -> game_mode_r53_coordinator
0x12FAC3 : input_poll_handler                  -> (already renamed)
0x1087B2 : (instruction in view_mode_set)      -> (add comment only)
```

### View Handlers (in jump table)
```
0x156C29 : (case 0)   -> view_handler_case_0
0x156D0B : (case 1-4) -> view_handler_cockpit_shared
0x156D81 : (case 5)   -> view_handler_case_5
0x156E75 : (case 6)   -> view_handler_case_6
0x156FE0 : (case 7)   -> view_handler_case_7
0x1570EF : (case 8)   -> view_handler_case_8
0x157118 : (case 9)   -> view_handler_case_9
```

## Key Comments to Add

### Input Capture
```
0x130709: "NUMBER KEY CAPTURE LOOP: Scan for keys 1-9,0 (scan 0x02-0x0B)"
0x130749: "Store scan code in input_scan_code_queue"
```

### Dispatchers
```
0x12DFD6: "INPUT DISPATCHER: Search table for scan code, dispatch via jmp [bx+8]"
0x12DFF1: "DISPATCH: Indirect jump to handler"
0x182476: "INPUT DISPATCHER (R53): Handle scan codes 0x01,0x03,0x04,0xFF"
0x182491: "DISPATCH: Indirect jump to view handler"
```

### View Handlers
```
0x18249A: "HANDLER: Set current_view_index = 7"
0x1824A3: "HANDLER: Set current_view_index = 8 (push param)"
```

### Rendering Dispatcher
```
0x156DC5: "VIEW RENDERING DISPATCHER: Read current_view_index (0-9)"
0x156DCA: "Bounds check: index must be 0-9"
0x156DD4: "JUMP TABLE: 10-case switch on current_view_index"
```

### Mode Selection
```
0x108BC5: "Read view_pipeline_mode: 0=Path A, 1=Path B (ACMI vs sim?)"
0x1087B2: "INIT: Set view_pipeline_mode (only write!)"
```

## Hypothesis on view_pipeline_mode

Based on user insight, this flag likely controls:
- **0 = Live simulation mode** (player flying)
- **1 = ACMI playback mode** (replay/recording playback)

NOT:
- ~~0 = cockpit, 1 = external~~ (wrong - that's controlled by current_view_index)

This makes more sense because:
- ACMI is a major Falcon 3.0 feature (Air Combat Maneuvering Instrumentation)
- ACMI needs different rendering path (replay data vs live simulation)
- ACMI mode is set at session start, never changes
- In both modes, all 10 view indices work (0-9)

## Update Documentation

After renaming in IDA, update these files with new names:

1. COMPLETE_VIEW_SYSTEM_DOCUMENTATION.md
2. VIEW_SYSTEM_ARCHITECTURE.md
3. VIEW_DISPATCH_FOUND.md
4. All JSON files that reference old names

Search and replace:
- `word_79F16` → `current_view_index`
- `r15_external_view_flag` → `view_pipeline_mode`
- `input_flag_pending_2` → `input_scan_code_queue`
- `overlay_r45_logic` → `view_rendering_dispatcher`

## Verification Checklist

After renaming:
- [ ] All 3 key variables renamed
- [ ] All 3+ key functions renamed  
- [ ] Jump table handlers labeled (7 unique + 1 shared)
- [ ] 15+ critical comments added
- [ ] Documentation files updated with new names
- [ ] Commit to git with clear message

## Git Commit Message

```
IDA: Rename view system components with proper names

Renamed based on complete understanding of view architecture:
- word_79F16 -> current_view_index (dynamic view selection 0-9)
- r15_external_view_flag -> view_pipeline_mode (ACMI vs sim?)
- input_flag_pending_2 -> input_scan_code_queue (keyboard input)
- overlay_r45_logic -> view_rendering_dispatcher (10-case dispatcher)

Added 15+ comments documenting input flow, dispatchers, and rendering.

This reflects discovery that view switching uses two-level system:
session-static mode selection + dynamic view index (0-9).
```
