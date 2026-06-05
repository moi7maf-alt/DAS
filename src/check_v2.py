import json, sys
sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open('src/data.json', encoding='utf-8'))
print('=== RANKING ===')
ranking = sorted(d['governorates'], key=lambda g: -g['composite_index'])
for i, g in enumerate(ranking, 1):
    secs = g['sectors']
    avg_s = sum(s['score'] for s in secs.values()) / len(secs)
    print(f'{i}. {g["name"]}: composite={g["composite_index"]:.1f} | sec_avg={avg_s:.1f} | adv={g["adv_sectors"]} beh={g["beh_sectors"]}')

print()
print('=== SECTOR SCORES ===')
names = [g['name'] for g in d['governorates']]
secs_order = list(d['governorates'][0]['sectors'].keys())
print(f'{"Gov":<10}', end='')
for s in secs_order:
    print(f'{s:<12}', end='')
print()
for g in d['governorates']:
    print(f'{g["name"]:<10}', end='')
    for s in secs_order:
        sc = g['sectors'][s]['score']
        print(f'{sc:<12.1f}', end='')
    print()
print()
print('=== NATIONAL AVERAGES ===')
for s, v in d['national_averages'].items():
    print(f'{s}: {v}')
print(f'Composite: avg={d["composite_index"]["national_avg"]}, std={d["composite_index"]["national_std"]}')
