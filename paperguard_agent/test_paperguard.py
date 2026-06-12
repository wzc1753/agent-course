#!/usr/bin/env python3
"""Quick test script for PaperGuard Agent."""

import sys
from pathlib import Path

# Test imports
print("Testing imports...")
try:
    from paperguard.schemas import ReferenceEntry, CitationMention, AuditIssue
    print("✓ Schemas imported")
    
    from paperguard.config import Config
    print("✓ Config imported")
    
    from paperguard.parser import split_paper
    print("✓ Parser imported")
    
    from paperguard.citation_extractor import extract_citations
    print("✓ Citation extractor imported")
    
    from paperguard.reference_parser import parse_references
    print("✓ Reference parser imported")
    
    from paperguard.matcher import normalize_text, title_similarity
    print("✓ Matcher imported")
    
    from paperguard.report import AuditReport
    print("✓ Report imported")
    
    from paperguard.pipeline import run_audit
    print("✓ Pipeline imported")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"\n❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test with demo paper
print("\n" + "="*50)
print("Testing with demo paper...")
print("="*50)

demo_path = Path("data/demo_bad_paper.md")
if not demo_path.exists():
    print(f"❌ Demo paper not found at {demo_path}")
    sys.exit(1)

try:
    with open(demo_path, 'r', encoding='utf-8') as f:
        paper_content = f.read()
    
    print(f"✓ Loaded demo paper ({len(paper_content)} chars)")
    
    # Test parsing
    body, refs = split_paper(paper_content)
    print(f"✓ Parsed paper: {len(body)} chars body, {len(refs)} chars references")
    
    # Test citation extraction
    citations = extract_citations(body)
    print(f"✓ Extracted {len(citations)} citations")
    
    # Test reference parsing
    references = parse_references(refs)
    print(f"✓ Parsed {len(references)} references")
    
    # Run quick audit (Fast mode to avoid API calls)
    print("\nRunning Fast audit (no external API calls)...")
    report = run_audit(paper_content, mode="Fast", max_claims=5)
    
    print(f"\n📊 Audit Results:")
    print(f"   Total issues: {len(report.issues)}")
    
    if report.issues:
        print(f"\n   Issues by severity:")
        for severity in ["HIGH", "MEDIUM", "LOW"]:
            count = sum(1 for i in report.issues if i.severity == severity)
            if count > 0:
                print(f"   - {severity}: {count}")
        
        print(f"\n   Issues by type:")
        issue_types = {}
        for issue in report.issues:
            issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1
        for itype, count in issue_types.items():
            print(f"   - {itype}: {count}")
    
    print("\n✅ All tests passed!")
    print("\nTo run the full Streamlit app:")
    print("  streamlit run app.py")
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
