# Falcon 3.0 Audio System Deep Dive

**Version:** 1.0  
**Status:** Active Analysis  
**Last Updated:** 2026-11-11

## Executive Summary

The audio system provides **sound effects and potentially music** for the simulation. With 25 functions identified, it's the smallest of the 9 major subsystems, reflecting 1991-era PC audio limitations.

**System Profile:**
- Functions: 25 identified (smallest subsystem)
- Audio Hardware: PC Speaker, Sound Blaster, AdLib, possibly Roland MT-32
- Audio Types: Sound effects (engine, weapons, warnings), possibly music
- Complexity: Low-Medium (constrained by 1991 hardware)
- Update Rate: Event-driven (trigger sounds) + continuous (engine)

**Analysis Progress:** 5% - Function count known, architecture to be discovered

## System Architecture

### Audio Pipeline

```
[GAME EVENTS]
    ↓ Weapon fire
    ↓ Engine sounds
    ↓ Warnings (stall, missile launch)
    ↓ Radio calls
    ↓
[AUDIO SYSTEM - 25 functions]
    ↓
    1. EVENT HANDLING
       ↓ Receive audio trigger event
       ↓ Select sound effect
       ↓
    2. SOUND MANAGEMENT
       ↓ Check available channels
       ↓ Priority system (important sounds override others)
       ↓ Load sound data if not in memory
       ↓
    3. HARDWARE OUTPUT
       ↓ PC Speaker (beeps, simple tones)
       ↓ OR Sound Blaster (PCM samples, 8-bit)
       ↓ OR AdLib (FM synthesis, music)
       ↓ OR Roland MT-32 (MIDI, high-quality)
    ↓
[AUDIO HARDWARE] → Speakers
```

### Integration Points

**Inputs (Game Events):**
- Weapons: gun fire, missile launch, explosion
- Engine: engine RPM (continuous, varies with throttle)
- Flight: wind noise, stall buffet, sonic boom
- Warnings: stall warning, missile warning, "beep beep beep"
- Radio: pilot comm, ATC, AWACS

**Outputs (Hardware):**
- PC Speaker: Direct port 0x61 (timer 2)
- Sound Blaster: DSP command interface, DMA transfer
- AdLib: OPL2/OPL3 FM synthesizer registers
- Roland MT-32: MIDI commands via MPU-401 interface

**Callers:**
- Weapons system: Triggers weapon sounds
- Physics system: Triggers engine sounds based on RPM
- AI system: Triggers radio calls
- Warning system: Triggers audio warnings

## Core Functions

### Expected Function Categories

### 1. Initialization & Cleanup (~3 functions)

- **audio_init**: Initialize audio system, detect hardware
- **audio_shutdown**: Cleanup, stop all sounds
- **audio_detect_hardware**: Detect available audio hardware

**Hardware Detection:**
- Check for Sound Blaster (port 0x220, 0x240, etc.)
- Check for AdLib (port 0x388)
- Check for Roland MT-32 (port 0x330 MPU-401)
- Fall back to PC Speaker if no sound card

### 2. PC Speaker Output (~3 functions)

- **audio_speaker_beep**: Generate beep at specific frequency
- **audio_speaker_tone**: Play tone for duration
- **audio_speaker_off**: Stop tone

**PC Speaker:**
- Programmable Interval Timer (PIT) channel 2
- Port 0x42: Frequency divisor (low byte)
- Port 0x42: Frequency divisor (high byte)
- Port 0x43: Mode control
- Port 0x61: Enable/disable speaker

**Frequency Formula:**
```
frequency = 1193180 / divisor
```

**Limitations:**
- Monophonic (one tone at a time)
- Square wave only (harsh sound)
- No volume control

### 3. Sound Blaster Output (~6 functions)

- **audio_sb_init**: Initialize Sound Blaster DSP
- **audio_sb_play_sample**: Play 8-bit PCM sample
- **audio_sb_stop**: Stop playback
- **audio_sb_set_volume**: Set volume (if supported)
- **audio_sb_dma_setup**: Setup DMA transfer for sample data
- **audio_sb_irq_handler**: Interrupt handler for playback complete

**Sound Blaster Interface:**
- DSP command port (base + 0xC)
- DSP data read (base + 0xA)
- DSP write buffer status (base + 0xC)
- DSP read buffer status (base + 0xE)

**Sample Format:**
- 8-bit PCM (unsigned)
- Sample rates: 11025 Hz (low), 22050 Hz (high)
- Mono (most common in 1991)

**DMA Transfer:**
- DMA channel 1 (typically)
- Transfer sample data from memory to DSP
- IRQ when transfer complete

### 4. AdLib/FM Synthesis (~4 functions)

- **audio_adlib_init**: Initialize AdLib OPL2 synthesizer
- **audio_adlib_set_instrument**: Configure FM operator parameters
- **audio_adlib_play_note**: Play note on channel
- **audio_adlib_stop_note**: Stop note

**AdLib Interface:**
- OPL2 chip at port 0x388 (address) and 0x389 (data)
- 9 FM channels (2-operator)
- 11 percussion instruments (in percussion mode)

