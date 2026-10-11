/* KEYBOARD-STATE UNIT - original translation unit, fully contiguous:
 *   0x19CB0 sub_19CB0  55B  far-ptr field reader
 *   0x19CE7 sub_19CE7  62B  read byte rec_0022[base*14+r]  (r->SI)
 *   0x19D25 sub_19D25  64B  read rec_0023[...] (r spilled, w first)
 *   0x19D65 sub_19D65  65B  write rec_0023[...] = c   (IDA-MISSED function!)
 *   0x19DA6 sub_19DA6  64B  read rec_0024[...] (r->bp-4, w->bp-2)
 *   0x19DE6 sub_19DE6  65B  write rec_0024[...] = c
 *   0x19E27 sub_19E27  20B  wrapper: sub_19DE6(a,b,0) - manual push-bp frame
 *   0x19E3B sub_19E3B  64B  read rec_0025[...] (r->bp-4, w->bp-2)
 *   0x19E7B sub_19E7B  63B  write rec_0025[...] = 1
 *   0x19EBA sub_19EBA  63B  write rec_0025[...] = 0
 *
 * Codegen rules locked (findings 25/26):
 *   - "int r = f()" decl-init            -> r kept in SI (CE7)
 *   - "if ((r = f()) == -1)" assign-cond -> r SPILLED to stack (all others)
 *   - first-declared local gets [bp-2]
 *   - DGROUP far externs (idx_0020 @0x20, rec_00NN arrays @0x22..) = fixups, masked
 *   - all calls intra-module: push cs; call rel16 -> exact cumulative sizes
 */

extern long far fn_0994_0D22(int, int);
extern int far idx_0020;             /* DGROUP word @ link-off 0x20 */
extern char far rec_0022[];          /* DGROUP record bytes @ link-off 0x22+ */
extern char far rec_0023[];
extern char far rec_0024[];
extern char far rec_0025[];

int far sub_19CB0(int a, int b) {
    int w;
    union { long l; char far *p; } u;
    u.l = fn_0994_0D22(a, b);
    if (u.l == -1L)
        return -1;
    u.p += 12;
    w = *(int far *)u.p;
    return w;
}

int far sub_19CE7(int a, int b) {
    int r = sub_19CB0(a, b);
    int w;
    if (r == -1)
        return -1;
    w = rec_0022[idx_0020 * 14 + r];
    return w;
}

int far sub_19D25(int a, int b) {
    int r, w;
    if ((r = sub_19CB0(a, b)) == -1)
        return -1;
    w = rec_0023[idx_0020 * 14 + r];
    return w;
}

int far sub_19D65(int a, int b, char c) {
    int r;
    if ((r = sub_19CB0(a, b)) == -1)
        return 0;
    rec_0023[idx_0020 * 14 + r] = c;
    return 1;
}

int far sub_19DA6(int a, int b) {
    int w, r;
    if ((r = sub_19CB0(a, b)) == -1)
        return -1;
    w = rec_0024[idx_0020 * 14 + r];
    return w;
}

int far sub_19DE6(int a, int b, char c) {
    int r;
    if ((r = sub_19CB0(a, b)) == -1)
        return 0;
    rec_0024[idx_0020 * 14 + r] = c;
    return 1;
}

int far sub_19E27(int a, int b) {
    return sub_19DE6(a, b, 0);
}

int far sub_19E3B(int a, int b) {
    int w, r;
    if ((r = sub_19CB0(a, b)) == -1)
        return -1;
    w = rec_0025[idx_0020 * 14 + r];
    return w;
}

int far sub_19E7B(int a, int b) {
    int r;
    if ((r = sub_19CB0(a, b)) == -1)
        return 0;
    rec_0025[idx_0020 * 14 + r] = 1;
    return 1;
}

int far sub_19EBA(int a, int b) {
    int r;
    if ((r = sub_19CB0(a, b)) == -1)
        return 0;
    rec_0025[idx_0020 * 14 + r] = 0;
    return 1;
}
