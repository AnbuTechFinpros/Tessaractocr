import os
import re
import json
from typing import Dict, Any, List

import pytesseract
from PIL import Image, ImageOps, ImageFilter
import fitz  # PyMuPDF
import pandas as pd


# ================= CONFIG ================= #

INPUT_FOLDERS = ["invoice"]
OUTPUT_DIR = "output"

JSON_OUTPUT = os.path.join(OUTPUT_DIR, "result.json")
EXCEL_OUTPUT = os.path.join(OUTPUT_DIR, "result.xlsx")

SUPPORTED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


# ================= OCR ================= #

def preprocess_image(img: Image.Image) -> Image.Image:
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
    img = img.point(lambda x: 0 if x < 160 else 255, mode="1")
    return img


def ocr_image_to_text(img: Image.Image) -> str:
    img = preprocess_image(img)
    return pytesseract.image_to_string(img, lang="eng", config="--psm 6")


def ocr_pdf_to_text(path: str) -> str:
    doc = fitz.open(path)
    pages = []

    for page in doc:
        text = page.get_text().strip()
        if text:
            pages.append(text)
        else:
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pages.append(ocr_image_to_text(img))

    doc.close()
    return "\n".join(pages)


# ================= REGEX HELPER ================= #

def rx(text: str, pattern: Any) -> str:
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


# ================= VENDOR DETECTION ================= #

def detect_vendor(text: str, patterns: Dict[str, Dict[str, Any]]) -> str:
    for vendor, cfg in patterns.items():
        if vendor == "default":
            continue
        name_pat = cfg.get("supplier_name")
        if name_pat and re.search(name_pat, text, re.I | re.S):
            return vendor
    return "default"


# ================= HEADER EXTRACTION ================= #

