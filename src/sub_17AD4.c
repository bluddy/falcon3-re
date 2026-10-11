/* Combined translation unit - original binary has these two ADJACENT:
 *   sub_17A85 @ 0x17A85 (79 B)
 *   sub_17AD4 @ 0x17AD4 (61 B)   call disp 0xFF7B requires same-module compile
 *                                 (BC emits 'push cs; call rel16' only intra-module)
 *
 * sub_17A85: copy 13 bytes from int far *src into DGROUP record at
 *   idx*14+0xAD52 (near->far conversion uses DS), then flags&3 as byte 14;
 *   finally calls far target 0x0761:057B (link-resolved, fixup masked).
 * sub_17AD4: widen-copy 13 bytes from char far *src into local int[14],
 *   then call sub_17A85(a, buf, c).
 *
 * Codegen notes (byte-exact recipe):
 *   - 'int i = 0;' declaration emits xor si,si BEFORE the dst computation
 *   - dst = (char *)(near expr)  -> mov [bp-2],ds + mov [bp-4],ax (DS segment!)
 *     (a direct (char far *) cast would zero the segment instead)
 *   - *dst = (char)(flags &= 3) as one expression -> and mem; mov ax,[C]; les; store
 */

extern int far loc_0761_057B(int);

void far sub_17A85(int idx, int far *src, int flags) {
    int i = 0;
    char far *dst;
    dst = (char near *)(idx * 14 + 0xAD52);
    for (; i < 13; i++)
        *dst++ = (char)*src++;
    *dst = (char)(flags &= 3);
    loc_0761_057B(idx);
}

void far sub_17AD4(int a, char far *src, int c) {
    int buf[14];
    int i;
    for (i = 0; i < 13; i++)
        buf[i] = (unsigned char)*src++;
    sub_17A85(a, (int far *)buf, c);
}
