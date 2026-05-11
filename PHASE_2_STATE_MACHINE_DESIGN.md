# Phase 2: White Marker State Machine Design

## Overview

The Phase 2 script detects boss damage events by analysing a cropped strip of the boss health bar across video frames. It uses a state machine to track the white marker — the boundary between the undamaged (red) portion of the bar and the damaged (empty) portion.

Each hit moves the white marker left. Healing moves it right. When the boss dies, both the red bar and the white marker disappear.

---

## Game Mechanics

### The Boss Health Bar

- The red health bar **appears in a single frame** — it does not animate in.
- When the bar first appears, there is **no white marker** — the boss is at full health.
- The white marker only appears when the boss **takes its first hit**.
- The bar always starts at the **left edge** of the cropped frame (x ≤ 10). Pre-boss UI elements that happen to contain red pixels appear further right and must be ignored.
- The bar is **fixed width** for the duration of the fight (it does not shrink as the boss loses health; the white marker moves left instead).

### Spurious bar_right Inflation

The Phase 2 crop covers a strip slightly wider than the health bar UI element. Gameplay footage is visible to the right of the bar in this strip. That gameplay footage can contain red pixels, which cause the rightmost-red-pixel detection (`bar_right`) to report a value far beyond the actual bar boundary.

This appears as `bar_right` spiking from the true bar edge (~305) to values like 500–800+, then snapping back when those gameplay pixels change. The white marker's position (`white_pos`) is unaffected — it sits at the fixed right end of the actual health bar and does not move during these spikes.

The algorithm guards against false first-hit detections caused by this spike pattern using `MIN_STABLE_FRAMES` and `MIN_QUIET_FRAMES` (see State 2 below).

### The White Marker

- The white marker sits at the **right edge of the red bar**.
- Moving **left** = boss took damage.
- Moving **right** = boss healed.
- Any movement ≥ 3px is counted (threshold exists only to filter pixel noise, not to exclude small real hits).
- When the boss **dies**, both the bar and the white marker disappear in the same frame (or within a few frames of each other).
- After a hit, the game overlays a **yellow damage indicator** on the bar showing the amount of damage dealt. This tints the white marker yellow (blue channel drops to ~160–176). The detection threshold accounts for this: R > 180, G > 180, B > 140.

### Mid-Combat Clips

- Some clips start with both the bar and white marker already visible (the clip was captured mid-fight).
- The current position of the white marker at the start of such a clip is **not** an event — it just establishes the tracking baseline.

### Phase Transitions (Intermission)

Some bosses have multiple phases separated by a cutscene animation:

- The white marker and bar both disappear (indistinguishable from defeat at that moment).
- Many frames pass with nothing visible.
- The bar reappears, followed shortly by the white marker at the same position as Phase 1 ended.
- The white marker reappearing after the bar returns is **not** an event — it is continuity from Phase 1.

Because defeat and intermission look identical at the moment of disappearance, the `final_hit` event is **deferred** until the clip ends without the bar returning.

---

## State Machine

