#!/usr/bin/env python3
"""Quick test for agent fix."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from paperguard.agents import ParserAgent

print("Testing ParserAgent fix...")

agent = ParserAgent()
test_input = {
    'paper_content': 'This is a test paper [1]. More text [2].\n\nReferences:\n[1] Test ref 1\n[2] Test ref 2',
    'bib_content': None
}

try:
    result = agent.run(test_input)
    print("✅ Agent fix successful!")
    print(f"  Citations: {result['stats']['citations_count']}")
    print(f"  References: {result['stats']['references_count']}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
