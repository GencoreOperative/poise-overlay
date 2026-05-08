#!/usr/bin/env python3
"""
Synthetic Test Case Generator for Phase 2 Hit Detection

Generates realistic but controlled health bar frame sequences for comprehensive testing.
Each test case is created programmatically to test specific scenarios.

Generated frames are 7px tall × 999px wide PNG images with:
- Background: Dark brownish color (mimics gameplay beneath health bar)
- Red health bar: Pure red (R=255, G=0, B=0) on left side
- White marker: Pure white (R=255, G=255, B=255) at health boundary (when health < max)
"""

import os
from PIL import Image
import numpy as np


def create_health_bar_frame(max_width=999, current_width=None, frame_height=7):
    """
    Create a single health bar frame.
    
    Args:
        max_width: Maximum health bar width (full health)
        current_width: Current health bar width (if None, uses max_width = full health)
        frame_height: Height of the frame in pixels
    
    Returns:
        PIL.Image: RGB image of the health bar frame
    """
    if current_width is None:
        current_width = max_width
    
    # Create frame array
    frame = np.zeros((frame_height, max_width, 3), dtype=np.uint8)
    
    # Background: dark brownish color (gameplay showing through)
    frame[:, :] = [44, 25, 11]  # BGR format in some places, but PIL uses RGB
    
    # Red health bar on the left (current health)
    if current_width > 0:
        frame[:, :current_width] = [255, 0, 0]  # Pure red
    
    # White marker at the boundary (unless at full health)
    if 0 < current_width < max_width:
        # Place white marker at the boundary
        marker_x = current_width
        if marker_x < max_width:
            frame[:, marker_x] = [255, 255, 255]  # Pure white
    
    return Image.fromarray(frame, 'RGB')


def generate_test_case_1_pre_boss(output_dir):
    """
    Test Case 1: Pre-Boss UI Phase
    
    Shows the cropped region BEFORE the boss bar appears.
    Should show only background, no red bar, no white marker.
    Expected: 0 damage events
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 50 frames of just background
    for frame_num in range(50):
        frame = create_health_bar_frame(current_width=0)  # No health bar
        frame_path = os.path.join(output_dir, f'frame_{frame_num+1:06d}.png')
        frame.save(frame_path, 'PNG', optimize=True)


def generate_test_case_2_entrance_animation(output_dir):
    """
    Test Case 2: Entrance Animation / Bar Appears
    
    Shows transition FROM no boss bar TO full health bar appearing.
    Frame 0: No bar
    Frame 1: Bar appears at full width (999px)
    Expected: 0 damage events (bar appearance is not a hit, white marker appears at transition)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Frame 1: No bar
    frame = create_health_bar_frame(current_width=0)
    frame.save(os.path.join(output_dir, 'frame_000001.png'), 'PNG', optimize=True)
    
    # Frames 2-50: Full health bar appears
    for frame_num in range(1, 50):
        frame = create_health_bar_frame(current_width=999)  # Full health, no white marker
        frame_path = os.path.join(output_dir, f'frame_{frame_num+1:06d}.png')
        frame.save(frame_path, 'PNG', optimize=True)


def generate_test_case_3_single_damage(output_dir):
    """
    Test Case 3: Single Damage Event
    
    Boss takes a single hit, reducing health from full to ~950px.
    Expected: 1 damage event (white marker appears at frame with damage)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Frames 1-10: Full health (999px)
    for i in range(10):
        frame = create_health_bar_frame(current_width=999)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)
    
    # Frames 11-20: Damage occurs, health drops to 950px
    for i in range(10, 20):
        frame = create_health_bar_frame(current_width=950)  # White marker at x=950
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)


def generate_test_case_4_multiple_damages(output_dir):
    """
    Test Case 4: Multiple Damage Events (Already from real video - keep as-is)
    
    Already generated from real video test.mp4, skip regeneration.
    """
    pass  # Already correct from real video extraction


def generate_test_case_5_boss_healing(output_dir):
    """
    Test Case 5: Boss Healing
    
    Boss takes damage, then healing occurs (health grows back).
    Frames 1-10: Full health (999px)
    Frames 11-20: Damage, health drops to 800px (first hit detected)
    Frames 21-30: Healing, health grows back to 900px (healing event, not counted as damage)
    Expected: 1 damage event (only the initial hit)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Frames 1-10: Full health
    for i in range(10):
        frame = create_health_bar_frame(current_width=999)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)
    
    # Frames 11-20: Damage to 800px
    for i in range(10, 20):
        frame = create_health_bar_frame(current_width=800)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)
    
    # Frames 21-30: Healing back to 900px
    for i in range(20, 30):
        frame = create_health_bar_frame(current_width=900)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)


