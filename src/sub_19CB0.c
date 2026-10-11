/* Resident routine @ 0x19CB0 (seg 0x19CB, ofs 0x0), 55 bytes.
 * Calls far 0x0994:0x0D22 (link-time seg; fixup masked), long result;
 * -1L -> -1; else reads a word at farptr(r)+12.
 * Byte-exact notes (finding 25 trail):
 *   - 'int w' declared FIRST -> BC slots w at [bp-2], r at [bp-6]
 *   - union forces in-place 'add [slot],0Ch' + zero-displacement deref
 *     (a folded cast-expression would emit es:[bx+0Ch] instead, -3 bytes) */
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
