"""Variant tester for sub_19D25 register allocation (spill vs SI)."""
import sys
sys.path.insert(0, 'tools')
import portcheck_falcon as pc

HEADER = open('src/kb_unit_19CB0.c').read().split('int far sub_19CB0')[0]
# include sub_19CB0 + sub_19CE7 (adjacency for calls from D25 onward)
UNIT_HEAD = open('src/kb_unit_19CB0.c').read()

VARIANTS = {
    "V1_declinit_tailorder": """
int far sub_19D25(int a, int b) {
    int r = sub_19CB0(a, b);
    int w;
    if (r == -1)
        return -1;
    w = rec_0023[r + idx_0020 * 14];
    return w;
}""",
    "V2_assign_headorder": """
int far sub_19D25(int a, int b) {
    int r, w;
    r = sub_19CB0(a, b);
    if (r == -1)
        return -1;
    w = rec_0023[r + idx_0020 * 14];
    return w;
}""",
    "V3_wfirst": """
int far sub_19D25(int a, int b) {
    int w, r;
    r = sub_19CB0(a, b);
    if (r == -1)
        return -1;
    w = rec_0023[idx_0020 * 14 + r];
    return w;
}""",
    "V4_declinit_plain": """
int far sub_19D25(int a, int b) {
    int r = sub_19CB0(a, b);
    int w;
    if (r == -1)
        return -1;
    w = rec_0023[idx_0020 * 14 + r];
    return w;
}""",
    "V5_assign_in_cond": """
int far sub_19D25(int a, int b) {
    int r, w;
    if ((r = sub_19CB0(a, b)) == -1)
        return -1;
    w = rec_0023[idx_0020 * 14 + r];
    return w;
}""",
    "V6_assign_in_cond_wfirst": """
int far sub_19D25(int a, int b) {
    int w, r;
    if ((r = sub_19CB0(a, b)) == -1)
        return -1;
    w = rec_0023[idx_0020 * 14 + r];
    return w;
}""",
}

# build unit = head (everything up to sub_19D25) + variant
base = open('src/kb_unit_19CB0.c').read()
pre = base.split('int far sub_19D25')[0]
post = base.split('int far sub_19DA6')[1]

want = pc.get_original_bytes_from_ida('sub_19D25', 1 << 30)
for name, fn in VARIANTS.items():
    src = pre + fn.strip() + "\n\nint far sub_19DA6" + post
    got, mask = pc._compile_bcc_extract('sub_19D25', src, '')
    ms = set(mask)
    n = min(len(got), len(want))
    diffs = [i for i in range(n) if i not in ms and got[i] != want[i]]
    status = "MATCH" if (not diffs and len(got) >= len(want)) else "diff@%s" % diffs[:6]
    print("%-26s len=%d  %s" % (name, len(got), status))
