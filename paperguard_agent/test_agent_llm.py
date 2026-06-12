import sys
sys.path.insert(0, '.')

from paperguard.pipeline_agent import run_audit_with_agents

test_paper = '''# Test Paper

This is a test paper with citation [1].

## References

[1] Smith, J. (2023). Test Paper. Journal of Testing.
'''

print('=' * 60)
print('Testing Agent system...')
print('=' * 60)

try:
    report = run_audit_with_agents(
        paper_content=test_paper,
        bib_content=None,
        mode='Standard',
        max_claims=5
    )
    
    print('\nSUCCESS! Agent system works!')
    print('Issues found:', len(report.issues))
    
    if hasattr(report, 'agent_traces'):
        print('Agent traces:', len(report.agent_traces))
    
    print('\n' + '=' * 60)
    print('Test PASSED!')
    
except Exception as e:
    print('\nERROR:', str(e))
    import traceback
    traceback.print_exc()
    exit(1)
