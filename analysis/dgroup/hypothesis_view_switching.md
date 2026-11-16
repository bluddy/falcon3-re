# View Switching Hypothesis

## Key Discovery

From the manual (f3keys.txt), I now understand the view key mapping:

### Inside Views (Cockpit) - Should set `r15_external_view_flag = 0`
- Key 3 (scan 0x04): View front
- Key 4 (scan 0x05): View left  
- Key 5 (scan 0x06): View rear
- Key 6 (scan 0x07): View right

### Outside Views (External) - Should set `r15_external_view_flag = 1`
- Key 1 (scan 0x02): Satellite view
- Key 2 (scan 0x03): Ground view
- Key 7 (scan 0x08): Wingman view
- Key 8 (scan 0x09): Padlock view
- Key 0 (scan 0x0B): Chase plane view

## Current Understanding

1. **Input Capture**: Number keys are captured at `0x130709-0x130749` in `input_poll_handler`
2. **Storage**: Scan code stored in `input_flag_pending_2` at `0x130749`
3. **Missing Link**: Don't see direct comparison with these scan codes in view dispatch

## New Hypothesis

The view switching likely works like this:

1. Key press stored in `input_flag_pending_2`
2. Game mode overlay reads `input_flag_pending_2`
3. Overlay calls appropriate view setup function based on scan code
4. **View setup function** sets `r15_external_view_flag` as a side effect

This would explain why we only see 1 WRITE to the flag (initialization) - the writes might be happening in:
- Overlay code we haven't examined yet
- Via indirect writes (pointer dereferencing)
- Via a view parameter/state structure that includes the flag

## Next Steps

1. Search for function calls that take scan code values 0x02-0x0B as parameters
2. Look for switch/jump tables with 10 entries (for keys 0-9)
3. Search for writes to address `0x107762` using different instruction patterns:
   - Indirect: `mov [bx], al` where bx contains 0x107762
   - Segment-relative: different segment register combinations
   - Byte vs word operations
4. Check if overlays can write to R15 segment data