```
State 1: Pre-Boss
  Bar absent, white absent.
  Ignore all white pixel detections.
  ─────────────────────────────────────────────────
  Bar appears, no white     → State 2  (no event)
  Bar appears WITH white    → State 2  (no event — mid_combat_start=True;
                                        State 2→3 transition fires immediately
                                        with no event, establishing baseline)

State 2: Bar Present, Not Yet Hit
  Bar present, white absent (or white present but not yet confirmed as genuine).
  Boss is at full health, or bar has returned after an intermission.
  Guards must all pass before transitioning to State 3:
    1. bar_stable_count ≥ MIN_STABLE_FRAMES (5 frames; or 1 for mid-combat start)
       Waits for bar_right to stop spiking from spurious gameplay red pixels.
    2. marker_in_range_count ≥ 2
       Requires the white marker to be within 30px of bar_right for 2 consecutive
       frames. Uses abs(gap) ≤ 30 (bidirectional) so a marker deep inside the bar
       (large negative gap) is also rejected.
    3. quiet_frames ≥ MIN_QUIET_FRAMES (37)
       Frames since the last large bar_right spike (>50px increase). Prevents
       firing during intermittent spike patterns in gameplay-footage red pixels.
       Mid-combat clip starts initialise last_increase_frame = -1000 so their
       quiet period is effectively infinite and this guard always passes.
  ─────────────────────────────────────────────────
  Bar disappears            → State 1  (no event)
  White confirmed (genuine) → State 3  + Record "first_hit"
  White confirmed (post-    → State 3  (no event — resume silently,
    intermission or mid-                set prev_position = white_pos)
    combat start)

State 3: Active Combat
  Bar present, tracking white marker position.
  ─────────────────────────────────────────────────
  White moves left  ≥ 3px   → Record "hit"
  White moves right ≥ 3px   → Record "heal"
  White disappears,          → If (bar_right − prev_position − gap) ≥ 10px:
    bar still present           Record "hit" (gap = last known white_pos − bar_right,
                                subtracted to exclude the structural offset between
                                marker and bar edge; bar_right must be < prev_position
                                and within 30px to be considered reliable)
  Both disappear             → State 5  (defer "final_hit")

State 4: Defeated
  Bar absent, white absent, clip has ended.
  Ignore all further frames. No further events possible.

State 5: Monitoring
  Both bar and white absent. A final_hit is pending — not yet committed.
  ─────────────────────────────────────────────────
  Bar reappears, no white   → State 2  (intermission confirmed,
                                        discard pending final_hit)
  Bar reappears WITH white  → State 3  (intermission confirmed,
                                        discard pending final_hit,
                                        set prev_position = white_pos)
  Clip ends                 → Commit deferred "final_hit" → State 4
```

---

## Rules

- ❌ Never detect the white marker before the red bar is confirmed present.
- ❌ Never record an event when the bar appears.
- ❌ Never record an event when the white marker appears after an intermission.
- ❌ Never commit `final_hit` immediately when bar+white disappear — it may be an intermission.
- ❌ Never process events after entering State 4.

---

## Timeline Examples

### Standard fight (bar appears, first hit, combat, defeat)

```
Frames 0–459:   Pre-boss gameplay                   State 1
Frame 460:      Red bar appears, no white            State 1 → 2  (no event)
Frame 462:      White marker appears at x=900        State 2 → 3  first_hit
Frame 470:      White moves 900 → 820                State 3       hit (-80px)
Frame 480:      White moves 820 → 900                State 3       heal (+80px)
Frame 500:      Bar and white disappear              State 3 → 5  (deferred final_hit)
Clip ends:      Bar never returned                   State 5 → 4  final_hit committed
```

### Mid-combat clip (clip starts after first hit already occurred)

```
Frame 0:        Bar present, white at x=830          State 1 → 2  (mid_combat_start=True)
                                                      State 2 → 3  (no event, prev=830)
Frame 12:       White moves 830 → 772                State 3       hit (-58px)
Clip ends.
```

### Phase transition (intermission between Phase 1 and Phase 2)

```
Frames 0–15:    Phase 1 mid-combat, white=598        State 1 → 3  (no event, prev=598)
Frame 16:       White moves 598 → 518                State 3       hit (-80px)
Frame 18:       White disappears, bar still present  State 3       (bar-drop check: <10px, no event)
Frame 21:       Bar disappears                       State 3 → 5  (deferred final_hit)
Frames 21–91:   Nothing visible                      State 5       (waiting)
Frame 92:       Bar reappears, no white              State 5 → 2  (intermission confirmed,
                                                                    final_hit discarded)
Frame 94:       White reappears at x=518             State 2 → 3  (post-intermission resume,
                                                                    no event, prev=518)
Frames 94–123:  Phase 2 active, white stable         State 3       (no further events)
Clip ends.      Total: 1 hit
```

---

## Output Format

One timestamp per hit event (`first_hit`, `hit`, `final_hit`), bare `MM:SS.mmm` format, one per line:

```
00:23.400
00:53.100
01:12.733
```

Heals are tracked internally but excluded from output.

