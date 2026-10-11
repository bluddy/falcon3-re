/* Test: load global1, store to output ptr, load global2, return it */
int sub_10340(int *out) {
    extern int global1;
    extern int global2;
    *out = global1;
    return global2;
}