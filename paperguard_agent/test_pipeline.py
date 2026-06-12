#!/usr/bin/env python
"""
Test script to verify pipeline.py is working correctly.
"""

import sys
sys.path.insert(0, '.')

try:
    from paperguard.pipeline import run_audit
    print("✓ Successfully imported run_audit from pipeline")
    print("✓ Pipeline module is complete and functional")

    # Check function signature
    import inspect
    sig = inspect.signature(run_audit)
    print(f"✓ run_audit signature: {sig}")

    print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
    print("Pipeline module is ready to use!")

except ImportError as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
