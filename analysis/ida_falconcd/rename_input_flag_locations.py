#!/usr/bin/env python3
"""
Rename and comment the key input flag locations we discovered.
"""

import idc
import idaapi

def main():
    idaapi.auto_wait()
    
    print("[*] Renaming and commenting input flag handling code...")
    print()
    
    # 1. Rename the loop that captures number keys
    addr = 0x130709
    idc.set_cmt(addr, "Loop: Check if scan code matches number keys 1-13 (0x01-0x0D)", 1)
    print(f"[+] Added comment at 0x{addr:X}")
    
    addr = 0x130744
    idc.set_cmt(addr, "Store matched scan code to input_flag_pending_2 for later processing", 1)
    print(f"[+] Added comment at 0x{addr:X}")
    
    addr = 0x130749
    idc.set_cmt(addr, "Number key handler: Store scan code in input_flag_pending_2", 1)
    print(f"[+] Added comment at 0x{addr:X}")
    
    # 2. Comment the jump to number key handling section
    addr = 0x12FD5D
    idc.set_cmt(addr, "Jump to number key handling section if byte_7A278+16h is 0", 1)
    print(f"[+] Added comment at 0x{addr:X}")
    
    # 3. Rename key functions
    func_addr = 0x12FAC3
    # Already named input_poll_handler
    
    # 4. Add overview comment to input_poll_handler
    func_addr = 0x12FAC3
    func_cmt = """Main keyboard input handler. Processes all keyboard input.
    
Number keys (0-9) for view switching:
  - Scan codes 0x02-0x0B captured in loop at 0x130709
  - Stored in input_flag_pending_2 for later dispatch
  - Keys: 1=satellite, 2=ground, 3-6=cockpit dirs, 0=chase, 7=wingman, 8=padlock
  
Function keys (F1-F10):
  - F1-F4: Zoom and rotation (NOT view switching)
  - F5-F7: Radar modes
  - F8-F10: Radar controls
  - Processed by 67-case switch starting at 0x12FDA9"""
    
    idc.set_func_cmt(func_addr, func_cmt, 1)
    print(f"[+] Updated function comment for input_poll_handler")
    
    print()
    print("[+] Renaming complete!")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
