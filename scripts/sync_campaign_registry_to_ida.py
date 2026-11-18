"""
Sync Campaign System Registry to IDA
=====================================
Applies names from registry files to IDA database:
- globals.json: Global variable names
- structs.json: Structure definitions
- enums.json: Enum definitions

Output: C:\\Users\\ybarnoy\\projects\\falcon3\\temp\\campaign_sync_report.txt
"""

import idaapi
import idc
import idautils
import json

def main():
    idaapi.auto_wait()
    
    output_path = r"C:\Users\ybarnoy\projects\falcon3\temp\campaign_sync_report.txt"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== Campaign Registry Sync Report ===\n\n")
            
            # Load registry files
            registry_base = r"C:\Users\ybarnoy\projects\falcon3\registry"
            
            globals_path = f"{registry_base}\\globals.json"
            structs_path = f"{registry_base}\\structs.json"
            enums_path = f"{registry_base}\\enums.json"
            
            stats = {
                'globals_renamed': 0,
                'globals_failed': 0,
                'structs_created': 0,
                'enums_created': 0,
                'errors': []
            }
            
            # Sync globals
            f.write("="*70 + "\n")
            f.write("SYNCING GLOBAL VARIABLES\n")
            f.write("="*70 + "\n\n")
            
            try:
                with open(globals_path, 'r', encoding='utf-8') as gf:
                    globals_data = json.load(gf)
                
                for glob in globals_data:
                    name = glob['name']
                    addr_str = glob.get('address', '')
                    segment = glob.get('segment', 'DS')
                    
                    if not addr_str:
                        f.write(f"SKIP: {name} - no address\n")
                        continue
                    
                    # Parse address
                    if addr_str.startswith('0x'):
                        addr = int(addr_str, 16)
                    else:
                        addr = int(addr_str)
                    
                    # Try to set name
                    current_name = idc.get_name(addr, idc.GN_VISIBLE)
                    
                    if idc.set_name(addr, name, idc.SN_CHECK):
                        f.write(f"✓ {addr:#x}: {current_name} → {name}\n")
                        stats['globals_renamed'] += 1
                    else:
                        f.write(f"✗ {addr:#x}: Failed to rename to {name} (current: {current_name})\n")
                        stats['globals_failed'] += 1
                        stats['errors'].append(f"Global {name} @ {addr:#x}")
                
                f.write(f"\nGlobals renamed: {stats['globals_renamed']}\n")
                f.write(f"Globals failed: {stats['globals_failed']}\n")
                
            except FileNotFoundError:
                f.write("WARNING: globals.json not found\n")
            except Exception as e:
                f.write(f"ERROR loading globals: {e}\n")
                stats['errors'].append(f"Globals load error: {e}")
            
            f.write("\n\n")
            
            # Sync functions
            f.write("="*70 + "\n")
            f.write("SYNCING CAMPAIGN FUNCTIONS\n")
            f.write("="*70 + "\n\n")
            
            campaign_functions = [
                (0x6A651, "squad_campaign_file_loader"),
                (0x136133, "campaign_save_temp_file_write"),
                (0x17B437, "squadron_mission_file_loader"),
                (0x1793C0, "overlay_r4F_handler"),
                (0x6AE59, "ui_slot_list_mode_enter"),
                (0x67781, "display_palette_hud_refresh_step"),
            ]
            
            for addr, name in campaign_functions:
                current_name = idc.get_func_name(addr)
                
                if current_name == name:
                    f.write(f"  {addr:#x}: {name} (already correct)\n")
                    continue
                
                if idc.set_name(addr, name, idc.SN_CHECK):
                    f.write(f"✓ {addr:#x}: {current_name} → {name}\n")
                    stats['globals_renamed'] += 1
                else:
                    f.write(f"✗ {addr:#x}: Failed to rename to {name}\n")
                    stats['globals_failed'] += 1
            
            f.write("\n\n")
            
            # Report enums (IDA Python enum API is complex, just document)
            f.write("="*70 + "\n")
            f.write("ENUMS TO CREATE MANUALLY\n")
            f.write("="*70 + "\n\n")
            
            try:
                with open(enums_path, 'r', encoding='utf-8') as ef:
                    enums_data = json.load(ef)
                
                new_enums = ['FileOperation', 'GraphicsMode']
                
                for enum_def in enums_data:
                    if enum_def['name'] in new_enums:
                        f.write(f"\nEnum: {enum_def['name']}\n")
                        f.write(f"Type: {enum_def['type']}\n")
                        f.write(f"Description: {enum_def['description']}\n")
                        f.write("Values:\n")
                        for val in enum_def['values']:
                            f.write(f"  {val['value']:3d} = {val['name']:<30s} // {val['description']}\n")
                        stats['enums_created'] += 1
                
                f.write(f"\nTotal new enums: {len(new_enums)}\n")
                
            except FileNotFoundError:
                f.write("WARNING: enums.json not found\n")
            except Exception as e:
                f.write(f"ERROR loading enums: {e}\n")
            
            f.write("\n\n")
            
            # Report structs (IDA Python struct API is complex, just document)
            f.write("="*70 + "\n")
            f.write("STRUCTS TO CREATE MANUALLY\n")
            f.write("="*70 + "\n\n")
            
            try:
                with open(structs_path, 'r', encoding='utf-8') as sf:
                    structs_data = json.load(sf)
                
                for struct_def in structs_data:
                    f.write(f"\nStruct: {struct_def['name']}\n")
                    f.write(f"Size: {struct_def['size']} bytes\n")
                    f.write(f"Description: {struct_def['description']}\n")
                    f.write("Fields:\n")
                    for field in struct_def['fields']:
                        offset = field.get('offset', '?')
                        fname = field['name']
                        ftype = field['type']
                        fdesc = field['description']
                        f.write(f"  +{offset:3} {fname:30s} {ftype:20s} // {fdesc}\n")
                    stats['structs_created'] += 1
                
                f.write(f"\nTotal structs: {len(structs_data)}\n")
                
            except FileNotFoundError:
                f.write("WARNING: structs.json not found\n")
            except Exception as e:
                f.write(f"ERROR loading structs: {e}\n")
            
            f.write("\n\n")
            
            # Summary
            f.write("="*70 + "\n")
            f.write("SYNC SUMMARY\n")
            f.write("="*70 + "\n\n")
            f.write(f"Globals renamed: {stats['globals_renamed']}\n")
            f.write(f"Globals failed: {stats['globals_failed']}\n")
            f.write(f"Enums documented: {stats['enums_created']}\n")
            f.write(f"Structs documented: {stats['structs_created']}\n")
            
            if stats['errors']:
                f.write(f"\nErrors ({len(stats['errors'])}):\n")
                for err in stats['errors']:
                    f.write(f"  - {err}\n")
            
            f.write("\n=== Sync Complete ===\n")
    
    except Exception as e:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"FATAL ERROR: {str(e)}\n")
            import traceback
            f.write(traceback.format_exc())
    
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
