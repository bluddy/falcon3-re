"""
Catalog all Falcon 3.0 game files with known and unknown formats.
Combines documentation knowledge with file system analysis.
"""

import os
import json
from pathlib import Path
from collections import defaultdict
import hashlib

# Known file format information from docs and analysis
KNOWN_FORMATS = {
    '.CAM': {
        'name': 'Campaign Save File',
        'size': 11828,
        'status': 'Partially Decoded',
        'docs': 'CAMPAIGN_FILE_FORMAT.md',
        'contains': 'Squadron data, campaign state, pilot records',
        'examples': ['SQUAD0.CAM', 'SQUAD1.CAM']
    },
    '.IDX': {
        'name': 'Index File',
        'status': 'Partially Decoded',
        'docs': 'findings_log.md',
        'contains': 'File offsets and metadata for paired .DAT files',
        'pairs_with': '.DAT'
    },
    '.DAT': {
        'name': 'Data File',
        'status': 'Partially Decoded',
        'docs': 'findings_log.md',
        'contains': 'Binary data indexed by .IDX files',
        'examples': ['DISPLAY.DAT', 'ARMSDATA/*.DAT', 'REPORT.DAT']
    },
    '.PAK': {
        'name': 'Package Archive',
        'status': 'Known',
        'contains': 'PKWARE compressed data',
        'notes': 'Assets already extracted in game/ directory'
    },
    '.MIS': {
        'name': 'Mission File',
        'status': 'Partially Known',
        'docs': 'manual_full.txt, game_knowledge.yaml',
        'contains': 'Mission definitions and parameters'
    },
    '.PAL': {
        'name': 'Palette File',
        'status': 'Likely Standard VGA',
        'contains': '256-color palette data',
        'format': 'Likely 768 bytes (RGB triplets)'
    },
    '.SHP': {
        'name': 'Shape/Sprite File',
        'status': 'Unknown',
        'contains': 'Graphics data (sprites, shapes)',
        'likely': '2D or 3D model data'
    },
    '.BIN': {
        'name': 'Binary Data',
        'status': 'Multiple Types',
        'contains': 'Various binary data (models, textures, etc)',
        'examples': ['FalcObj.Bin', 'FSXObj.Bin']
    },
    '.RFM': {
        'name': 'Unknown Format',
        'status': 'Unknown',
        'count': 42,
        'notes': 'Second most common extension'
    },
    '.EXE': {
        'name': 'Executable',
        'status': 'Analyzed',
        'docs': 'Complete IDA analysis',
        'examples': ['FALCONCD.EXE']
    },
    '.OVL': {
        'name': 'Overlay File',
        'status': 'Known',
        'docs': 'overlay_architecture_note.md',
        'contains': 'Code overlays for memory management'
    },
    # Mission/Campaign related
    '.SQU': {'name': 'Squadron File', 'status': 'Unknown'},
    '.WAR': {'name': 'War/Theater File', 'status': 'Unknown'},
    '.THE': {'name': 'Theater File', 'status': 'Unknown'},
    
    # Graphics/Media
    '.MTV': {'name': 'Video File?', 'status': 'Unknown'},
    '.PAN': {'name': 'Panorama/Panel?', 'status': 'Unknown'},
    '.VCR': {'name': 'Video Capture/Replay', 'status': 'Unknown'},
    
    # Text/Strings
    '.STR': {'name': 'String File', 'status': 'Unknown'},
    '.TXT': {'name': 'Text File', 'status': 'Standard'},
    
    # Configuration
    '.CFG': {'name': 'Configuration', 'status': 'Standard'},
    '.DEF': {'name': 'Definition File', 'status': 'Unknown'},
    
    # Language/Localization (8 of each suggests language packs)
    '.KOR': {'name': 'Korean Language', 'status': 'Unknown', 'count': 8},
    '.NEL': {'name': 'Unknown Language?', 'status': 'Unknown', 'count': 8},
    '.BOS': {'name': 'Unknown Language?', 'status': 'Unknown', 'count': 8},
    '.HOK': {'name': 'Unknown Language?', 'status': 'Unknown', 'count': 8},
    
    # Misc Data Files (8 of each - likely related set)
    '.MFF': {'name': 'Unknown', 'status': 'Unknown', 'count': 8},
    '.MFI': {'name': 'Unknown', 'status': 'Unknown', 'count': 8},
    '.MIF': {'name': 'Unknown', 'status': 'Unknown'},
    '.MIM': {'name': 'Unknown', 'status': 'Unknown'},
    '.MHF': {'name': 'Unknown', 'status': 'Unknown', 'count': 8},
    '.MHC': {'name': 'Unknown', 'status': 'Unknown', 'count': 8},
}

