import re
src=open('analysis/segsplit/verify_idb_local.py').read()
src=re.sub(r'^LOG = .*$', 'import os\nLOG = os.environ.get("ILOG", r"C:/Users/ybarnoy/projects/falcon3/analysis/s1/integrity.log")', src, flags=re.M)
src=re.sub(r'^HOLES_OUT = .*$', 'HOLES_OUT = r"C:/Users/ybarnoy/projects/falcon3/analysis/s1/data_holes_live.json"', src, flags=re.M)
src=src.replace('\nidaapi.qexit(0)','\nidaapi.set_database_flag(idaapi.DBFL_KILL)\nidaapi.qexit(0)')
open('analysis/s1/verify_idb_s1.py','w').write(src)
