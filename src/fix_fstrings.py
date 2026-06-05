# -*- coding: utf-8 -*-
# Fix f-strings that have ctx.get() with unicode escapes inside them
import re

with open('src/build_predictive2.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
new_lines = []
fixes = []

for i, line in enumerate(lines):
    stripped = line.strip()
    # Check if line has ctx.get inside an f-string
    if stripped.startswith("f'") and 'ctx.get(' in stripped:
        # Find all ctx.get(...) calls with unicode escapes in default values
        # Pattern: ctx.get("key", "\uXXXX...")
        matches = list(re.finditer(r"ctx\.get\(\"(\w+)\",\s*\"((?:\\u[0-9a-fA-F]{4})+)\"\)", stripped))
        for m in matches:
            key = m.group(1)
            default_raw = m.group(2)
            # Decode the unicode escapes
            default_str = default_raw.encode('utf-8').decode('unicode_escape')
            fixes.append((i+1, key, default_raw, default_str))
            # Replace the ctx.get() with the variable name
            var_name = f'ctx_{key}'
            new_line = stripped.replace(m.group(0), var_name)
            # Add the variable definition before the line
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(f'{indent}{var_name} = ctx.get("{key}", "{default_str}")')
            new_lines.append(f'{indent}{new_line}')
            break  # Only fix first match per line for simplicity
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open('src/build_predictive2.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print(f'Fixed {len(fixes)} lines:')
for ln, key, raw, decoded in fixes:
    print(f'  Line {ln}: ctx.get("{key}", ...) -> ctx_{key}')
