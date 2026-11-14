#!/usr/bin/env python3
"""
Falcon 3.0 AI Context Parser

Parses the 40-entity AI context array from memory dumps or runtime captures.
Location: 0x65A7:0x000C (960 bytes total)

Usage:
    python parse_ai_contexts.py memory_dump.bin
    python parse_ai_contexts.py --dosbox 65A7:000C 960
"""

import struct
import sys
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class AIContext:
    """24-byte AI context structure"""
    index: int                  # Array index (0-39)
    active: int                 # +0x00: Active flag (0/1)
    entity_id: int              # +0x01: Entity/slot ID (word)
    data_table_idx: int         # +0x03: Index for farptr_table_get (word)
    param_1: int                # +0x05: Data param 1 (word)
    param_2: int                # +0x07: Data param 2 (word)
    param_3: int                # +0x09: Data param 3 (word)
    behavior_flags: int         # +0x0B: Behavior state flags (word)
    field_d: int                # +0x0D: Unknown byte
    counter: int                # +0x0E: Timer/counter byte
    threshold: int              # +0x0F: Threshold byte
    velocity_x: int             # +0x10: Movement param (word)
    velocity_y: int             # +0x12: Movement param (word)
    remaining: bytes            # +0x14: Last 4 bytes
    
    @property
    def is_active(self) -> bool:
        return self.active != 0
    
    @property
    def has_data_table(self) -> bool:
        return self.data_table_idx != 0xFFFF
    
    @property
    def tactical_state(self) -> int:
        """Bits 0-4: Tactical state from data table"""
        return self.behavior_flags & 0x1F
    
    @property
    def temp_state(self) -> bool:
        """Bit 5 (0x20): Temporary state flag"""
        return bool(self.behavior_flags & 0x20)
    
    @property
    def is_armed(self) -> bool:
        """Bit 6 (0x40): Armed/weapon ready"""
        return bool(self.behavior_flags & 0x40)
    
    @property
    def target_sync(self) -> bool:
        """Bit 7 (0x80): Target synchronization"""
        return bool(self.behavior_flags & 0x80)
    
    def tactical_state_name(self) -> str:
        """Human-readable tactical state"""
        state = self.tactical_state
        states = {
            0x00: "Idle",
            0x01: "Ground Attack",
            0x02: "Landing",
            0x03: "Ground+Landing",
            0x04: "Cruise",
            0x05: "Cruise+Ground",
            0x06: "Cruise+Landing",
            0x07: "Cruise+Ground+Landing",
            0x08: "Combat",
            0x09: "Combat+Ground",
            0x0A: "Combat+Landing",
            0x0B: "Combat+Ground+Landing",
            0x0C: "Combat+Cruise",
            0x0D: "Combat+Cruise+Ground",
            0x0E: "Combat+Cruise+Landing",
            0x0F: "Combat+Cruise+Ground+Landing",
            0x10: "Special",
        }
        
        if state in states:
            return states[state]
        elif state > 0x10:
            return f"Special+0x{state-0x10:X}"
        else:
            return f"Unknown(0x{state:02X})"
    
    def format_flags(self) -> str:
        """Format all behavior flags"""
        parts = []
        
        # Tactical state (bits 0-4)
        parts.append(self.tactical_state_name())
        
        # Status flags (bits 5-7)
        status = []
        if self.temp_state:
            status.append("TEMP")
        if self.is_armed:
            status.append("ARMED")
        if self.target_sync:
            status.append("SYNC")
        
        if status:
            parts.append(f"[{' '.join(status)}]")
        
        return " ".join(parts)


