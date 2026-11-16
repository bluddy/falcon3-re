import json

d = json.load(open('ida_naming_report.json'))
print(f'Total: {d["total_functions"]}')
print(f'Renamed: {d["renamed"]}')
print(f'Already correct: {d["already_correct"]}')
print(f'Failed: {d["failed"]}')
print()
print('Checking Top 500 batch 2 functions:')

addrs = ['0x1854cf', '0x1a6aa6', '0x1a86c6', '0x2978e', '0x3e01a',
         '0x3f287', '0x43842', '0x47b68', '0x4aaa4', '0x4ac1e',
         '0x4ae66', '0x106b07', '0x11d346', '0x11d388', '0x11d3ca',
         '0x11fc1b', '0x127ff6', '0x1298ab', '0x1299ae', '0x129a87',
         '0x12be93', '0x12bed1', '0x12d4e3', '0x132182', '0x13296e',
         '0x13367b', '0x136133']

for addr in addrs:
    func = d['functions'].get(addr)
    if func:
        status = "OK" if func.get("current_name") == func.get("name") else "MISMATCH"
        print(f'{addr}: {func.get("name", "NO NAME"):<45s} - {status}')
    else:
        print(f'{addr}: NOT IN REPORT')
