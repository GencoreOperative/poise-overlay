#!/usr/bin/env python3
"""
Phase 2: Hit Detection using White Marker State Machine

This algorithm tracks the Elden Ring boss health bar white marker (the boundary
between undamaged and damaged health) across frames to detect and measure damage
events and healing.

State Machine:
  State 1 (Pre-Boss): Miscellaneous pixels, no red bar visible.
    → Transition to State 2 when red bar detected (no white marker). No event.
    → Transition to State 3 when red bar AND white marker both detected (mid-combat clip). No event.

  State 2 (Bar Visible, Not Yet Hit): Red bar present, no white marker.
    → Boss is at full health and has not been damaged yet (or bar just returned after intermission).
    → Transition to State 3 when white marker appears. Records "first_hit".

  State 3 (Active Combat): Red bar and white marker both present.
    → Track rightmost white pixel position.
    → Position moving left = damage event ("hit").
    → Position moving right = healing event ("heal").
    → Both disappear → Transition to State 5 (Monitoring). Deferred "final_hit".

  State 4 (Defeated): Boss health depleted, bar and marker gone.
    → No further events processed.

  State 5 (Monitoring): Both bar and white marker gone — awaiting outcome.
    → Bar reappears → Intermission confirmed. Discard pending final_hit. Back to State 2 or 3.
    → Clip ends with no bar → Commit deferred "final_hit". Transition to State 4.

Critical rule: White marker detection only begins after the red bar is confirmed.
Pre-boss frames may contain white pixels from game scenery/UI — these must be ignored.

Usage:
  python3 phase2-detect-hits.py <input_dir> [-o OUTPUT_FILE] [--debug]

  <input_dir>: Directory with frame_XXXXXX.png files (cropped 1000px × 7px health bars)
  -o OUTPUT_FILE: Write hit events to file (default: stdout)
  --debug: Print detailed state machine trace
"""

import os
import sys
import argparse
from PIL import Image
import numpy as np


def find_white_marker_position(frame_rgb):
    """
    Find rightmost white pixel in health bar frame (rightmost edge of white marker).
    
    Works with both full-frame video and pre-cropped health bar images.
    
    Args:
        frame_rgb: numpy array of shape (height, width, 3) with RGB values
    
    Returns:
        int: x-coordinate of rightmost white pixel (relative to crop), or None if not found
    """
    r = frame_rgb[:, :, 0].astype(np.float32)
    g = frame_rgb[:, :, 1].astype(np.float32)
    b = frame_rgb[:, :, 2].astype(np.float32)
    
    # White marker: R, G, B all bright. After a hit the marker develops a yellow
    # tint from the damage indicator animation (B drops to ~160-176). Use a lower
    # B threshold (140) while keeping R and G strict to avoid false positives.
    white_mask = (r > 180) & (g > 180) & (b > 140)
    
    # Find columns that contain white pixels
    white_cols = np.where(white_mask.any(axis=0))[0]
    
    if len(white_cols) > 0:
        return int(white_cols[-1])  # Rightmost white pixel
    return None


def find_bar_extent(frame_rgb):
    """
    Find extent of red health bar (left and right edges).
    Used to detect State 1 (full red bar) vs bar being present but damaged.
    
    Args:
        frame_rgb: numpy array of shape (height, width, 3)
    
    Returns:
        tuple: (left_x, right_x) or None if bar not found
    """
    r = frame_rgb[:, :, 0].astype(np.float32)
    g = frame_rgb[:, :, 1].astype(np.float32)
    b = frame_rgb[:, :, 2].astype(np.float32)
    
    # Red pixels: R high, G and B low (capturing both bright and dark red)
    red_mask = (r > 60) & (g < 30) & (b < 30)
    
    red_cols = np.where(red_mask.any(axis=0))[0]
    
    # Boss health bar always anchors to the left edge of the frame.
    # Pre-boss game elements (UI, scenery) that happen to contain red pixels
    # appear well into the frame. Only accept bars starting within 10px of x=0.
    if len(red_cols) > 0 and red_cols[0] <= 10:
        return (int(red_cols[0]), int(red_cols[-1]))
    return None


