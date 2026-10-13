/* KEYBOARD-STATE UNIT - original translation unit, fully contiguous:
 *   0x19BFF kb_record_base        11B  returns MK_FP(DGROUP,0x22)
 *   0x19C0A kb_index_get          14B  returns idx_0020 (word @0x20)
 *   0x19C18 kb_farptr_get         19B  returns far ptr stored @0x0c/0x0e
 *   0x19C2B kb_name_copy          33B  copy 13B @0x12 to caller buffer (void)
 *   0x19C4C kb_record_name_get   100B  clear dest[13]; idx guard; copy <=12B NUL-stopped (i->DI, k->SI)
 *                                      known 2B diff: our bcc peepholes "p[k]==0" to cmp-byte (finding 28)
 *   0x19CB0 farptr_field_reader   55B  far-ptr field reader
 *   0x19CE7 kb_field_get_22       62B  read byte rec_0022[base*14+r]  (r->SI)
 *   0x19D25 kb_field_get_23       64B  read rec_0023[...] (r spilled, w first)
 *   0x19D65 kb_field_set_23       65B  write rec_0023[...] = c   (IDA-MISSED function!)
 *   0x19DA6 kb_field_get_24       64B  read rec_0024[...] (r->bp-4, w->bp-2)
 *   0x19DE6 kb_field_set_24       65B  write rec_0024[...] = c
 *   0x19E27 kb_clear_24           20B  wrapper: kb_field_set_24(a,b,0) - manual push-bp frame
 *   0x19E3B kb_field_get_25       64B  read rec_0025[...] (r->bp-4, w->bp-2)
 *   0x19E7B kb_field_set_25_1     63B  write rec_0025[...] = 1
 *   0x19EBA kb_field_set_25_0     63B  write rec_0025[...] = 0
 *   0x19EF9 kb_field_get_26       64B  read byte rec_0026[...] @ +0x26, cwde (finding 27)
 *   0x19F39 kb_field_set_26       65B  write rec_0026[...] = c
 *   0x19F7A kb_clear_26           20B  wrapper: kb_field_set_26(a,b,0)
 *   0x19F8E kb_field_get_27       64B  read byte rec_0027[...] @ +0x27, cwde
 *   0x19FCE kb_field_set_27       65B  write rec_0027[...] = c
 *   0x1A00F kb_field_set_27_1     20B  wrapper: kb_field_set_27(a,b,1)
 *   0x1A023 kb_field_get_28       80B  long getter @+0x28, r->bp-2, w->bp-4..-1
 *   0x1A073 kb_field_set_28       73B  long setter @+0x28 (v at bp+0xa/0xc)
 *   0x1A0BC kb_clear_28           22B  wrapper: kb_field_set_28(a,b,0L)
 *   0x1A0D2 kb_field_get_2c       81B  byte getter @+0x2c, guard get_22==0
 *   0x1A123 kb_field_set_2c       83B  byte setter @+0x2c, guard get_22==0
 *   0x1A176 kb_field_get_2d       96B  long getter @+0x2d, guard get_22==0
 *   0x1A1D6 kb_field_get_31      117B  word getter @+0x31; guards get_22/25/24
 *   0x1A24B kb_field_set_31       65B  word setter @+0x31
 *   0x1A28C kb_count_2c           82B  byte @+0x2c when get_22==1 (array bound)
 *   0x1A2DE kb_array_get_1       106B  indexed byte read @+0x2d+i (i->SI)
 *   0x1A348 kb_array_set_1       107B  indexed byte write @+0x2d+i
 *   0x1A3B3 kb_array_get_2       112B  indexed byte read @+0x2d+count+i
 *   0x1A423 kb_array_set_2       113B  indexed byte write @+0x2d+count+i
 *   0x1A494 kb_flag_get_10        14B  returns word @DGROUP:0x10
 *   0x1A4A2 kb_flag_set_10_1      20B  sets word @0x10 = 1, returns 1
 *   0x1A4B6 kb_flag_set_10_0      20B  sets word @0x10 = 0, returns 1
 *   0x1A4CA dgroup_long_get_08    19B  returns long @DGROUP:0x08/0x0a
 *
 * Codegen rules locked (findings 25/26):
 *   - "int r = f()" decl-init            -> r kept in SI (CE7)
 *   - "if ((r = f()) == -1)" assign-cond -> r SPILLED to stack (all others)
 *   - first-declared local gets [bp-2]
 *   - DGROUP far externs (idx_0020 @0x20, rec_00NN arrays @0x22..) = fixups, masked
 *   - all calls intra-module: push cs; call rel16 -> exact cumulative sizes
 *
 * The #pragma option -r- region (get_2c..count_2c) is a verification aid, not
 * original source - see finding 28: our bcc2.0 build caches push-only params
 * into si/di under -r; the original compiler build did not.
 */

