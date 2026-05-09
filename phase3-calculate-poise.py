#!/usr/bin/env python3

"""
Phase 3: Calculate boss poise level for each millisecond.

Given:
- Annotated hit data (timestamps and poise damage per hit)
- Boss total poise
- Boss poise regen rate and timer
- Optional stagger window (how long poise stays at 0 before resetting)

Calculate the poise level at every millisecond of the video.

Poise mechanics:
1. When hit is detected, poise decreases by the hit's damage amount
2. After a hit, there's a delay (regen_timer) before poise starts recovering
3. Poise recovers at regen_rate per second
4. Multiple hits reset the regen timer
5. If poise reaches 0, the boss is staggered:
   - Poise stays at 0 for stagger_window seconds
   - Hits during this window are ignored (boss is in stun animation)
   - After the window, poise resets to max and the cycle restarts
"""

import sys
import argparse
from pathlib import Path


def parse_annotated_hits(hits_file):
    """Parse annotated hits file with format: MM:SS,poise_damage"""
    hits = []
    with open(hits_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(',')
            if len(parts) != 2:
                raise ValueError(f"Invalid line format: {line} (expected MM:SS,damage)")
            
            timestamp = parts[0].strip()
            try:
                poise_damage = float(parts[1].strip())
            except ValueError:
                raise ValueError(f"Invalid poise damage value: {parts[1]}")
            
            # Convert MM:SS to milliseconds
            mm, ss = map(int, timestamp.split(':'))
            ms = mm * 60 * 1000 + ss * 1000
            
            hits.append((ms, poise_damage))
    
    return hits


def calculate_poise_timeline(hits, boss_poise, regen_timer_sec, regen_rate, stagger_window_sec=0.0):
    """
    Calculate poise level for each millisecond of the video.
    
    Args:
        hits: List of (timestamp_ms, poise_damage) tuples
        boss_poise: Maximum poise value
        regen_timer_sec: Time in seconds before regen starts after a hit
        regen_rate: Poise per second regeneration rate
        stagger_window_sec: Seconds poise stays at 0 after a stagger before resetting.
                            Hits during this window are ignored. 0 = disabled.
    
    Returns:
        List of (ms, poise_level) tuples for every millisecond
    """
    regen_timer_ms = int(regen_timer_sec * 1000)
    regen_rate_per_ms = regen_rate / 1000.0
    stagger_window_ms = int(stagger_window_sec * 1000)
    
    if not hits:
        return [(0, boss_poise)]
    
    max_time = max(ts for ts, _ in hits) + 10000  # Add 10 seconds buffer
    
    poise = boss_poise
    last_hit_ms = -float('inf')
    poise_at_last_hit = boss_poise
    hit_index = 0
    stagger_end_ms = None  # Set when poise hits 0; clears when stagger window expires
    
    timeline = []
    
    for ms in range(0, max_time + 1):
        # --- Stagger window ---
        if stagger_end_ms is not None:
            if ms < stagger_end_ms:
                # Inside stagger: ignore any hit at this ms, show poise at 0
                if hit_index < len(hits) and hits[hit_index][0] == ms:
                    hit_index += 1
                timeline.append((ms, 0.0))
                continue
            else:
                # Stagger window just expired: reset poise to full
                poise = boss_poise
                poise_at_last_hit = boss_poise
                last_hit_ms = -float('inf')
                stagger_end_ms = None
                # Fall through — process any hit that lands exactly at this ms
        
        # --- Apply hit at this ms ---
        if hit_index < len(hits) and hits[hit_index][0] == ms:
            hit_time, damage = hits[hit_index]
            poise = max(0.0, poise - damage)
            poise_at_last_hit = poise
            last_hit_ms = ms
            hit_index += 1
            
            # Check for stagger
            if poise <= 0.0 and stagger_window_ms > 0:
                stagger_end_ms = ms + stagger_window_ms
                timeline.append((ms, 0.0))
                continue
        
        # --- Regen ---
        time_since_hit_ms = ms - last_hit_ms
        if time_since_hit_ms >= regen_timer_ms:
            regen_duration_ms = time_since_hit_ms - regen_timer_ms
            regen_amount = regen_duration_ms * regen_rate_per_ms
            poise = min(boss_poise, poise_at_last_hit + regen_amount)
        
        timeline.append((ms, poise))
    
    return timeline


def write_poise_output(timeline, output_file):
    """Write poise timeline to output file."""
    with open(output_file, 'w') as f:
        for ms, poise in timeline:
            f.write(f"{ms} {poise:.6f}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Phase 3: Calculate boss poise level for each millisecond',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
EXAMPLES:
  # Calculate poise with default regeneration parameters
  %(prog)s test.txt -o poise_timeline.txt --boss-poise 47 --regen-timer 3.85 --regen-rate 13
  
  # Different boss settings
  %(prog)s hits_annotated.txt -o output.txt --boss-poise 120 --regen-timer 2.5 --regen-rate 20
        '''
    )
    
    parser.add_argument('hits_file', help='Annotated hits file with format: MM:SS,poise_damage')
    parser.add_argument('-o', '--output', required=True, help='Output file for poise timeline')
    parser.add_argument('--boss-poise', type=float, required=True, help='Boss total poise value')
    parser.add_argument('--regen-timer', type=float, required=True,
                       help='Seconds to wait before poise regeneration starts (default: 3.85)')
    parser.add_argument('--regen-rate', type=float, required=True,
                       help='Poise per second regeneration rate (default: 13)')
    parser.add_argument('--stagger-window', type=float, default=6.0,
                       help='Seconds poise stays at 0 after stagger before resetting to max. '
                            'Hits during this window are ignored. 0 = disabled (default: 6.0)')
    
    args = parser.parse_args()
    
    try:
        # Parse annotated hits
        print(f"Reading annotated hits from: {args.hits_file}", file=sys.stderr)
        hits = parse_annotated_hits(args.hits_file)
        
        if not hits:
            print(f"✗ No hits found in {args.hits_file}", file=sys.stderr)
            sys.exit(1)
        
        print(f"✓ Parsed {len(hits)} hits", file=sys.stderr)
        for ms, damage in hits:
            mm = ms // 60000
            ss = (ms % 60000) // 1000
            print(f"  {mm:02d}:{ss:02d} - {damage:.1f} poise damage", file=sys.stderr)
        
        # Calculate poise timeline
        print(f"\nCalculating poise timeline...", file=sys.stderr)
        print(f"  Boss poise: {args.boss_poise}", file=sys.stderr)
        print(f"  Regen timer: {args.regen_timer}s", file=sys.stderr)
        print(f"  Regen rate: {args.regen_rate} poise/sec", file=sys.stderr)
        if args.stagger_window > 0:
            print(f"  Stagger window: {args.stagger_window}s (hits ignored, poise=0 during window)", file=sys.stderr)
        
        timeline = calculate_poise_timeline(hits, args.boss_poise, args.regen_timer, args.regen_rate, args.stagger_window)
        
        # Write output
        write_poise_output(timeline, args.output)
        
        print(f"\n✓ Wrote poise timeline to {args.output}", file=sys.stderr)
        print(f"  Duration: {len(timeline)} milliseconds", file=sys.stderr)
        
        # Show sample output
        print(f"\nSample output (first 10 lines):", file=sys.stderr)
        with open(args.output, 'r') as f:
            for i, line in enumerate(f):
                if i >= 10:
                    break
                print(f"  {line.rstrip()}", file=sys.stderr)
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
