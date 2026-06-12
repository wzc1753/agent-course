import sys
sys.path.insert(0, '.')

from paperguard.parser import split_paper
from paperguard.reference_parser import parse_references

# 模拟你上传的PDF提取的文本
pdf_text = '''
HybridSparse: An End-to-End Hybrid Framework

Hybrid retrieval methods [11, 16, 20, 28, 33] aim to combine their advantages.

References
[1] Qi Chen et al. Spann. NeurIPS, 34:5199-5212, 2021.
[2] Qi Chen et al. MS MARCO web search. WWW 2024, pages 292-301, 2024.
'''

print('Step 1: Split paper into body and refs...')
body, refs = split_paper(pdf_text)
print(f'Body length: {len(body)}')
print(f'Refs section: {repr(refs[:100])}...')
print()

print('Step 2: Parse references...')
references = parse_references(refs)
print(f'Parsed: {len(references)} references')
print()

if len(references) == 0:
    print('ERROR: No references parsed!')
    print('Refs section was:', repr(refs))
else:
    print('SUCCESS: References parsed')
    for ref in references:
        print(f'  [{getattr(ref, "ref_id", "?")}] year={getattr(ref, "year", "?")}')
