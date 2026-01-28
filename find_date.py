import fitz
from PIL import Image
import pytesseract

doc = fitz.open('invoice/Shine Traders Bill [08.03.2024].pdf')
page = doc[0]
pix = page.get_pixmap(dpi=300)
img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
text = pytesseract.image_to_string(img, lang='eng')

lines = text.split('\n')
for i, line in enumerate(lines):
    if '2024' in line or '24' in line or 'MAR' in line or '07' in line or '08' in line:
        print(f'{i}: {repr(line)}')
