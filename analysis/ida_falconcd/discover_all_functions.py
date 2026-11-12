"""
Discover and categorize all functions in Falcon 3.0 by system.
Extract actual function names from IDA database.
"""
import idc
import idaapi
import idautils
import json
import re

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\all_functions_categorized.json"

def categorize_function(name, addr):
    """Categorize a function by name patterns."""
    name_lower = name.lower()
    
    # Overlay system
    if any(x in name_lower for x in ['overlay', 'hud_draw', 'draw_line', 'draw_circle', 'draw_text']):
        return 'overlay'
    
    # HUD system
    if any(x in name_lower for x in ['hud_', 'airspeed', 'altitude', 'heading', 'reticle', 'target_box']):
        return 'hud'
    
    # Physics system
    if any(x in name_lower for x in ['physics', 'aero', 'flight', 'lift', 'drag', 'thrust', 'integrate']):
        return 'physics'
    
    # Weapons system
    if any(x in name_lower for x in ['weapon', 'missile', 'gun', 'bomb', 'fire', 'launch', 'damage']):
        return 'weapons'
    
    # AI system
    if any(x in name_lower for x in ['ai_', 'maneuver', 'engage', 'evade', 'pursuit', 'threat', 'formation']):
        return 'ai'
    
    # Targeting/Radar
    if any(x in name_lower for x in ['radar', 'target', 'lock', 'track', 'rwr', 'sensor']):
        return 'targeting'
    
    # Terrain system
    if any(x in name_lower for x in ['terrain', 'ground', 'elevation', 'height']):
        return 'terrain'
    
    # Rendering system
    if any(x in name_lower for x in ['render', 'view', 'projection', 'transform', 'camera']):
        return 'rendering'
    
    # Input system
    if any(x in name_lower for x in ['input', 'keyboard', 'mouse', 'joystick', 'joy_', 'control']):
        return 'input'
    
    # Audio system
    if any(x in name_lower for x in ['audio', 'sound', 'snd_', 'music', 'speaker', 'beep']):
        return 'audio'
    
    return 'uncategorized'

def get_all_functions():
    """Get all functions from IDA database."""
    idaapi.auto_wait()
    
    functions = []
    for ea in idautils.Functions():
        func = idaapi.get_func(ea)
        if not func:
            continue
        
        name = idc.get_name(ea, idc.GN_VISIBLE)
        if not name:
            name = f"sub_{ea:X}"
        
        # Get basic info
        size = func.end_ea - func.start_ea
        
        # Count calls
        call_count = 0
        for item_ea in idautils.FuncItems(ea):
            if idc.print_insn_mnem(item_ea) == "call":
                call_count += 1
        
        # Categorize
        category = categorize_function(name, ea)
        
        functions.append({
            "name": name,
            "address": hex(ea),
            "start": hex(func.start_ea),
            "end": hex(func.end_ea),
            "size": size,
            "calls": call_count,
            "category": category
        })
    
    return functions

def analyze_by_category(functions):
    """Group functions by category and compute stats."""
    categories = {}
    
    for func in functions:
        cat = func['category']
        if cat not in categories:
            categories[cat] = {
                'functions': [],
                'count': 0,
                'total_size': 0,
                'total_calls': 0
            }
        
        categories[cat]['functions'].append(func)
        categories[cat]['count'] += 1
        categories[cat]['total_size'] += func['size']
        categories[cat]['total_calls'] += func['calls']
    
    return categories

# Main execution
try:
    print("Discovering all functions...")
    functions = get_all_functions()
    print(f"Found {len(functions)} functions")
    
    print("\nCategorizing by system...")
    categories = analyze_by_category(functions)
    
    # Print summary
    print("\n" + "="*80)
    print("FUNCTION CATEGORIZATION SUMMARY")
    print("="*80)
    
    category_order = [
        'rendering', 'culling', 'terrain', 'overlay', 'hud', 
        'physics', 'weapons', 'ai', 'targeting', 'input', 'audio',
        'uncategorized'
    ]
    
    for cat in category_order:
        if cat in categories:
            info = categories[cat]
            avg_size = info['total_size'] / info['count'] if info['count'] > 0 else 0
            avg_calls = info['total_calls'] / info['count'] if info['count'] > 0 else 0
            print(f"\n{cat.upper()}:")
            print(f"  Functions: {info['count']}")
            print(f"  Total size: {info['total_size']} bytes")
            print(f"  Total calls: {info['total_calls']}")
            print(f"  Avg size: {avg_size:.1f} bytes")
            print(f"  Avg calls: {avg_calls:.1f}")
            
            # Show first 10 function names
            if info['count'] > 0:
                print(f"  Sample functions:")
                for func in info['functions'][:10]:
                    print(f"    {func['name']} ({func['size']} bytes, {func['calls']} calls)")
    
    # Save to JSON
    output = {
        'total_functions': len(functions),
        'categories': categories,
        'all_functions': functions
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n\nComplete analysis saved to: {OUTPUT_FILE}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

idc.qexit(0)