**FM Synthesis:**
- Two operators per channel (modulator + carrier)
- Attack, Decay, Sustain, Release (ADSR envelope)
- Frequency, waveform, feedback parameters

**Usage:**
- Background music (unlikely in flight sim)
- Possibly engine sounds (FM can synthesize engine tones)

### 5. Roland MT-32/MIDI (~3 functions)

- **audio_midi_init**: Initialize MIDI interface (MPU-401)
- **audio_midi_send_message**: Send MIDI message
- **audio_midi_play_note**: Play note on channel

**MIDI Interface:**
- MPU-401 at port 0x330 (command/status) and 0x331 (data)
- MIDI messages: Note On, Note Off, Program Change, etc.

**Roland MT-32:**
- 32-voice multitimbral synthesizer
- High-quality sound (compared to AdLib)
- Expensive hardware in 1991 (not common)

### 6. Sound Management (~4 functions)

- **audio_play_sound**: High-level function to trigger sound effect
- **audio_stop_sound**: Stop specific sound
- **audio_stop_all**: Stop all sounds
- **audio_set_volume**: Set master volume

**Priority System:**
- High priority: Warnings, missile launch
- Medium priority: Gun fire, explosions
- Low priority: Engine hum, wind noise

**If all channels busy:**
- Stop lowest-priority sound
- Play new sound in that channel

### 7. Continuous Sounds (~2 functions)

- **audio_update_engine_sound**: Update engine sound based on RPM
- **audio_update_wind_sound**: Update wind noise based on airspeed

**Engine Sound:**
- Varies with throttle/RPM
- Possible implementation: Modulate pitch/volume of continuous tone
- Or: Crossfade between multiple engine samples at different RPMs

**Wind Sound:**
- Varies with airspeed
- Continuous white/pink noise, volume proportional to speed

## Audio Hardware (1991)

### PC Speaker

**Pros:**
- Available on every PC (no extra hardware)
- Simple to program

**Cons:**
- Monophonic (one tone at a time)
- Square wave only (harsh sound)
- No volume control
- Ties up CPU for tone duration

**Typical Usage:**
- Beeps for warnings
- Simple sound effects (if no sound card)

### Sound Blaster (8-bit)

**Pros:**
- PCM playback (realistic sounds)
- DMA transfer (low CPU usage)
- Relatively affordable (~$100 in 1991)

**Cons:**
- 8-bit, 11-22 kHz (low quality by modern standards)
- Mono only (early cards)
- Limited simultaneous sounds (need mixing)

**Typical Usage:**
- Sound effects (gun fire, explosions, engine)
- Voice (pilot comms, warnings)

### AdLib / Sound Blaster FM

**Pros:**
- FM synthesis (musical tones)
- 9 channels (multiple simultaneous sounds)
- Low memory footprint (no samples)

**Cons:**
- Synthetic sound (not realistic for effects)
- Difficult to program (complex parameters)

**Typical Usage:**
- Background music
- Possibly engine tones

### Roland MT-32

**Pros:**
- High-quality synthesis
- 32 voices
- Excellent for music

**Cons:**
- Expensive ($500+ in 1991)
- Rare
- External device

**Typical Usage:**
- Music (unlikely in Falcon 3.0)

## Sound Effect Details

### Weapon Sounds

**Gun Fire:**
- Short burst, 50-100ms
- Loud, high-priority
- Possible sample: Recorded Vulcan cannon

**Missile Launch:**
- "Whoosh" sound, 200-500ms
- High-priority

**Explosion:**
- Loud, low-frequency, 500-1000ms
- Medium-priority

### Engine Sounds

**Jet Engine:**
- Continuous sound
- Varies with throttle (pitch and volume)
- Possible implementation: Multiple samples (idle, mid, full, afterburner)
- Or: Single sample pitch-shifted

**Afterburner:**
- Distinct roar
- Triggered when throttle > 100%

### Warning Sounds

**Stall Warning:**
- Continuous tone or pulsing beep
- Triggers at high AoA

**Missile Warning:**
- "Beep beep beep" rapid pulsing
- Triggers when missile lock detected (RWR)

**Altitude Warning:**
- "Whoop whoop pull up" (GPWS - Ground Proximity Warning System)
- Triggers when low altitude, high descent rate

### Radio Calls

**Pilot Comms:**
- Voice samples: "Fox two" (missile launch), "Splash one" (kill), etc.
- Possibly digitized speech

**AWACS:**
- "Picture" calls (radar contacts)
- Vectoring instructions

## Data Structures

### Expected Structures (Need Verification)

