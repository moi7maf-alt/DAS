import json, sys
sys.stdout.reconfigure(encoding='utf-8')

data = json.load(open('src/data.json', encoding='utf-8'))
plans = json.load(open('src/strategic_plans.json', encoding='utf-8'))

html = open('src/index.html', encoding='utf-8').read()

TABS_TO_REMOVE = ['projects', 'trends', 'solutions']
ALL_TAB_IDS = ['overview', 'sectors', 'projects', 'budget', 'predictive', 'trends', 'solutions', 'alignment', 'report']

def remove_tab_section(html, gov_name, tab_id):
    tag = f'id="tab-{gov_name}-{tab_id}"'
    idx = html.find(tag)
    if idx == -1:
        return html
    start = idx
    while start > 0 and html[start] != '<':
        start -= 1
    search_from = idx + len(tag)
    candidates = []
    for tid in ALL_TAB_IDS:
        pat = f'id="tab-{gov_name}-{tid}"'
        pos = html.find(pat, search_from)
        if pos != -1:
            candidates.append(pos)
    ep = html.find(f'<!-- END_PANEL_{gov_name} -->', search_from)
    if ep != -1:
        candidates.append(ep)
    if not candidates:
        return html
    end = min(candidates)
    # Walk back to the '<' of the next tab's opening tag to avoid eating its <div class="tc"
    while end > 0 and html[end] != '<':
        end -= 1
    return html[:start] + html[end:]

# ===== STEP 1: Remove unwanted tab sections =====
for g in data['governorates']:
    name = g['name']
    for tab_id in TABS_TO_REMOVE:
        html = remove_tab_section(html, name, tab_id)

print(f'Removed {TABS_TO_REMOVE} tab sections')

# ===== STEP 2: Remove unwanted tab buttons =====
for g in data['governorates']:
    name = g['name']
    # Remove all variants of unwanted tab buttons (with/without ,this)
    html = html.replace(f'<button class="tb" onclick="switchTab(\'{name}\',\'projects\',this)">🔧 المشاريع المقترحة</button>', '')
    html = html.replace(f'<button class="tb" onclick="switchTab(\'{name}\',\'projects\')">🔧 المشاريع المقترحة</button>', '')
    html = html.replace(f'<button class="tb" onclick="switchTab(\'{name}\',\'trends\')">📊 اتجاهات القطاعات</button>', '')
    html = html.replace(f'<button class="tb" onclick="switchTab(\'{name}\',\'solutions\')">🚀 الحلول الذكية</button>', '')

print('Removed unwanted tab buttons')

open('src/index.html', 'w', encoding='utf-8').write(html)
import os
size = os.path.getsize('src/index.html')
print(f'Tab removal complete. Final size: {size/1024:.1f} KB')
