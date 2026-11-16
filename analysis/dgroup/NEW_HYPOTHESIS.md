# New Hypothesis: r15_external_view_flag is Session-Static

## Observation

We've found view key handlers that set **word_79F16** to values like 7, 8, etc. But we haven't found runtime writes to **r15_external_view_flag**.

## Hypothesis

**The flag might be session-static while view mode is dynamic!**

### Two-Level View System

1. **r15_external_view_flag** (0x107762) - **Mode selection** (set once at mission start)
   - 0 = Cockpit mode (Path A in simulation loop)
   - 1 = External mode (Path B in simulation loop)
   - Set by `view_mode_set` at initialization
   - Controls which rendering path is used

2. **word_79F16** (0x79F16) - **View index** (changes dynamically)
   - Values like 0, 1, 2, 3, 4, 5, 6, 7, 8...
   - Set by view key handlers
   - Selects specific view within the current mode

### How It Works

```
Mission Start:
  view_mode_set() sets r15_external_view_flag based on mission type/config
  
During Flight:
  User presses view key (e.g., Key 2 for ground view)
  ↓
  Dispatcher finds handler for scan 0x03
  ↓
  Handler sets word_79F16 = 7 (or whatever index ground view is)
  ↓
  Simulation loop reads:
    - r15_external_view_flag (0 or 1) → chooses Path A or B
    - word_79F16 (0-8) → chooses specific view within that path
  ↓
  Appropriate view rendering function called
```

### Evidence For This

1. **Only 1 write to flag found** - in initialization function
2. **Flag only read 4 times** - all in simulation loop path selection
3. **Handlers set word_79F16** - not the external flag
4. **Manual says both internal and external views available** - maybe simultaneously?

### Evidence Against This

1. **User confirmed views can switch** - But maybe they mean switching WITHIN a mode?
2. **Keys 1,2,7,8,0 vs 3,4,5,6 are different types** - External vs Internal

### Alternative Interpretation

Maybe ALL 10 view keys work in BOTH modes:
- In cockpit mode (flag=0): Keys select different cockpit angles + can switch to chase/external temporarily
- In external mode (flag=1): Keys select different external views + can look at cockpit

This would explain why both types are always available.

## Test This Hypothesis

Need to examine what the simulation loop does with word_79F16:

1. Find where word_79F16 is read
2. See how it's used in Path A vs Path B
3. Check if there are view functions indexed by this value

## Next Steps

1. Search for reads of word_79F16 in r15_simulation_loop
2. Look for switch/jump tables indexed by word_79F16
3. Find the view rendering functions
4. Map word_79F16 values to actual view types

## If True, This Means

- **r15_external_view_flag** = Game mode (sim vs replay, pilot vs chase camera mode)
- **word_79F16** = Which specific view within that mode
- View keys just change the view index, not the mode
- The "external vs internal" distinction might be:
  - Controlled by mission setup, OR
  - Inferred from the word_79F16 value itself

## Why This Matters

If this is true, we need to:
1. Rename word_79F16 to something like "view_index" or "active_view_number"
2. Document that r15_external_view_flag is NOT toggled during flight
3. Find how word_79F16 values map to view types
4. Understand when/why the flag IS set (mission type? user preference?)

## How to Confirm

Run the game and:
1. Start in cockpit view
2. Press Key 1 (satellite) - does it switch to external?
3. If yes: flag must change OR satellite works in cockpit mode
4. If no: there must be a mode lock somewhere

Unfortunately we can't run the game from here, so we have to deduce from static analysis.
