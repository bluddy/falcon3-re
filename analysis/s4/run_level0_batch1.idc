#include <idc.idc>

static main() {
    auto script_path = "C:\\Users\\ybarnoy\\projects\\falcon3\\analysis\\s4\\level0_naming_batch1.py";
    auto result = load_and_run_script(script_path, IDC_LANG_PYTHON);
    if (result == 0) {
        Message("Script executed successfully\n");
    } else {
        Message("Script failed with code %d\n", result);
    }
    qexit(0);  // quit IDA after script completes
}
