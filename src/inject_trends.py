# inject_trends.py — حقن تبويب اتجاهات القطاعات

import json

data = json.load(open('src/data.json', encoding='utf-8'))
pred = json.load(open('src/predictive_data.json', encoding='utf-8'))

html = open('src/index.html', encoding='utf-8').read()

# ===== STEP 1: Add tab button after predictive tab =====
for g in data['governorates']:
    name = g['name']
    old_btn = f'onclick="switchTab(\'{name}\',\'predictive\')">🔮 التحليل التنبؤي</button>'
    new_btn = (f'onclick="switchTab(\'{name}\',\'predictive\')">🔮 التحليل التنبؤي</button>\n'
               f'<button class="tb" onclick="switchTab(\'{name}\',\'trends\')">📊 اتجاهات القطاعات</button>')
    html = html.replace(old_btn, new_btn)

print('Trends tab buttons injected')

# ===== STEP 2: Build trends tab HTML per governorate =====
trend_tabs = {}

TREND_ICON_MAP = {
    'تراجع_حاد': '🔽',
    'تراجع_معتدل': '🔽',
    'مستقر': '➡️',
    'تحسن_تدريجي': '🔼',
    'تحسن_ملحوظ': '🔼',
}

TREND_COLORS = {
    'تراجع_حاد':    '#ef4444',
    'تراجع_معتدل':  '#f97316',
    'مستقر':        '#f59e0b',
    'تحسن_تدريجي':  '#22c55e',
    'تحسن_ملحوظ':   '#16a34a',
}

TREND_BG = {
    'تراجع_حاد':    '#fef2f2',
    'تراجع_معتدل':  '#fff7ed',
    'مستقر':        '#fffbeb',
    'تحسن_تدريجي':  '#f0fdf4',
    'تحسن_ملحوظ':   '#f0fdf4',
}

