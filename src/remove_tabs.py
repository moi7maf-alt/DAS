"""
remove_tabs.py — removes specified tabs and their JS code from index.html.
Removes: تقرير المحافظة, موائمة المشاريع, اتجاهات القطاعات
"""

import re, os

html_path = os.path.join(os.path.dirname(__file__), 'index.html')
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1) Remove tab buttons: <button class="tb" onclick="switchTab('...','{tab}')"...>
for tab in ['report', 'alignment', 'trends']:
    pat = r'<button\s+class="tb"[^>]*onclick="switchTab\([^)]*,\'' + re.escape(tab) + r'\'[^)]*\)[^>]*>.*?</button>'
    html = re.sub(pat, '', html)

# 2) Remove tab content panels using tag-depth matching
def remove_panel(html, tab_id):
    """Remove a div with id='tab-...-{tab_id}' including all nested content."""
    out_lines = []
    in_panel = False
    depth = 0
    for line in html.split('\n'):
        # Detect opening of target panel
        if f'id="tab-' in line and f'-{tab_id}"' in line:
            in_panel = True
            depth = 0
        if in_panel:
            # Count opening and closing div tags on this line
            opens = line.count('<div') - line.count('</div>')
            # Handle self-closing divs
            opens -= line.count('<div ')
            if line.count('<div ')>0 or line.count('<div>')>0 or line.count('<div\t')>0:
                pass
            # Actually simpler: count all openings and closings
            depth += line.count('<div ') + line.count('<div>') + line.count('<div\t') + line.count('<div\n')
            depth -= line.count('</div>')
            if depth <= 0 and not any(x in line for x in ['<div ','<div>','<div\t']):
                pass
            if depth <= 0 and depth + (line.count('<div ') + line.count('<div>')) > 0:
                pass
            # If we've closed back to depth 0 and we're past the opening line, stop
            if depth <= 0 and in_panel:
                # Check if this line closes the panel
                in_panel = False
                continue
            continue
        out_lines.append(line)
    return '\n'.join(out_lines)

# Simpler approach: match from opening tag to next tab panel or end marker
def remove_tab_panel(html, tab_id):
    """Remove tab panel div by matching opening tag to next tab/panel boundary."""
    # Match: <div class="tc ..." id="tab-...-{tab_id}"...> ...content... </div>
    # The content may contain nested divs, so we match until we hit:
    #   - the next <div class="tc" (next tab panel start)
    #   - or <!-- END_PANEL_ (end of all panels for this governorate)
    #   - or a standalone </div> that's NOT inside the panel
    # 
    # Better approach: use a stack-based removal
    
    result = []
    i = 0
    lines = html.split('\n')
    while i < len(lines):
        line = lines[i]
        # Check if this line opens a tab panel we want to remove
        if f'id="tab-' in line and f'-{tab_id}"' in line and 'class="tc' in line:
            # Skip until we find the matching closing </div>
            depth = 0
            # Count divs on the opening line
            depth += line.count('<div ')
            depth += line.count('<div>')
            depth -= line.count('</div>')
            i += 1
            while i < len(lines) and depth > 0:
                depth += lines[i].count('<div ')
                depth += lines[i].count('<div>')
                depth += lines[i].count('<div\t')
                depth -= lines[i].count('</div>')
                i += 1
            continue
        result.append(line)
        i += 1
    return '\n'.join(result)

for tab in ['report', 'alignment', 'trends']:
    html = remove_tab_panel(html, tab)

# 3) Remove JS modules
html = re.sub(
    r'\n// ===== ALIGNMENT MODULE =====.*?(?=\n</script>\n</body>)',
    '',
    html,
    flags=re.DOTALL,
)
html = re.sub(
    r'\n// ===== REPORT MODULE =====.*?(?=\n// ===== ALIGNMENT MODULE|\n</script>\n</body>)',
    '',
    html,
    flags=re.DOTALL,
)

# 4) Clean up triple+ blank lines
html = re.sub(r'\n{4,}', '\n\n\n', html)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Removed tabs: report, alignment, trends')
print(f'Final size: {os.path.getsize(html_path)/1024:.1f} KB')
