import sys
sys.path.insert(0, '.')

from paperguard.parser import load_paper, split_paper
from paperguard.citation_extractor import extract_citations
from paperguard.reference_parser import parse_references

print('Testing PDF parsing...')
print('=' * 60)

# Test with the PDF text you provided
pdf_text = '''
Hybrid retrieval methods [11, 16, 20, 28, 33] aim to combine these advantages.

References
[1] Qi Chen et al. SPANN: Highly-efficient billion-scale approximate nearest neighborhood search. NeurIPS, 2021.
[11] Luyu Gao et al. Complement lexical retrieval model with semantic residual embeddings. ECIR 2021.
[16] Saar Kuzi et al. Leveraging semantic and lexical matching. arXiv:2010.01195, 2020.
'''

print('\n1. Splitting paper...')
body, refs = split_paper(pdf_text)
print(f'Body length: {len(body)}')
print(f'References section length: {len(refs)}')

print('\n2. Extracting citations...')
citations = extract_citations(body)
print(f'Found {len(citations)} citations')
for cit in citations[:3]:
    print(f'  - {cit.raw_marker}: {cit.ref_ids}')

print('\n3. Parsing references...')
references = parse_references(refs)
print(f'Found {len(references)} references')
for ref in references[:3]:
    ref_id = getattr(ref, 'ref_id', '?')
    title = getattr(ref, 'title', 'No title')
    print(f'  - [{ref_id}] {title[:50]}...')

print('\n' + '=' * 60)
print('PDF parsing test completed!')
