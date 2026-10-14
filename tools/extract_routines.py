#!/usr/bin/env python3
"""
Falcon 3.0 Track C - Extract Routines from IDB Assembly
Adapted from gunship_2000/tools/f19re/mzretools/tools/extract_routines.py

This script processes an assembly file exported from IDA (with fixups applied),
extracts procedures, and puts each one in a file for the splice pipeline.
"""

import sys
import re
import os.path
import argparse

# Regex patterns for Borland C++ 2.0 / MSC 5.1 / TASM assembly
PROC_RE = re.compile(r'^([_a-zA-Z0-9@?]+)\s+proc\s+(near|far)', re.IGNORECASE)
ENDP_RE = re.compile(r'^([_a-zA-Z0-9@?]+)\s+endp', re.IGNORECASE)
SEGMENT_RE = re.compile(r'^([_a-zA-Z0-9@?]+)\s+segment', re.IGNORECASE)
ENDSEG_RE = re.compile(r'^([_a-zA-Z0-9@?]+)\s+ends', re.IGNORECASE)

# Known library symbols to ignore
LIB_SYMBOLS = {
    'memcpy', 'memset', 'malloc', 'free', 'printf', 'scanf',
    'strcpy', 'strlen', 'strcmp', 'strcat',
    'abs', 'labs', 'sqrt', 'sin', 'cos',
    'inp', 'outp', 'inpd', 'outpd',
    '_dos_allocmem', '_dos_freemem', '_dos_setblock',
    'calloc', 'realloc', 'exit', 'atexit',
    '_chkstk', '_acrtused', '_aNchkstk',
}

def symbol_islib(symbol):
    return symbol in LIB_SYMBOLS

def token_ignored(token):
    if token.startswith('__'):
        return True
    if symbol_islib(token):
        return True
    return False

def line_empty(line):
    return not line.strip()

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

def process_token(token):
    if token_ignored(token):
        return None
    if len(token) > 2 and token[0] == '_' and token[1] != '_':
        striptoken = token[1:]
        if not symbol_islib(striptoken):
            return striptoken
    return token

def process_line(line):
    if not line or line_empty(line) or line.lstrip().startswith(';'):
        return ''
    
    # Handle IDA code byte annotation lines (starting with whitespace + address + bytes)
    stripped = line.lstrip()
    if re.match(r'^[0-9A-Fa-f]+:', stripped):
        # IDA format: address: bytes  instruction
        parts = stripped.split(None, 2)
        if len(parts) >= 3:
            return '\t' + parts[2]
        return ''
    
    if start_segment(line) or end_segment(line):
        return line.rstrip()
    elif start_proc(line) or end_proc(line):
        return line.rstrip()
    else:
        tokens = line.split()
        if not tokens:
            return ''
        newline = '\t'
        for i, t in enumerate(tokens):
            if i > 0:
                newline += ' '
            newtoken = process_token(t)
            if newtoken is None:
                return ''
            newline += newtoken
        return newline

def process_assembly(infile, outdir):
    curseg = ''
    curproc = ''
    outfile = None
    lineno = 0
    curproc_externs = set()
    
    for line in infile:
        lineno += 1
        p = process_line(line)
        if not p:
            continue
            
        if newseg := start_segment(p):
            if curseg:
                sys.stderr.write(f"WARNING: New segment '{newseg}' opened without closing previous '{curseg}' at line {lineno}\n")
            elif curproc:
                sys.stderr.write(f"WARNING: New segment '{newseg}' opened while procedure '{curproc}' not closed at line {lineno}\n")
            curseg = newseg
            curproc = ''
            sys.stderr.write(f"Segment start: '{curseg}'\n")
        elif endseg := end_segment(p):
            if not curseg:
                sys.stderr.write(f"WARNING: Closing segment '{endseg}' without one being open at line {lineno}\n")
            elif endseg != curseg:
                sys.stderr.write(f"WARNING: Closing segment '{endseg}' while current segment is '{curseg}' at line {lineno}\n")
            sys.stderr.write(f"Segment ends: '{curseg}'\n")
            curseg = ''
            curproc = ''
        elif newproc := start_proc(p):
            if not curseg:
                sys.stderr.write(f"WARNING: New procedure '{newproc}' without open segment at line {lineno}\n")
            curproc = newproc
            curproc_externs = set()
            outfilename = os.path.join(outdir, f"{newproc}.asm")
            sys.stderr.write(f"Found routine: '{curproc}' -> {outfilename}\n")
            if outfile:
                outfile.close()
            outfile = open(outfilename, "w", encoding='cp850')
        elif endproc := end_proc(p):
            if not curseg:
                sys.stderr.write(f"WARNING: Closing procedure '{endproc}' without open segment at line {lineno}\n")
            if not curproc:
                sys.stderr.write(f"WARNING: Closing procedure '{endproc}' without it being open at line {lineno}\n")
            if curproc_externs and outfile:
                for sym in sorted(curproc_externs):
                    outfile.write(f"EXTRN {sym}:FAR\n")
            sys.stderr.write(f"Routine end: '{curproc}'\n")
            # Keep curproc for potential function chunks
        if curproc and p and outfile:
            outfile.write(p + "\n")
    
    if outfile:
        outfile.close()

def main():
    parser = argparse.ArgumentParser(description='Extract routines from IDA assembly listing for Falcon 3.0 splice pipeline')
    parser.add_argument('asmfile', help='Input assembly file from IDA')
    parser.add_argument('outdir', help='Output directory for routine .asm files')
    args = parser.parse_args()
    
    if not os.path.isfile(args.asmfile):
        sys.exit(f"Input file does not exist: {args.asmfile}")
    
    os.makedirs(args.outdir, exist_ok=True)
    
    with open(args.asmfile, encoding='cp850', errors='ignore') as f:
        process_assembly(f, args.outdir)

if __name__ == '__main__':
    main()