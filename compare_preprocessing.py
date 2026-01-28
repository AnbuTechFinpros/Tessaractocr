import pytesseract
from PIL import Image, ImageOps, ImageFilter
import fitz

def preprocess_image(img):
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
    img = img.point(lambda x: 0 if x < 160 else 255, mode="1")
    return img

# Extract with and without preprocessing
doc = fitz.open('invoice/Shine Traders Bill [08.03.2024].pdf')
page = doc[0]
pix = page.get_pixmap(dpi=300)
img_orig = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
img_processed = preprocess_image(img_orig.copy())

# Extract text
text_orig = pytesseract.image_to_string(img_orig, lang="eng")
text_proc = pytesseract.image_to_string(img_processed, lang="eng", config="--psm 6")

# Search for key patterns
print("KEY TEXT SEARCHES:")
print(f"'L64/305' in original: {'L64/305' in text_orig}")
print(f"'L64/305' in processed: {'L64/305' in text_proc}")
print(f"'COMTEN' in original: {'COMTEN' in text_orig}")
print(f"'COMTEN' in processed: {'COMTEN' in text_proc}")
print(f"'Taxable Total' in original: {'Taxable Total' in text_orig}")
print(f"'Taxable Total' in processed: {'Taxable Total' in text_proc}")
print(f"'7944' in original: {'7944' in text_orig}")
print(f"'7944' in processed: {'7944' in text_proc}")

# Show which addresses appear
print(f"\nAddress lines in original:")
for line in text_orig.split('\n'):
    if 'Police' in line or 'Coimbatore' in line or 'L64' in line:
        print(f"  {line}")

print(f"\nAddress lines in processed:")
for line in text_proc.split('\n'):
    if 'Police' in line or 'Coimbatore' in line or 'L64' in line:
        print(f"  {line}")
