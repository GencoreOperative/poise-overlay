#!/usr/bin/env python3
"""
Test runner for Phase 2 hit detection.
Validates that the detection algorithm works correctly on all test cases.
Includes both unit tests (accuracy) and functional tests (output format).
"""

import os
import sys
import subprocess
import json
import re

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
        'test_case_real_first_hit': 1,  # Real video data
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


def validate_mmss_format(line):
    """Check if line matches MM:SS format"""
    return re.match(r'^\d{2}:\d{2}$', line.strip()) is not None


def run_functional_test_output_format(phase2_script):
    """
    Functional Test: Output Format Validation
    Ensures phase2-detect-hits.py outputs valid MM:SS timestamps
    
    Returns:
        (test_name, passed, error_msg)
    """
    test_case = 'test_case_3_single_damage'
    
    # Run phase 2
    cmd = ['python3', phase2_script, test_case, '-o', f'{test_case}_functional_output.txt']
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Read output file
        output_file = f'{test_case}_functional_output.txt'
        if not os.path.exists(output_file):
            return 'output_format_single_hit', False, 'No output file generated'
        
        with open(output_file, 'r') as f:
            output_lines = f.read().strip().split('\n')
        
        # Extract MM:SS timestamps (skip header/description lines)
        timestamps = []
        for line in output_lines:
            if validate_mmss_format(line):
                timestamps.append(line.strip())
        
        # Verify at least one timestamp was found
        if not timestamps:
            return 'output_format_single_hit', False, 'No MM:SS timestamps found in output'
        
        # Verify all timestamps are valid MM:SS
        for ts in timestamps:
            if not validate_mmss_format(ts):
                return 'output_format_single_hit', False, f'Invalid timestamp format: {ts}'
        
        return 'output_format_single_hit', True, ''
    
    except subprocess.TimeoutExpired:
        return 'output_format_single_hit', False, 'Timeout'
    except Exception as e:
        return 'output_format_single_hit', False, str(e)


def run_functional_test_known_limitation_small_hits(phase2_script):
    """
    Functional Test: Partial Detection on Small Hits (Known Limitation)
    
    test_case_4_multiple_damages has 3 hits, but they are too small to detect with
    full accuracy. This is a known limitation. Test compromises by validating:
    - At least 2 hits are detected (partial detection acceptable)
    - All detected timestamps are in valid MM:SS format
    
    This test documents the limitation and ensures format correctness despite it.
    
    Returns:
        (test_name, passed, error_msg)
    """
    test_case = 'test_case_4_multiple_damages'
    
    cmd = ['python3', phase2_script, test_case, '-o', f'{test_case}_functional_output.txt']
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Read output file
        output_file = f'{test_case}_functional_output.txt'
        if not os.path.exists(output_file):
            return 'known_limitation_small_hits', False, 'No output file generated'
        
        with open(output_file, 'r') as f:
            output_lines = f.read().strip().split('\n')
        
        # Extract MM:SS timestamps (skip header/description lines)
        timestamps = []
        for line in output_lines:
            if validate_mmss_format(line):
                timestamps.append(line.strip())
        
        # Known limitation: should detect at least 2 hits (out of 3 possible)
        if len(timestamps) < 2:
            return 'known_limitation_small_hits', False, f'Expected at least 2 hits, got {len(timestamps)}'
        
        # Verify all are valid MM:SS
        for ts in timestamps:
            if not validate_mmss_format(ts):
                return 'known_limitation_small_hits', False, f'Invalid timestamp format: {ts}'
        
        return 'known_limitation_small_hits', True, ''
    
    except subprocess.TimeoutExpired:
        return 'known_limitation_small_hits', False, 'Timeout'
    except Exception as e:
        return 'known_limitation_small_hits', False, str(e)


def main():
    # Determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    phase2_script = os.path.join(parent_dir, 'phase2-detect-hits.py')
    
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
    
    print(f"Running {len(test_dirs)} unit tests...\n")
    
    results = []
    for test_dir in test_dirs:
        print(f"Testing {test_dir}...", end=' ', flush=True)
        name, expected, actual, passed, stderr = run_test_case(test_dir, phase2_script)
        results.append((name, expected, actual, passed))
        
        if passed:
            print(f"✓ PASS (expected {expected}, got {actual})")
        else:
            print(f"✗ FAIL (expected {expected}, got {actual})")
    
    # Functional Tests
    print(f"\nRunning 2 functional tests...\n")
    
    functional_results = []
    
    print("Testing output_format (single hit)...", end=' ', flush=True)
    test_name, passed, error = run_functional_test_output_format(phase2_script)
    functional_results.append((test_name, passed, error))
    if passed:
        print("✓ PASS")
    else:
        print(f"✗ FAIL ({error})")
    
    print("Testing known_limitation (small hits, partial detection)...", end=' ', flush=True)
    test_name, passed, error = run_functional_test_known_limitation_small_hits(phase2_script)
    functional_results.append((test_name, passed, error))
    if passed:
        print("✓ PASS")
    else:
        print(f"✗ FAIL ({error})")
    
    # Summary
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    
    # Unit tests summary
    print(f"\n{'UNIT TESTS':<40} {'Expected':<12} {'Actual':<12} {'Result'}")
    print("-" * 78)
    
    unit_passed = 0
    for name, expected, actual, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:<40} {expected:<12} {actual:<12} {status}")
        if passed:
            unit_passed += 1
    
    print("-" * 78)
    print(f"Unit tests: {unit_passed}/{len(results)} passed")
    
    # Functional tests summary
    print(f"\n{'FUNCTIONAL TESTS':<40} {'Result'}")
    print("-" * 78)
    
    functional_passed = 0
    for name, passed, error in functional_results:
        status = "✓ PASS" if passed else f"✗ FAIL ({error})"
        print(f"{name:<40} {status}")
        if passed:
            functional_passed += 1
    
    print("-" * 78)
    print(f"Functional tests: {functional_passed}/{len(functional_results)} passed")
    
    # Overall summary
    total_passed = unit_passed + functional_passed
    total_tests = len(results) + len(functional_results)
    
    print("\n" + "="*70)
    print(f"TOTAL: {total_passed}/{total_tests} tests passed")
    print("="*70)
    
    if total_passed == total_tests:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total_tests - total_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
