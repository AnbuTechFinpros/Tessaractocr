import re
import json
import fitz
from PIL import Image
import pytesseract

# Load patterns
with open('patterns.json', 'r') as f:
    patterns = json.load(f)

# Extract text
doc = fitz.open('invoice/Shine Traders Bill [08.03.2024].pdf')
page = doc[0]
pix = page.get_pixmap(dpi=300)
img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
text = pytesseract.image_to_string(img, lang='eng')

# Get shine traders patterns
shine_pat = patterns['shine_traders']

# Test each field extraction
fields_to_test = [
    'supplier_address',
    'buyer_name',
    'buyer_gstin',
    'taxable_total',
    'cgst_total_amount',
    'sgst_total_amount',
    'grand_total'
]

def rx(text, pattern):
    if not text or not pattern:
        return ""
    if isinstance(pattern, dict):
        for k in ("primary", "fallback"):
            p = pattern.get(k)
            if p:
                m = re.search(p, text, re.I | re.S)
                if m:
                    return (m.group(m.lastindex) if m.lastindex else m.group(0)).strip()
        return ""
    if isinstance(pattern, str):
        m = re.search(pattern, text, re.I | re.S)
        if m:
            return (m.group(m.lastindex) if m.lastindex else m.group(0)).strip()
    return ""

print("=== Field Extraction Results ===\n")
for field in fields_to_test:
    pattern = shine_pat.get(field)
    result = rx(text, pattern)
    status = "✅" if result else "❌"
    print(f"{status} {field:25} = {result[:60] if result else 'EMPTY'}")
