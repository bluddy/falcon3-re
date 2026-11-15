# BUTTON2 - Armament Loading Screen

**Purpose**: Weapon loadout/armament screen buttons  
**Total Records**: 20  
**Color Issue**: ❌ Palette is incorrect (showing blue, should be grey)  

---

## Button Map

### Scroll Controls (Records 16-19)
- **19**: Scroll Down button (state 1)
- **18**: Scroll Down button (state 2 - different visual state)
- **17**: Scroll Up button (state 1)
- **16**: Scroll Up button (state 2)

**Note**: Hard to distinguish states due to wrong palette (blue instead of grey)

### Weapon Category Buttons (Records 8-15)

#### "Other Stores" (Records 14-15)
- **15**: "Other Stores" button (unpressed)
- **14**: "Other Stores" button (pressed)

#### "A-G Bombs" (Records 12-13)
- **13**: "A-G Bombs" button (unpressed)
- **12**: "A-G Bombs" button (pressed)

#### "A-G Missiles" (Records 10-11)
- **11**: "A-G Missiles" button (unpressed)
- **10**: "A-G Missiles" button (pressed)

#### "A-A Missiles" (Records 8-9)
- **9**: "A-A Missiles" button (unpressed)
- **8**: "A-A Missiles" button (pressed)

**Pattern**: Odd number = unpressed, Even number = pressed (or reversed)

### Action Buttons (Records 0-5)

#### Load Button (Records 0-2)
- **2**: "Load" button (greyed out/disabled)
- **1**: "Load" button (state 1)
- **0**: "Load" button (state 2)

#### Unload Button (Records 3-5)
- **5**: "Unload" button (greyed out/disabled)
- **4**: "Unload" button (state 1)
- **3**: "Unload" button (state 2)

### Status Displays (Records 6-7)
- **7**: "# LOADED" (number display, not pressable)
- **6**: "# AVAILABLE" (number display, not pressable)

**Note**: These are read-only status indicators showing weapon counts

---

## Button States

Based on the pattern:

1. **Unpressed/Normal**: Default button state
2. **Pressed/Selected**: Active/clicked state
3. **Disabled/Greyed**: Not currently available

**Uncertainty**: Exact state order may be reversed (lower number = unpressed vs pressed)

---

## Palette Issue

**Current**: Blue tones  
**Expected**: Grey tones  
**Impact**: Hard to distinguish button states and text clarity

The palette being used is the standard VGA approximation, but the actual game clearly uses a different palette for the armament screen. This is likely a menu-specific palette that differs from the standard VGA colors.

---

## Screen Context

This is the **weapons loadout screen** where you:
1. Select weapon category (A-A Missiles, A-G Bombs, etc.)
2. See available vs loaded counts
3. Load/Unload weapons onto hardpoints
4. Scroll through available weapons

Classic flight sim armament management interface.

---

## File Details

**Source**: `game/BUTTON2`  
**Size**: 21,658 bytes  
**Records**: 20  
**Format**: Uncompressed VGA

All buttons are 88×16 except:
- Records 6-7: 112×16 (status displays)
- Records 8-15: 50×18 (weapon category buttons)
- Records 16-19: 24×24 (scroll buttons)

---

## Next Steps for Correct Palette

To get the correct grey palette:
1. Find the actual palette used by the armament/loadout screen
2. Look for palette loading in loadout menu code
3. Check if there's a separate ARMSPLT.PAL or similar file
4. May be embedded in the executable or menu data files

The menu system (SYSMENU, etc.) likely shares this palette.

---

**Annotated by**: User  
**Date**: 2026-11-11  
**Status**: Documented - Needs correct palette
