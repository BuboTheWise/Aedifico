#!/usr/bin/env python3
"""Comprehensive test suite for Aedifico CLI."""

import sys
import os
import tempfile
import glob
sys.path.insert(0, '/home/stefan/Projects/Aedifico')


def run_aedifico(*args):
    """Helper to run aedifico with given args."""
    from subprocess import run
    cmd = [sys.executable, "-m", "aedifico"] + list(args)
    result = run(cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def cleanup_reports():
    """Remove all report files to ensure clean state."""
    import glob
    for f in glob.glob(os.path.join(".", "aedifico-report-*.md")):
        os.remove(f)


def test_normal_mode():
    """Test normal mode writes a file."""
    print("\n" + "=" * 60)
    print("TEST: Normal mode writes file")
    print("=" * 60)
    
    cleanup_reports()
    
    stdout, stderr, exit_code = run_aedifico("weekly")
    
    if exit_code != 0:
        print(f"✗ Expected exit code 0, got {exit_code}")
        return False
    
    print("✓ Exit code is 0")
    
    import glob
    report_files = glob.glob(os.path.join(".", "aedifico-report-*.md"))
    
    if not report_files:
        print("✗ No report files found after normal mode run")
        return False
    
    print(f"✓ Report file created: {report_files[0]}")
    
    with open(report_files[0]) as f:
        content = f.read()
    
    if "# Aedifico Weekly Reflection Report" not in content:
        print("✗ Report missing expected title")
        return False
    
    print("✓ Report contains expected sections")
    
    cleanup_reports()
    
    return True


def test_dry_run_mode():
    """Test dry-run mode doesn't write file."""
    print("\n" + "=" * 60)
    print("TEST: Dry-run mode doesn't write file")
    print("=" * 60)
    
    cleanup_reports()
    
    stdout, stderr, exit_code = run_aedifico("weekly", "--dry-run")
    
    if exit_code != 0:
        print(f"✗ Expected exit code 0 for dry-run, got {exit_code}")
        return False
    
    print("✓ Exit code is 0")
    
    if "would write" not in stderr.lower():
        print("✗ Stderr missing 'would write' message")
        return False
    
    print("✓ Stderr contains 'would write' message")
    
    report_files = glob.glob(os.path.join(".", "aedifico-report-*.md"))
    
    if report_files:
        print(f"✗ Report files found after dry-run (should be empty): {report_files}")
        cleanup_reports()
        return False
    
    print("✓ No report files created in dry-run mode")
    
    return True


def test_dry_run_with_write_flag():
    """Test that --dry-run takes precedence over --write."""
    print("\n" + "=" * 60)
    print("TEST: --dry-run takes precedence over --write")
    print("=" * 60)
    
    cleanup_reports()
    
    os.environ["AEDIFICO_DRY_RUN_DIR"] = "."
    stdout, stderr, exit_code = run_aedifico("weekly", "--dry-run", "-w")
    del os.environ["AEDIFICO_DRY_RUN_DIR"]
    
    if exit_code != 0:
        print(f"✗ Expected exit code 0, got {exit_code}")
        return False
    
    print("✓ Exit code is 0")
    
    if "would write" not in stderr.lower():
        print("✗ Stderr missing 'would write' message")
        return False
    
    print("✓ Dry-run message shown in stderr")
    
    report_files = glob.glob(os.path.join(".", "aedifico-report-*.md"))
    
    if report_files:
        print(f"✗ Files were written despite --dry-run flag: {report_files}")
        cleanup_reports()
        return False
    
    print("✓ No files written in dry-run with --write")
    
    return True


def test_unknown_subcommand():
    """Test unknown subcommand exits with non-zero."""
    print("\n" + "=" * 60)
    print("TEST: Unknown subcommand exits non-zero")
    print("=" * 60)
    
    cleanup_reports()
    
    stdout, stderr, exit_code = run_aedifico("unknown_command")
    
    if exit_code == 0:
        print(f"✗ Expected non-zero exit code for unknown subcommand")
        return False
    
    print(f"✓ Exit code is {exit_code} (non-zero)")
    
    if "invalid choice" not in stderr.lower():
        print("✗ Error message missing expected text")
        return False
    
    print("✓ Error message displayed to stderr")
    
    return True


def test_missing_subcommand():
    """Test missing subcommand exits with non-zero."""
    print("\n" + "=" * 60)
    print("TEST: Missing subcommand exits non-zero")
    print("=" * 60)
    
    cleanup_reports()
    
    stdout, stderr, exit_code = run_aedifico()
    
    if exit_code == 0:
        print(f"✗ Expected non-zero exit code for missing subcommand")
        return False
    
    print(f"✓ Exit code is {exit_code} (non-zero)")
    
    # Accept any reasonable error message about invalid/missing subcommand
    valid_error_patterns = ["invalid choice", "unknown or missing", "usage:"]
    if not any(pattern.lower() in stderr.lower() for pattern in valid_error_patterns):
        print(f"✗ Error message doesn't contain expected text:\n{stderr}")
        return False
    
    print("✓ Appropriate error message displayed to stderr")
    
    return True


def test_typo_subcommand():
    """Test typo in subcommand ('wekly' vs 'weekly')."""
    print("\n" + "=" * 60)
    print("TEST: Typo in subcommand exits non-zero")
    print("=" * 60)
    
    cleanup_reports()
    
    stdout, stderr, exit_code = run_aedifico("wekly")
    
    if exit_code == 0:
        print(f"✗ Expected non-zero exit code for typo")
        return False
    
    print(f"✓ Exit code is {exit_code} (non-zero)")
    
    if "invalid choice" not in stderr.lower():
        print("✗ Error message missing expected text")
        return False
    
    print("✓ Argparse rejected invalid subcommand")
    
    return True


def test_error_handling_polygraph():
    """Test error handling when polygraph computation fails."""
    print("\n" + "=" * 60)
    print("TEST: Error handling for failed evidence source")
    print("=" * 60)
    
    cleanup_reports()
    
    # Set environment variable to trigger failure
    os.environ["AEDIFICO_TEST_FAIL_POLYGRAPH"] = "1"
    
    stdout, stderr, exit_code = run_aedifico("weekly", "--dry-run")
    
    if exit_code != 1:
        print(f"✗ Expected exit code 1 for evidence failure, got {exit_code}")
        return False
    
    print(f"✓ Exit code is {exit_code} (non-zero)")
    
    if "Simulated failure" not in stderr:
        print("✗ Error message missing expected text")
        return False
    
    print("✓ Error message displayed to stderr")
    
    del os.environ["AEDIFICO_TEST_FAIL_POLYGRAPH"]
    
    return True


def test_output_consistency():
    """Test that normal mode and dry-run produce same output content (ignoring generated timestamp)."""
    print("\n" + "=" * 60)
    print("TEST: Normal and dry-run modes produce identical content")
    print("=" * 60)
    
    cleanup_reports()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["AEDIFICO_DRY_RUN_DIR"] = tmpdir
        
        stdout_normal, _, _ = run_aedifico("weekly")
        
        stdout_dryrun, _, _ = run_aedifico("weekly", "--dry-run")
        
        del os.environ["AEDIFICO_DRY_RUN_DIR"]
    
    # Normalize: strip trailing newlines for comparison
    stdout_normal_normalized = stdout_normal.rstrip()
    stdout_dryrun_normalized = stdout_dryrun.rstrip()
    
    # Both outputs should contain report title and sections
    if "# Aedifico Weekly Reflection Report" not in stdout_normal_normalized:
        print("✗ Normal mode missing report title")
        return False
    
    if "# Aedifico Weekly Reflection Report" not in stdout_dryrun_normalized:
        print("✗ Dry-run mode missing report title")
        return False
    
    # Compare content excluding timestamp differences
    # Extract everything after the "Generated:" line and period info
    normal_content = "".join([line for line in stdout_normal_normalized.split("\n")[2:]])
    dryrun_content = "".join([line for line in stdout_dryrun_normalized.split("\n")[2:]])
    
    if normal_content != dryrun_content:
        print("✗ Content differs after first two lines (title, generated, period)")
        return False
    
    print("✓ Both modes produce identical content structure")
    print("  (Generated timestamp may differ between runs - that's expected)")
    
    return True


def test_evidence_source_labeling():
    """Test that evidence sources are properly labeled as real or mock."""
    print("\n" + "=" * 60)
    print("TEST: Evidence source labeling")
    print("=" * 60)
    
    cleanup_reports()
    
    stdout_normal, _, _ = run_aedifico("weekly", "--dry-run")
    
    # Check that output mentions real vs mock sources
    if "Real Evidence Sources:" in stdout_normal:
        print("✓ Output labels real vs mock sources")
        
        # Count real sources (should be at least 0)
        import re
        match = re.search(r'Real Evidence Sources:\s*(\d+) of (\d+)', stdout_normal)
        if match:
            real_count, total = int(match.group(1)), int(match.group(2))
            print(f"  Real: {real_count}, Total: {total}")
    else:
        print("✗ Missing evidence source labeling")
        return False
    
    return True


def main():
    """Run all tests."""
    import glob
    
    cleanup_reports()
    
    results = [
        test_normal_mode(),
        test_dry_run_mode(),
        test_dry_run_with_write_flag(),
        test_unknown_subcommand(),
        test_missing_subcommand(),
        test_typo_subcommand(),
        test_error_handling_polygraph(),
        test_output_consistency(),
        test_evidence_source_labeling(),
    ]
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for r in results if r)
    failed = total - passed
    
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {failed}/{total}")
    
    cleanup_reports()
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
