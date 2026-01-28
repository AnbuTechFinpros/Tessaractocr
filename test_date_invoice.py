import re
import fitz
from PIL import Image
import pytesseract

doc = fitz.open('invoice/Shine Traders Bill [08.03.2024].pdf')
page = doc[0]
pix = page.get_pixmap(dpi=300)
img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
text = pytesseract.image_to_string(img, lang='eng')

# Test invoice_date pattern
pattern = r'(?is)Date\s*:?\s*(\d{2}\.\d{2}\.\d{2})'
m = re.search(pattern, text)
result = m.group(1) if m else "NO MATCH"
print(f'invoice_date match: {result}')

# Look for date manually
print(f'\nLooking for date patterns:')
if '08.03.24' in text:
    print('Found 08.03.24')
    idx = text.find('08.03.24')
    print(f'Context: {repr(text[max(0,idx-20):idx+30])}')
    
# Check what the pattern looks like
pattern = r'(?is)No\.\s*:?\s*(\d{3,})'
m = re.search(pattern, text)
result = m.group(1) if m else "NO MATCH"
print(f'\ninvoice_number match: {result}')

# Let me find the actual date format
print(f'\nSearching for actual date:')
pattern = r'(\d{2}[.-]\d{2}[.-]\d{2,4})'
matches = re.findall(pattern, text)
print(f'Date patterns found: {matches}')
