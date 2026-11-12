#!/usr/bin/env python3
"""
Dump Level-1 batch 1 functions (top 15 by dynamic calls).
Level-1 = functions that call Level-0 (but are not Level-0 themselves).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CG = ROOT / "analysis" / "traces" / "callgraph_partial.json"
FB = ROOT / "analysis" / "ida_falconcd" / "function_bytes.json"
CLS = ROOT / "analysis" / "ida_falconcd" / "classification.json"
REG = ROOT / "registry" / "naming.yaml"

# Load data
cg = json.loads(CG.read_text())
fb = json.loads(FB.read_text())
cls = json.loads(CLS.read_text())

# Load named functions
import re
named = set()
for line in REG.read_text(encoding='utf-8').split('\n'):
    if m := re.match(r'^\s*-\s+ida:\s+(\w+)', line):
        named.add(m.group(1))

# Build Level-0 set (leaves with no callees)
all_fns = set(cls.keys())
level0 = set()
for fn in all_fns:
    callees = [edge[1] for edge in cg['edges'] if edge[0] == fn and edge[1] != fn]
    if len(callees) == 0:
        level0.add(fn)

# Build Level-1: functions that call Level-0 (but are not Level-0 themselves)
level1 = set()
for edge in cg['edges']:
    caller, callee = edge
    if callee in level0 and caller not in level0:
        level1.add(caller)

# Analyze Level-1 unnamed functions
level1_unnamed = [fn for fn in level1 if fn not in named]
level1_candidates = []

for fn in level1_unnamed:
    dyn = cg['dyn_target_calls'].get(fn, 0)
    static_in = cg['static_in_degree'].get(fn, 0)
    callees = [edge[1] for edge in cg['edges'] if edge[0] == fn and edge[1] != fn]
    
    level1_candidates.append({
        'name': fn,
        'ea': cls[fn]['ea'],
        'size': cls[fn]['size'],
        'dyn': dyn,
        'in': static_in,
        'out': len(callees),
    })

level1_candidates.sort(key=lambda x: (-x['dyn'], -x['in']))

# Extract batch 1: top 15
BATCH_SIZE = 15
batch1 = level1_candidates[:BATCH_SIZE]

print('Level-1 Batch 1 (top {} by dynamic calls)'.format(len(batch1)))
print('=' * 80)
print()

for i, node in enumerate(batch1, start=1):
    name = node['name']
    ea = node['ea']
    dyn = node['dyn']
    in_deg = node['in']
    out_deg = node['out']
    size = node['size']
    
    # Get bytecode
    fb_entry = fb.get(name, {})
    bytecode = fb_entry.get('bytes', '')
    
    # Get callees
    callees = [edge[1] for edge in cg['edges'] if edge[0] == name and edge[1] != name]
    
    print('Rank {}: {} (0x{:05X})'.format(i, name, ea))
    print('  size={}B, dyn={}, in={}, out={}'.format(size, dyn, in_deg, out_deg))
    print('  bytecode: {}'.format(bytecode))
    if callees:
        callee_list = ', '.join(callees[:5])
        if len(callees) > 5:
            callee_list += ' ... +{} more'.format(len(callees) - 5)
        print('  callees: {}'.format(callee_list))
    print()

print()
print('Summary:')
print('  Total: {} functions'.format(len(batch1)))
print('  Size range: {}-{}B'.format(min(n['size'] for n in batch1), max(n['size'] for n in batch1)))
print('  Call range: {}-{} dyn_calls'.format(min(n['dyn'] for n in batch1), max(n['dyn'] for n in batch1)))
print('  Callees range: {}-{} (out-degree)'.format(min(n['out'] for n in batch1), max(n['out'] for n in batch1)))
