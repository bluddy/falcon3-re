"""
Address translation utilities using exported segment map.

Converts between linear addresses and IDA segment:offset notation.
"""

import json
import sys
from pathlib import Path

class AddressTranslator:
    def __init__(self, segment_map_path):
        """Load segment map from JSON export."""
        with open(segment_map_path, 'r') as f:
            data = json.load(f)
        
        self.segments = data['segments']
        self.multi_entry = data.get('multi_entry_functions', {})
        self.functions = {f['start_ea']: f for f in data.get('functions', [])}
        
        # Build lookup indices
        self._build_indices()
    
    def _build_indices(self):
        """Build efficient lookup structures."""
        # Sort segments by start address
        self.segments.sort(key=lambda s: s['start_ea'])
        
        # Build name to segment map
        self.seg_by_name = {s['name']: s for s in self.segments}
    
    def linear_to_segoff(self, linear_addr):
        """
        Convert linear address to segment:offset.
        
        Returns: tuple (segment_name, offset) or None if not found
        """
        for seg in self.segments:
            if seg['start_ea'] <= linear_addr < seg['end_ea']:
                offset = linear_addr - seg['start_ea']
                return (seg['name'], offset)
        return None
    
    def segoff_to_linear(self, seg_name, offset):
        """
        Convert segment:offset to linear address.
        
        Args:
            seg_name: Segment name (e.g., 'seg020')
            offset: Offset within segment
        
        Returns: linear address or None if segment not found
        """
        seg = self.seg_by_name.get(seg_name)
        if seg:
            return seg['start_ea'] + offset
        return None
    
    def parse_segoff(self, segoff_str):
        """
        Parse segment:offset string like 'seg020:051B'.
        
        Returns: linear address or None
        """
        if ':' not in segoff_str:
            return None
        
        seg_name, offset_str = segoff_str.split(':', 1)
        try:
            offset = int(offset_str, 16)
            return self.segoff_to_linear(seg_name, offset)
        except ValueError:
            return None
    
    def format_segoff(self, linear_addr):
        """
        Format linear address as segment:offset string.
        
        Returns: string like 'seg020:051B' or hex if not in segment
        """
        result = self.linear_to_segoff(linear_addr)
        if result:
            seg_name, offset = result
            return f"{seg_name}:{offset:04X}"
        return f"0x{linear_addr:X}"
    
    def find_function(self, addr):
        """
        Find function containing address (main entry or secondary).
        
        Returns: dict with function info and entry type
        """
        # Check if it's a main entry point
        if addr in self.functions:
            func = self.functions[addr]
            return {
                'type': 'main_entry',
                'function': func['name'],
                'start_ea': func['start_ea'],
                'segoff': func['segoff']
            }
        
        # Check if it's a secondary entry point
        for func_name, entries in self.multi_entry.items():
            for entry in entries:
                if entry['address'] == addr:
                    return {
                        'type': 'secondary_entry',
                        'function': func_name,
                        'entry_address': addr,
                        'segoff': entry['segoff'],
                        'offset_from_start': entry['offset_from_start'],
                        'xref_count': entry['xref_count']
                    }
        
        # Check if address is inside any function
        for func in self.functions.values():
            if func['start_ea'] <= addr < func['end_ea']:
                return {
                    'type': 'mid_function',
                    'function': func['name'],
                    'function_start': func['start_ea'],
                    'offset_from_start': addr - func['start_ea']
                }
        
        return None
    
    def list_segments(self):
        """Print segment map."""
        print("\nSegment Map:")
        print("=" * 70)
        print(f"{'Name':<12} {'Start':<10} {'End':<10} {'Size':<8} {'Class':<12}")
        print("-" * 70)
        for seg in self.segments:
            size = seg['end_ea'] - seg['start_ea']
            print(f"{seg['name']:<12} 0x{seg['start_ea']:08X} 0x{seg['end_ea']:08X} "
                  f"{size:7d}  {seg.get('class', ''):<12}")
        print("=" * 70)
    
    def list_multi_entry(self, limit=20):
        """Print multi-entry functions."""
        print("\nMulti-Entry Functions:")
        print("=" * 70)
        
        # Sort by total entry count
        sorted_funcs = sorted(
            self.multi_entry.items(),
            key=lambda x: sum(e['xref_count'] for e in x[1]),
            reverse=True
        )
        
        for i, (func_name, entries) in enumerate(sorted_funcs[:limit], 1):
            total_xrefs = sum(e['xref_count'] for e in entries)
            print(f"\n{i}. {func_name} - {len(entries)} secondary entries, {total_xrefs} total xrefs")
            for entry in entries:
                print(f"   {entry['segoff']:<16} (+0x{entry['offset_from_start']:04X})  "
                      f"{entry['xref_count']:5d} xrefs")
        print("=" * 70)

def main():
    if len(sys.argv) < 2:
        print("Usage: python address_translator.py <segment_map.json> [command]")
        print("\nCommands:")
        print("  segments              - List all segments")
        print("  multi                 - List multi-entry functions")
        print("  linear <addr>         - Convert linear to segment:offset")
        print("  segoff <seg:off>      - Convert segment:offset to linear")
        print("  find <addr>           - Find function containing address")
        return
    
    map_path = Path(sys.argv[1])
    if not map_path.exists():
        print(f"Error: {map_path} not found")
        return
    
    translator = AddressTranslator(map_path)
    
    if len(sys.argv) < 3:
        # Default: show summary
        translator.list_segments()
        translator.list_multi_entry(limit=10)
        return
    
    command = sys.argv[2].lower()
    
    if command == 'segments':
        translator.list_segments()
    
    elif command == 'multi':
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        translator.list_multi_entry(limit=limit)
    
    elif command == 'linear':
        if len(sys.argv) < 4:
            print("Usage: linear <address>")
            return
        addr_str = sys.argv[3]
        addr = int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str, 16)
        
        segoff = translator.format_segoff(addr)
        func_info = translator.find_function(addr)
        
        print(f"\nLinear: 0x{addr:X}")
        print(f"SegOff: {segoff}")
        if func_info:
            print(f"Function: {func_info}")
    
    elif command == 'segoff':
        if len(sys.argv) < 4:
            print("Usage: segoff <seg:offset>")
            return
        segoff_str = sys.argv[3]
        
        linear = translator.parse_segoff(segoff_str)
        if linear is not None:
            func_info = translator.find_function(linear)
            print(f"\nSegOff: {segoff_str}")
            print(f"Linear: 0x{linear:X}")
            if func_info:
                print(f"Function: {func_info}")
        else:
            print(f"Error: Could not parse '{segoff_str}'")
    
    elif command == 'find':
        if len(sys.argv) < 4:
            print("Usage: find <address>")
            return
        
        addr_str = sys.argv[3]
        # Try to parse as linear or segment:offset
        if ':' in addr_str:
            addr = translator.parse_segoff(addr_str)
        else:
            addr = int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str, 16)
        
        if addr is not None:
            func_info = translator.find_function(addr)
            print(f"\nAddress: {translator.format_segoff(addr)} (0x{addr:X})")
            if func_info:
                print("\nFunction Info:")
                for key, value in func_info.items():
                    if isinstance(value, int):
                        print(f"  {key}: 0x{value:X}")
                    else:
                        print(f"  {key}: {value}")
            else:
                print("Not found in any function")
        else:
            print(f"Error: Could not parse address '{addr_str}'")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == '__main__':
    main()
