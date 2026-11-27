#!/usr/bin/env python3
"""Comprehensive test suite for Aedifico --dry-run implementation."""

import subprocess
import sys
import os
from pathlib import Path

# Project path
AEDIFICO_PATH = Path("/home/stefan/Projects/Aedifico")

def run_cmd(cmd, env=None):
    """Run command and return result."""
    env = {**os.environ, **env} if env else os.environ
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=AEDIFICO_PATH,
        capture_output=True,
        text=True,
        env=env
    )
    return result


def test_dry_run():
    """Test 1: Verify --dry-run prints summary without writing files."""
    print("=" * 70)
    print("TEST 1: Dry-run mode prints summary without writing files")
    print("=" * 70)
    
    result = run_cmd("python -m aedifico weekly --dry-run")
    
    # Check exit code
    assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"
    print(f"✓ Exit code: {result.returncode}")
    
    # Check output contains expected sections
    stdout = result.stdout
    
    required_sections = [
        "Aedifico Weekly Reflection Report",
        "Polygraph Test Results",
        "Task Completion Metrics",
        "Communication Analysis"
    ]
    
    for section in required_sections:
        assert section in stdout, f"Missing section: {section}"
        print(f"✓ Output contains: {section}")
    
    # Check that no report files were written
    import os
    workspace = AEDIFICO_PATH / "scratch_reports"
    if workspace.exists():
        files = list(workspace.glob("*"))
        assert len(files) == 0, f"Found unexpected files in scratch_reports: {files}"
        print(f"✓ No report files written to {workspace}")
    
    print("✓ TEST 1 PASSED\n")


def test_normal_mode():
    """Test 2: Verify normal mode (--dry-run omitted) works identically."""
    print("=" * 70)
    print("TEST 2: Normal mode works without --dry-run flag")
    print("=" * 70)
    
    # Test without --dry-run
    result_normal = run_cmd("python -m aedifico weekly")
    
    # Verify normal mode succeeds and produces report content
    assert result_normal.returncode == 0, f"Normal mode failed: {result_normal.stderr}"
    
    normal_output = result_normal.stdout.strip()
    
    # Check all required sections are present
    required_sections = [
        "Aedifico Weekly Reflection Report",
        "Polygraph Test Results",
        "Task Completion Metrics", 
        "Communication Analysis"
    ]
    
    for section in required_sections:
        assert section in normal_output, f"Missing section: {section}"
    
    print("✓ Normal mode produces complete report")
    
    # Verify no dry-run message appears
    assert "Dry-run mode" not in normal_output, \
        "Normal mode should not mention dry-run mode"
    print("✓ Output doesn't mention dry-run (as expected)")
    
    print("✓ TEST 2 PASSED\n")


def test_error_handling():
    """Test 3: Verify errors propagate to stderr with exit code 1."""
    print("=" * 70)
    print("TEST 3: Error handling - failures go to stderr with exit code 1")
    print("=" * 70)
    
    result = run_cmd(
        "AEDIFICO_TEST_FAIL_COMPLETION=1 python -m aedifico weekly --dry-run"
    )
    
    # Check exit code is 1
    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"
    print(f"✓ Exit code: {result.returncode} (as expected)")
    
    # Check error message is in stderr
    assert "Simulated failure" in result.stderr, \
        f"Expected 'Simulated failure' in stderr. Got:\n{result.stderr}"
    print(f"✓ Error message correctly sent to stderr")
    
    # Check no output to stdout (or minimal)
    stdout = result.stdout.strip()
    assert "Weekly Reflection Report" not in stdout, \
        "Report should not be printed when evidence computation fails"
    print("✓ No report output when evidence computation fails")
    
    print("✓ TEST 3 PASSED\n")


def test_no_writes_in_dryrun():
    """Test 4: Verify no file writes occur in dry-run mode."""
    print("=" * 70)
    print("TEST 4: No file writes in dry-run mode")
    print("=" * 70)
    
    import tempfile
    
    # Create a unique marker file
    marker_path = AEDIFICO_PATH / "scratch_reports" / "test_dryrun_marker.txt"
    
    if marker_path.exists():
        marker_path.unlink()
    
    # Run dry-run
    run_cmd("python -m aedifico weekly --dry-run")
    
    # Check marker wasn't created and no other files in scratch_reports
    assert not marker_path.exists(), "Marker file shouldn't exist"
    print(f"✓ Marker file not created")
    
    # List all files in scratch_reports (if directory exists)
    if (AEDIFICO_PATH / "scratch_reports").exists():
        files = list((AEDIFICO_PATH / "scratch_reports").glob("*"))
        assert len(files) == 0, f"Unexpected files found: {files}"
        print(f"✓ No report files in scratch_reports")
    
    # Clean up marker if it somehow exists
    if marker_path.exists():
        marker_path.unlink()
    
    print("✓ TEST 4 PASSED\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("AEDIFICO DRY-RUN IMPLEMENTATION - TEST SUITE")
    print("=" * 70 + "\n")
    
    try:
        test_dry_run()
        test_normal_mode()
        test_error_handling()
        test_no_writes_in_dryrun()
        
        print("=" * 70)
        print("ALL TESTS PASSED!")
        print("=" * 70)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
