import json
import codecs

path = r'c:\Users\acer\Documents\final research\datasets\Dataset1.json'
with codecs.open(path, 'r', 'utf-16le') as f:
    text = f.read().lstrip('\ufeff')
    data = json.loads(text)

with open('dataset1_obj_utf8.txt', 'w', encoding='utf-8') as out:
    out.write(json.dumps(data[0], indent=2))
