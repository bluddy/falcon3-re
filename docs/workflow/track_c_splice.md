# Track C Splice Pipeline
### 5. Track C splice pipeline (verification)

```
idat -A -S tools\ida_export.asm                <IDB>   # export full assembly listing
venv\Scripts\python tools\extract_routines.py  listing.asm  src/routines/
venv\Scripts\python tools\splice.py            listing.asm  listing_spliced.asm  src/routines/  --verified registry/routines.yaml
# Assemble listing_spliced.asm → spliced.exe (TASM/MASM + TLINK or BCC)
venv\Scripts\python tools\mzdiff.py            game/FALCONCD.EXE  spliced.exe  --functions analysis/ida_falconcd/function_bytes.json  --routines registry/routines.yaml
```
`idat` fails **exit=4** if the IDB is open in interactive IDA — close it first.
(Also: never open Falcon in the MCP-connected IDA — it holds the Gunship DB.)

---