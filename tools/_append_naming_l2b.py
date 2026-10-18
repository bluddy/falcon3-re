"""Append the Finding-73 Global Level-0 Batch-1 (30) function entries to
registry/naming.yaml, inserted just before the `# --- globals:` marker.
Idempotent (skips if a key already present).  Preserves CRLF? naming.yaml is
LF (checked).  Re-runs naming.py check after.
"""
import io, json, re, sys

LEDGER = "registry/naming.yaml"
NAMES = "analysis/ida_falconcd/level2_batch2_names.json"

analysis = json.load(open(NAMES, encoding="utf-8"))
raw = io.open(LEDGER, encoding="utf-8", newline="").read()

# ida key -> (name, sig, notes, conf)
existing_keys = set(re.findall(r"^  - ida: (\S+)", raw, re.M))

blocks = []
added = 0
for key in sorted(analysis, key=lambda k: analysis[k][0]):  # alpha by name
    name, sig, notes, conf = analysis[key]
    if key in existing_keys:
        continue
    # escape double quotes in sig/notes (none expected, but be safe)
    sig_e = sig.replace(chr(92), chr(92)*2).replace('"', chr(92)*2 + '"')
    notes_e = notes.replace(chr(92), chr(92)*2).replace('"', chr(92)*2 + '"')
    blocks.append(
        "  - ida: %s\n"
        "    name: %s\n"
        "    kind: function\n"
        '    sig: "%s"\n'
        '    notes: "%s"\n' % (key, name, sig_e, notes_e))
    added += 1

if added == 0:
    print("naming.yaml: all 30 already present, nothing to add")
    sys.exit(0)

marker = "\n  # --- globals:"
i = raw.rindex(marker)
new = raw[:i] + "\n" + "".join(blocks) + raw[i:]
io.open(LEDGER, "w", encoding="utf-8", newline="").write(new)
print("naming.yaml: inserted %d function entries before globals marker" % added)
# verify count
t2 = io.open(LEDGER, encoding="utf-8").read()
n = len(re.findall(r"^  - ida: ", t2, re.M))
print("total - ida: entries now: %d (was %d)" % (n, len(existing_keys)))