# R45 Data Structures (Generated from Code Analysis)


## overlay_r45_logic

```c
struct Unknown {
    uint16_t field_002;  // +0x2 (2 accesses)
    uint16_t field_028;  // +0x28 (8 accesses)
    uint16_t field_029;  // +0x29 (8 accesses)
    uint16_t field_25C;  // +0x25C (2 accesses)
    uint16_t field_25E;  // +0x25E (2 accesses)
    uint16_t field_260;  // +0x260 (2 accesses)
};
```

Sample accesses:
  +0x2: push    word ptr es:[bx+2]
  +0x28: mov     al, es:[bx+40h]
  +0x29: mov     al, es:[bx+41h]
  +0x25C: mov     word ptr es:[bx+604h], 0A68h
  +0x25E: mov     word ptr es:[bx+606h], 4FC2h

## r45_position_calculator

```c
struct Unknown {
    uint16_t field_001;  // +0x1 (2 accesses)
    uint16_t field_002;  // +0x2 (6 accesses)
    uint16_t field_004;  // +0x4 (2 accesses)
    uint16_t field_006;  // +0x6 (2 accesses)
    uint16_t field_25C;  // +0x25C (2 accesses)
    uint16_t field_25E;  // +0x25E (2 accesses)
    uint16_t field_260;  // +0x260 (2 accesses)
};
```

Sample accesses:
  +0x1: cmp     word ptr es:[bx+1], 0FFFFh
  +0x2: push    word ptr es:[bx+2]
  +0x4: add     ax, es:[bx+4]
  +0x6: add     ax, es:[bx+6]
  +0x25C: mov     word ptr es:[bx+604h], 0