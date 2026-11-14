#!/usr/bin/env python3
"""Fix doubled CRs in manifest"""
data = open('../../registry/orphan_funcs_expected.json', 'rb').read()
fixed = data.replace(b'\r\r\n', b'\r\n')
open('../../registry/orphan_funcs_expected.json', 'wb').write(fixed)
count = data.count(b'\r\r\n')
print(f"Fixed {count} doubled CRs")
