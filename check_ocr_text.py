import pytesseract
from PIL import Image, ImageOps, ImageFilter
import fitz

def preprocess_image(img):
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
    return img

# Extract text
doc = fitz.open('invoice/Shine Traders Bill [08.03.2024].pdf')
page = doc[0]
pix = page.get_pixmap(dpi=300)
img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
img = preprocess_image(img)
text = pytesseract.image_to_string(img, lang="eng", config="--psm 6")

# Print first 30 lines
lines = text.split('\n')
print("First 35 lines:")
for i, line in enumerate(lines[:35]):
    print(f"{i:2d}: {repr(line)}")

# Check for key patterns
print("\nKey searches:")
print(f"'L64/305' found: {'L64/305' in text}")
print(f"'COMTEN' found: {'COMTEN' in text}")
