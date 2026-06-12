import sys
sys.path.insert(0, '.')

from paperguard.parser import split_paper

# 模拟PDF提取的混乱文本（真实场景）
messy_pdf_text = '''
HybridSparse: An End-to-End Framework for Efficient Large-Scale Retrieval
Anonymous submission

Hybrid retrieval methods [11, 16, 20] aim to combine their advantages.

Refer ences [1] Qi Chen, Bing Zhao, Haidong Wang, Mingqin Li, Chuanjie Liu, Zengzhong Li, Mao Yang, and Jingdong Wang. Spann: Highly-efficient billion-scale approximate nearest neighborhood search. Advances in Neural Information Processing Systems, 34:5199-5212, 2021. 1, 2 [2] Qi Chen, Xiubo Geng, Corby Rosset. Ms marco web search: a large-scale information-rich web dataset. WWW 2024, pages 292-301, 2024. 5
'''

print('Testing enhanced PDF parsing...')
print('=' * 60)

body, refs = split_paper(messy_pdf_text)

print(f'Body length: {len(body)} chars')
print(f'Refs length: {len(refs)} chars')
print()

if refs:
    print('SUCCESS: References section found!')
    print(f'Refs preview: {refs[:200]}...')
    
    # Now parse the references
    from paperguard.reference_parser import parse_references
    references = parse_references(refs)
    print(f'\nParsed {len(references)} references')
    for ref in references[:3]:
        print(f'  [{getattr(ref, "ref_id", "?")}] year={getattr(ref, "year", "?")}')
else:
    print('FAILED: No references section detected')
    print('Trying pattern-based detection might help')
