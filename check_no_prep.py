import pytesseract
from PIL import Image
import fitz

# Extract text with NO preprocessing
doc = fitz.open('invoice/Shine Traders Bill [08.03.2024].pdf')
page = doc[0]
pix = page.get_pixmap(dpi=300)
img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
text = pytesseract.image_to_string(img, lang="eng")

print("Key searches:")
print(f"'L64/305' found: {'L64/305' in text}")
print(f"'COMTEN' found: {'COMTEN' in text}")
print(f"'CGST 9.00% for' found: {'CGST 9.00% for' in text}")

# Show the lines with CGST
lines = text.split('\n')
for i, line in enumerate(lines):
    if 'CGST' in line and '%' in line:
        print(f"\nLine {i}: {repr(line)}")
