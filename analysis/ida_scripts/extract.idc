#include <idc.idc>

static main() {
    auto ea, func, ah_val, check, output;
    auto count, term_ea;
    
    output = fopen("analysis/strings_found.txt", "w");
    fprintf(output, "=== STRING SEARCH ===\n\n");
    
    // Search for "ARMS" string
    ea = 0;
    while (1) {
        ea = find_text(ea, SEARCH_DOWN | SEARCH_CASE, 0, 0, "ARMS");
        if (ea == BADADDR) break;
        
        fprintf(output, "Found ARMS at %08X\n", ea);
        ea = ea + 1;
    }
    
    // Search for ".IDX"
    ea = 0;
    while (1) {
        ea = find_text(ea, SEARCH_DOWN | SEARCH_CASE, 0, 0, ".IDX");
        if (ea == BADADDR) break;
        
        fprintf(output, "Found .IDX at %08X\n", ea);
        ea = ea + 1;
    }
    
    // Search for ".DAT"
    ea = 0;
    while (1) {
        ea = find_text(ea, SEARCH_DOWN | SEARCH_CASE, 0, 0, ".DAT");
        if (ea == BADADDR) break;
        
        fprintf(output, "Found .DAT at %08X\n", ea);
        ea = ea + 1;
    }
    
    fprintf(output, "\n=== INT 21h CALLS ===\n\n");
    
    // Find INT 21h calls
    ea = get_inf_attr(INF_MIN_EA);
    count = 0;
    while (ea != BADADDR && count < 100) {
        if (print_insn_mnem(ea) == "int" && get_operand_value(ea, 0) == 0x21) {
            func = get_func_name(ea);
            
            // Look backwards for MOV AH
            ah_val = -1;
            check = ea - 30;
            while (check < ea) {
                if (print_insn_mnem(check) == "mov" && print_operand(check, 0) == "ah") {
                    ah_val = get_operand_value(check, 1);
                    break;
                }
                check = next_head(check, BADADDR);
            }
            
            fprintf(output, "%08X: %s - AH=%02X\n", ea, func, ah_val);
            count++;
        }
        ea = next_head(ea, BADADDR);
    }
    
    fclose(output);
    
    message("Extraction complete! Check analysis/strings_found.txt\n");
    qexit(0);
}
