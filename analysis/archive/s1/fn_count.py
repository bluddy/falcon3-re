import idautils, json
from pathlib import Path
c = sum(1 for _ in idautils.Functions())
Path("analysis/s1/fn_count.txt").write_text(str(c))
import idaapi; idaapi.qexit(0)
