/* Test: load word from global and return it */
int test_load_global(void) {
    extern int global_var;
    return global_var;
}