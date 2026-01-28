import json
with open('output/result.json', 'r') as f:
    data = json.load(f)
    total_rows = len(data['Data'])
    print(f'Total rows: {total_rows}')
    print(f'\nFirst 3 rows (files):')
    for i in range(min(3, len(data['Data']))):
        row = data['Data'][i]
        print(f"  {i}: {row.get('file_name')} - {row.get('vendor')}")
    
    print(f'\nLast 3 rows (files):')
    for i in range(max(0, len(data['Data'])-3), len(data['Data'])):
        row = data['Data'][i]
        print(f"  {i}: {row.get('file_name')} - {row.get('vendor')}")
