# Phase 2 Test Suite: Hit Detection

This test suite validates the Phase 2 hit detection algorithm by using synthetic test cases that exercise specific behaviors.

## Test Cases

### test_case_1_pre_boss
- **Description**: Pre-boss gameplay (no health bar visible)
- **Frames**: 50 black frames (no red pixels)
- **Expected Events**: 0
- **Purpose**: Verify that pre-boss frames don't trigger false events

### test_case_2_entrance_animation
- **Description**: Boss entrance animation with health bar flickering
- **Structure**:
  - 60 frames: Health bar flickering (300-800 pixels, unstable)
  - 60 frames: Health bar stabilization at 989 pixels
- **Expected Events**: 0
- **Purpose**: Verify that entrance animation and stabilization don't trigger false damage/heal events

### test_case_3_single_damage
- **Description**: Single damage event in stable gameplay
- **Structure**:
  - 50 frames: Full health (989)
  - 3 frames: Damage animation (989 → 750)
  - 50 frames: Damaged health (750)
- **Expected Events**: 1
- **Purpose**: Verify single damage detection

### test_case_4_multiple_damages
- **Description**: Three sequential damage events
- **Structure**:
  - 50 frames @ 989, damage → 800, 50 @ 800
  - 50 frames @ 800, damage → 650, 50 @ 650
  - 50 frames @ 650, damage → 500, 50 @ 500
- **Expected Events**: 3
- **Purpose**: Verify multiple damage detection with proper spacing

### test_case_5_boss_healing
- **Description**: Boss takes damage then heals
- **Structure**:
  - 10 black frames (pre-boss)
  - 42 frames: Entrance animation
  - 50 frames: Stabilization at 989
  - 3 frames: Damage (989 → 750)
  - 50 frames: At 750
  - 4 frames: Heal (750 → 989)
  - 50 frames: At 989
- **Expected Events**: 2 (damage + heal)
- **Purpose**: Verify boss healing detection

### test_case_6_death_animation
- **Description**: Boss death animation with health bar disappearing
- **Structure**:
  - 50 frames: Full health (989)
  - 3 frames: Final damage (989 → 100)
  - 12 frames: Death animation (flickering 0-400)
  - 20 frames: Black (health bar gone)
- **Expected Events**: 1
- **Purpose**: Verify that death animation doesn't create spurious events

### test_case_7_damage_threshold
- **Description**: Test damage threshold filtering
- **Structure**:
  - 50 frames: Full health (989)
  - 3 frames: Small damage (989 → 950, 40px - below threshold)
  - 50 frames: At 950
  - 3 frames: Large damage (950 → 840, 110px - above threshold)
  - 50 frames: At 840
- **Expected Events**: 1 (only the large damage)
- **Purpose**: Verify that small damage below threshold is ignored

### test_case_8_complex_scenario
- **Description**: Real-world complex scenario with all elements
- **Structure**:
  - 10 black frames (pre-boss)
  - 42 frames: Entrance animation
  - 50 frames: Stabilization at 989
  - 3 hits: 989→800, 800→700, 700→650 (with 20 frame stable periods between)
  - 4 frames: Boss heal (650 → 989)
  - 20 frames: At 989
  - 10 frames: Death animation
  - 20 black frames
- **Expected Events**: 4 (3 damage + 1 heal)
- **Purpose**: Test the algorithm on a realistic combat scenario

## Running the Tests

### Generate all test cases:
```bash
python3 test_case_generator.py
```

### Run the test suite:
```bash
python3 run_tests.py
```

This will execute phase2-detect-hits-v2-white-strip.py on each test case and verify that the actual event count matches the expected count.

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
