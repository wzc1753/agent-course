import sys
sys.path.insert(0, '.')

print("Testing agent fix...")

# Test 1: Parser
from paperguard.agents import ParserAgent
parser = ParserAgent()

test_paper = """
This is a test paper [1]. More text here.

References:
[1] Test Reference 2023.
"""

try:
    result = parser.run({"paper_content": test_paper, "bib_content": None})
    print("✅ ParserAgent works!")
    print(f"  Found {result['stats']['citations_count']} citations")
    print(f"  Found {result['stats']['references_count']} references")
except Exception as e:
    print(f"❌ ParserAgent error: {e}")
    sys.exit(1)

# Test 2: Supervisor
from paperguard.agents import SupervisorAgent
supervisor = SupervisorAgent()

try:
    result = supervisor.run({
        "paper_content": test_paper,
        "bib_content": None,
        "mode": "Fast"
    })
    print("✅ SupervisorAgent works!")
    print(f"  Workflow completed")
except Exception as e:
    print(f"❌ SupervisorAgent error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n🎉 All tests passed! Agent system is working.")
