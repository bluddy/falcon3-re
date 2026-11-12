#!/usr/bin/env python3
"""
Map dispatcher table using RUNTIME segment translation.

Key insight: The dispatcher table segments (0x6E05-0x90B4) are likely RUNTIME segments,
not link segments. We need to:
1. Subtract load base 0x1F5 (493) to get link segment
2. Convert link segment to IDA address using overlay_placement.json

OR: These might be runtime CS values seen during execution, which need runtime_seg_map.json