for g in data['governorates']:
    name = g['name']
    gov_pred = pred['governorates'].get(name, {})
    indicators = gov_pred.get('indicators', {})
    recommendations = gov_pred.get('recommendations', [])

    # Group indicators by sector
    sectors = {}
    for ind_key, ind in indicators.items():
        sec = ind.get('sector', 'أخرى')
        if sec not in sectors:
            sectors[sec] = []
        sectors[sec].append(ind)

    h = []
    h.append(f'<div class="tc" id="tab-{name}-trends">')
    h.append('<div class="cg">')

    # Description
    h.append(f'''<div style="background:linear-gradient(135deg,#ecfdf5,#f0fdf4);border-radius:10px;padding:14px 18px;margin-bottom:16px;border-right:4px solid #10b981;display:flex;gap:12px;align-items:flex-start">
<span style="font-size:20px">📊</span>
<div>
<div style="font-size:13px;font-weight:700;color:#065f46;margin-bottom:4px">اتجاهات القطاعات — تحليل الأداء التنموي</div>
<div style="font-size:12px;color:#374151;line-height:1.7">تصنف المؤشرات حسب القطاع وتظهر اتجاهاتها <strong style="color:#16a34a">🔼 صعوداً</strong> أو <strong style="color:#ef4444">🔽 هبوطاً</strong> أو <strong style="color:#f59e0b">➡️ استقراراً</strong>. لكل قطاع بطاقة خاصة تجمع مؤشراتها مع حلول مقترحة للقطاعات المتراجعة وتعزيز للقطاعات الإيجابية.</div>
</div>
</div>''')

    # Summary legend
    h.append(f'''<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">
<div style="display:flex;align-items:center;gap:4px;background:#f0fdf4;padding:4px 10px;border-radius:20px;font-size:11px">
  <span style="font-size:14px">🔼</span> <span style="color:#16a34a;font-weight:600">تحسن</span>
</div>
<div style="display:flex;align-items:center;gap:4px;background:#fef2f2;padding:4px 10px;border-radius:20px;font-size:11px">
  <span style="font-size:14px">🔽</span> <span style="color:#ef4444;font-weight:600">تراجع</span>
</div>
<div style="display:flex;align-items:center;gap:4px;background:#fffbeb;padding:4px 10px;border-radius:20px;font-size:11px">
  <span style="font-size:14px">➡️</span> <span style="color:#f59e0b;font-weight:600">مستقر</span>
</div>
</div>''')

    # Sector trend cards in grid
    sector_order = ['التعليم', 'الصحة', 'الزراعة', 'المياه والصرف الصحي', 'الثقافة', 'السياحة', 'البنية التحتية', 'التنمية الاجتماعية']
    sorted_sectors = sorted(sectors.keys(), key=lambda s: sector_order.index(s) if s in sector_order else 99)

    for sec in sorted_sectors:
        inds = sectors[sec]
        # Calculate sector trend: majority vote
        up = sum(1 for i in inds if i.get('trend_class','') in ('تحسن_ملحوظ','تحسن_تدريجي'))
        down = sum(1 for i in inds if i.get('trend_class','') in ('تراجع_حاد','تراجع_معتدل'))
        stable = len(inds) - up - down

        if up > down and up >= stable:
            sec_icon = '🔼'
            sec_color = '#16a34a'
            sec_bg = '#f0fdf4'
            sec_border = '#86efac'
            sec_label = 'إيجابي'
        elif down > up and down > stable:
            sec_icon = '🔽'
            sec_color = '#ef4444'
            sec_bg = '#fef2f2'
            sec_border = '#fca5a5'
            sec_label = 'تراجع'
        else:
            sec_icon = '➡️'
            sec_color = '#f59e0b'
            sec_bg = '#fffbeb'
            sec_border = '#fde68a'
            sec_label = 'مستقر'

        h.append(f'''<div class="card fw" style="border-right:4px solid {sec_color}">
<div class="ct" style="display:flex;align-items:center;gap:8px">
  <span style="font-size:18px">{sec_icon}</span>
  <span>{sec}</span>
  <span style="margin-right:auto;background:{sec_bg};color:{sec_color};padding:2px 10px;border-radius:12px;font-size:10px;font-weight:700;border:1px solid {sec_border}">{sec_label}</span>
  <span style="font-size:10px;color:#6b7280">{len(inds)} مؤشر(ات)</span>
</div>
<div style="overflow-x:auto">
<table class="pt" style="font-size:11px;margin-top:6px">
<tr><th>المؤشر</th><th>القيمة</th><th>المتوسط</th><th>الفجوة</th><th>الاتجاه</th><th>توقع 2028</th></tr>''')
        for ind in inds:
            tc = ind.get('trend_class', 'مستقر')
            ti = TREND_ICON_MAP.get(tc, '➡️')
            tc_color = TREND_COLORS.get(tc, '#6b7280')
            tc_bg = TREND_BG.get(tc, '#f9fafb')
            cur = ind.get('current', 0) or 0
            nat = ind.get('national_avg', 0) or 0
            gap = ind.get('gap', 0) or 0
            f2028 = ind.get('forecast', {}).get('2028', cur) or cur
            unit = ind.get('unit', '')
            gap_sign = '+' if gap > 0 else ''
            gap_color = '#16a34a' if gap > 0 else ('#ef4444' if gap < 0 else '#6b7280')

            diff_2028 = round(f2028 - cur, 1)
            diff_sign = '+' if diff_2028 > 0 else ''
            is_lower_better = ind.get('lower_better', False)
            diff_color = '#16a34a' if (diff_2028 > 0 and not is_lower_better) or (diff_2028 < 0 and is_lower_better) else ('#ef4444' if diff_2028 != 0 else '#6b7280')

            h.append(f'<tr>')
            h.append(f'<td><strong>{ind["label"]}</strong></td>')
            h.append(f'<td style="font-weight:700">{cur:.1f}</td>')
            h.append(f'<td style="color:#6b7280">{nat:.1f}</td>')
            h.append(f'<td style="font-weight:700;color:{gap_color}">{gap_sign}{gap:.1f} {unit}</td>')
            h.append(f'<td><span style="background:{tc_bg};color:{tc_color};padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;white-space:nowrap">{ti} {tc.replace("_"," ")}</span></td>')
            h.append(f'<td style="font-weight:700;color:{diff_color}">{diff_sign}{f2028:.1f}</td>')
            h.append('</tr>')
        h.append('</table></div>')

        # Solutions / Reinforcement for this sector
        urgent_recs = [r for r in recommendations if r.get('type') in ('استباقي_عاجل','تدخل_تنموي') and sec in r.get('detail','')]
        pos_recs = [r for r in recommendations if r.get('type') == 'استثمار_ميزة' and sec in r.get('detail','')]

        recs_for_sector = []
        for rec in recommendations:
            detail = rec.get('detail','')
            if sec in detail or any(ind['label'] in detail for ind in inds):
                recs_for_sector.append(rec)

        if recs_for_sector:
            for rec in recs_for_sector[:2]:
                rtype = rec.get('type','')
                ricon = rec.get('icon','📌')
                rtitle = rec.get('title','')
                ractions = rec.get('actions',[])
                type_bgs = {'استباقي_عاجل': ('#fef2f2','#ef4444'), 'تدخل_تنموي': ('#fffbeb','#f59e0b'), 'استثمار_ميزة': ('#f0fdf4','#16a34a'), 'تعزيز_مستمر': ('#eff6ff','#3b82f6')}
                bg, co = type_bgs.get(rtype, ('#f9fafb','#6b7280'))
                h.append(f'<div style="background:{bg};border:1px solid {co}44;border-radius:8px;padding:10px 14px;margin-top:10px;border-right:3px solid {co}">')
                h.append(f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">')
                h.append(f'<span style="font-size:14px">{ricon}</span>')
                h.append(f'<strong style="font-size:11px;color:#1a1a2e">{rtitle}</strong>')
                h.append(f'<span style="margin-right:auto;background:{co};color:#fff;padding:1px 6px;border-radius:8px;font-size:9px;font-weight:700">{rtype.replace("_"," ")}</span>')
                h.append('</div>')
                if ractions:
                    h.append('<div style="display:flex;flex-wrap:wrap;gap:4px">')
                    for act in ractions[:3]:
                        h.append(f'<span style="background:rgba(255,255,255,.8);border-radius:4px;padding:3px 8px;font-size:10px;color:#374151;border:1px solid #e5e7eb">◆ {act}</span>')
                    h.append('</div>')
                h.append('</div>')

        h.append('</div>')

    h.append('</div>')  # end cg
    h.append('</div>')  # end tab

    trend_tabs[name] = '\n'.join(h)

print(f'Trends tabs built for {len(trend_tabs)} governorates')

# ===== STEP 3: Inject tabs =====
for g in data['governorates']:
    name = g['name']
    end_marker = f'<!-- END_PANEL_{name} -->'
    inject_pos = html.find(end_marker)
    if inject_pos == -1:
        print(f'  WARNING: marker not found for {name}')
        continue
    html = html[:inject_pos] + '\n' + trend_tabs[name] + '\n' + html[inject_pos:]
    print(f'  Injected trends tab for {name}')

# ===== STEP 4: Save =====
open('src/index.html', 'w', encoding='utf-8').write(html)

import os
size = os.path.getsize('src/index.html')
print(f'\nTrends module injected. Final size: {size/1024:.1f} KB')