extern long far fn_0994_0D22(int, int);
extern int far idx_0020;             /* DGROUP word @ link-off 0x20 */
extern long far lng_0008;            /* DGROUP long @ link-off 0x08 (lo@0x08, hi@0x0a) */
extern int far flag_0010;            /* DGROUP word @ link-off 0x10 */
extern char far name_0012[];         /* DGROUP 13B name buffer @ link-off 0x12 */
extern char far * far ptr_000c;      /* DGROUP far ptr @ link-off 0x0c (off@0x0c, seg@0x0e) */
extern char far rec_0022[];          /* DGROUP record bytes @ link-off 0x22+ */
extern char far rec_0023[];
extern char far rec_0024[];
extern char far rec_0025[];
extern char far rec_0026[];          /* DGROUP byte @ link-off 0x26 */
extern char far rec_0027[];          /* DGROUP byte @ link-off 0x27 */
extern char far rec_0028[];          /* DGROUP long @ link-off 0x28 (lo@0x28, hi@0x2a) */
extern char far rec_002c[];          /* DGROUP byte @ link-off 0x2c */
extern char far rec_002d[];          /* DGROUP long @ link-off 0x2d (lo@0x2d, hi@0x2f) */
extern char far rec_0031[];          /* DGROUP word @ link-off 0x31 */

char far * kb_record_base(void) {
    return rec_0022;
}

int far kb_index_get(void) {
    return idx_0020;
}

char far * kb_farptr_get(void) {
    return ptr_000c;
}

void far kb_name_copy(char *buf) {
    int k;
    for (k = 0; k < 13; k++)
        buf[k] = name_0012[k];
}

int far kb_record_name_get(int i, char *buf) {
    char *p;
    int k;
    for (k = 0; k < 13; k++)
        buf[k] = 0;
    if (idx_0020 < i)
        return 0;
    p = rec_0022 + i * 14;
    for (k = 0; k < 12; k++) {
        if (p[k] == 0)
            break;
        buf[k] = p[k];
    }
    return 1;
}

int far farptr_field_reader(int a, int b) {
    int w;
    union { long l; char far *p; } u;
    u.l = fn_0994_0D22(a, b);
    if (u.l == -1L)
        return -1;
    u.p += 12;
    w = *(int far *)u.p;
    return w;
}

int far kb_field_get_22(int a, int b) {
    int r = farptr_field_reader(a, b);
    int w;
    if (r == -1)
        return -1;
    w = rec_0022[idx_0020 * 14 + r];
    return w;
}

int far kb_field_get_23(int a, int b) {
    int r, w;
    if ((r = farptr_field_reader(a, b)) == -1)
        return -1;
    w = rec_0023[idx_0020 * 14 + r];
    return w;
}

int far kb_field_set_23(int a, int b, char c) {
    int r;
    if ((r = farptr_field_reader(a, b)) == -1)
        return 0;
    rec_0023[idx_0020 * 14 + r] = c;
    return 1;
}

int far kb_field_get_24(int a, int b) {
    int w, r;
    if ((r = farptr_field_reader(a, b)) == -1)
        return -1;
    w = rec_0024[idx_0020 * 14 + r];
    return w;
}

