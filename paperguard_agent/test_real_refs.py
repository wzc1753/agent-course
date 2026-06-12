import sys
sys.path.insert(0, '.')

from paperguard.reference_parser import parse_references

# 使用你PDF中的实际引用格式
real_refs = '''
[1] Qi Chen, Bing Zhao, Haidong Wang, Mingqin Li, Chuanjie Liu, Zengzhong Li, Mao Yang, and Jingdong Wang. Spann: Highly-efficient billion-scale approximate nearest neighborhood search. Advances in Neural Information Processing Systems, 34:5199-5212, 2021.

[11] Luyu Gao, Zhuyun Dai, Tongfei Chen, Zhen Fan, Benjamin Van Durme, and Jamie Callan. Complement lexical retrieval model with semantic residual embeddings. In Advances in Information Retrieval: 43rd European Conference on IR Research, ECIR 2021, Virtual Event, March 28-April 1, 2021, Proceedings, Part I 43, pages 146-160. Springer, 2021.

[16] Saar Kuzi, Mingyang Zhang, Cheng Li, Michael Bendersky, and Marc Najork. Leveraging semantic and lexical matching to improve the recall of document retrieval systems: A hybrid approach. arXiv preprint arXiv:2010.01195, 2020.
'''

print('Testing real PDF reference parsing...')
print('=' * 60)

references = parse_references(real_refs)
print(f'\nParsed {len(references)} references:\n')

for ref in references:
    ref_id = getattr(ref, 'ref_id', '?')
    title = getattr(ref, 'title', None)
    authors = getattr(ref, 'authors', [])
    year = getattr(ref, 'year', None)
    arxiv = getattr(ref, 'arxiv_id', None)
    
    print(f'[{ref_id}]')
    print(f'  Title: {title if title else "NOT EXTRACTED"}')
    print(f'  Authors: {len(authors)} found')
    print(f'  Year: {year}')
    print(f'  arXiv: {arxiv if arxiv else "N/A"}')
    print()

print('=' * 60)
if all(getattr(r, 'title', None) for r in references):
    print('SUCCESS: All titles extracted')
else:
    print('ISSUE: Some titles not extracted')
    print('This is a known limitation with complex reference formats')
    print('However, ref_id, authors, and year should still work for matching')
