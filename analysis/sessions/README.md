# Session Notes

**Temporary work notes from analysis sessions**

## Purpose

This directory contains work-in-progress notes from reverse engineering sessions. These are **temporary** and should be promoted to permanent documentation when complete.

## Structure

```
sessions/
├── 2026-11-10_ai_system/
│   ├── notes.md
│   ├── hypotheses.md
│   └── findings.md
├── 2026-11-11_hud_rendering/
│   └── work_log.md
└── README.md (this file)
```

## When to Use Session Notes

✅ **Use session notes for**:
- Daily work logs
- Experimental hypotheses
- Debugging traces
- Dead ends and failed approaches
- Work-in-progress findings
- Quick dumps of assembly code
- Temporary data analysis

❌ **Don't use session notes for**:
- Confirmed, verified findings → use `docs/`
- Function name registry → use `ida_scripts/apply_known_names.py`
- Data format specifications → use `docs/data_formats/`
- Architecture documentation → use `docs/architecture/`

## Lifecycle

1. **Create**: Start a new session directory when beginning work on a topic
   ```
   sessions/YYYY-MM-DD_topic_name/
   ```

2. **Work**: Document findings, hypotheses, dead ends as you go

3. **Promote**: When analysis is complete:
   - Extract confirmed findings
   - Write clean documentation in `docs/<system>/`
   - Update `ida_scripts/apply_known_names.py` with function names
   - Run IDA synchronization

4. **Archive**: Move old session notes to `archive/old_sessions/`
   - Keep recent sessions (last 2 weeks)
   - Archive older sessions for historical reference

## Session Naming Convention

```
YYYY-MM-DD_<topic>/
```

Examples:
- `2026-11-11_ai_behavior/`
- `2026-11-11_terrain_rendering/`
- `2026-11-12_mission_file_format/`

## What to Include

Each session directory can contain:
- `notes.md` - Main work notes
- `hypotheses.md` - Theories being tested
- `findings.md` - What was discovered
- `dead_ends.md` - What didn't work (saves future time!)
- Assembly dumps, hex dumps, screenshots

## Example Session Note

```markdown
# 2026-11-11: AI Behavior System Analysis

## Goal
Understand how AI behavior flags control entity actions

## Hypotheses
1. Flags are at [si+0Bh] - CONFIRMED ✓
2. Bit 0x01 = ground attack mode - TESTING
3. Bit 0x08 = combat mode - CONFIRMED ✓

## Findings
- Found behavior dispatcher at 0x3CE92
- 66 test instructions found
- Priority cascade: Special > Combat > Cruise > Landing > Ground

## Next Steps
- Document in docs/architecture/ai.md
- Add ai_entity_behavior_dispatcher to apply_known_names.py
- Test hypothesis #2 tomorrow

## Dead Ends
- Thought flags were at [si+0Dh] - wrong, it's 0x0B
```

## Promoting to Permanent Docs

When analysis is complete:

1. **Review** session notes for confirmed findings
2. **Clean up** - remove hypotheses, dead ends, temporary traces
3. **Write** clean documentation in `docs/`
4. **Update** `ida_scripts/apply_known_names.py`
5. **Commit** everything together
6. **Archive** session notes to `archive/old_sessions/`

## Benefits of Session Notes

✅ **Capture thoughts in real-time** - don't lose ideas  
✅ **Track dead ends** - don't repeat failed experiments  
✅ **Show progress** - see how understanding evolved  
✅ **Separate WIP from verified** - keep docs/ clean  

---

**Remember**: Session notes are temporary. Promote findings to `docs/` when done!

---

*Last updated: 2026-11-11*
