import zipfile
import xml.etree.ElementTree as ET
import sys
import json

try:
    z = zipfile.ZipFile(r'c:\Users\DELL\OneDrive\Desktop\synthetix 4.0\customer_support_ticket_triage_report (1).docx')
    xml_content = z.read('word/document.xml')
    tree = ET.fromstring(xml_content)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    texts = [node.text for node in tree.findall('.//w:t', namespaces=ns) if node.text]

    with open('output.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(texts))
    print("SUCCESS")
except Exception as e:
    print("ERROR:", e)
