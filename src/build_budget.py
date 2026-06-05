# budget module builder

import json

data = json.load(open('src/data.json', encoding='utf-8'))
plans = json.load(open('src/strategic_plans.json', encoding='utf-8'))

# ===== SECTOR PACKAGES =====
# Map each sector to one of 3 packages
PACKAGES = {
    'البنية التحتية': {
        'name': 'حزمة البنية التحتية',
        'icon': '🏗️',
        'color': '#8b5cf6',
        'sectors': ['البنية التحتية', 'المياه والصرف الصحي'],
        'desc': 'الطرق، الشبكات، المياه، الصرف الصحي'
    },
    'الخدمات': {
        'name': 'الحزمة الخدمية',
        'icon': '🏥',
        'color': '#3b82f6',
        'sectors': ['التعليم', 'الصحة', 'الثقافة', 'التنمية الاجتماعية'],
        'desc': 'التعليم، الصحة، الثقافة، التنمية الاجتماعية'
    },
    'الإنتاج': {
        'name': 'الحزمة الإنتاجية',
        'icon': '🌾',
        'color': '#22c55e',
        'sectors': ['الزراعة', 'السياحة'],
        'desc': 'الزراعة، السياحة'
    },
}

def compute_budget_allocation(gov_data):
    """
    Compute optimal budget allocation based on gap analysis.
    Sectors with bigger negative gaps get higher priority.
    Returns allocation percentages per package.
    """
    sectors = gov_data['sectors']

    # Compute priority score per package
    # Priority = sum of absolute negative gaps in package sectors
    package_priority = {}
    package_gap_details = {}

    for pkg_key, pkg in PACKAGES.items():
        total_gap = 0
        gap_details = []
        for sec in pkg['sectors']:
            if sec in sectors:
                gap = sectors[sec]['gap']
                score = sectors[sec]['score']
                status = sectors[sec]['status']
                # Negative gap = needs investment
                # Positive gap = can leverage (lower priority but still gets share)
                priority_weight = max(0, -gap) * 2 + max(0, gap) * 0.3
                total_gap += priority_weight
                gap_details.append({
                    'sector': sec,
                    'score': score,
                    'gap': gap,
                    'status': status,
                    'weight': priority_weight
                })
        package_priority[pkg_key] = total_gap
        package_gap_details[pkg_key] = gap_details

    # Normalize to percentages (minimum 15% per package)
    total = sum(package_priority.values())
    if total == 0:
        alloc = {k: 33.33 for k in PACKAGES}
    else:
        raw = {k: (v / total) * 100 for k, v in package_priority.items()}
        # Apply minimum 15% floor
        MIN_PCT = 15
        floored = {k: max(MIN_PCT, v) for k, v in raw.items()}
        # Re-normalize after floor
        total2 = sum(floored.values())
        alloc = {k: round(v / total2 * 100, 1) for k, v in floored.items()}

    return alloc, package_gap_details

# Build budget data for all governorates
budget_data = {}
for g in data['governorates']:
    name = g['name']
    alloc, gap_details = compute_budget_allocation(g)
    budget_2026 = g['budget_2026']

    # Build justifications per package
    justifications = {}
    for pkg_key, details in gap_details.items():
        pkg = PACKAGES[pkg_key]
        behind = [d for d in details if d['status'] == 'متأخر']
        advanced = [d for d in details if d['status'] == 'متقدم']
        avg_score = sum(d['score'] for d in details) / len(details) if details else 0

        if behind:
            just = f"تعاني {len(behind)} قطاع(ات) من فجوة سلبية: " + \
                   "، ".join([f"{d['sector']} ({d['gap']:+.1f})" for d in behind])
        elif advanced:
            just = f"قطاعات متقدمة يمكن تعزيزها: " + \
                   "، ".join([f"{d['sector']} (+{d['gap']:.1f})" for d in advanced])
        else:
            just = "قطاعات في المستوى المتوسط تحتاج دعماً للارتقاء"

        justifications[pkg_key] = just

    budget_data[name] = {
        'allocation_pct': alloc,
        'gap_details': gap_details,
        'justifications': justifications,
        'budget_2026': budget_2026
    }

# Save budget data
with open('src/budget_data.json', 'w', encoding='utf-8') as f:
    json.dump({'packages': PACKAGES, 'governorates': budget_data}, f, ensure_ascii=False, indent=2)

print('Budget data saved to src/budget_data.json')
print('Governorates processed:', len(budget_data))
