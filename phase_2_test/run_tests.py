#!/usr/bin/env python3
"""
Test runner for Phase 2 hit detection.
Validates that the detection algorithm works correctly on all test cases.
"""

import os
import sys
import subprocess
import json

def run_test_case(test_dir, phase2_script):
    """
    Run phase2 detection on a test case and return results.
    
    Returns:
        (test_name, expected_events, actual_events, passed)
    """
    test_name = os.path.basename(test_dir)
    
    # Parse expected events from test case name
    # Expectations based on v3 analysis of synthetic and real test cases
    expected_map = {
        # Synthetic test cases (programmatically generated)
        'test_case_1_pre_boss': 0,  # Pre-boss UI, no bar
        'test_case_2_entrance_animation': 0,  # Bar appears, first white marker = no hit counted yet
        'test_case_3_single_damage': 1,  # Single damage event
        'test_case_5_boss_healing': 1,  # First damage only (healing not counted)
        'test_case_6_death_animation': 3,  # Multiple damage events as health depletes
        'test_case_7_damage_threshold': 2,  # Two separate damage events
        'test_case_8_complex_scenario': 3,  # Three rapid damages
        # Real test cases (from actual videos)
        'test_case_4_multiple_damages': 3,  # Real video data
        'test_case_real_boss_health_bar_appears_004': 3,  # Real video data
        'test_case_real_false_negative_01_24_006': 3,  # Real video data
        'test_case_real_false_positive_01_03_005': 1,  # Real video data
        'test_case_real_false_positive_02_15_02_17_007': 1,  # Real video data
        'test_case_real_hit_001': 1,  # Real video data
        'test_case_real_hit_002': 2,  # Real video data
        'test_case_real_hit_003': 2,  # Real video data
    }
    
    expected_events = expected_map.get(test_name, -1)
    
    # Run phase2 detection
    output_file = f"{test_name}_output.txt"
    cmd = [
        'python3',
        phase2_script,
        test_dir,
        '-o',
        output_file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Parse event count from output file (v3 format: "Damage Events: N" on first line)
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                first_line = f.readline().strip()
                # Parse "Damage Events: N"
                if first_line.startswith('Damage Events:'):
                    actual_events = int(first_line.split(':')[1].strip())
                else:
                    actual_events = -1
        else:
            actual_events = -1
        
        passed = (actual_events == expected_events)
        
        return test_name, expected_events, actual_events, passed, result.stderr
    
    except subprocess.TimeoutExpired:
        return test_name, expected_events, -1, False, "TIMEOUT"
    except Exception as e:
        return test_name, expected_events, -1, False, str(e)


def main():
    # Determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    phase2_script = os.path.join(parent_dir, 'phase2-detect-hits-v3-white-marker.py')
    
    if not os.path.exists(phase2_script):
        print(f"Error: Cannot find {phase2_script}")
        sys.exit(1)
    
    os.chdir(script_dir)
    
    print("="*70)
    print("PHASE 2 TEST SUITE")
    print("="*70)
    print()
    
    # Find all test case directories (synthetic and real)
    test_dirs = sorted([
        d for d in os.listdir('.')
        if os.path.isdir(d) and (d.startswith('test_case_') or d.startswith('test_case_real_'))
    ])
    
    if not test_dirs:
        print("No test cases found!")
        sys.exit(1)
    
    print(f"Running {len(test_dirs)} test cases...\n")
    
    results = []
    for test_dir in test_dirs:
        print(f"Testing {test_dir}...", end=' ', flush=True)
        name, expected, actual, passed, stderr = run_test_case(test_dir, phase2_script)
        results.append((name, expected, actual, passed))
        
        if passed:
            print(f"✓ PASS (expected {expected}, got {actual})")
        else:
            print(f"✗ FAIL (expected {expected}, got {actual})")
    
    # Summary
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    print(f"\n{'Test Case':<40} {'Expected':<12} {'Actual':<12} {'Result'}")
    print("-" * 78)
    
    passed_count = 0
    for name, expected, actual, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:<40} {expected:<12} {actual:<12} {status}")
        if passed:
            passed_count += 1
    
    print("-" * 78)
    print(f"\nTotal: {passed_count}/{len(results)} tests passed")
    
    if passed_count == len(results):
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {len(results) - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
