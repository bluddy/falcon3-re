import json

d = json.load(open('ida_naming_report.json'))
print(f'Total: {d["total_functions"]}')
print(f'Renamed: {d["renamed"]}')
print(f'Already correct: {d["already_correct"]}')
print(f'Failed: {d["failed"]}')
print()
print('Checking Top 500 batch 1 functions:')

addrs = ['0x3de6f', '0x4fecc', '0x100acc', '0x102932', '0x1086c1',
         '0x11cb23', '0x11ceab', '0x123fdd', '0x12a114', '0x12a908',
         '0x12bc4f', '0x12bc64', '0x12bc83', '0x12d4f6', '0x12d525',
         '0x139169', '0x13d744', '0x163ccd', '0x17df4d', '0x1852e5']

for addr in addrs:
    func = d['functions'].get(addr)
    if func:
        status = "OK" if func.get("current_name") == func.get("name") else "MISMATCH"
        print(f'{addr}: {func.get("name", "NO NAME"):<45s} - {status}')
    else:
        print(f'{addr}: NOT IN REPORT')
