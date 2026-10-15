# Environment / Paths
## Environment / Paths

| Variable | Value |
|----------|-------|
| Repo root | `C:\Users\yotam\projects\falcon3` |
| IDA 9.1 headless | `C:\Program Files\IDA Professional 9.1\idat.exe` |
| DOSBox-X | `C:\dosbox-x\dosbox-x.exe` |
| MSC 5.1 root | `C:\Users\yotam\projects\falcon3\dos_compilers\msc5.1` (RBIN\CL.EXE) |
| Python venv | `C:\Users\yotam\projects\falcon3\venv\Scripts\python.exe` |
| Ground truth bytes | `analysis\ida_falconcd\function_bytes.json` |
| mzretools | Shared WSL binaries: `/mnt/c/.../gunship_2000/tools/f19re/mzretools/debug/{mzdiff,mzmap}` v1.0.20 (source: `C:\Users\yotam\projects\f19re\mzretools`) |
| Reference projects | `C:\Users\yotam\projects\f19re` (MSC 5.1 rebuild), `C:\Users\yotam\projects\gunship_2000` (RTLink + registry + this doc's template) |

Shell notes: Windows PowerShell 5.1 — **no heredocs**; write script files first.
`ls`/`wc`/`grep` Unix tools absent — use Python one-liners or Glob/Grep tools.

---