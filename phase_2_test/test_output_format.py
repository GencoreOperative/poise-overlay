#!/usr/bin/env python3
"""
Functional Test: Phase 2 Output Format Validation

Ensures that phase2-detect-hits.py outputs in the correct
format: one MM:SS timestamp per line, one for each hit detected.
"""

import subprocess
import re
import sys

def validate_mmss_format(line):
    """Check if line matches MM:SS format"""
    return re.match(r'^\d{2}:\d{2}$', line.strip()) is not None

def test_output_format():
    """Test that output is valid MM:SS format, one per hit"""
    
    # Test on a simple case: test_case_3_single_damage has 1 hit
    test_case = 'test_case_3_single_damage'
    
    print(f"Testing output format on {test_case}...")
    
    # Run phase 2
    cmd = ['python3', '../phase2-detect-hits.py', test_case]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    # Extract MM:SS timestamps (everything that looks like MM:SS)
    output_lines = result.stdout.strip().split('\n')
    
    timestamps = []
    for line in output_lines:
        if validate_mmss_format(line):
            timestamps.append(line.strip())
    
    print(f"\nDetected {len(timestamps)} timestamps:")
    for ts in timestamps:
        print(f"  {ts}")
    
    # Find expected count from "Damage Events:" line
    expected_count = None
    for line in output_lines:
        if 'Damage Events:' in line:
            expected_count = int(line.split()[-1])
            break
    
    if expected_count is None:
        print("❌ FAIL: Could not find 'Damage Events:' line")
        return False
    
    print(f"\nExpected {expected_count} hits, found {len(timestamps)} timestamps")
    
    # Verify format and count
    if len(timestamps) != expected_count:
        print(f"❌ FAIL: Timestamp count ({len(timestamps)}) != expected ({expected_count})")
        return False
    
    # Verify all are valid MM:SS
    for ts in timestamps:
        if not validate_mmss_format(ts):
            print(f"❌ FAIL: Invalid format '{ts}' (expected MM:SS)")
            return False
    
    print("✓ PASS: All timestamps in MM:SS format, one per hit")
    return True

def test_multiple_hits():
    """Test on case with multiple hits"""
    
    test_case = 'test_case_4_multiple_damages'
    
    print(f"\nTesting on {test_case}...")
    
    cmd = ['python3', '../phase2-detect-hits.py', test_case]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    output_lines = result.stdout.strip().split('\n')
    
    timestamps = []
    for line in output_lines:
        if validate_mmss_format(line):
            timestamps.append(line.strip())
    
    expected_count = None
    for line in output_lines:
        if 'Damage Events:' in line:
            expected_count = int(line.split()[-1])
            break
    
    print(f"Detected {len(timestamps)} timestamps (expected {expected_count})")
    
    if len(timestamps) != expected_count:
        print(f"❌ FAIL: Count mismatch")
        return False
    
    print("✓ PASS: Format test on multiple hits")
    return True

if __name__ == '__main__':
    print("=" * 70)
    print("PHASE 2 OUTPUT FORMAT VALIDATION TEST")
    print("=" * 70)
    
    test1 = test_output_format()
    test2 = test_multiple_hits()
    
    print("\n" + "=" * 70)
    if test1 and test2:
        print("✓ ALL FORMAT TESTS PASSED")
        print("=" * 70)
        sys.exit(0)
    else:
        print("❌ FORMAT TESTS FAILED")
        print("=" * 70)
        sys.exit(1)
