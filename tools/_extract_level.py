"""Extract the naming-queue keys at a given topological level from
analysis/traces/callgraph_partial.json, sorted by
(-dyn, -static_in_degree, -caller_dyn_sum, ea), into
analysis/ida_falconcd/level<N>_targets.json as {"A": [keys]}.
Usage: python tools/_extract_level.py <level>
"""
import json, sys

LEVEL = int(sys.argv[1])
G = "analysis/traces/callgraph_partial.json"
FB = "analysis/ida_falconcd/function_bytes.json"
OUT = "analysis/ida_falconcd/level%d_targets.json" % LEVEL

g = json.load(open(G, encoding="utf-8"))
fb = json.load(open(FB, encoding="utf-8"))

queue = set(g["naming_queue"])
nl = g["node_levels"]
dyn = g["dyn_target_calls"]
ind = g["static_in_degree"]
cds = g["caller_dyn_sum"]

keys = [k for k in queue if nl.get(k) == LEVEL]
keys.sort(key=lambda k: (-dyn.get(k, 0), -ind.get(k, 0), -cds.get(k, 0),
                         fb[k]["ea"]))
json.dump({"A": keys}, open(OUT, "w"), indent=1)
print("level %d: %d targets -> %s" % (LEVEL, len(keys), OUT))
for k in keys[:30]:
    print("  %-20s dyn=%-4d cd=%-6d in=%-3d ea=0x%X"
          % (k, dyn.get(k, 0), ind.get(k, 0), cds.get(k, 0), fb[k]["ea"]))
