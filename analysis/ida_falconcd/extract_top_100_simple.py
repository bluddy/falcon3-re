import ida_auto
import ida_funcs
import ida_xref
import idc
import json

ida_auto.auto_wait()

print("Extracting function data...")

function_data = []

# Iterate through all functions
for func_ea in ida_funcs.Functions():
    func_name = idc.get_func_name(func_ea)
    
    # Count callers
    callers = set()
    for xref in ida_xref.XrefsTo(func_ea, 0):
        if xref.type in [ida_xref.fl_CN, ida_xref.fl_CF]:
            callers.add(xref.frm)
    
    # Get size
    func = ida_funcs.get_func(func_ea)
    size = func.end_ea - func.start_ea if func else 0
    
    function_data.append({
        'address': func_ea,
        'name': func_name,
        'callers': len(callers),
        'size': size
    })

# Sort by callers
function_data.sort(key=lambda x: x['callers'], reverse=True)

# Write JSON
output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\top_100_functions.json"
with open(output_file, 'w') as f:
    json.dump(function_data[:100], f, indent=2)

print(f"Wrote {len(function_data[:100])} functions to {output_file}")
print("\nTop 10:")
for i, func in enumerate(function_data[:10], 1):
    print(f"  {i}. {func['name']}: {func['callers']} callers")

idc.qexit(0)
