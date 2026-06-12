#!/usr/bin/env python3
"""Test agent fix."""
import sys
sys.path.insert(0, '.')

from paperguard.pipeline_agent import run_audit_with_agents

test_paper = """
# Test Paper

This is a test paper with citation [1].

## References

[1] Smith, J. (2023). Test Paper. Journal of Testing.
"""

print("Testing Agent fix...")
print("=" * 60)

try:
    report = run_audit_with_agents(
        paper_content=test_paper,
        bib_content=None,
        mode="Standard",
        max_claims=5
    )
    
    print("✅ Agent system works!")
    print(f"Issues found: {len(report.issues)}")
    print(f"Agent traces: {len(report.agent_traces) if hasattr(report, 'agent_traces') else 0}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("🎉 Test passed! Agent system is working correctly.")