def analyze_health_sequence(frame_dir, max_frames=None, debug=False):
    """
    Analyze health bar frames using white marker state machine.
    
    Args:
        frame_dir: Directory containing frame_XXXXXX.png files
        max_frames: Maximum frames to process (None = all)
        debug: Print detailed trace
    
    Returns:
        list: Hit events with (frame_num, position_before, position_after, pixel_change)
    """
    # Collect frames
    frames = []
    for f in sorted(os.listdir(frame_dir)):
        if f.startswith('frame_') and f.endswith('.png'):
            frames.append(f)
            if max_frames and len(frames) >= max_frames:
                break
    
    if not frames:
        raise ValueError(f"No frames found in {frame_dir}")
    
    if debug:
        print(f"Found {len(frames)} frames")
    
    hits = []  # List of hit events
    
    # Minimum consecutive stable frames required in State 2 before accepting a FIRST_HIT.
    # The health bar appears in a single frame and does not animate in. However, the crop area
    # extends beyond the UI bar, and gameplay footage visible to the right can contain red pixels.
    # These spurious pixels inflate bar_right far beyond the actual bar boundary. When they
    # disappear, bar_right snaps back to the true value (~5 frames = ~167ms at 30fps of spikes).
    # Mid-combat clip starts don't need this — the bar has been stable since before the clip began.
    MIN_STABLE_FRAMES = 5
    MIN_STABLE_FRAMES_MID_COMBAT = 1
    # Minimum frames since the last large bar_right spike before accepting a FIRST_HIT.
    # When gameplay red pixels inflate bar_right, then vanish, bar_right "increases" sharply as
    # the spurious pixels appear, then drops back to the true value. The white marker at the end
    # of the fixed-width health bar can then appear within 30px of the true bar_right — giving a
    # false first-hit signal. This guard requires 37 spike-free frames before firing.
    # 37 was chosen because the longest observed false-positive quiet window was 36 frames.
    MIN_QUIET_FRAMES = 37

    state = 1  # State 1: Pre-Boss
    prev_position = None
    last_gap = None            # Structural gap (white_pos - bar_right) when both visible
    pending_final_hit = None   # Deferred final_hit pending intermission confirmation
    post_intermission = False  # True when returning to State 2 after a phase transition
    mid_combat_start = False   # True when clip appears to have started mid-combat (no event on first marker)
    bar_stable_count = 0       # Consecutive frames where bar right edge hasn't moved much
    prev_bar_right_s2 = None   # Bar right edge from previous frame while in State 2
    marker_in_range_count_s2 = 0  # Consecutive frames where marker is within 30px of bar right edge
    last_increase_frame = -1000   # Frame index of the last large bar_right spike from spurious gameplay pixels
    
    for idx, frame_file in enumerate(frames):
        frame_path = os.path.join(frame_dir, frame_file)
        frame_img = Image.open(frame_path).convert('RGB')
        frame_rgb = np.array(frame_img)
        
        white_pos = find_white_marker_position(frame_rgb)
        bar_extent = find_bar_extent(frame_rgb)
        
        bar_present = bar_extent is not None
        white_present = white_pos is not None
        
        # State transitions and event detection
        if state == 1:  # Pre-Boss: Waiting for red bar
            if bar_present:
                bar_right_init = bar_extent[1]
                if white_present:
                    marker_gap = white_pos - bar_right_init  # Signed: positive = beyond bar, negative = inside bar
                    if abs(marker_gap) > 30:
                        # Marker is far from bar's right edge (either deep inside or well outside) — spurious.
                        state = 2
                        bar_stable_count = 0
                        prev_bar_right_s2 = bar_right_init
                        marker_in_range_count_s2 = 0
                        if debug:
                            print(f"Frame {idx}: STATE 1→2 (BAR APPEARED, spurious marker ignored at x={white_pos}, gap={marker_gap:+d}px)")
                    else:
                        # Marker is within 30px of bar's right edge — genuine mid-combat clip start.
                        # Route through State 2 stability check; suppress the first_hit event.
                        state = 2
                        mid_combat_start = True
                        bar_stable_count = 0
                        prev_bar_right_s2 = bar_right_init
                        marker_in_range_count_s2 = 1  # Already in range on entry
                        if debug:
                            print(f"Frame {idx}: STATE 1→2 (BAR+MARKER, routing via stability check) - bar x={bar_extent[0]}–{bar_right_init}, marker x={white_pos}")
                else:
                    state = 2
                    bar_stable_count = 0
                    prev_bar_right_s2 = bar_extent[1]
                    marker_in_range_count_s2 = 0
                    if debug:
                        print(f"Frame {idx}: STATE 1→2 (BAR APPEARED) - red bar x={bar_extent[0]}–{bar_extent[1]}")
        
        elif state == 2:  # Bar visible, not yet hit: Waiting for white marker
            if not bar_present:
                # Bar vanished before any hit — back to pre-boss
                state = 1
                post_intermission = False
                mid_combat_start = False
                bar_stable_count = 0
                prev_bar_right_s2 = None
                marker_in_range_count_s2 = 0
                last_increase_frame = -1000
                if debug:
                    print(f"Frame {idx}: STATE 2→1 (BAR VANISHED, no hits)")
            else:
                # Update bar stability tracking.
                # Only reset on INCREASE: gameplay red pixels to the right of the health bar
                # inflate bar_right when they appear. When they vanish, bar_right snaps back
                # to the true bar boundary. Damage shrinks the bar — that must not reset stability.
                bar_right_s2 = bar_extent[1]
                if prev_bar_right_s2 is not None and (bar_right_s2 - prev_bar_right_s2) > 50:
                    # bar_right spiked upward — spurious gameplay pixels inflating the detection
                    bar_stable_count = 0
                    marker_in_range_count_s2 = 0
                    last_increase_frame = idx
                    if debug:
                        print(f"Frame {idx}: STATE 2 (bar still entering, right edge {prev_bar_right_s2}→{bar_right_s2}, stable_count reset)")
                else:
                    bar_stable_count += 1
                prev_bar_right_s2 = bar_right_s2

                stable_threshold = MIN_STABLE_FRAMES_MID_COMBAT if mid_combat_start else MIN_STABLE_FRAMES

                if white_present:
                    marker_gap_s2 = white_pos - bar_right_s2  # Signed gap
                    if abs(marker_gap_s2) > 30:
                        # Marker is far from bar's right edge — spurious pixel / false positive.
                        marker_in_range_count_s2 = 0
                        if debug:
                            print(f"Frame {idx}: STATE 2 (spurious marker at x={white_pos}, gap={marker_gap_s2}px, staying)")
                    elif bar_stable_count < stable_threshold:
                        # Bar not yet stable — spurious pixel spikes may still be occurring.
                        marker_in_range_count_s2 += 1
                        if debug:
                            print(f"Frame {idx}: STATE 2 (bar not yet stable, count={bar_stable_count}/{stable_threshold}, ignoring marker at x={white_pos})")
                    else:
                        marker_in_range_count_s2 += 1
                        quiet_frames = idx - last_increase_frame
                        if marker_in_range_count_s2 < 2:
                            # Require 2 consecutive in-range frames before accepting — prevents
                            # false positives where bar briefly overlaps a static UI element.
                            if debug:
                                print(f"Frame {idx}: STATE 2 (marker in range but awaiting confirmation, count={marker_in_range_count_s2})")
                        elif quiet_frames < MIN_QUIET_FRAMES:
                            # A bar_right spike occurred recently — gameplay pixels may still be
                            # causing intermittent inflation. Require MIN_QUIET_FRAMES spike-free
                            # frames before firing a first_hit.
                            if debug:
                                print(f"Frame {idx}: STATE 2 (marker confirmed but oscillation {quiet_frames}/{MIN_QUIET_FRAMES} frames ago, waiting)")
                        else:
                            state = 3
                            prev_position = white_pos
                            if 0 < bar_right_s2 < white_pos:
                                last_gap = marker_gap_s2
                            bar_stable_count = 0
                            prev_bar_right_s2 = None
                            marker_in_range_count_s2 = 0
                            if post_intermission or mid_combat_start:
                                # Resuming after intermission, or clip started mid-combat — no event
                                post_intermission = False
                                mid_combat_start = False
                                if debug:
                                    print(f"Frame {idx}: STATE 2→3 (RESUME, no event) - marker at x={white_pos}")
                            else:
                                # White marker appeared for the first time — genuine first hit
                                hits.append({
                                    'frame': idx,
                                    'type': 'first_hit',
                                    'position': white_pos,
                                    'pixel_change': None,
                                    'description': f'First hit: white marker appeared at x={white_pos}'
                                })
                                if debug:
                                    print(f"Frame {idx}: STATE 2→3 (FIRST HIT) - white marker at x={white_pos}")
                else:
                    marker_in_range_count_s2 = 0
        
        elif state == 3:  # Active Combat: Track white marker movement
            if not bar_present and not white_present:
                # Both gone — could be defeat or phase transition. Defer the event.
                state = 5
                pending_final_hit = {
                    'frame': idx,
                    'type': 'final_hit',
                    'position': None,
                    'pixel_change': None,
                    'description': f'Final hit: white marker and red bar disappeared (boss defeated)'
                }
                if debug:
                    print(f"Frame {idx}: STATE 3→5 (MONITORING) - bar and marker gone, awaiting outcome")
            elif white_present:
                if prev_position is not None:
                    change = prev_position - white_pos  # Positive = moved left = damage
                    if abs(change) >= 3:
                        if change > 0:
                            hits.append({
                                'frame': idx,
                                'type': 'hit',
                                'position_before': prev_position,
                                'position_after': white_pos,
                                'pixel_change': change,
                                'description': f'Hit: white marker moved left by {change}px (x={prev_position}→{white_pos})'
                            })
                            if debug:
                                print(f"Frame {idx}: HIT -{change}px (x={prev_position}→{white_pos})")
                        else:
                            hits.append({
                                'frame': idx,
                                'type': 'heal',
                                'position_before': prev_position,
                                'position_after': white_pos,
                                'pixel_change': change,
                                'description': f'Healing: white marker moved right by {abs(change)}px (x={prev_position}→{white_pos})'
                            })
                            if debug:
                                print(f"Frame {idx}: HEAL +{abs(change)}px (x={prev_position}→{white_pos})")
                prev_position = white_pos
                if bar_extent:
                    bar_right_cur = bar_extent[1]
                    if 0 < bar_right_cur < white_pos and (white_pos - bar_right_cur) < 30:
                        last_gap = white_pos - bar_right_cur
            elif bar_present and prev_position is not None:
                # White marker vanished but bar still present.
                # The raw drop (prev_position - bar_right) includes the structural gap between
                # the white marker and the bar's right edge. Subtract last_gap to get the
                # actual bar movement; only record a hit if the bar genuinely moved.
                bar_right = bar_extent[1]
                raw_drop = prev_position - bar_right
                gap = last_gap if last_gap is not None else 0
                adjusted_drop = raw_drop - gap
                if adjusted_drop >= 10:
                    hits.append({
                        'frame': idx,
                        'type': 'hit',
                        'position_before': prev_position,
                        'position_after': bar_right,
                        'pixel_change': adjusted_drop,
                        'description': f'Hit: bar dropped by {adjusted_drop}px while marker hidden (bar right x={bar_right})'
                    })
                    if debug:
                        print(f"Frame {idx}: HIT (marker hidden) -{adjusted_drop}px (bar right={bar_right}, raw={raw_drop}, gap={gap})")
                    prev_position = bar_right
        
        elif state == 4:  # Defeated: No further events
            if debug:
                print(f"Frame {idx}: STATE 4 (DEFEATED) - ignoring")
        
        elif state == 5:  # Monitoring: Both bar and white gone — awaiting outcome
            if bar_present:
                # Bar returned — this was a phase transition (intermission), not a defeat.
                # Discard the pending final_hit and resume tracking.
                pending_final_hit = None
                if white_present:
                    # Bar and white both back — resume active combat silently
                    state = 3
                    prev_position = white_pos
                    bar_right_s5 = bar_extent[1]
                    if 0 < bar_right_s5 < white_pos and (white_pos - bar_right_s5) < 30:
                        last_gap = white_pos - bar_right_s5
                    if debug:
                        print(f"Frame {idx}: STATE 5→3 (INTERMISSION CONFIRMED) - bar and marker back, prev={white_pos}")
                else:
                    # Bar returned, white not yet present — wait for it
                    state = 2
                    post_intermission = True
                    prev_position = None
                    bar_stable_count = 0
                    prev_bar_right_s2 = bar_extent[1]
                    if debug:
                        print(f"Frame {idx}: STATE 5→2 (INTERMISSION CONFIRMED) - bar back, waiting for marker")
        
    # If clip ended while monitoring (both bar and white gone and never returned),
    # commit the deferred final_hit — the boss was genuinely defeated.
    if state == 5 and pending_final_hit is not None:
        hits.append(pending_final_hit)
        if debug:
            print(f"Clip ended in STATE 5 — committing deferred final_hit at frame {pending_final_hit['frame']}")
    
    return hits


