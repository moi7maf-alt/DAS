import re
html = open('src/index.html', encoding='utf-8').read()
tabs = ['overview', 'sectors', 'budget', 'predictive', 'alignment', 'report']
removed = ['projects', 'trends', 'solutions']
for t in tabs:
    pattern = re.escape(t) + "'"
    c = len(re.findall(pattern, html))
    print(f'  {t}: {c} buttons (should be 12)')
for t in removed:
    pattern = re.escape(t) + "'"
    c = len(re.findall(pattern, html))
    print(f'  {t}: {c} buttons (should be 0)')
cc = html.count('chat-container')
print(f'  chat containers: {cc} (should be 12)')
oc = html.count('توليد التقرير')
print(f'  old report style (توليد التقرير): {oc} (should be 0)')
