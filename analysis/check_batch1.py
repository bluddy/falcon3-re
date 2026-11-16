import json

d = json.load(open('ida_naming_report.json'))
print(f'Total: {d["total_functions"]}')
print(f'Renamed: {d["renamed"]}')
print(f'Already correct: {d["already_correct"]}')
print(f'Failed: {d["failed"]}')
print()
print('Checking our new batch 1 functions:')
addrs = ['0x2c53b', '0x2c8ab', '0x2c8c9', '0x2c8d3', '0x2c905', '0x2c919', '0x36fe5',
         '0x100bd0', '0x101659', '0x12fa2a', 
         '0x1573c3', '0x181bc7', '0x1a0a0f', '0x11cf6a', '0x122595']

for addr in addrs:
    func = d['functions'].get(addr)
    if func:
        print(f'{addr}: {func.get("name", "NO NAME")} - {"OK" if func.get("current_name") == func.get("name") else "MISMATCH"}')
    else:
        print(f'{addr}: NOT IN REPORT')
