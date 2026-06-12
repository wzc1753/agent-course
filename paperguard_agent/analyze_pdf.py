import sys
sys.path.insert(0, '.')

# 找到你的PDF
import os
pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
print(f'Found PDF files: {pdf_files}')

if pdf_files:
    pdf_path = pdf_files[0]
    print(f'\nExtracting text from: {pdf_path}')
    
    import PyPDF2
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        print(f'Total pages: {len(reader.pages)}')
        
        # Extract first page
        page1 = reader.pages[0].extract_text()
        print(f'\n=== Page 1 (first 500 chars) ===')
        print(page1[:500])
        
        # Extract last page (likely has references)
        last_page = reader.pages[-1].extract_text()
        print(f'\n=== Last page (first 500 chars) ===')
        print(last_page[:500])
        
        # Check if 'References' or 'Refer ences' appears
        all_text = '\n'.join(page.extract_text() for page in reader.pages)
        
        if 'References' in all_text:
            idx = all_text.find('References')
            print(f'\n=== Found "References" at position {idx} ===')
            print(all_text[idx:idx+200])
        elif 'Refer ences' in all_text:
            print('\n=== Found "Refer ences" (with space) ===')
            idx = all_text.find('Refer ences')
            print(all_text[idx:idx+200])
        else:
            print('\n=== "References" not found in PDF ===')
else:
    print('No PDF files in current directory')
