#!/usr/bin/env python3
"""
Falcon 3.0 Track C - Splice Verified Routines into IDB Assembly
Adapted from gunship_2000/tools/f19re/mzretools/tools/replace_routines.py

This script takes an assembly listing exported from IDA and replaces routines
with their verified C implementations (compiled to .asm by portcheck).
"""

import sys
import os
import argparse

# Reuse the same regex patterns
PROC_RE = re.compile(r'^([_a-zA-Z0-9@?]+)\s+proc\s+(near|far)', re.IGNORECASE)
ENDP_RE = re.compile(r'^([_a-zA-Z0-9@?]+)\s+endp', re.IGNORECASE)
SEGMENT_RE = re.compile(r'^([_a-zA-Z0-9@?]+)\s+segment', re.IGNORECASE)
ENDSEG_RE = re.compile(r'^([_a-zA-Z0-9@?]+)\s+ends', re.IGNORECASE)

import re

def start_proc(line):
    m = PROC_RE.match(line.strip())
    return m.group(1) if m else None

def end_proc(line):
    m = ENDP_RE.match(line.strip())
    return m.group(1) if m else None

def start_segment(line):
    m = SEGMENT_RE.match(line.strip())
    return m.group(1) if m else None

def end_segment(line):
    m = ENDSEG_RE.match(line.strip())
    return m.group(1) if m else None

def process_assembly(infile, outfile, routine_dir, verified_file=None):
    """Replace routines in assembly with verified implementations.
    
    Args:
        infile: Input IDB assembly file
        outfile: Output spliced assembly file
        routine_dir: Directory containing verified .asm files
        verified_file: Optional path to registry/routines.yaml for verification status
    """
    proc = None
    lineno = 0
    replaced = 0
    skipped = 0
    
    # Load verified routines list
    verified_routines = set()
    if verified_file and os.path.isfile(verified_file):
        import yaml
        with open(verified_file, 'r') as f:
            data = yaml.safe_load(f)
        for entry in data.get('routines', []):
            if entry.get('verified') == 'MATCH' and entry.get('port_file'):
                verified_routines.add(entry['ida_name'])
        sys.stderr.write(f"Loaded {len(verified_routines)} verified routines from {verified_file}\n")
    
    for line in infile:
        lineno += 1
        if newproc := start_proc(line):
            if proc:
                sys.stderr.write(f"WARNING: New routine ({newproc}) start while previous ({proc}) not closed at line {lineno}\n")
            
            # Check if we have a verified implementation
            routine_path = os.path.join(routine_dir, newproc + ".asm")
            
            if newproc in verified_routines and os.path.isfile(routine_path):
                sys.stderr.write(f"SPLICE: {newproc} -> {routine_path}\n")
                proc = newproc
                outfile.write(f"; SPLICED: {newproc} replaced with verified implementation\n")
                outfile.write(f"include {routine_dir}{os.sep}{newproc}.asm\n")
                replaced += 1
            else:
                if newproc in verified_routines:
                    sys.stderr.write(f"SKIP: {newproc} verified but no .asm file at {routine_path}\n")
                else:
                    sys.stderr.write(f"KEEP: {newproc} not verified\n")
                proc = None
                outfile.write(line)
        elif proc and (endproc := end_proc(line)):
            if endproc != proc:
                sys.stderr.write(f"WARNING: End of routine {endproc} without closing previous routine: {proc} at line {lineno}\n")
            proc = None
        elif proc is None:
            outfile.write(line)
    
    sys.stderr.write(f"Splice complete: {replaced} replaced, {skipped} skipped\n")
    return replaced

def main():
    parser = argparse.ArgumentParser(description='Splice verified Falcon 3.0 routines into IDB assembly')
    parser.add_argument('infile', help='Input IDB assembly file (.asm)')
    parser.add_argument('outfile', help='Output spliced assembly file (.asm)')
    parser.add_argument('routine_dir', help='Directory containing verified routine .asm files')
    parser.add_argument('--verified', help='Path to registry/routines.yaml for verification status')
    args = parser.parse_args()
    
    if not os.path.isfile(args.infile):
        sys.exit(f"Input file does not exist: {args.infile}")
    if not os.path.isdir(args.routine_dir):
        sys.exit(f"Routines directory '{args.routine_dir}' does not exist")
    
    with open(args.infile, encoding='cp850', errors='ignore') as infile, \
         open(args.outfile, "w", encoding='cp850') as outfile:
        process_assembly(infile, outfile, args.routine_dir, args.verified)

if __name__ == '__main__':
    main()