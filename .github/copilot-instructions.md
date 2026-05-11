# Copilot Instructions: Elden Ring Poise Overlay

> **See README.md for project overview, basic usage, technical details, customization, and troubleshooting.** This file contains context *not* in README for efficient development.

---

## Quick Reference: Critical Commands

### ⚠️ Frame Extraction — ALWAYS Use the Project Script
**Never use raw `ffmpeg` with hardcoded crop coordinates.** The crop region varies by recording setup.
Always use `phase1-extract-health-bar.sh` which has the correct defaults:

```bash
# Standard extraction (uses correct default crop: x=465, y=873, w=999, h=7)
bash phase1-extract-health-bar.sh -o <output_dir> <video_file>

# With custom crop if needed
bash phase1-extract-health-bar.sh -x 465 -y 873 -w 999 -h 7 -o <output_dir> <video_file>
```

This applies to ALL frame extraction: debugging, investigation, testing, re-running analysis.

### Test Suite (Phase 2 validation)
```bash
cd phase_2_test/
python3 test_case_generator.py  # Generate 8 synthetic test cases
python3 run_tests.py            # Validate hit detection accuracy
```

### Single Test Phase 2 Run
```bash
python3 phase2-detect-hits.py <frames_dir> -o output.txt --debug
```

---

## Internal Architecture (Not in README)

### Phase 2: Hit Detection Implementation
Single implementation: `phase2-detect-hits.py` (state machine approach)

**Algorithm approach:**
- Tracks white marker position in health bar
- State machine prevents post-death false positives
- Handles entrance stabilization and rapid hit coalescing
- Outputs MM:SS timestamps, one per hit detected

### Phase 3: Poise Physics Model
The simulation runs **per-millisecond** with this exact logic:

```python
for each millisecond:
  1. Check for hit at this timestamp
  2. If hit: poise = max(0, poise - damage)
  3. If (time since last hit) > regen_timer:
     elapsed = (current_time - last_hit_time) - regen_timer
     regen = (elapsed / 1000) * regen_rate
     poise = min(max_poise, poise + regen)
```

Key: **Each hit restarts the regen delay.** Multiple rapid hits don't accumulate recovery.

### Key Internal Data Flows

```
test.mp4 [VIDEO]
    ↓ (Phase 1: ffmpeg crop + extract)
frames/frame_000000.png ... frame_005279.png [5280 PNG FILES]
    ↓ (Phase 2: analyze health bar boundary)
test.txt [TIMESTAMPS ONLY]
    00:23
    00:53
    ↓ (USER ANNOTATES)
test.txt [ANNOTATED]
    00:23,18.72
    00:53,18.72
    ↓ (Phase 3: millisecond-granularity simulation)
poise_timeline.txt [176,000+ LINES]
    0 47.000000
    1 47.000000
    ...
    ↓ (Phase 4: graph plot)
poise_graph.png [POISE TIMELINE VISUALISATION]
    ↓ (Phase 5: frame generation + ffmpeg encoding)
poise_overlay_final.mp4 [OUTPUT VIDEO]
```

---

## Testing Strategy

### When to Add Tests
- New hit detection edge case discovered
- Algorithm behavior change to validate
- Boss with different health bar characteristics

### Adding a Test Case
1. Create directory: `phase_2_test/test_case_N_description/`
2. Add PNG frames following pattern from existing cases (use test_case_generator.py as reference)
3. Document expected event count in test name or README
4. Run `python3 run_tests.py` — it auto-discovers and validates

### Synthetic Test Cases Included
- `test_case_1_pre_boss` - No health bar, expect 0 events
- `test_case_2_entrance_animation` - Flickering on boss arrival, expect 0 events
- `test_case_3_single_damage` - Single hit detection
- `test_case_4_multiple_damages` - Sequential hits with stabilization
- `test_case_5_boss_healing` - Damage + heal cycle
- `test_case_6_death_animation` - Boss dies without spurious events
- `test_case_7_damage_threshold` - Filters small damage below threshold
- `test_case_8_complex_scenario` - All elements: entrance, multiple hits, heal, death

Each case is a directory with frame PNGs + `_output.txt` file showing detected events.

---

## Development Patterns

### Modifying Hit Detection
- **Sensitivity:** Change `--damage-threshold` flag (default 50px)
- **Timing:** Adjust `--min-hit-spacing` for merge window
- **State behavior:** Edit state machine constants in script
- **⚠️ IMPORTANT:** After any change to `phase2-detect-hits.py`, run full test suite:
  ```bash
  cd phase_2_test/
  python3 run_tests.py
  ```
  All 8+ test cases must pass before considering the change complete.

### Debugging Hit Detection
1. Run with `--debug` flag to see frame-by-frame health values
2. Check `test_case_*_output.txt` to see what was detected vs. expected
3. Inspect frame PNGs visually to understand health bar state
4. Add new test case if edge case isn't covered
5. Run full test suite to ensure fix doesn't break other cases

### Poise Parameter Tuning
- **Boss-specific:** Each boss has different max poise (Gideon=47)
- **Recovery delay:** Usually 3.85s; may vary by weapon/build
- **Recovery rate:** Standard is 13 poise/second for Elden Ring
- All configurable via CLI flags in phase3-calculate-poise.py

### Phase 4: Poise Graph
`phase4-plot-poise.py` — reads poise timeline, plots per-second graph with coloured zones.
- `--max-poise N` to override y-axis max
- `-o file.png` to save; omit to display interactively
- Uses matplotlib; install with `pip install matplotlib`

### Phase 5: Overlay Rendering
`phase5-create-overlay.py` — pipes RGBA frames to FFmpeg (qtrle → MOV → composite MP4)

---

## Common Development Tasks

### Test a New Hit Detection Algorithm Variant
1. Copy `phase2-detect-hits.py` → `phase2-detect-hits-v4-yourname.py`
2. Modify algorithm
3. Update `phase_2_test/run_tests.py` to reference your new script
4. Run: 
   ```bash
   cd phase_2_test/
   python3 run_tests.py
   ```
5. All test cases must pass before promoting variant to default

### Making Production Changes to phase2-detect-hits.py
1. Make changes to algorithm or parameters
2. **Must run full test suite before finishing:**
   ```bash
   cd phase_2_test/
   python3 run_tests.py
   ```
3. All tests must pass (verify no regressions on other edge cases)
4. Only then consider the change production-ready

---

## Notes for Copilot Sessions

- **Do not commit changes to git.** User will handle all git operations.
- README.md is the user-facing documentation; keep copilot-instructions.md narrowly focused on implementation context.
- Phase 2 hit detection is the most complex piece; algorithm changes here have cascading effects.
- All external dependencies (ffmpeg, PIL, numpy) are listed in README prerequisites.
- Test suite is comprehensive; add cases before implementing algorithm changes.