def frame_to_timestamp(frame_num, fps=30):
    """Convert frame number to MM:SS.mmm format at given frame rate."""
    total_ms = round(frame_num * 1000 / fps)
    minutes = total_ms // 60000
    seconds = (total_ms % 60000) // 1000
    millis = total_ms % 1000
    return f"{minutes:02d}:{seconds:02d}.{millis:03d}"


def format_output(hits):
    """Format hits as MM:SS.mmm timestamps, one per line. Only damage events, not heals."""
    damage_events = [h for h in hits if h['type'] in ('hit', 'first_hit', 'final_hit')]
    return '\n'.join(frame_to_timestamp(e['frame']) for e in damage_events)


def main():
    parser = argparse.ArgumentParser(
        description='Detect boss health bar hits using white marker state machine'
    )
    parser.add_argument('input_dir', help='Directory with frame PNG files')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('--debug', action='store_true', help='Print debug trace')
    parser.add_argument('--max-frames', type=int, help='Process only first N frames')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.input_dir):
        print(f"Error: {args.input_dir} is not a directory", file=sys.stderr)
        sys.exit(1)
    
    try:
        hits = analyze_health_sequence(
            args.input_dir,
            max_frames=args.max_frames,
            debug=args.debug
        )
    except Exception as e:
        print(f"Error analyzing frames: {e}", file=sys.stderr)
        sys.exit(1)
    
    output = format_output(hits)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
    else:
        print(output)


if __name__ == '__main__':
    main()
