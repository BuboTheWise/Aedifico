#!/usr/bin/env python3
"""Simple test for Aedifico error handling."""

import sys
import os
sys.path.insert(0, '/home/stefan/Projects/Aedifico')


def main():
    """Test that errors are properly raised and caught."""
    
    print("=" * 60)
    print("ERROR HANDLING TEST")
    print("=" * 60)
    
    # Test 1: Import and verify module loads
    import aedifico
    
    try:
        result = aedifico.compute_polygraph_results()
        print("✓ Module imports correctly")
        print(f"  Polygraph results type: {type(result)}")
        
        # Verify it returns expected structure
        if "results" in result and "source" in result:
            print("✓ Returns proper dict with source label")
        else:
            print("✗ Missing expected fields in result")
            return 1
            
    except Exception as e:
        print(f"✗ Module failed to import/run: {e}")
        return 1
    
    # Test 2: Verify environment variable triggers failure
    print("\nTesting environment variable failure injection:")
    os.environ["AEDIFICO_TEST_FAIL_POLYGRAPH"] = "1"
    
    try:
        result = aedifico.compute_polygraph_results()
        print("✗ Expected failure with env var, got success")
        return 1
    except Exception as e:
        if "Simulated failure" in str(e):
            print(f"✓ Env var correctly triggers failure: {e}")
        else:
            print(f"✗ Wrong error: {e}")
            return 1
    finally:
        del os.environ["AEDIFICO_TEST_FAIL_POLYGRAPH"]
    
    # Test 3: Verify we can call the functions without issues
    print("\nTesting all evidence sources:")
    try:
        p = aedifico.compute_polygraph_results()
        c = aedifico.compute_completion_data()
        m = aedifico.compute_communication_metrics()
        ss = aedifico.compute_session_search()
        
        print("✓ All evidence sources compute successfully")
        real_count = sum(1 for s in [p, c, m, ss] if s.get('real_source', False))
        print(f"  Sources with real_source=True: {real_count}")
        
    except Exception as e:
        print(f"✗ Evidence computation failed: {e}")
        return 1
    
    print("\n✓ All error handling tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
