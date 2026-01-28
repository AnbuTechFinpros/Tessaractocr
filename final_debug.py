#!/usr/bin/env python
"""Debug extraction flow for Shine Traders invoice"""

import os
import re
import json
from typing import Dict, Any, List

import pytesseract
from PIL import Image
import fitz

# Load patterns
with open("patterns.json", "r", encoding="utf-8") as f:
    patterns = json.load(f)

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

def detect_vendor(text: str, patterns: Dict[str, Dict[str, Any]]) -> str:
    for vendor, cfg in patterns.items():
        if vendor == "default":
            continue
        name_pat = cfg.get("supplier_name")
        if name_pat and re.search(name_pat, text, re.I | re.S):
            return vendor
    return "default"

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
            pages.append(pytesseract.image_to_string(img, lang="eng"))
    doc.close()
    return "\n".join(pages)

def extract_header(text: str, vendor: str, patterns: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    pat = patterns.get(vendor, patterns.get("default", {}))
    result = {
        "vendor": vendor,
        "invoice_number": rx(text, pat.get("invoice_number")),
        "invoice_date": rx(text, pat.get("invoice_date")),
        "supplier_name": rx(text, pat.get("supplier_name")),
        "supplier_gstin": rx(text, pat.get("supplier_gstin")),
        "supplier_pan": rx(text, pat.get("supplier_pan")),
        "supplier_address": rx(text, pat.get("supplier_address")),
        "supplier_phone_no": rx(text, pat.get("supplier_phone_no")),
        "supplier_email": rx(text, pat.get("supplier_email_id")),
        "account_holder_name": rx(text, pat.get("account_holder_name")),
        "account_number": rx(text, pat.get("account_number")),
        "ifsc_code": rx(text, pat.get("ifsc_code")),
        "buyer_name": rx(text, pat.get("buyer_name")),
        "buyer_gstin": rx(text, pat.get("buyer_gstin")),
        "taxable_total": rx(text, pat.get("taxable_total")),
        "cgst_total_amount": rx(text, pat.get("cgst_total_amount")),
        "sgst_total_amount": rx(text, pat.get("sgst_total_amount")),
        "igst_total_amount": rx(text, pat.get("igst_total_amount")),
        "grand_total": rx(text, pat.get("grand_total")),
    }
    return result

# Process invoice
text = ocr_pdf_to_text("invoice/Shine Traders Bill [08.03.2024].pdf")
vendor = detect_vendor(text, patterns)
header = extract_header(text, vendor, patterns)

print(f"Vendor: {vendor}")
print("\n=== Header Fields ===")
for k, v in sorted(header.items()):
    status = "✅" if v else "❌"
    print(f"{status} {k:25} = {str(v)[:50]}")
