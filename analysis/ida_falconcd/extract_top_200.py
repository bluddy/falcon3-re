import idaapi
import idautils
import idc
import json

def get_top_200_by_calls():
    """Extract top 200 functions by call count"""
    
    functions = []
    
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        func = idaapi.get_func(func_ea)
        if not func:
            continue
            
        # Count xrefs (calls to this function)
        xrefs = list(idautils.XrefsTo(func_ea))
        call_count = len([x for x in xrefs if x.type in [
            idaapi.fl_CN,  # Near call
            idaapi.fl_CF,  # Far call
        ]])
        
        size = func.end_ea - func.start_ea
        
        functions.append({
            'name': name,
            'address': f'0x{func_ea:x}',
            'start': f'0x{func.start_ea:x}',
            'end': f'0x{func.end_ea:x}',
            'size': size,
            'calls': call_count,
            'category': 'uncategorized'
        })
    
    # Sort by call count descending
    functions.sort(key=lambda x: x['calls'], reverse=True)
    
    # Take top 200
    top_200 = functions[:200]
    
    # Write to JSON
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\top_200_functions.json'
    with open(output_path, 'w') as f:
        json.dump(top_200, f, indent=4)
    
    print(f"[+] Extracted top 200 functions by call count")
    print(f"[+] Saved to {output_path}")
    print(f"\nTop 10:")
    for i, func in enumerate(top_200[:10], 1):
        print(f"  {i}. {func['name']} @ {func['address']}: {func['calls']} calls, {func['size']} bytes")
    
    print(f"\nRank #101-110:")
    for i, func in enumerate(top_200[100:110], 101):
        print(f"  {i}. {func['name']} @ {func['address']}: {func['calls']} calls, {func['size']} bytes")

if __name__ == '__main__':
    get_top_200_by_calls()
