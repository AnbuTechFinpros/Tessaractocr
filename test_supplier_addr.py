import re
import pytesseract
from PIL import Image
import fitz

# Extract text
doc = fitz.open('invoice/Shine Traders Bill [08.03.2024].pdf')
page = doc[0]
pix = page.get_pixmap(dpi=300)
img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
text = pytesseract.image_to_string(img, lang="eng")

# Test supplier_address pattern
pattern = r'(?is)L64\/305,\s*Police\s*Quarters,\s*Ganapathy,\s*Coimbatore\s*-\s*641\s*006'
m = re.search(pattern, text)
if m:
    print(f"supplier_address found: '{m.group(0)}'")
    print(f"lastindex: {m.lastindex}")
else:
    print("supplier_address NOT found")
    
# Show raw text around L64
if 'L64' in text:
    idx = text.find('L64')
    print(f"\nRaw text: {repr(text[idx:idx+100])}")
