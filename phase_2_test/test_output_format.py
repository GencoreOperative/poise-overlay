#!/usr/bin/env python3
"""
Functional Test: Phase 2 Output Format Validation

Ensures that phase2-detect-hits.py outputs in the correct
format: one MM:SS.mmm timestamp per line, one for each hit detected.
"""

import subprocess
import re
import sys

def validate_mmss_format(line):
    """Check if line matches MM:SS.mmm format"""
    return re.match(r'^\d{2}:\d{2}\.\d{3}$', line.strip()) is not None

def run_phase2(test_case):
    """Run phase2 on a test case directory and return list of timestamp lines."""
    cmd = ['python3', '../phase2-detect-hits.py', test_case]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    output_lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
    return [line.strip() for line in output_lines]

def test_output_format():
    """Test that output is valid MM:SS.mmm format on a single-hit case."""
    test_case = 'test_case_3_single_damage'
    expected_count = 1
    
    print(f"Testing output format on {test_case}...")
    
    timestamps = run_phase2(test_case)
    
    print(f"\nDetected {len(timestamps)} timestamps:")
    for ts in timestamps:
        print(f"  {ts}")
    
    print(f"\nExpected {expected_count} hits, found {len(timestamps)} timestamps")
    
    if len(timestamps) != expected_count:
        print(f"❌ FAIL: Timestamp count ({len(timestamps)}) != expected ({expected_count})")
        return False
    
    for ts in timestamps:
        if not validate_mmss_format(ts):
            print(f"❌ FAIL: Invalid format '{ts}' (expected MM:SS.mmm)")
            return False
    
    print("✓ PASS: All timestamps in MM:SS.mmm format, one per hit")
    return True

def test_multiple_hits():
    """Test on case with multiple hits"""
    test_case = 'test_case_4_multiple_damages'
    expected_count = 4
    
    print(f"\nTesting on {test_case}...")
    
    timestamps = run_phase2(test_case)
    
    print(f"Detected {len(timestamps)} timestamps (expected {expected_count})")
    
    if len(timestamps) != expected_count:
        print(f"❌ FAIL: Count mismatch (got {len(timestamps)}, expected {expected_count})")
        return False
    
    for ts in timestamps:
        if not validate_mmss_format(ts):
            print(f"❌ FAIL: Invalid format '{ts}' (expected MM:SS.mmm)")
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
