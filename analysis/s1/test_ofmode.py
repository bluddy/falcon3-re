import os, idaapi
from pathlib import Path
Path('analysis/s1/ofmode_result.txt').write_text(repr(os.environ.get('OFMODE')))
idaapi.qexit(0)
