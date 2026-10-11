/* Test: load word from global and return it */
int sub_1034(void) {
    extern int global_var;
    return global_var;
}