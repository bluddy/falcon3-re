# Verified Routines
## Verified Routines (43 / 2,282 bytes)

| IDA name | Semantic name | ea | B | Source | Finding |
|---|---|---|---|---|---|
| sub_16FDD | always_true | 0x16FDD | 4 | `src/sub_16FDD.c` | 08/22 |
| sub_2CB6E | always_false | 0x2CB6E | 4 | `src/sub_2CB6E.c` | 08/22 |
| sub_1A6D4 | long_accumulate | 0x1A6D4 | 44 | `src/sub_1A6D4.c` | 22 (first real port) |
| sub_17A85 | dgroup_record_writer | 0x17A85 | 79 | `src/sub_17AD4.c` (unit) | 23 |
| sub_17AD4 | widen_and_forward | 0x17AD4 | 61 | `src/sub_17AD4.c` (unit) | 23 |
| sub_197EA | key_mapper | 0x197EA | 69 | `src/sub_197EA.c` | 24 |
| sub_19BFF | kb_record_base | 0x19BFF | 11 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_19C0A | kb_index_get | 0x19C0A | 14 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_19C18 | kb_farptr_get | 0x19C18 | 19 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_19C2B | kb_name_copy | 0x19C2B | 33 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_19CB0 | farptr_field_reader | 0x19CB0 | 55 | `src/kb_unit_19CB0.c` | 25 |
| sub_19CE7 | kb_field_get_22 | 0x19CE7 | 62 | `src/kb_unit_19CB0.c` | 26 |
| sub_19D25 | kb_field_get_23 | 0x19D25 | 64 | `src/kb_unit_19CB0.c` | 26 |
| sub_19D65 | kb_field_set_23 | 0x19D65 | 65 | `src/kb_unit_19CB0.c` | 26 (IDA-missed fn) |
| sub_19DA6 | kb_field_get_24 | 0x19DA6 | 64 | `src/kb_unit_19CB0.c` | 26 |
| sub_19DE6 | kb_field_set_24 | 0x19DE6 | 65 | `src/kb_unit_19CB0.c` | 26 |
| sub_19E27 | kb_clear_24 | 0x19E27 | 20 | `src/kb_unit_19CB0.c` | 26 |
| sub_19E3B | kb_field_get_25 | 0x19E3B | 64 | `src/kb_unit_19CB0.c` | 26 |
| sub_19E7B | kb_field_set_25_1 | 0x19E7B | 63 | `src/kb_unit_19CB0.c` | 26 |
| sub_19EBA | kb_field_set_25_0 | 0x19EBA | 63 | `src/kb_unit_19CB0.c` | 26 |
| sub_19EF9 | kb_field_get_26 | 0x19EF9 | 64 | `src/kb_unit_19CB0.c` | 27 |
| sub_19F39 | kb_field_set_26 | 0x19F39 | 65 | `src/kb_unit_19CB0.c` | 28 |
| sub_19F7A | kb_clear_26 | 0x19F7A | 20 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_19F8E | kb_field_get_27 | 0x19F8E | 64 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_19FCE | kb_field_set_27 | 0x19FCE | 65 | `src/kb_unit_19CB0.c` | 28 |
| sub_1A00F | kb_field_set_27_1 | 0x1A00F | 20 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_1A023 | kb_field_get_28 | 0x1A023 | 80 | `src/kb_unit_19CB0.c` | 28 |
| sub_1A073 | kb_field_set_28 | 0x1A073 | 73 | `src/kb_unit_19CB0.c` | 28 |
| sub_1A0BC | kb_clear_28 | 0x1A0BC | 22 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_1A0D2 | kb_field_get_2c | 0x1A0D2 | 81 | `src/kb_unit_19CB0.c` | 28 (pragma -r-) |
| sub_1A123 | kb_field_set_2c | 0x1A123 | 83 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_1A176 | kb_field_get_2d | 0x1A176 | 96 | `src/kb_unit_19CB0.c` | 28 |
| sub_1A1D6 | kb_field_get_31 | 0x1A1D6 | 117 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_1A24B | kb_field_set_31 | 0x1A24B | 65 | `src/kb_unit_19CB0.c` | 28 |
| sub_1A28C | kb_count_2c | 0x1A28C | 82 | `src/kb_unit_19CB0.c` | 28 |
| sub_1A2DE | kb_array_get_1 | 0x1A2DE | 106 | `src/kb_unit_19CB0.c` | 28 (struct param) |
| sub_1A348 | kb_array_set_1 | 0x1A348 | 107 | `src/kb_unit_19CB0.c` | 28 (struct param) |
| sub_1A3B3 | kb_array_get_2 | 0x1A3B3 | 112 | `src/kb_unit_19CB0.c` | 28 (struct param) |
| sub_1A423 | kb_array_set_2 | 0x1A423 | 113 | `src/kb_unit_19CB0.c` | 28 (struct param) |
| sub_1A494 | kb_flag_get_10 | 0x1A494 | 14 | `src/kb_unit_19CB0.c` | 28 |
| sub_1A4A2 | kb_flag_set_10_1 | 0x1A4A2 | 20 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_1A4B6 | kb_flag_set_10_0 | 0x1A4B6 | 20 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |
| sub_1A4CA | dgroup_long_get_08 | 0x1A4CA | 19 | `src/kb_unit_19CB0.c` | 28 (IDA-missed fn) |

Known-diff tracked: `sub_19C4C` (kb_record_name_get, 98B vs 100B NUL-peephole, finding 28).
Unverified tracked: `sub_10340` (hand ASM, `not_c-portable`).