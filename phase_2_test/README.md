# Phase 2 Test Suite: Hit Detection

This test suite validates the Phase 2 hit detection algorithm using:
- **Synthetic test cases** (programmatically generated, fully controlled)
- **Real video test cases** (extracted from actual gameplay)

---

## Quick Start

### Generate or regenerate synthetic test cases:
```bash
python3 synthetic_test_generator.py
```
This creates synthetic test cases in the current directory with controlled frame sequences.

### Run the full test suite:
```bash
python3 run_tests.py
```
This runs:
- 19 unit tests (accuracy on all test cases)
- 2 functional tests (output format validation)

Expected output:
```
✓ 21/21 tests passed
```

### Debugging test failures:

On any failure, the runner automatically shows which timestamps were actually detected, so you can see immediately whether the algorithm found too many, too few, or the wrong events.

For a deeper investigation, add `--debug` to get a full frame-by-frame state machine trace re-run for every failing test:

```bash
python3 run_tests.py --debug
```

This passes `--debug` to `phase2-detect-hits.py` for each failing case, printing every state transition and marker position decision.

---

## Synthetic Test Case Generator

**File:** `synthetic_test_generator.py`

Programmatically creates realistic but fully-controlled health bar frame sequences for testing specific edge cases.

### Generated Test Cases

Each test case consists of a directory with PNG frames (7px tall × 999px wide) showing health bar states.

#### test_case_1_pre_boss
- **Description**: Pre-boss gameplay (no health bar visible)
- **Frames**: 50 frames with background only
- **Expected Events**: 0
- **Purpose**: Verify pre-boss frames don't trigger false events

#### test_case_2_entrance_animation
- **Description**: Boss bar appears (health bar transition)
- **Frames**: 1 empty frame, then 49 frames at full health (999px)
- **Expected Events**: 0
- **Purpose**: Verify entrance doesn't count as damage

#### test_case_3_single_damage
- **Description**: Single damage event
- **Frames**: 10 frames at full health (999px), then 10 frames at damaged (950px)
- **Expected Events**: 1
- **Purpose**: Verify basic hit detection

#### test_case_5_boss_healing
- **Description**: Damage followed by healing
- **Frames**: Full (999) → Damaged (800) → Healed (900)
- **Expected Events**: 1
- **Purpose**: Verify damage detection and healing handling

#### test_case_6_death_animation
- **Description**: Progressive health depletion to zero
- **Frames**: 100px → 50px → 0px (final hit)
- **Expected Events**: Multiple (health decreases)
- **Purpose**: Verify final hit detection without spurious events

#### test_case_7_damage_threshold
- **Description**: Tests damage threshold filtering
- **Frames**: Full (999) → Small damage (996, 3px) → Large damage (950, 46px)
- **Expected Events**: 2
- **Purpose**: Verify threshold detection

#### test_case_8_complex_scenario
- **Description**: Multiple rapid hits with varying magnitudes
- **Frames**: 999 → 850 → 700 → 500px
- **Expected Events**: 3
- **Purpose**: Test algorithm on realistic multi-hit scenario

### Why Synthetic Tests?

- **Reproducible**: Same frames every time, no video compression artifacts
- **Controlled**: Exact pixel positions, no ambiguity
- **Fast**: No video processing needed
- **Targeted**: Each case tests a specific edge case
- **Automatable**: Can be regenerated and validated in CI/CD

### Regenerating Tests

If you modify the test case generation logic (e.g., to change thresholds or health bar widths), regenerate:

```bash
python3 synthetic_test_generator.py
```

This deletes old frames and creates fresh ones. Run `python3 run_tests.py` to validate.

---

## Real Video Test Cases

In addition to synthetic cases, the suite includes real video test cases extracted from actual gameplay:
- `test_case_4_multiple_damages` - 4 sequential hits from real combat
- `test_case_real_boss_health_bar_appears_004` - Bar appears, no hits
- `test_case_real_false_negative_01_24_006` - Mid-combat clip, two genuine hits
- `test_case_real_false_positive_01_03_005` - Real false positive test (expect 0)
- `test_case_real_false_positive_02_15_02_17_007` - bar_right spike test (expect 0)
- `test_case_real_barright_spike_first_hit_010` - Gameplay pixels inflate bar_right; first real hit detected
- `test_case_real_first_hit` - First hit scenario
- `test_case_real_hit_002`, `test_case_real_hit_003` - Individual hits
- `test_case_real_rapid_hit_008` - Rapid hit with flicker suppression
- `test_case_real_spurious_entrance_first_hit_009` - Spurious entrance flicker suppressed
- `test_case_real_intermission` - Phase transition: one hit in Phase 1, intermission, no hits in Phase 2

These provide validation against actual video artifacts (compression, colour variations, gameplay pixel bleed-through, etc.).

---

## Test Suite Output

### Running Tests

```bash
python3 run_tests.py
```

Output includes:
- **Unit Tests (19 total)**: Each synthetic/real test case, showing expected vs actual event count
- **Functional Tests (2 total)**:
  - `output_format_single_hit` - Validates MM:SS.mmm timestamp format on single hit
  - `known_limitation_small_hits` - Validates partial detection (at least 2/4 hits) and format

On any **failure**, the runner prints the timestamps that were actually detected — no extra flags needed. For the full frame-by-frame trace, use `--debug`.

### Test Results Summary

```
======================================================================
PHASE 2 TEST SUITE
======================================================================

Running 19 unit tests...
[results for each test case]

Running 2 functional tests...
[format validation results]

======================================================================
TEST RESULTS SUMMARY
======================================================================

UNIT TESTS                               Expected     Actual       Result
...

FUNCTIONAL TESTS                         Result
...

======================================================================
TOTAL: 21/21 tests passed
======================================================================

✓ All tests passed!
```

## Algorithm Details

The hit detection algorithm is a state machine. See [`PHASE_2_STATE_MACHINE_DESIGN.md`](../PHASE_2_STATE_MACHINE_DESIGN.md) in the project root for the full design.

Key behaviours tested here:

- ✓ Pre-boss frames don't trigger events
- ✓ Health bar appearance doesn't count as a hit
- ✓ Gameplay pixels bleeding into the crop area (inflating `bar_right`) don't cause false positives
- ✓ Single and multiple damage events are detected correctly
- ✓ Boss healing is handled without false events
- ✓ Damage below threshold is filtered out
- ✓ Death animation doesn't create spurious events
- ✓ Mid-combat clip starts (bar already present) are handled correctly
- ✓ Phase transitions (intermissions) are handled without spurious events
- ✓ Complex multi-event scenarios work correctly

## Known Limitations

- Test cases use idealized or pruned frame sequences. Real video compression and frame artifacts may behave differently; real test cases cover many of these.
- The algorithm assumes the health bar crop strip is always extracted by `phase1-extract-health-bar.sh`. Do not use ad-hoc ffmpeg extraction for investigation — the crop position will be wrong.