int far kb_field_set_24(int a, int b, char c) {
    int r;
    if ((r = farptr_field_reader(a, b)) == -1)
        return 0;
    rec_0024[idx_0020 * 14 + r] = c;
    return 1;
}

int far kb_clear_24(int a, int b) {
    return kb_field_set_24(a, b, 0);
}

int far kb_field_get_25(int a, int b) {
    int w, r;
    if ((r = farptr_field_reader(a, b)) == -1)
        return -1;
    w = rec_0025[idx_0020 * 14 + r];
    return w;
}

int far kb_field_set_25_1(int a, int b) {
    int r;
    if ((r = farptr_field_reader(a, b)) == -1)
        return 0;
    rec_0025[idx_0020 * 14 + r] = 1;
    return 1;
}

int far kb_field_set_25_0(int a, int b) {
    int r;
    if ((r = farptr_field_reader(a, b)) == -1)
        return 0;
    rec_0025[idx_0020 * 14 + r] = 0;
    return 1;
}

int far kb_field_get_26(int a, int b) {
    int w, r;
    if ((r = farptr_field_reader(a, b)) == -1)
        return -1;
    w = rec_0026[idx_0020 * 14 + r];    /* byte read @ +0x26, cwde sign-extend */
    return w;
}

int far kb_field_set_26(int a, int b, char c) {
    int r;
    if ((r = farptr_field_reader(a, b)) == -1)
        return 0;
    rec_0026[idx_0020 * 14 + r] = c;    /* byte store @ +0x26 */
    return 1;
}

int far kb_clear_26(int a, int b) {
    return kb_field_set_26(a, b, 0);     /* manual push-bp frame, no locals */
}

int far kb_field_get_27(int a, int b) {
    int w, r;
    if ((r = farptr_field_reader(a, b)) == -1)
        return -1;
    w = rec_0027[idx_0020 * 14 + r];    /* byte read @ +0x27, cwde sign-extend */
    return w;
}

int far kb_field_set_27(int a, int b, char c) {
    int r;
    if ((r = farptr_field_reader(a, b)) == -1)
        return 0;
    rec_0027[idx_0020 * 14 + r] = c;    /* byte store @ +0x27 */
    return 1;
}

int far kb_field_set_27_1(int a, int b) {
    return kb_field_set_27(a, b, 1);      /* manual push-bp frame, no locals */
}

long far kb_field_get_28(int a, int b) {
    long w;
    int r;
    if ((r = farptr_field_reader(a, b)) == -1)
        return -1L;
    w = *(long far *)((char far *)rec_0028 + idx_0020 * 14 + r);
    return w;
}

int far kb_field_set_28(int a, int b, long v) {
    int r;
    if ((r = farptr_field_reader(a, b)) == -1)
        return 0;
    *(long far *)((char far *)rec_0028 + idx_0020 * 14 + r) = v;
    return 1;
}

int far kb_clear_28(int a, int b) {
    return kb_field_set_28(a, b, 0L);   /* push 0; push 0; manual push-bp frame */
}

/* --- push-only param region (finding 28): compiled with -r- so that params
 *     used only as call arguments stay on the stack, matching the original
 *     binary.  Our bcc2.0 build's -r caches them into si/di (2B extra per
 *     param); the original compiler build did not. --- */
#pragma option -r-

int far kb_field_get_2c(int a, int b) {
    int r, w;
    if (kb_field_get_22(a, b) != 0)
        return 0;
    if ((r = farptr_field_reader(a, b)) == -1)
        return 0;
    w = rec_002c[idx_0020 * 14 + r];    /* byte read @ +0x2c, cwde */
    return w;
}

int far kb_field_set_2c(int a, int b, char c) {
    int r;
    if (kb_field_get_22(a, b) != 0)
        return 0;
    if ((r = farptr_field_reader(a, b)) == -1)
        return 0;
    rec_002c[idx_0020 * 14 + r] = c;    /* byte store @ +0x2c */
    return 1;
}

