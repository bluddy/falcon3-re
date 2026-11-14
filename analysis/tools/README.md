# Analysis Tools

**Python scripts for parsing, extracting, and analyzing game data**

## Purpose

This directory contains helper scripts for working with Falcon 3.0 binary data, memory dumps, and game files.

## Structure

```
tools/
├── data_parsers/       # Parse binary formats to readable data
├── data_extractors/    # Extract data from game files or memory
├── address_translator.py
├── segment_map.json
└── README.md (this file)
```

## Tool Categories

### `data_parsers/`
**Parse binary formats into readable data**

Scripts that read binary files and output structured data:
- `parse_mission_*.py` - Mission file parsers
- `parse_campaign_*.py` - Campaign data parsers
- `parse_ai_contexts.py` - AI memory dump parser
- `decode_*.py` - Binary format decoders

**Input**: Binary files (`.CAM`, `.bin`, etc.)  
**Output**: JSON, text, or structured data

### `data_extractors/`
**Extract data from game files**

Scripts that extract specific data from game files or running game:
- `extract_*.py` - Extract data from binary files
- `analyze_*.py` - Analyze extracted data
- `find_*.py` - Search for patterns in binaries

**Input**: Game files or memory dumps  
**Output**: Extracted binary data or analysis results

## Common Tools

### Address Translation
```python
# address_translator.py + segment_map.json
# Convert linear addresses to segment:offset
python address_translator.py segment_map.json linear 0x1297F0
# Output: R29_29FEs:1549
```

Used for:
- Converting IDA addresses to game memory layout
- Finding code in overlay segments
- Mapping between different address spaces

## Usage Patterns

### Parsing a Mission File
```bash
cd tools/data_parsers
python parse_mission_file.py ../../game/MISSIONS/TRAINING01.CAM > mission_parsed.json
```

### Extracting AI Contexts
```bash
cd tools/data_extractors
python extract_ai_from_memdump.py ../data_samples/memdump.bin > ../data_samples/ai_contexts/ai_extracted.bin
```

### Analyzing Data
```bash
cd tools/data_extractors
python analyze_flight_records.py ../data_samples/mission_files/waypoints.bin
```

## Creating New Tools

### Parser Template
```python
#!/usr/bin/env python3
"""
Parse <format> files from Falcon 3.0

Input: Binary <format> file
Output: Structured JSON data
"""

import sys
import json
import struct

def parse_format(data):
    """Parse binary format"""
    # Parse logic here
    return parsed_data

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input_file>")
        sys.exit(1)
    
    with open(sys.argv[1], 'rb') as f:
        data = f.read()
    
    result = parse_format(data)
    print(json.dumps(result, indent=2))
```

### Extractor Template
```python
#!/usr/bin/env python3
"""
Extract <data> from Falcon 3.0 files

Input: Game file or memory dump
Output: Extracted binary data
"""

import sys

def extract_data(input_data):
    """Extract specific data"""
    # Extraction logic
    return extracted

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input_file>")
        sys.exit(1)
    
    with open(sys.argv[1], 'rb') as f:
        data = f.read()
    
    extracted = extract_data(data)
    
    sys.stdout.buffer.write(extracted)
```

## Tool Organization

### When to create a parser
- Need to read a specific binary format
- Want human-readable output
- Format is documented in `docs/data_formats/`

### When to create an extractor
- Need to pull data from larger files
- Extracting from memory dumps
- Searching for specific patterns

### When to create an analyzer
- Need to understand data relationships
- Validating hypotheses about format
- Generating statistics or visualizations

## Documentation

Each tool should have:
1. **Docstring** at top of file explaining:
   - What it does
   - Input format
   - Output format
   - Example usage
2. **Usage message** if run with wrong arguments
3. **Comments** for non-obvious logic

## Dependencies

Most tools use only Python standard library:
- `struct` - Binary data parsing
- `json` - Structured output
- `sys` - I/O and arguments

If you need external libraries, document them in tool's docstring.

## Testing Tools

Before committing a new tool:
1. Test with sample data
2. Verify output is correct
3. Document expected behavior
4. Add example usage to docstring

## Maintenance

### When format changes
1. Update parser to handle new format
2. Update format spec in `docs/data_formats/`
3. Test with new sample files
4. Update tool version/timestamp

### When tool is superseded
1. Move to `archive/old_tools/`
2. Document why it was replaced
3. Update documentation to point to new tool

## Common Issues

### Binary data reading
```python
# Read binary file
with open(file, 'rb') as f:  # 'rb' not 'r'
    data = f.read()

# Parse structures
value = struct.unpack('<H', data[0:2])[0]  # Little-endian word
```

### Argument handling
```python
if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <file>", file=sys.stderr)
    sys.exit(1)
```

### Output formatting
```python
# JSON to stdout
print(json.dumps(data, indent=2))

# Binary to stdout
sys.stdout.buffer.write(binary_data)

# Text to stderr
print("Error: ...", file=sys.stderr)
```

## Questions?

- **Data formats**: Check `docs/data_formats/`
- **Sample data**: Check `data_samples/`
- **Python help**: Check tool docstrings

---

*Last updated: 2026-11-11*
