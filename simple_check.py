import json
data = json.load(open('output/result.json'))
print(len(data['Data']))
print(data['Data'][0]['file_name'])
print(data['Data'][0]['invoice_number'])
print(data['Data'][0]['invoice_date'])
print(data['Data'][0]['cgst_total_amount'])
print(data['Data'][0]['supplier_address'])
