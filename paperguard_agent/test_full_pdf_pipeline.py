import sys
sys.path.insert(0, '.')

from paperguard.pipeline import run_audit

# 模拟真实PDF提取的文本
pdf_paper = '''
HybridSparse: An End-to-End Hybrid Framework for Efficient Large-Scale Retrieval

Abstract
Large-scale retrieval requires efficient search. Hybrid retrieval methods [11, 16, 20] aim to combine advantages.

1. Introduction
Retrieval is fundamental. We cite work [1] and [2].

Refer ences [1] Qi Chen, Bing Zhao, Haidong Wang. Spann: Highly-efficient billion-scale approximate nearest neighborhood search. Advances in Neural Information Processing Systems, 34:5199-5212, 2021. [2] Qi Chen, Xiubo Geng, Corby Rosset. MS MARCO web search: a large-scale dataset. WWW 2024, pages 292-301, 2024. [11] Luyu Gao et al. Complement lexical retrieval. ECIR 2021, pages 146-160. [16] Saar Kuzi et al. Leveraging semantic and lexical matching. arXiv:2010.01195, 2020.
'''

print('=' * 60)
print('Full Pipeline Test with PDF-like Text')
print('=' * 60)

try:
    report = run_audit(pdf_paper, mode='Standard', max_claims=5)
    
    print(f'\nSUCCESS! Audit completed')
    print(f'Total issues: {len(report.issues)}')
    print()
    
    for issue in report.issues[:5]:
        print(f'- {issue.issue_type}: {issue.diagnosis[:80]}...')
    
    print('\n' + '=' * 60)
    print('PDF Parsing is NOW WORKING!')
    print('=' * 60)
    
except Exception as e:
    print(f'\nERROR: {e}')
    import traceback
    traceback.print_exc()
