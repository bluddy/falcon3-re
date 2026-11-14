#include <idc.idc>

static main() {
    auto ea, end_ea, output;
    
    // Target function addresses
    auto func_addrs = {0x1297F0, 0x6A651, 0x226BD, 0x226E4, 0x226F5, 0x2274D};
    auto i, func_ea, func_name;
    
    output = fopen("analysis/functions_disasm.txt", "w");
    fprintf(output, "Falcon 3.0 File I/O Functions Disassembly\n");
    fprintf(output, "==========================================\n\n");
    
    for (i = 0; i < 6; i++) {
        func_ea = func_addrs[i];
        func_name = get_func_name(func_ea);
        
        fprintf(output, "\n### Function: %s @ %08X ###\n\n", func_name, func_ea);
        
        ea = get_func_attr(func_ea, FUNCATTR_START);
        end_ea = get_func_attr(func_ea, FUNCATTR_END);
        
        if (ea == BADADDR) {
            fprintf(output, "ERROR: Could not find function\n");
            continue;
        }
        
        fprintf(output, "Start: %08X, End: %08X, Size: %d bytes\n\n", ea, end_ea, end_ea - ea);
        
        while (ea < end_ea && ea != BADADDR) {
            fprintf(output, "%08X: %s\n", ea, generate_disasm_line(ea, 0));
            ea = next_head(ea, BADADDR);
        }
        
        fprintf(output, "\n");
    }
    
    fclose(output);
    message("Extraction complete! Check analysis/functions_disasm.txt\n");
    qexit(0);
}
