/* Resident routine @ 0x197EA (seg009, CS=0x180F0), 69 bytes.
 * Sparse 5-case switch -> BC search-loop + jump table (table follows the
 * function at CS:0x173F = linear 0x1982F). Case table read from EXE:
 *   0x103->10, 0x108->11, 0x111->12, 0x112->4, 0x113->3, default->key.
 * Intermediate 'r' is required: it drives BC's register choice (r->SI,
 * key->DI, push/pop di); direct 'return const' in cases allocates differently. */
int far sub_197EA(int key) {
    int r;
    switch (key) {
    case 0x103: r = 10; break;
    case 0x108: r = 11; break;
    case 0x111: r = 12; break;
    case 0x112: r = 4;  break;
    case 0x113: r = 3;  break;
    default:    r = key; break;
    }
    return r;
}
