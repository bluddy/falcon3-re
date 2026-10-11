/* Combined translation unit (finding 26):
 *   sub_19CB0 @ 0x19CB0 (55 B)  - verified standalone too
 *   sub_19CE7 @ 0x19CE7 (62 B)  - same-module push cs; call -0x46 (adjacency)
 * sub_19CE7: r = sub_19CB0(a,b); r == -1 -> -1; else byte-load
 *   rec_0022[idx_0020 * 14 + r] via DGROUP far externs (link-offs 0x20/0x22;
 *   seg words + offs are linker fixups -> masked in portcheck).
 */
extern long far fn_0994_0D22(int, int);

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

extern int far idx_0020;        /* DGROUP word @ link-off 0x20 */
extern char far rec_0022[];     /* DGROUP record array @ link-off 0x22 (14-byte stride) */

int far sub_19CE7(int a, int b) {
    int r = sub_19CB0(a, b);
    int w;
    if (r == -1)
        return -1;
    w = rec_0022[idx_0020 * 14 + r];
    return w;
}
