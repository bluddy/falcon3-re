import json

d = json.load(open('ida_naming_report.json'))
print(f'Total: {d["total_functions"]}')
print(f'Renamed: {d["renamed"]}')
print(f'Already correct: {d["already_correct"]}')
print(f'Failed: {d["failed"]}')
print()
print('Checking batch 2 functions:')
addrs = ['0x128028', '0x128042', '0x130ce7', '0x133bd5', '0x13aba7', 
         '0x1558c8', '0x16f4b1', '0x172436', '0x17b2b6', 
         '0x196bb9', '0x19fe2d', '0x2c185', '0x345fd']

for addr in addrs:
    func = d['functions'].get(addr)
    if func:
        print(f'{addr}: {func.get("name", "NO NAME")} - {"OK" if func.get("current_name") == func.get("name") else "MISMATCH"}')
    else:
        print(f'{addr}: NOT IN REPORT')
