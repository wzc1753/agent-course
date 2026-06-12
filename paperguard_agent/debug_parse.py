import sys
sys.path.insert(0, '.')

from paperguard.reference_parser import parse_references

# 你PDF中真实的引用
real_ref = '''[1] Qi Chen, Bing Zhao, Haidong Wang, Mingqin Li, Chuanjie Liu, Zengzhong Li, Mao Yang, and Jingdong Wang. Spann: Highly-efficient billion-scale approximate nearest neighborhood search. Advances in Neural Information Processing Systems, 34:5199-5212, 2021.'''

print('Testing parse_references with real PDF format...')
print('Input:', real_ref[:100])
print()

result = parse_references(real_ref)
print(f'Result: {len(result)} references parsed')

if result:
    ref = result[0]
    print(f'ref_id: {getattr(ref, "ref_id", "NONE")}')
    print(f'title: {getattr(ref, "title", "NONE")}')
    print(f'authors: {getattr(ref, "authors", [])}')
    print(f'year: {getattr(ref, "year", "NONE")}')
else:
    print('ERROR: Nothing parsed!')
    print()
    print('Debugging: Checking _split_references...')
    from paperguard.reference_parser import _split_references
    items = _split_references(real_ref)
    print(f'Split into {len(items)} items')
    for i, item in enumerate(items[:3]):
        print(f'  Item {i}: {item[:80]}...')