def extract_header(text: str, vendor: str, patterns: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    pat = patterns.get(vendor, patterns.get("default", {}))

    return {
        "vendor": vendor,
        "invoice_number": rx(text, pat.get("invoice_number")),
        "invoice_date": rx(text, pat.get("invoice_date")),
        "supplier_name": rx(text, pat.get("supplier_name")),
        "supplier_gstin": rx(text, pat.get("supplier_gstin")),
        "supplier_pan": rx(text, pat.get("supplier_pan")),
        "supplier_address": rx(text, pat.get("supplier_address")),
        "supplier_phone_no": rx(text, pat.get("supplier_phone_no")),
        "supplier_email": rx(text, pat.get("supplier_email_id")),  # ✅ FIXED
        "account_holder_name": rx(text, pat.get("account_holder_name")),
        "account_number": rx(text, pat.get("account_number")),
        "ifsc_code": rx(text, pat.get("ifsc_code")),
        "taxable_total": rx(text, pat.get("taxable_total")),
        "cgst_total_amount": rx(text, pat.get("cgst_total_amount")),
        "sgst_total_amount": rx(text, pat.get("sgst_total_amount")),
        "igst_total_amount": rx(text, pat.get("igst_total_amount")),
        "grand_total": rx(text, pat.get("grand_total")),
    }


# ================= SMART ITEM EXTRACTION ================= #

def extract_items_smart(text: str) -> List[Dict[str, str]]:
    """
    Intelligent fallback extraction for ANY invoice layout.
    Detects item lines based on universal patterns: 
    Lines with text + numbers (HSN/item code, qty, price, amount, GST%)
    """
    items = []
    lines = text.split('\n')
    
    # Patterns to identify item lines (contains: 8-digit code, qty, price, amount)
    for line in lines:
        line = line.strip()
        if not line or len(line) < 20:
            continue
        
        # Skip header/footer lines
        if any(skip in line.upper() for skip in ['GSTIN', 'EMAIL', 'STATE', 'BANK', 'SUBJECT', 'TOTAL', 'TAXABLE', 'INVOICE', 'DATE', 'M/S', 'RUPEES', 'GRAND']):
            continue
        
        # Look for lines with: text + 8-digit HSN/code + qty + price + unit + gst + amount
        pattern = r'^[\s&:|,0-9/\\.]*(.{3,80}?)\s+([2-9]\d{7})\s+(\d+)\s+([0-9.]+)\s*[|:;]*\s*([A-Za-z}]{2,6})\s*[|:;]*\s*([0-9]{1,2})\s+([0-9,]+\\.\\d{2}|\\d+\\.\\d{2})'
        
        m = re.match(pattern, line, re.I)
        if m:
            try:
                row = {
                    "item_name": m.group(1).strip(),
                    "hsn_code": m.group(2).strip(),
                    "quantity": m.group(3).strip(),
                    "unit_price": m.group(4).strip(),
                    "unit": m.group(5).strip(),
                    "gst_rate": m.group(6).strip(),
                    "amount": m.group(7).strip(),
                    "HSN/SAC_type": "HSN",
                    "supply_type": "Goods",
                    "voucher_type": "Sales"
                }
                items.append(row)
            except:
                pass
    
    return items


# ================= SHRI SIVAAYAM SPECIAL EXTRACTION ================= #

def extract_items_shri_sivaayam(text: str) -> List[Dict[str, str]]:
    """
    Special extraction for Shri Sivaayam invoice format.
    Items are spread across multiple lines with specific pattern.
    """
    items = []
    lines = text.split('\n')
    
    i = 0
    item_count = 0
    max_items = 10  # Safety limit
    
    while i < len(lines) and item_count < max_items:
        line = lines[i].strip()
        
        # Look for line starting with item number (1-9) followed by description
        match = re.match(r'^(\d)\s+(.+?)$', line)
        if match and int(match.group(1)) <= 9:
            item_num = int(match.group(1))
            item_desc = match.group(2).strip()
            
            # Skip if this looks like a GST/tax line or all numbers/units
            if any(x in item_desc.upper() for x in ['CGST', 'SGST', 'IGST', 'TAX', 'TOTAL']):
                i += 1
                continue
            
            # Skip lines that are just "Nos", "Kgs", "Bags" etc (unit names)
            if item_desc.upper() in ['NOS', 'KGS', 'BAGS', 'NO.', 'KG', 'BAG']:
                i += 1
                continue
            
            # Extract HSN from the description if present
            hsn_from_desc = ""
            hsn_search = re.search(r'\((\d{8})\)', item_desc)
            if hsn_search:
                hsn_from_desc = hsn_search.group(1)
                item_name = item_desc[:hsn_search.start()].strip()
            else:
                item_name = item_desc
            
            # Collect fields from following lines
            quantity = ""
            unit = ""
            unit_price = ""
            amount = ""
            hsn_code = hsn_from_desc
            line_gst_rate = "9"
            found_qty = False
            found_amount = False
            
            # Look ahead for up to 12 lines
            for j in range(i + 1, min(i + 13, len(lines))):
                next_line = lines[j].strip()
                if not next_line:
                    continue
                
                # Stop if we hit the totals/GST section (lines with just numbers and CGST/SGST)
                if re.match(r'^(CGST|SGST|IGST|Total|Taxable)', next_line, re.I):
                    break
                
                # Stop if we find the next item number
                if re.match(r'^(\d)\s+', next_line) and int(next_line[0]) > item_num:
                    break
                
                # Skip GST/TAX lines
                if any(x in next_line.upper() for x in ['CGST', 'SGST', 'IGST']):
                    continue
                
                # Extract 8-digit HSN code (usually alone on a line)
                if re.match(r'^\d{8}$', next_line) and not hsn_code:
                    hsn_code = next_line
                    continue
                
                # Extract quantity with unit (e.g., "135.20 Kgs" or "50 Bags" or "1 Nos")
                qty_match = re.search(r'(\d+(?:\.\d+)?)\s+(Kgs|Bags|Nos)', next_line, re.I)
                if qty_match and not found_qty:
                    quantity = qty_match.group(1)
                    unit = qty_match.group(2)
                    found_qty = True
                    continue
                
                # Check for GST info (e.g., "Charges @ 18%")
                if "@" in next_line and "%" in next_line and not found_qty:
                    gst_match = re.search(r'@\s*(\d+)%', next_line)
                    if gst_match:
                        line_gst_rate = gst_match.group(1)
                    # Append to item name only if it's part of the description
                    item_name = (item_name + " " + next_line).strip()
                    continue
                
                # Extract decimal numbers (rates/amounts)
                # Skip lines that are purely numeric or GST-like
                if re.search(r'[A-Za-z]', next_line):  # Has letters, skip pure number lines
                    continue
                    
                decimals = re.findall(r'[\d,]+\.\d{2}', next_line)
                if len(decimals) >= 1 and not found_amount:
                    # Clean decimals
                    cleaned = [d.replace(',', '') for d in decimals]
                    if quantity and len(cleaned) >= 2:
                        # Has quantity: first is per-unit, second is total amount
                        if not unit_price:
                            unit_price = cleaned[0]
                        if not amount:
                            amount = cleaned[-1]  # Last one is usually the amount
                        found_amount = True
                    elif not quantity and len(cleaned) >= 1:
                        # No quantity: single decimal is the amount
                        amount = cleaned[0]
                        found_amount = True
            
            # Add item if we have meaningful data
            if item_name.strip() and (hsn_code or quantity or amount):
                items.append({
                    "item_name": item_name.strip(),
                    "hsn_code": hsn_code,
                    "quantity": quantity,
                    "unit": unit,
                    "unit_price": unit_price,
                    "amount": amount,
                    "gst_rate": line_gst_rate,
                    "HSN/SAC_type": "HSN",
                    "supply_type": "Goods",
                    "voucher_type": "Sales"
                })
                item_count += 1
        
        i += 1
    
    return items


# ================= ITEM EXTRACTION ================= #

def extract_items_rk_security(text: str) -> List[Dict[str, str]]:
    """Custom extractor for RK Security Services invoices"""
    items = []
    
    # First, get only the service details section
    service_section_start = text.find("Service Details")
    service_section_end = text.find("Total", service_section_start)
    
    if service_section_start > -1 and service_section_end > -1:
        service_section = text[service_section_start:service_section_end]
        
        # Pattern: S.No | Service type | (Nos) | Rate | Man days | Amount
        # Matches: "1 Security Officer (2 Nos) 29000 53.00 51,233"
        officer_pattern = r"(\d)\s+Security\s+Officer\s+\([^)]*\)\s+(\d+)\s+([\d.]+)\s+([0-9,]+)"
        for match in re.finditer(officer_pattern, service_section, re.IGNORECASE | re.DOTALL):
            sno, rate, man_days, amount = match.groups()
            items.append({
                "item_name": "Security Officer",
                "hsn_code": "998522",  # SAC code for security services
                "quantity": man_days,
                "unit": "Man days",
                "unit_price": rate,
                "amount": amount.replace(',', ''),
                "gst_rate": "18",
                "HSN/SAC_type": "SAC",
                "supply_type": "Services",
                "voucher_type": "Sales"
            })
        
        # Pattern for Security Guard
        guard_pattern = r"(\d)\s+Security\s+Guard\s+\([^)]*\)\s+(\d+)\s+([\d.]+)\s+([0-9,]+)"
        for match in re.finditer(guard_pattern, service_section, re.IGNORECASE | re.DOTALL):
            sno, rate, man_days, amount = match.groups()
            items.append({
                "item_name": "Security Guard",
                "hsn_code": "998522",  # SAC code for security services
                "quantity": man_days,
                "unit": "Man days",
                "unit_price": rate,
                "amount": amount.replace(',', ''),
                "gst_rate": "18",
                "HSN/SAC_type": "SAC",
                "supply_type": "Services",
                "voucher_type": "Sales"
            })
    
    return items


def extract_items(text: str, vendor: str, patterns: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    pat = patterns.get(vendor, {})
    items = []

    # Special handling for specific vendors
    if vendor == "shri_sivaayam_traders":
        items = extract_items_shri_sivaayam(text)
    elif vendor == "rk_security_services":
        items = extract_items_rk_security(text)
    else:
        for rule in pat.get("item_patterns", []):
            # Use appropriate flags based on vendor
            flags = re.I | re.M  # Use re.M for multiline matching
            if vendor != "shine_traders":  # For other vendors, use re.S if needed
                flags |= re.S
            
            for m in re.finditer(rule["regex"], text, flags):
                row = {}
                for k, v in rule["mapping"].items():
                    row[k] = m.group(v) if isinstance(v, int) else v
                items.append(row)

    # Fallback: If no items found with vendor patterns, try smart extraction
    if not items:
        items = extract_items_smart(text)
    
    return items


# ================= FILE PROCESS ================= #

def process_file(path: str, patterns: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_EXT:
        return []

    text = ocr_pdf_to_text(path) if ext == ".pdf" else ocr_image_to_text(Image.open(path))
    vendor = detect_vendor(text, patterns)

    header = extract_header(text, vendor, patterns)
    items = extract_items(text, vendor, patterns)

    if items:
        return [{**header, **item, "file_name": os.path.basename(path)} for item in items]
    else:
        # If no items extracted, still output the header with empty item fields
        default_item = {
            "item_name": "",
            "hsn_code": "",
            "quantity": "",
            "unit": "",
            "unit_price": "",
            "amount": "",
            "gst_rate": "",
            "HSN/SAC_type": "",
            "supply_type": "",
            "voucher_type": "",
            "cgst_amount": "",
            "sgst_amount": "",
            "igst_amount": ""
        }
        return [{**header, **default_item, "file_name": os.path.basename(path)}]


# ================= POST PROCESSING ================= #

def clean_number(value: str) -> float:
    """Clean and convert string numbers to float"""
    if not value or not str(value).strip():
        return 0.0
    try:
        # Remove commas, spaces and convert
        cleaned = str(value).replace(',', '').replace(' ', '').strip()
        return float(cleaned) if cleaned else 0.0
    except:
        return 0.0


def post_process(rows: List[Dict[str, Any]]) -> None:
    """Enhanced post-processing with stronger calculations and validation"""
    for r in rows:
        # 1. Clean number fields
        for field in ['taxable_total', 'cgst_total_amount', 'sgst_total_amount', 
                      'igst_total_amount', 'grand_total', 'amount', 'unit_price']:
            if field in r and r[field]:
                try:
                    r[field] = str(clean_number(r[field]))
                except:
                    pass
        
        # 2. PAN from GSTIN fallback
        if not r.get("supplier_pan") and r.get("supplier_gstin"):
            gstin = r.get("supplier_gstin", "")
            if len(gstin) >= 10:
                r["supplier_pan"] = gstin[2:12]
        
        # 3. Strong GST and amount calculations
        amt_raw = r.get("amount", "")
        rate = float(r.get("gst_rate", 0) or 0)
        
        if amt_raw and rate > 0:
            try:
                amt = clean_number(amt_raw)
                if amt > 0:
                    gst_total = amt * rate / 100
                    # Check if IGST or CGST+SGST
                    if r.get("supply_type", "").upper() in ["GOODS", "SERVICES"]:
                        # Default to CGST+SGST if not specified
                        if not r.get("igst_total_amount") or clean_number(r.get("igst_total_amount", 0)) == 0:
                            r["cgst_amount"] = f"{gst_total/2:.2f}"
                            r["sgst_amount"] = f"{gst_total/2:.2f}"
                            r["igst_amount"] = "0"
                        else:
                            r["igst_amount"] = f"{gst_total:.2f}"
                            r["cgst_amount"] = "0"
                            r["sgst_amount"] = "0"
                    else:
                        r["cgst_amount"] = f"{gst_total/2:.2f}"
                        r["sgst_amount"] = f"{gst_total/2:.2f}"
                        r["igst_amount"] = "0"
            except Exception as e:
                r["cgst_amount"] = r.get("cgst_amount", "")
                r["sgst_amount"] = r.get("sgst_amount", "")
                r["igst_amount"] = r.get("igst_amount", "")
        else:
            # Keep existing values if no amount/rate
            if not r.get("cgst_amount"):
                r["cgst_amount"] = ""
            if not r.get("sgst_amount"):
                r["sgst_amount"] = ""
            if not r.get("igst_amount"):
                r["igst_amount"] = ""
        
        # 4. Ensure all required fields exist
        required_fields = [
            "vendor", "invoice_number", "invoice_date", "supplier_name", "supplier_gstin",
            "supplier_pan", "supplier_address", "supplier_phone_no", "supplier_email",
            "account_holder_name", "account_number", "ifsc_code", "taxable_total",
            "cgst_total_amount", "sgst_total_amount", "igst_total_amount", "grand_total",
            "item_name", "hsn_code", "quantity", "unit", "unit_price", "amount",
            "gst_rate", "HSN/SAC_type", "supply_type", "voucher_type",
            "cgst_amount", "sgst_amount", "igst_amount", "file_name"
        ]
        
        for field in required_fields:
            if field not in r:
                r[field] = ""
        
        # 5. Trim whitespace from all string fields
        for k, v in r.items():
            if isinstance(v, str):
                r[k] = v.strip()


# ================= MAIN ================= #

def main():
    print("🔥 RUNNING OCR INVOICE ENGINE 🔥")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open("patterns.json", "r", encoding="utf-8") as f:
        patterns = json.load(f)

    all_rows = []

    for root, dirs, files in os.walk('.'):
        if 'output' in root or 'inv_x' in root:
            continue
        for file in files:
            all_rows.extend(process_file(os.path.join(root, file), patterns))

    post_process(all_rows)

    # JSON output
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"Data": all_rows}, f, indent=2)

    # Excel output
    if all_rows:
        pd.DataFrame(all_rows).to_excel(EXCEL_OUTPUT, index=False)

    print("EXTRACTION COMPLETE")
    print(f" JSON  : {JSON_OUTPUT}")
    print(f" EXCEL : {EXCEL_OUTPUT}")


if __name__ == "__main__":
    main()