```c
// Sound effect definition
struct SoundEffect {
    uint8_t* sample_data;      // PCM sample data (or NULL for PC speaker)
    uint16_t sample_length;    // Length in bytes
    uint16_t sample_rate;      // Sample rate (11025, 22050 Hz)
    uint8_t priority;          // 0=low, 255=high
    uint8_t looping;           // 0=one-shot, 1=loop
};

// Audio channel (for mixing)
struct AudioChannel {
    uint8_t active;            // 0=free, 1=playing
    SoundEffect* sound;        // Current sound effect
    uint16_t position;         // Current position in sample
    uint8_t volume;            // Volume (0-255)
};

// Audio system state
struct AudioState {
    uint8_t hardware_type;     // 0=PC speaker, 1=SB, 2=AdLib, 3=MT-32
    uint16_t hardware_base;    // Base I/O port (e.g., 0x220 for SB)
    uint8_t hardware_irq;      // IRQ number
    uint8_t hardware_dma;      // DMA channel
    
    AudioChannel channels[8];  // Audio channels for mixing
    uint8_t master_volume;     // Master volume (0-255)
};
```

### Memory Locations (Need Discovery)

- Audio state: Unknown (likely DGROUP)
- Sound samples: Unknown (possibly separate data file or embedded in executable)
- Channel state: Unknown

## Performance Characteristics

### Expected Timings (1991 Hardware)

**Audio Update Budget:** 0.5-1ms per frame

**Costs (estimated):**
- Trigger sound effect: 10-50 µs (check channels, start playback)
- Update continuous sounds: 50-100 µs (modulate engine/wind sounds)
- Software mixing: 1-2ms per frame (if mixing multiple samples in software)

**Hardware DMA:**
- If using Sound Blaster DMA, no CPU cost during playback
- Only cost is triggering playback (~50 µs)

**Optimization:**
- Use hardware mixing/DMA when available (Sound Blaster)
- Limit simultaneous sounds (e.g., max 8 channels)
- Priority system (stop low-priority sounds if channels full)

## Integration with Other Systems

### Weapons System

**Weapons trigger sounds:**
- Gun fire → gun sound
- Missile launch → missile sound
- Explosion → explosion sound

### Physics System

**Physics triggers engine sounds:**
- Engine RPM → engine sound pitch/volume
- Airspeed → wind noise volume

### Warning System

**Warnings trigger audio alerts:**
- Stall warning
- Missile warning
- Altitude warning

### AI System

**AI triggers radio calls:**
- "Tally two"
- "Engaged"
- "Winchester"

## Discovery Status

### ✅ Completed

1. **Function Count:** 25 functions identified

### 🔄 In Progress

1. **Function List:** Need to extract actual function names
2. **Hardware Support:** Need to identify which audio hardware is supported
3. **Sound Effects:** Need to locate sound sample data

### 📋 Next Steps

1. **Search for Audio Functions:**
   - Pattern: "audio_*", "sound_*", "snd_*"
   - Pattern: "speaker_*", "sb_*" (Sound Blaster), "adlib_*", "midi_*"
   - Search for strings: "sound", "beep", "volume"

2. **Identify Hardware Support:**
   - Find hardware detection code
   - Identify Sound Blaster support
   - Check for AdLib/MIDI support

3. **Locate Sound Data:**
   - Find sound effect samples
   - Identify sample format
   - Map sound effect IDs

4. **Analyze Audio Triggers:**
   - Find where sounds are triggered
   - Map event → sound effect
   - Understand priority system

5. **Profile Performance:**
   - Measure audio update cost
   - Check if software mixing is used
   - Identify optimization opportunities

## Open Questions

### Hardware
1. **Supported Hardware:** PC Speaker, Sound Blaster, AdLib, MT-32?
2. **Detection:** How is hardware detected?
3. **Fallback:** What's the fallback if no sound card?

### Implementation
4. **Mixing:** Software mixing or hardware-only?
5. **Sample Format:** 8-bit PCM, sample rates?
6. **Sample Storage:** Embedded in exe or external files?
7. **Priority System:** How are sound priorities handled?

### Sounds
8. **Sound Count:** How many distinct sound effects?
9. **Engine Sound:** Sample-based or synthesized?
10. **Voice:** Are there voice samples (pilot comms)?

### Performance
11. **Bottleneck:** Is audio a performance concern?
12. **DMA Usage:** Is DMA used for Sound Blaster?

### Data
13. **State Location:** Where is audio state in memory?
14. **Sample Location:** Where are sound samples stored?

## Next Steps

1. **Search for audio functions** - Build complete function list
2. **Identify hardware support** - Determine supported audio hardware
3. **Locate sound data** - Find sound samples and format
4. **Map sound triggers** - Document event → sound mappings
5. **Analyze playback** - Understand audio playback implementation
6. **Profile execution** - Measure audio system cost
7. **Update ARCHITECTURE.md** - Add audio system details

## References

- **ARCHITECTURE.md**: Overall system structure
- **WEAPONS_AI_SYSTEM.md**: Triggers weapon sounds
- **PHYSICS_SYSTEM.md**: Triggers engine sounds
- **HUD_SYSTEM.md**: Visual warnings (complement to audio)
- **SYSTEM_MAP.md**: Initial discovery of 25 audio functions

---

**Analysis Status:** Stage 1 - Function count known, architecture estimated, detailed analysis needed  
**Confidence:** Medium (architecture based on typical 1991 PC audio)  
**Verification:** 5% (function count known, details need IDA analysis)