def analyze_file(path):
    """Analyze a single file and return metadata."""
    stat = path.stat()
    
    # Read first 16 bytes for signature detection
    signature = b''
    try:
        with open(path, 'rb') as f:
            signature = f.read(16)
    except:
        pass
    
    return {
        'name': path.name,
        'size': stat.st_size,
        'signature_hex': signature.hex() if signature else '',
        'signature_ascii': ''.join(chr(b) if 32 <= b < 127 else '.' for b in signature) if signature else ''
    }

def main():
    game_dir = Path(r"C:\Users\ybarnoy\projects\falcon3\game")
    
    if not game_dir.exists():
        print(f"ERROR: Game directory not found: {game_dir}")
        return
    
    print("=" * 80)
    print("FALCON 3.0 FILE CATALOG")
    print("=" * 80)
    print()
    
    # Collect all files by extension
    files_by_ext = defaultdict(list)
    
    for file_path in game_dir.rglob('*'):
        if file_path.is_file():
            ext = file_path.suffix.upper() if file_path.suffix else '(no extension)'
            files_by_ext[ext].append(file_path)
    
    # Sort by count
    sorted_exts = sorted(files_by_ext.items(), key=lambda x: len(x[1]), reverse=True)
    
    print(f"Total file extensions: {len(sorted_exts)}")
    print(f"Total files: {sum(len(files) for files in files_by_ext.values())}")
    print()
    
    # Generate report
    report = {
        'summary': {
            'total_extensions': len(sorted_exts),
            'total_files': sum(len(files) for files in files_by_ext.values()),
            'known_formats': len([k for k in KNOWN_FORMATS if k in files_by_ext]),
            'unknown_formats': len([ext for ext in files_by_ext if ext not in KNOWN_FORMATS and ext != '(no extension)'])
        },
        'extensions': {}
    }
    
    for ext, files in sorted_exts[:50]:  # Top 50
        count = len(files)
        total_size = sum(f.stat().st_size for f in files)
        avg_size = total_size / count if count > 0 else 0
        
        # Get format info
        format_info = KNOWN_FORMATS.get(ext, {})
        status = format_info.get('status', 'Unknown')
        name = format_info.get('name', '?')
        
        print(f"{ext:15s} {count:4d} files  {total_size:12,d} bytes  avg={avg_size:10,.0f}  [{status}] {name}")
        
        # Sample a few files for signature analysis
        samples = []
        for file_path in files[:3]:
            samples.append(analyze_file(file_path))
        
        report['extensions'][ext] = {
            'count': count,
            'total_size': total_size,
            'avg_size': int(avg_size),
            'status': status,
            'name': name,
            'format_info': format_info,
            'samples': samples
        }
    
    # Save report
    output_path = Path(r"C:\Users\ybarnoy\projects\falcon3\temp\file_catalog.json")
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print()
    print("=" * 80)
    print(f"Full report saved to: {output_path}")
    print()
    
    # Priority unknown formats to investigate
    print("PRIORITY UNKNOWN FORMATS (by frequency):")
    print("-" * 80)
    
    unknown = [(ext, len(files)) for ext, files in sorted_exts 
               if ext not in KNOWN_FORMATS and ext != '(no extension)'][:15]
    
    for ext, count in unknown:
        print(f"  {ext:15s} {count:4d} files")
    
    print()
    print("IMAGE FILE CANDIDATES:")
    print("-" * 80)
    
    image_candidates = ['.SHP', '.BIN', '.PAL', '.PAN', '.MTV']
    for ext in image_candidates:
        if ext in files_by_ext:
            print(f"  {ext:15s} {len(files_by_ext[ext]):4d} files")
    
    print()

if __name__ == "__main__":
    main()
