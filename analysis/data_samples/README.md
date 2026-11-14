# Data Samples

**Extracted game data for analysis and visualization**

## Purpose

This directory contains binary data, visualizations, and parsed data extracted from Falcon 3.0 game files for analysis purposes.

## Structure

```
data_samples/
├── isldat/             # Island terrain data
├── ai_contexts/        # AI memory dumps
├── mission_files/      # Parsed mission data
└── README.md (this file)
```

## Subdirectories

### `isldat/`
**Island terrain data and visualizations**

Extracted and visualized terrain data from .ISL/.DAT files:
- SVG visualizations of coastlines, rivers, roads
- Extracted polygon geometry
- Tile heightmap data
- Quad-tree structure samples

**File format documentation**: `docs/data_formats/isldat.md`

**Contents**:
- `coast_edges/` - Coastline polygon data
- `clean_coasts/` - Cleaned coastline visualizations
- `rivers/` - River and road vectors
- `tiles/` - Individual terrain tile samples
- `svgs/` - Various SVG visualizations

### `ai_contexts/`
**AI system memory dumps**

Binary dumps of AI context data from running game:
- `ai_contexts_flight.bin` - In-flight AI states
- `ai_contexts_mission.bin` - Mission AI data
- `ai_contexts_sim.bin` - Simulator AI states

**Format**: 40 × 24-byte AI context records

**Documentation**: `docs/architecture/ai.md`

### `mission_files/`
**Parsed mission and campaign data**

Extracted mission files, campaign state, and parsed data:
- Mission waypoints
- Squadron data
- Supply inventory
- Campaign targets

**Format documentation**: `docs/data_formats/mission_files.md`

## When to Add Data Samples

✅ **Add data samples when**:
- Extracting binary data from game files
- Creating visualizations for analysis
- Dumping memory from running game
- Parsing data files into readable formats
- Need examples for testing tools

❌ **Don't add**:
- Complete game files (keep those in `game/`)
- Temporary debugging output (those go in `archive/output_files/`)
- Generated files that can be recreated (unless they're expensive to generate)

## Naming Conventions

### Binary dumps
```
<system>_<data_type>_<context>.bin
```
Examples:
- `ai_contexts_flight.bin`
- `terrain_heightmap_isr.bin`

### Visualizations
```
<map>_<feature>_<variant>.svg
```
Examples:
- `isr_coastline_clean.svg`
- `kor_rivers_full.svg`

### Parsed data
```
<file_type>_<mission>_parsed.json
```
Examples:
- `waypoints_mission01_parsed.json`
- `squadron_23tfs_parsed.json`

## Tools for Working with Data Samples

Extraction and parsing scripts are in `../tools/`:
- `tools/data_parsers/` - Parse binary data into readable formats
- `tools/data_extractors/` - Extract data from game files

See `../tools/README.md` for details.

## Data Sample Documentation

Each major data type should have:
1. **Format specification** in `docs/data_formats/<format>.md`
2. **Extraction tool** in `tools/data_extractors/<tool>.py`
3. **Parser tool** (if needed) in `tools/data_parsers/<parser>.py`
4. **Sample files** here in `data_samples/<category>/`

## Maintenance

### Weekly
- Remove obsolete test data
- Verify extracted data matches current understanding
- Update extraction tools if format changes

### Monthly
- Archive old samples that are no longer needed
- Consolidate duplicate or similar samples
- Document any new data types

## Size Considerations

**Keep data samples small**:
- ✅ Small binary dumps (< 1 MB)
- ✅ SVG visualizations (text-based, small)
- ✅ JSON parsed data (readable, compresses well)
- ❌ Large binary blobs (extract what you need, not everything)
- ❌ Redundant samples (one example is enough unless comparing variations)

## Questions?

- **Data formats**: Check `docs/data_formats/`
- **Extraction**: Check `tools/data_extractors/`
- **Parsing**: Check `tools/data_parsers/`

---

*Last updated: 2026-11-11*
