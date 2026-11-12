"""create_entity_tables.py — create IDA data symbols for entity type tables."""
import idc, ida_bytes, idaapi

# Table A: entity attributes at R05_33AE + 0x1662
table_a_ea = 0x45150
idc.create_data(table_a_ea, idc.FF_WORD, 2, idaapi.BADADDR)
idc.set_name(table_a_ea, "entity_attr_table", idc.SN_CHECK)

# Table B: entity class codes at R05_33AE + 0x16F4  
table_b_ea = 0x455E2
idc.create_data(table_b_ea, idc.FF_WORD, 2, idaapi.BADADDR)
idc.set_name(table_b_ea, "entity_class_table", idc.SN_CHECK)

print("Created entity_attr_table at 0x%X" % table_a_ea)
print("Created entity_class_table at 0x%X" % table_b_ea)

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
