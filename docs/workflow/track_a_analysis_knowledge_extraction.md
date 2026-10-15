# Track A: Analysis & Knowledge Extraction
## Track A: Analysis & Knowledge Extraction

### Prerequisites
- IDA Professional 9.1 at `C:\Program Files\IDA Professional 9.1\idat.exe` (headless)
- **NEVER open FALCONCD.EXE in the MCP-connected interactive IDA** (it holds `GS2.exe.i64` for the ongoing Gunship decompilation). Always run `idat.exe` as a separate headless process.
- Python venv

### Steps

1. **Headless snapshot + full analysis**
   ```
   idat.exe -A -S"tools\ida_snapshot.py" analysis\ida_falconcd\FALCONCD.EXE.i64
   ```
   Produces `survey.json`, `functions.tsv`, `overlays.json`, etc.

2. **RTLink fixup extraction** (static, no IDA needed)
   ```
   venv\Scripts\python tools\extract_fixups.py     # → fixup_tables_*.json
   venv\Scripts\python tools\analyze_all_records.py
   ```

3. **Apply RTLink fixups inside IDA**
   ```
   idat.exe -A -S"tools\apply_fixups_ida.py" analysis\ida_falconcd\FALCONCD.EXE.i64
   ```
   1569 fixups across 21 records → overlay code relocated to runtime paragraphs.

4. **Extract ground-truth function bytes**
   ```
   idat.exe -A -S"tools\extract_ida_bytes.py" analysis\ida_falconcd\FALCONCD.EXE.i64
   ```
   → `function_bytes.json` (839 functions, bytes **as relocated in IDA**).

5. **Knowledge base update** — extract manual text, fold into `registry/game_knowledge.yaml`:
   ```
   venv\Scripts\python -c "...pymupdf open('game/manual.pdf')..." > manual_full.txt
   ```

### IDA Coordinate System (CRITICAL)

| Fact | Value |
|------|-------|
| IDA image base | `0x10000` (paragraph `0x1000`) |
| Function EA (linear) | from `survey.json` `ea` field |
| segment / offset | `seg = ea >> 4`, `ofs = ea & 0xF` |
| Raw EXE file offset | `hdr + (ea - 0x10000)` where `hdr = 0x2C00` (704 paragraphs × 16) |
| Entry point | linear `0x2B19C` (`CS:IP = 0x1AA3:0x076C`) |

**Trap**: raw EXE bytes ≠ IDA bytes. The MZ loader applies 2717 relocations at load time
(spread across segments `0x1AA3`, `0xE56`, `0x80F`, …) and IDA applies them too. Always
compare against `function_bytes.json`, never against a naive file-offset read.

---