def generate_test_case_6_death_animation(output_dir):
    """
    Test Case 6: Boss Death Animation
    
    Boss health depletes to zero (final hit).
    Frames 1-5: Health at 100px
    Frames 6-10: Health drops to 50px
    Frames 11-15: Health drops to 0px (white marker disappears = final hit)
    Frames 16-20: Bar gone (defeated state)
    Expected: Multiple events as health decreases, final when bar empties
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Frames 1-10: Small health (100px)
    for i in range(10):
        frame = create_health_bar_frame(current_width=100)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)
    
    # Frames 11-20: Smaller health (50px)
    for i in range(10, 20):
        frame = create_health_bar_frame(current_width=50)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)
    
    # Frames 21-25: Health to 0px (final hit)
    for i in range(20, 25):
        frame = create_health_bar_frame(current_width=0)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)


def generate_test_case_7_damage_threshold(output_dir):
    """
    Test Case 7: Damage Threshold Test
    
    Series of small damage events to test threshold detection.
    Frames 1-5: Full health (999px)
    Frames 6-10: Small damage drop (999→996px = 3px damage, threshold)
    Frames 11-15: Stable (996px)
    Frames 16-20: Larger damage (996→950px = 46px damage)
    Expected: 2 damage events (both above 3px threshold)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Frames 1-5: Full health
    for i in range(5):
        frame = create_health_bar_frame(current_width=999)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)
    
    # Frames 6-10: Small damage (3px drop)
    for i in range(5, 10):
        frame = create_health_bar_frame(current_width=996)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)
    
    # Frames 11-15: Stable
    for i in range(10, 15):
        frame = create_health_bar_frame(current_width=996)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)
    
    # Frames 16-20: Large damage (46px drop)
    for i in range(15, 20):
        frame = create_health_bar_frame(current_width=950)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)


def generate_test_case_8_complex_scenario(output_dir):
    """
    Test Case 8: Complex Scenario
    
    Multiple rapid damages with varying magnitudes.
    Expected: Multiple damage events
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Frames 1-5: Full health (999px)
    for i in range(5):
        frame = create_health_bar_frame(current_width=999)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)
    
    # Frames 6-10: Damage to 850px
    for i in range(5, 10):
        frame = create_health_bar_frame(current_width=850)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)
    
    # Frames 11-15: Damage to 700px
    for i in range(10, 15):
        frame = create_health_bar_frame(current_width=700)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)
    
    # Frames 16-20: Damage to 500px
    for i in range(15, 20):
        frame = create_health_bar_frame(current_width=500)
        frame.save(os.path.join(output_dir, f'frame_{i+1:06d}.png'), 'PNG', optimize=True)


def main():
    """Generate all synthetic test cases."""
    test_dir = 'phase_2_test'
    
    test_cases = [
        ('test_case_1_pre_boss', generate_test_case_1_pre_boss),
        ('test_case_2_entrance_animation', generate_test_case_2_entrance_animation),
        ('test_case_3_single_damage', generate_test_case_3_single_damage),
        ('test_case_5_boss_healing', generate_test_case_5_boss_healing),
        ('test_case_6_death_animation', generate_test_case_6_death_animation),
        ('test_case_7_damage_threshold', generate_test_case_7_damage_threshold),
        ('test_case_8_complex_scenario', generate_test_case_8_complex_scenario),
    ]
    
    for test_name, generator_func in test_cases:
        test_path = os.path.join(test_dir, test_name)
        print(f"Generating {test_name}...", end=' ', flush=True)
        
        # Remove old frames
        if os.path.exists(test_path):
            for f in os.listdir(test_path):
                if f.endswith('.png'):
                    os.remove(os.path.join(test_path, f))
        
        # Generate new frames
        generator_func(test_path)
        
        frame_count = len([f for f in os.listdir(test_path) if f.endswith('.png')])
        print(f"✓ {frame_count} frames")


if __name__ == '__main__':
    main()
