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
This creates 7 synthetic test cases in the current directory with controlled frame sequences.

### Run the full test suite:
```bash
python3 run_tests.py
```
This runs:
- 15 unit tests (accuracy on all test cases)
- 2 functional tests (output format validation)

Expected output:
```
✓ 17/17 tests passed
```

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
- `test_case_4_multiple_damages` - 3 sequential hits from real combat
- `test_case_real_boss_health_bar_appears_004` - Real entrance animation
- `test_case_real_false_negative_01_24_006` - Real detection edge case
- `test_case_real_false_positive_01_03_005` - Real false positive test
- `test_case_real_false_positive_02_15_02_17_007` - Real false positive test
- `test_case_real_hit_001`, `002`, `003` - Real individual hits

These provide validation against actual video artifacts (compression, color variations, etc.).

---

## Test Suite Output

### Running Tests

```bash
python3 run_tests.py
```

Output includes:
- **Unit Tests (15 total)**: Each synthetic/real test case, showing expected vs actual event count
- **Functional Tests (2 total)**:
  - `output_format_single_hit` - Validates MM:SS timestamp format on single hit
  - `known_limitation_small_hits` - Validates partial detection (at least 2/3 hits) and format

### Test Results Summary

```
======================================================================
PHASE 2 TEST SUITE
======================================================================

Running 15 unit tests...
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
TOTAL: 17/17 tests passed
======================================================================

✓ All tests passed!
```

## Algorithm Details

The hit detection algorithm uses the following approach:

1. **Health Bar Extraction**: Each frame has a 998×6 pixel health bar. The rightmost red pixel indicates current health.

2. **Auto-Detection (Optional)**: Automatically detect when the health bar appears (frames with health value >= 0).

3. **Stabilization Detection**: Find when health values stabilize at ~980+ pixels (boss at full health for 50+ consecutive frames).

4. **Rolling Minimum**: Apply a 60-frame rolling minimum window to smooth out transient flickering from damage/death animations.

5. **Event Detection**: Detect damage (health drops by 50+ pixels) and healing (health increases by 50+ pixels).

6. **Event Coalescing**: Merge nearby events (within 500ms) into single events to handle multi-frame animations.

## Key Behaviors Tested

- ✓ Pre-boss frames don't trigger events
- ✓ Entrance animation and stabilization are skipped
- ✓ Single damage events are detected
- ✓ Multiple consecutive hits are detected separately
- ✓ Boss healing is detected
- ✓ Damage below threshold is filtered out
- ✓ Death animation doesn't create spurious events
- ✓ Complex multi-event scenarios work correctly

## Known Limitations

- Test cases use idealized frame sequences. Real video compression and frame artifacts may behave differently.
- The algorithm assumes health bar is always at the same vertical position (row 0-5).
- Entrance animation behavior varies per video; the 60-frame stabilization detection may need tuning for different boss types.