long far kb_field_get_2d(int a, int b) {
    int r;
    long w;
    if (kb_field_get_22(a, b) != 0)
        return 0L;
    if ((r = farptr_field_reader(a, b)) == -1)
        return 0L;
    w = *(long far *)((char far *)rec_002d + idx_0020 * 14 + r);
    return w;
}

int far kb_field_get_31(int a, int b) {
    int r, w;
    if (kb_field_get_22(a, b) != 0)
        return 0;
    if (kb_field_get_25(a, b) == 0)
        return 0;
    if (kb_field_get_24(a, b) != 2)
        return 0;
    if ((r = farptr_field_reader(a, b)) == -1)
        return 0;
    w = *(int far *)((char far *)rec_0031 + idx_0020 * 14 + r);  /* word read @ +0x31 */
    return w;
}

int far kb_field_set_31(int a, int b, int v) {
    int r;
    if ((r = farptr_field_reader(a, b)) == -1)
        return 0;
    *(int far *)((char far *)rec_0031 + idx_0020 * 14 + r) = v;  /* word store @ +0x31 */
    return 1;
}

int far kb_count_2c(int a, int b) {
    int w, r;
    if (kb_field_get_22(a, b) != 1)
        return 0;
    if ((r = farptr_field_reader(a, b)) == -1)
        return 0;
    w = rec_002c[idx_0020 * 14 + r];    /* byte read @ +0x2c; array bound */
    return w;
}

#pragma option -r

/* The array fns need SI for the register-context param i while a,b (push-only)
 * must stay on the stack - a combination our bcc2.0 -r cannot produce (it gives
 * si/di to a,b).  Passing a,b as one struct keeps them out of registers (finding
 * 28); stack layout is identical to separate int params. */
struct kb_ab { int a; int b; };

int far kb_array_get_1(struct kb_ab ab, int i) {
    int w, r;
    if (kb_field_get_22(ab.a, ab.b) != 1)
        return -1;
    if (kb_count_2c(ab.a, ab.b) <= i)
        return -1;
    if ((r = farptr_field_reader(ab.a, ab.b)) == -1)
        return -1;
    w = rec_002d[idx_0020 * 14 + r + i];
    return w;
}

int far kb_array_set_1(struct kb_ab ab, int i, char c) {
    int r;
    if (kb_field_get_22(ab.a, ab.b) != 1)
        return 0;
    if (kb_count_2c(ab.a, ab.b) <= i)
        return 0;
    if ((r = farptr_field_reader(ab.a, ab.b)) == -1)
        return 0;
    rec_002d[idx_0020 * 14 + r + i] = c;
    return 1;
}

int far kb_array_get_2(struct kb_ab ab, int i) {
    int w, count, r;
    if (kb_field_get_22(ab.a, ab.b) != 1)
        return -1;
    if ((count = kb_count_2c(ab.a, ab.b)) <= i)
        return -1;
    if ((r = farptr_field_reader(ab.a, ab.b)) == -1)
        return -1;
    w = rec_002d[idx_0020 * 14 + r + count + i];
    return w;
}

int far kb_array_set_2(struct kb_ab ab, int i, char c) {
    int r, count;
    if (kb_field_get_22(ab.a, ab.b) != 1)
        return 0;
    if ((count = kb_count_2c(ab.a, ab.b)) <= i)
        return 0;
    if ((r = farptr_field_reader(ab.a, ab.b)) == -1)
        return 0;
    rec_002d[idx_0020 * 14 + r + count + i] = c;
    return 1;
}

int far kb_flag_get_10(void) {
    return flag_0010;
}

int far kb_flag_set_10_1(void) {
    flag_0010 = 1;
    return 1;
}

int far kb_flag_set_10_0(void) {
    flag_0010 = 0;
    return 1;
}

long far dgroup_long_get_08(void) {
    return lng_0008;
}
