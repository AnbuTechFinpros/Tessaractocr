import json
with open('output/result.json', 'r') as f:
    data = json.load(f)
    first_row = data['Data'][0]
    print('Key values:')
    print(f"taxable_total:  '{first_row.get('taxable_total')}'")
    print(f"cgst_total_amount: '{first_row.get('cgst_total_amount')}'")
    print(f"sgst_total_amount: '{first_row.get('sgst_total_amount')}'")
    print(f"grand_total: '{first_row.get('grand_total')}'")
    
    # Calculate what it should be
    try:
        taxable = float(first_row.get('taxable_total') or 0)
        cgst = float(first_row.get('cgst_total_amount') or 0)
        sgst = float(first_row.get('sgst_total_amount') or 0)
        print(f"\nCalculated total: {taxable + cgst + sgst}")
    except Exception as e:
        print(f"Error calculating: {e}")
