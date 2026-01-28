import re
import fitz
from PIL import Image
import pytesseract

doc = fitz.open('invoice/Shine Traders Bill [08.03.2024].pdf')
page = doc[0]
pix = page.get_pixmap(dpi=300)
img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
text = pytesseract.image_to_string(img, lang='eng')

# Test supplier_address
pattern = r'(?is)L64/305,\s*Police\s*Quarters,\s*Ganapathy,\s*Coimbatore\s*-\s*641\s*006'
match = re.search(pattern, text)
result = match.group(0) if match else "NO MATCH"
print(f'✅ supplier_address: {result[:50]}...' if match else f'❌ supplier_address: {result}')

# Test buyer_name
pattern = r'(?is)M/S\.\s+(COMTEN\s+CONSULTING\s+ENGINEERS\s+Pvt\s+LTD)'
match = re.search(pattern, text)
result = match.group(1) if match else "NO MATCH"
print(f'✅ buyer_name: {result}' if match else f'❌ buyer_name: {result}')

# Test buyer_gstin
pattern = r'(?is)GSTIN\s+([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z])\s+GSTIN'
match = re.search(pattern, text)
result = match.group(1) if match else "NO MATCH"
print(f'✅ buyer_gstin: {result}' if match else f'❌ buyer_gstin: {result}')

# Test taxable_total
pattern = r'(?is)Taxable\s*Total\s+([0-9,]+\.\d{2}|\d+\.\d{2}|\d+)'
match = re.search(pattern, text)
result = match.group(1) if match else "NO MATCH"
print(f'✅ taxable_total: {result}' if match else f'❌ taxable_total: {result}')

# Test CGST
pattern = r'(?is)\|?\s*CGST\s+9\.00%\s+for\s+[0-9,]+\.00\s*=\s*([0-9,]+\.\d{2})'
match = re.search(pattern, text)
result = match.group(1) if match else "NO MATCH"
print(f'✅ cgst_total_amount: {result}' if match else f'❌ cgst_total_amount: {result}')

# Test SGST
pattern = r'(?is)SGST\s+9\.00\s*%\s+for\s+[0-9,]+\.00\s*=\s*([0-9,]+\.\d{2})'
match = re.search(pattern, text)
result = match.group(1) if match else "NO MATCH"
print(f'✅ sgst_total_amount: {result}' if match else f'❌ sgst_total_amount: {result}')

# Test grand_total
pattern = r'(?is)(?:Taxable\s+Total|Grand\s+Total)\s+([0-9,]+\.\d{2}|\d+)'
match = re.search(pattern, text)
result = match.group(1) if match else "NO MATCH"
print(f'✅ grand_total: {result}' if match else f'❌ grand_total: {result}')

print('\n--- Summary ---')
print('All main fields should show ✅')
