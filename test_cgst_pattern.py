import re

line = '| CGST 9.00% for 5,844.00 = 525.96'

pattern = r'(?is)\|?\s*CGST\s+9\.00%\s+for\s+[0-9,]+\.00\s*=\s*([0-9,]+\.\d{2})'
m = re.search(pattern, line)
if m:
    print(f"Match found: {m.group(1)}")
else:
    print("No match")
    
# Try simpler pattern
pattern = r'CGST.*?([0-9]+\.[0-9]{2})$'
m = re.search(pattern, line)
if m:
    print(f"Simple pattern match: {m.group(1)}")