def parse_context(data: bytes, index: int) -> AIContext:
    """Parse a single 24-byte AI context"""
    if len(data) < 24:
        raise ValueError(f"Context {index}: Need 24 bytes, got {len(data)}")
    
    # Unpack the structure (little-endian)
    # Format: B=byte, H=word(2 bytes)
    # +0: B active
    # +1: H entity_id
    # +3: H data_table_idx
    # +5: H param_1
    # +7: H param_2
    # +9: H param_3
    # +11: H behavior_flags
    # +13: B field_d
    # +14: B counter
    # +15: B threshold
    # +16: H velocity_x
    # +18: H velocity_y
    # +20: 4 bytes remaining
    values = struct.unpack_from('<BHHHHHHBBBHH', data, 0)
    
    return AIContext(
        index=index,
        active=values[0],
        entity_id=values[1],
        data_table_idx=values[2],
        param_1=values[3],
        param_2=values[4],
        param_3=values[5],
        behavior_flags=values[6],
        field_d=values[7],
        counter=values[8],
        threshold=values[9],
        velocity_x=values[10],
        velocity_y=values[11],
        remaining=data[20:24]
    )


def parse_all_contexts(data: bytes) -> List[AIContext]:
    """Parse all 40 AI contexts from 960-byte array"""
    if len(data) < 960:
        raise ValueError(f"Need 960 bytes for 40 contexts, got {len(data)}")
    
    contexts = []
    for i in range(40):
        offset = i * 24
        context_data = data[offset:offset+24]
        context = parse_context(context_data, i)
        contexts.append(context)
    
    return contexts


def print_context(ctx: AIContext, verbose: bool = False):
    """Print a single context"""
    if not verbose and not ctx.is_active:
        return
    
    print(f"Context[{ctx.index:2d}]:", end=" ")
    
    if not ctx.is_active:
        print("INACTIVE")
        return
    
    print(f"Entity={ctx.entity_id:04X}", end=" ")
    print(f"Table={ctx.data_table_idx:04X}" if ctx.has_data_table else "Table=NONE", end=" ")
    print(f"| {ctx.format_flags()}")
    
    if verbose:
        print(f"            Params: {ctx.param_1:04X} {ctx.param_2:04X} {ctx.param_3:04X}")
        print(f"            State:  counter={ctx.counter} threshold={ctx.threshold}")
        print(f"            Vel:    X={ctx.velocity_x:04X} Y={ctx.velocity_y:04X}")
        print()


def print_summary(contexts: List[AIContext]):
    """Print summary statistics"""
    active = [c for c in contexts if c.is_active]
    with_data = [c for c in active if c.has_data_table]
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Total contexts:     40")
    print(f"Active contexts:    {len(active)}")
    print(f"With data tables:   {len(with_data)}")
    print()
    
    if not with_data:
        print("No active contexts with data tables found.")
        return
    
    # Tactical state distribution
    tactical_counts = {}
    for ctx in with_data:
        state = ctx.tactical_state
        tactical_counts[state] = tactical_counts.get(state, 0) + 1
    
    print("Tactical State Distribution:")
    for state in sorted(tactical_counts.keys()):
        count = tactical_counts[state]
        ctx_temp = AIContext(0, 0, 0, 0, 0, 0, 0, state, 0, 0, 0, 0, 0, b'')
        name = ctx_temp.tactical_state_name()
        print(f"  0x{state:02X} {name:30s} : {count:2d} entities")
    
    # Status flags distribution
    armed = len([c for c in with_data if c.is_armed])
    synced = len([c for c in with_data if c.target_sync])
    temp = len([c for c in with_data if c.temp_state])
    
    print(f"\nStatus Flags:")
    print(f"  Armed:       {armed}")
    print(f"  Synced:      {synced}")
    print(f"  Temp state:  {temp}")
    
    # Data table indices
    print(f"\nData Table Indices:")
    indices = sorted(set(c.data_table_idx for c in with_data))
    print(f"  Unique indices: {len(indices)}")
    if len(indices) <= 20:
        print(f"  Indices: {', '.join(f'0x{i:04X}' for i in indices)}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    filename = sys.argv[1]
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    # Read binary file
    try:
        with open(filename, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    
    # Parse contexts
    try:
        contexts = parse_all_contexts(data)
    except ValueError as e:
        print(f"Error parsing contexts: {e}")
        sys.exit(1)
    
    # Print results
    print(f"{'='*70}")
    print(f"Falcon 3.0 AI Context Array")
    print(f"Source: {filename}")
    print(f"{'='*70}\n")
    
    for ctx in contexts:
        print_context(ctx, verbose)
    
    print_summary(contexts)


if __name__ == "__main__":
    main()
