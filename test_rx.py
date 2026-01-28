import re
import json
import fitz
from PIL import Image
import pytesseract

# Load patterns
with open("patterns.json", "r") as f:
    patterns = json.load(f)

def rx(text: str, pattern):
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

# Extract text
doc = fitz.open('invoice/Shine Traders Bill [08.03.2024].pdf')
page = doc[0]
pix = page.get_pixmap(dpi=300)
img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
text = pytesseract.image_to_string(img, lang='eng')

# Get patterns
shine_pat = patterns['shine_traders']

# Test extraction
print("Testing rx() function with patterns.json:")
print(f"supplier_address: '{rx(text, shine_pat.get('supplier_address'))}'")
print(f"buyer_name: '{rx(text, shine_pat.get('buyer_name'))}'")
print(f"buyer_gstin: '{rx(text, shine_pat.get('buyer_gstin'))}'")
print(f"taxable_total: '{rx(text, shine_pat.get('taxable_total'))}'")
print(f"cgst_total_amount: '{rx(text, shine_pat.get('cgst_total_amount'))}'")

# Also test with direct regex
print("\nDirect regex test:")
pattern_str = shine_pat.get('supplier_address')
m = re.search(pattern_str, text, re.I | re.S)
print(f"supplier_address match: {m is not None}")
if m:
    print(f"  Groups: {m.groups()}")
    print(f"  lastindex: {m.lastindex}")
    print(f"  group(0): '{m.group(0)[:50]}'")
