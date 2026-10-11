/* Variant: unsigned params for zero-extend add (adc hi,0), /O for ENTER/SI codegen */
long far sub_1A6D4(unsigned a, unsigned n) {
    long acc = 0;
    while (n != 0) {
        acc += a;
        n--;
    }
    return acc;
}
