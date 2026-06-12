#!/usr/bin/env python3
"""Test MiniMax-M3 configuration for PaperGuard."""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from paperguard.schemas import ReferenceEntry
from paperguard.claim_verifier import verify_claim

print("🧪 Testing MiniMax-M3 Configuration")
print("=" * 60)

# Check environment variables
minimax_key = os.getenv("MINIMAX_API_KEY")
minimax_group = os.getenv("MINIMAX_GROUP_ID")
openai_key = os.getenv("OPENAI_API_KEY")

print("\n📋 Configuration Check:")
print(f"  MINIMAX_API_KEY: {'✅ Configured' if minimax_key else '❌ Not set'}")
print(f"  MINIMAX_GROUP_ID: {'✅ Configured' if minimax_group else '❌ Not set'}")
print(f"  OPENAI_API_KEY: {'✅ Configured' if openai_key else '❌ Not set'}")

if not minimax_key:
    print("\n⚠️  MiniMax API Key not configured!")
    print("   Please set MINIMAX_API_KEY and MINIMAX_GROUP_ID in .env file")
    print("   See MINIMAX_SETUP.md for instructions")
    sys.exit(1)

if not minimax_group:
    print("\n⚠️  MiniMax Group ID not configured!")
    print("   Please set MINIMAX_GROUP_ID in .env file")
    sys.exit(1)

# Test claim verification
print("\n🔬 Testing MiniMax-M3 API Call...")
print("-" * 60)

test_claim = "Our method achieves state-of-the-art performance on all benchmarks [1]."
test_ref = ReferenceEntry(
    ref_id="1",
    raw_text="Smith et al. (2023). A Novel Approach. NeurIPS.",
    title="A Novel Approach to Machine Learning",
    authors=["John Smith", "Jane Doe"],
    year=2023,
    venue="NeurIPS"
)

print(f"\nClaim: {test_claim}")
print(f"Reference: {test_ref.title}")
print(f"\nCalling MiniMax-M3...")

try:
    result = verify_claim(test_claim, test_ref, abstract=None)
    
    print("\n✅ API Call Successful!")
    print("-" * 60)
    print(f"Verdict: {result.verdict}")
    print(f"Severity: {result.severity}")
    print(f"Reason: {result.reason}")
    print(f"Evidence: {', '.join(result.evidence_used)}")
    
    if result.suggested_revision:
        print(f"\nSuggested Revision:")
        print(f"  {result.suggested_revision}")
    
    # Check if MiniMax was actually used
    if "MiniMax" in str(result.evidence_used):
        print("\n🎉 MiniMax-M3 is working correctly!")
    elif "GPT-4" in str(result.evidence_used):
        print("\n⚠️  Fell back to OpenAI GPT-4")
        print("   Check MiniMax API key and group ID")
    else:
        print("\n⚠️  Used fallback verification")
        print("   Check MiniMax configuration")
    
    print("\n" + "=" * 60)
    print("✅ Test completed successfully!")
    print("\nYou can now use Full mode with MiniMax-M3:")
    print("  streamlit run app_enhanced.py")
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    print("\nTroubleshooting:")
    print("  1. Check MINIMAX_API_KEY is correct")
    print("  2. Check MINIMAX_GROUP_ID is correct")
    print("  3. Verify account has sufficient balance")
    print("  4. Check network connection")
    sys.exit(1)
