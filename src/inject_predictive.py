# inject_predictive.py — حقن تبويب التحليل التنبؤي (منطق معدل وطني)
# التصنيف:
#   🟢 تحسن استراتيجي: يتحسن سنوياً ويُتوقع أن يقلص ≥50% من الفجوة خلال 5 سنوات
#   🟡 تحسن حذر: يتحسن لكن بطيء جداً (لن يصل للمعدل خلال 5 سنوات)
#   🟠 فجوة حرجة: يتحسن لكن الفجوة تتسع (المعدل الوطني ينمو أسرع)
#   🔴 تراجع تنموي: انخفاض عن السنة السابقة

import json, math, sys
sys.stdout.reconfigure(encoding='utf-8')

data = json.load(open('src/data.json', encoding='utf-8'))
pred = json.load(open('src/predictive_data.json', encoding='utf-8'))

html = open('src/index.html', encoding='utf-8').read()

# ===== STEP 1: Add tab button =====
for g in data['governorates']:
    name = g['name']
    old_btn = f'onclick="switchTab(\'{name}\',\'budget\')">\U0001f4b0 \u062a\u0648\u062c\u064a\u0647 \u0627\u0644\u0645\u0648\u0627\u0632\u0646\u0629</button>'
    new_btn = (f'onclick="switchTab(\'{name}\',\'budget\')">\U0001f4b0 \u062a\u0648\u062c\u064a\u0647 \u0627\u0644\u0645\u0648\u0627\u0632\u0646\u0629</button>\n'
               f'<button class="tb" onclick="switchTab(\'{name}\',\'predictive\')">\U0001f52e \u0627\u0644\u062a\u062d\u0644\u064a\u0644 \u0627\u0644\u062a\u0646\u0628\u0624\u064a</button>')
    html = html.replace(old_btn, new_btn)
print('Predictive tab buttons injected')

# ===== Helper functions =====

def compute_cagr(values_dict):
    """Compute CAGR from a dict of {year: value}. Returns CAGR as decimal."""
    yrs = sorted(v for v in values_dict.keys() if values_dict[v] is not None)
    if len(yrs) < 2:
        return 0.0
    first_v = values_dict[yrs[0]]
    last_v = values_dict[yrs[-1]]
    if first_v is None or last_v is None or first_v == 0:
        return 0.0
    n = len(yrs) - 1
    return (last_v / first_v) ** (1.0 / n) - 1.0

def predict_values(current, cagr, n_years):
    """Return list of projected values for years 1..n_years."""
    return [round(current * (1 + cagr) ** t, 2) for t in range(1, n_years + 1)]

def years_to_reach_target(current, target, cagr, lower_better):
    """Years needed for current*(1+cagr)^t to reach target.
    Returns float or None if unreachable."""
    if cagr == 0 or target is None or current is None or current == 0:
        return None
    if lower_better:
        # Lower is better: we want current to drop to target
        if current <= target:
            return 0.0  # Already there or better
        if cagr >= 0:
            return None  # Moving away, will never reach
    else:
        # Higher is better: we want current to rise to target
        if current >= target:
            return 0.0  # Already there or better
        if cagr <= 0:
            return None  # Moving away, will never reach
    ratio = target / current
    t = math.log(ratio) / math.log(1 + cagr)
    if t < 0 or not math.isfinite(t):
        return None
    return t

def classify_national_approach(indicator, local_cagr, nat_cagr):
    """Classify indicator based on national-approach logic.
    Returns (label_ar, icon, color)."""
    cur = indicator.get('current', 0) or 0
    prev = indicator.get('prev_value', cur)
    nat = indicator.get('national_avg', 0) or 0
    lb = indicator.get('lower_better', False)

    # Determine if improving year-over-year
    if lb:
        improving = cur < prev
    else:
        improving = cur > prev

    if not improving:
        return '\u062a\u0631\u0627\u062c\u0639 \u062a\u0646\u0645\u0648\u064a', '\U0001f534', '#ef4444'

    # Determine if CAGR closes >=50% of the gap in 5 years
    if lb:
        gap = cur - nat  # positive means behind (higher is bad)
        target_gap_reduction = gap * 0.5  # need to close 50%
        projected_improvement = cur - cur * (1 + local_cagr) ** 5  # negative cagr means improvement
    else:
        gap = nat - cur  # positive means behind
        target_gap_reduction = gap * 0.5
        projected_improvement = cur * (1 + local_cagr) ** 5 - cur

    reach_yrs = years_to_reach_target(cur, nat, local_cagr, lb)

    if reach_yrs is not None and reach_yrs <= 5:
        return '\u062a\u062d\u0633\u0646 \u0627\u0633\u062a\u0631\u0627\u062a\u064a\u062c\u064a', '\U0001f7e2', '#22c55e', reach_yrs

    # Check if gap is widening (national CAGR > local CAGR)
    if local_cagr > 0 and nat_cagr > local_cagr and not lb:
        return '\u0641\u062c\u0648\u0629 \u062d\u0631\u062c\u0629', '\U0001f7e0', '#f97316', None
    if local_cagr < 0 and nat_cagr < local_cagr and lb:
        return '\u0641\u062c\u0648\u0629 \u062d\u0631\u062c\u0629', '\U0001f7e0', '#f97316', None

    return '\u062a\u062d\u0633\u0646 \u062d\u0630\u0631', '\U0001f7e1', '#eab308', None


# ===== Compute national CAGR for each indicator key across all governorates =====
nat_cagrs = {}
# Keys across all gov indicators
all_ind_keys = set()
for g in data['governorates']:
    gov_pred = pred['governorates'].get(g['name'], {})
    all_ind_keys.update(gov_pred.get('indicators', {}).keys())

for ind_key in all_ind_keys:
    # Compute national average for each year
    year_sums = {}
    year_counts = {}
    for g in data['governorates']:
        gov_pred = pred['governorates'].get(g['name'], {})
        ind = gov_pred.get('indicators', {}).get(ind_key, {})
        vals = ind.get('values', {})
        for yr, v in vals.items():
            if v is not None:
                year_sums[yr] = year_sums.get(yr, 0) + v
                year_counts[yr] = year_counts.get(yr, 0) + 1
    nat_annual_avgs = {}
    for yr in sorted(year_sums.keys()):
        if year_counts[yr] > 0:
            nat_annual_avgs[yr] = year_sums[yr] / year_counts[yr]
    nat_cagrs[ind_key] = compute_cagr(nat_annual_avgs)

# ===== Build predictive tab HTML per governorate =====
pred_tabs = {}
NEW_FORECAST_YEARS = [2026, 2027, 2028, 2029, 2030, 2031]
N_FORECAST = len(NEW_FORECAST_YEARS)

for g in data['governorates']:
    name = g['name']
    gov_pred = pred['governorates'].get(name, {})
    indicators = gov_pred.get('indicators', {})
    indicators.pop('\u0627\u0644\u0633\u0643\u0627\u0646', None)
    risk_summary = gov_pred.get('risk_summary', {})
    recommendations = gov_pred.get('recommendations', [])
    overall_risk = gov_pred.get('overall_risk_score', 0)
    narrative = gov_pred.get('trend_narrative', '')

    # Risk color
    if overall_risk >= 60:
        risk_color = '#ef4444'
        risk_label = '\u0645\u0631\u062a\u0641\u0639'
        risk_bg = '#fef2f2'
    elif overall_risk >= 35:
        risk_color = '#f59e0b'
        risk_label = '\u0645\u062a\u0648\u0633\u0637'
        risk_bg = '#fffbeb'
    else:
        risk_color = '#22c55e'
        risk_label = '\u0645\u0646\u062e\u0641\u0636'
        risk_bg = '#f0fdf4'

    h = []
    h.append(f'<div class="tc" id="tab-{name}-predictive">')

    # Description banner
    h.append(f'''<div style="background:linear-gradient(135deg,#f5f3ff,#ede9fe);border-radius:10px;padding:14px 18px;margin-bottom:16px;border-right:4px solid #8b5cf6;display:flex;gap:12px;align-items:flex-start">
<span style="font-size:20px">\U0001f52e</span>
<div>
<div style="font-size:13px;font-weight:700;color:#5b21b6;margin-bottom:4px">\u0627\u0644\u062a\u062d\u0644\u064a\u0644 \u0627\u0644\u062a\u0646\u0628\u0624\u064a — \u0645\u0627 \u0627\u0644\u0647\u062f\u0641 \u0645\u0646 \u0647\u0630\u0627 \u0627\u0644\u062a\u0628\u0648\u064a\u0628\u061f</div>
<div style="font-size:12px;color:#374151;line-height:1.7">\u064a\u0631\u0635\u062f \u0647\u0630\u0627 \u0627\u0644\u062a\u0628\u0648\u064a\u0628 <strong>\u0627\u062a\u062c\u0627\u0647\u0627\u062a \u0627\u0644\u0645\u0624\u0634\u0631\u0627\u062a \u0627\u0644\u062a\u0646\u0645\u0648\u064a\u0629</strong> \u0644\u0645\u062d\u0627\u0641\u0638\u0629 {name} \u0648\u064a\u062a\u0646\u0628\u0623 \u0628\u0645\u0633\u0627\u0631\u0627\u062a\u0647\u0627 \u062d\u062a\u0649 2031 \u0628\u0627\u0639\u062a\u0645\u0627\u062f \u0645\u0639\u062f\u0644 \u0627\u0644\u0646\u0645\u0648 \u0627\u0644\u0645\u0631\u0643\u0628 (CAGR). \u064a\u0639\u062a\u0645\u062f \u062a\u0635\u0646\u064a\u0641 \u0627\u0644\u0627\u062a\u062c\u0627\u0647 \u0639\u0644\u0649 \u0645\u062f\u0649 \u0627\u0642\u062a\u0631\u0627\u0628 \u0627\u0644\u0642\u064a\u0645\u0629 \u0645\u0646 \u0627\u0644\u0645\u062a\u0648\u0633\u0637 \u0627\u0644\u0648\u0637\u0646\u064a.</div>
</div>
</div>''')

    h.append('<div class="cg">')

    # Overall risk card
    h.append(f'''<div class="card">
<div class="ct">\u26a1 \u062f\u0631\u062c\u0629 \u0627\u0644\u0645\u062e\u0627\u0637\u0631\u0629 \u0627\u0644\u062a\u0646\u0645\u0648\u064a\u0629 \u0627\u0644\u0625\u062c\u0645\u0627\u0644\u064a\u0629</div>
<div style="text-align:center;padding:20px 0">
  <div style="font-size:52px;font-weight:800;color:{risk_color}">{overall_risk}</div>
  <div style="font-size:14px;font-weight:700;color:{risk_color};margin-top:4px">\u0645\u062e\u0627\u0637\u0631\u0629 {risk_label}</div>
  <div style="height:12px;background:#e5e7eb;border-radius:6px;margin:14px 0;overflow:hidden">
    <div style="height:100%;width:{overall_risk}%;background:{risk_color};border-radius:6px;transition:width 1s ease"></div>
  </div>
  <div style="font-size:12px;color:#374151;line-height:1.7;background:{risk_bg};border-radius:8px;padding:10px 14px;text-align:right">{narrative}</div>
</div>
</div>''')

    # Sector risk summary
    if risk_summary:
        h.append('<div class="card">')
        h.append('<div class="ct">\U0001f4ca \u0645\u0633\u062a\u0648\u0649 \u0627\u0644\u0645\u062e\u0627\u0637\u0631\u0629 \u062d\u0633\u0628 \u0627\u0644\u0642\u0637\u0627\u0639</div>')
        for sec, rs in risk_summary.items():
            sc = rs['score']
            lv = rs['level']
            co = rs['color']
            h.append(f'<div style="margin-bottom:10px">')
            h.append(f'<div style="display:flex;justify-content:space-between;margin-bottom:4px">')
            h.append(f'<span style="font-size:12px;font-weight:600">{sec}</span>')
            h.append(f'<span style="font-size:11px;font-weight:700;color:{co}">{lv} ({sc:.0f})</span>')
            h.append('</div>')
            h.append(f'<div style="height:8px;background:#e5e7eb;border-radius:4px;overflow:hidden">')
            h.append(f'<div style="height:100%;width:{sc}%;background:{co};border-radius:4px"></div>')
            h.append('</div></div>')
        h.append('</div>')

    # ===== ENHANCED INDICATORS TABLE =====
    if indicators:
        h.append('<div class="card fw">')
        h.append('<div class="ct">\U0001f4c8 \u0645\u0624\u0634\u0631\u0627\u062a \u0627\u0644\u0627\u062a\u062c\u0627\u0647 \u0627\u0644\u062a\u0646\u0645\u0648\u064a (\u062d\u0633\u0628 \u0627\u0644\u0645\u0639\u062f\u0644 \u0627\u0644\u0648\u0637\u0646\u064a)</div>')
        h.append('<div style="overflow-x:auto">')
        h.append('<table class="pt"><tr>'
                 '<th>\u0627\u0644\u0645\u0624\u0634\u0631</th>'
                 '<th>\u0627\u0644\u0642\u0637\u0627\u0639</th>'
                 '<th>\u0627\u0644\u0642\u064a\u0645\u0629 \u0627\u0644\u062d\u0627\u0644\u064a\u0629</th>'
                 '<th>\u0627\u0644\u0645\u062a\u0648\u0633\u0637 \u0627\u0644\u0648\u0637\u0646\u064a</th>'
                 '<th>\u0627\u0644\u0641\u062c\u0648\u0629</th>'
                 '<th>\u062a\u0648\u0642\u0639 2031</th>'
                 '<th>\u0633\u0646\u0629 \u0627\u0644\u0648\u0635\u0648\u0644</th>'
                 '<th>\u062a\u0642\u064a\u064a\u0645 \u0627\u0644\u0627\u062a\u062c\u0627\u0647</th>'
                 '</tr>')

        for ind_key, ind in indicators.items():
            cur = ind.get('current', ind.get('current_2025', 0)) or 0
            nat = ind.get('national_avg', 0) or 0
            gap = ind.get('gap', 0) or 0
            lb = ind.get('lower_better', False)
            vals_dict = ind.get('values', {})

            # Previous value (year before current)
            sorted_yrs = sorted(v for v in vals_dict.keys() if vals_dict[v] is not None)
            prev_val = cur
            if len(sorted_yrs) >= 2:
                prev_val_yr = sorted_yrs[-2]
                prev_val = vals_dict.get(prev_val_yr, cur)
            ind['prev_value'] = prev_val

            # Compute local CAGR
            local_cagr = compute_cagr(vals_dict)

            # Get national CAGR for this indicator
            nat_cagr = nat_cagrs.get(ind_key, 0)

            # New classification and year-to-reach
            cls_result = classify_national_approach(ind, local_cagr, nat_cagr)
            cls_label = cls_result[0]
            cls_icon = cls_result[1]
            cls_color = cls_result[2]
            reach_yrs = cls_result[3] if len(cls_result) > 3 else None

            # Predict 2031 value
            proj_vals = predict_values(cur, local_cagr, N_FORECAST)
            val_2031 = proj_vals[-1] if proj_vals else cur

            # Year to reach national
            if reach_yrs is not None and reach_yrs == 0:
                year_str = '\u0627\u0644\u0622\u0646'
            elif reach_yrs is not None and reach_yrs <= N_FORECAST:
                yr_idx = int(math.ceil(reach_yrs)) - 1
                yr_idx = max(0, min(yr_idx, N_FORECAST - 1))
                year_str = str(NEW_FORECAST_YEARS[yr_idx])
            else:
                year_str = '\u062e\u0627\u0631\u062c \u0627\u0644\u0646\u0637\u0627\u0642 \u0627\u0644\u062e\u0645\u0627\u0633\u064a'

            unit = ind.get('unit', '')
            gap_sign = '+' if gap > 0 else ''
            gap_color = '#22c55e' if gap > 0 else ('#ef4444' if gap < 0 else '#6b7280')

            # Status badge style
            status_bg = {
                '\u062a\u062d\u0633\u0646 \u0627\u0633\u062a\u0631\u0627\u062a\u064a\u062c\u064a': '#f0fdf4',
                '\u062a\u062d\u0633\u0646 \u062d\u0630\u0631': '#fffbeb',
                '\u0641\u062c\u0648\u0629 \u062d\u0631\u062c\u0629': '#fff7ed',
                '\u062a\u0631\u0627\u062c\u0639 \u062a\u0646\u0645\u0648\u064a': '#fef2f2',
            }.get(cls_label, '#f9fafb')

            h.append('<tr>')
            h.append(f'<td><strong style="font-size:11px">{ind["label"]}</strong></td>')
            h.append(f'<td style="font-size:11px">{ind["sector"]}</td>')
            h.append(f'<td style="font-weight:700">{cur:.1f} {unit}</td>')
            h.append(f'<td style="color:#6b7280">{nat:.1f} {unit}</td>')
            h.append(f'<td style="font-weight:700;color:{gap_color}">{gap_sign}{gap:.1f}</td>')
            h.append(f'<td style="font-weight:700;color:{cls_color}">{val_2031:.1f} {unit}</td>')
            h.append(f'<td style="font-size:11px;font-weight:600;color:#6b7280">{year_str}</td>')
            h.append(f'<td><span style="background:{status_bg};color:{cls_color};padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;white-space:nowrap">{cls_icon} {cls_label}</span></td>')
            h.append('</tr>')
        h.append('</table></div>')

        # Legend for new classification
        h.append(f'''<div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:12px;padding:10px 14px;background:#f8fafc;border-radius:8px;border:1px solid #e5e7eb">
<div style="display:flex;align-items:center;gap:4px;font-size:11px;color:#374151"><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#22c55e"></span> \u062a\u062d\u0633\u0646 \u0627\u0633\u062a\u0631\u0627\u062a\u064a\u062c\u064a: \u064a\u0642\u0644\u0635 \u226550% \u0645\u0646 \u0627\u0644\u0641\u062c\u0648\u0629 \u062e\u0644\u0627\u0644 5 \u0633\u0646\u0648\u0627\u062a</div>
<div style="display:flex;align-items:center;gap:4px;font-size:11px;color:#374151"><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#eab308"></span> \u062a\u062d\u0633\u0646 \u062d\u0630\u0631: \u0644\u0646 \u064a\u0635\u0644 \u0644\u0644\u0645\u0639\u062f\u0644 \u0627\u0644\u0648\u0637\u0646\u064a \u062e\u0644\u0627\u0644 5 \u0633\u0646\u0648\u0627\u062a</div>
<div style="display:flex;align-items:center;gap:4px;font-size:11px;color:#374151"><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#f97316"></span> \u0641\u062c\u0648\u0629 \u062d\u0631\u062c\u0629: \u0627\u0644\u0641\u062c\u0648\u0629 \u062a\u062a\u0633\u0639 (\u0627\u0644\u0648\u0637\u0646\u064a \u064a\u0646\u0645\u0648 \u0623\u0633\u0631\u0639)</div>
<div style="display:flex;align-items:center;gap:4px;font-size:11px;color:#374151"><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:#ef4444"></span> \u062a\u0631\u0627\u062c\u0639 \u062a\u0646\u0645\u0648\u064a: \u0627\u0646\u062e\u0641\u0627\u0636 \u0639\u0646 \u0627\u0644\u0639\u0627\u0645 \u0627\u0644\u0633\u0627\u0628\u0642</div>
</div>''')
        h.append('</div>')

    # Trend chart
    h.append(f'<div class="card no-print fw">')
    h.append(f'''<div class="ct">\U0001f4c9 \u0645\u062e\u0637\u0637 \u0627\u0644\u0627\u062a\u062c\u0627\u0647\u0627\u062a \u0627\u0644\u062a\u0627\u0631\u064a\u062e\u064a\u0629 \u0648\u0627\u0644\u062a\u0648\u0642\u0639\u0627\u062a \u062d\u062a\u0649 2031</div>
<div style="background:linear-gradient(135deg,#f5f3ff,#ede9fe);border-radius:8px;padding:12px 16px;margin-bottom:14px;border-right:3px solid #8b5cf6;font-size:12px;color:#374151;line-height:1.8">
  <strong style="color:#5b21b6">\u0643\u064a\u0641 \u062a\u0642\u0631\u0623 \u0647\u0630\u0627 \u0627\u0644\u0645\u062e\u0637\u0637\u061f</strong><br>
  \u0627\u0644\u062e\u0637 \u0627\u0644\u0645\u062a\u0635\u0644 <span style="display:inline-block;width:28px;height:3px;background:#1a3a5c;vertical-align:middle;border-radius:2px"></span> = \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u0641\u0639\u0644\u064a\u0629 &nbsp;|&nbsp;
  \u0627\u0644\u062e\u0637 \u0627\u0644\u0645\u062a\u0642\u0637\u0639 <span style="display:inline-block;width:28px;height:3px;background:#8b5cf6;vertical-align:middle;border-radius:2px;border-top:2px dashed #8b5cf6;background:none"></span> = \u0627\u0644\u062a\u0648\u0642\u0639 \u0628\u0640 CAGR (\u062d\u062a\u0649 2031)<br>
  \u0627\u0644\u0645\u0646\u0637\u0642\u0629 \u0627\u0644\u0645\u0644\u0648\u0646\u0629 \u0627\u0644\u0641\u0627\u062a\u062d\u0629 = \u0646\u0637\u0627\u0642 \u0627\u0644\u062b\u0642\u0629 \u00b1 10%
</div>
<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap">
  <label style="font-size:12px;font-weight:700;color:#1a3a5c">\u0627\u062e\u062a\u0631 \u0627\u0644\u0645\u0624\u0634\u0631:</label>
  <select id="ind-select-{name}" onchange="switchTrendIndicator('{name}')"
    style="padding:7px 14px;border:2px solid #c7d2fe;border-radius:8px;font-size:12px;font-family:Tahoma,Arial;color:#1a3a5c;background:#fff;cursor:pointer;min-width:220px">
  </select>
  <div id="ind-badge-{name}" style="display:flex;gap:6px;align-items:center;flex-wrap:wrap"></div>
</div>
<div style="display:grid;grid-template-columns:1fr 280px;gap:16px;align-items:start">
  <div style="height:300px"><canvas id="trend-chart-{name}"></canvas></div>
  <div id="ind-detail-{name}" style="background:#f8fafc;border-radius:10px;padding:14px;border:1px solid #e5e7eb;font-size:12px;line-height:1.9">
    <div style="color:#9ca3af;text-align:center;padding:20px 0">\u0627\u062e\u062a\u0631 \u0645\u0624\u0634\u0631\u0627\u064b \u0644\u0639\u0631\u0636 \u062a\u0641\u0627\u0635\u064a\u0644\u0647</div>
  </div>
</div>''')
    h.append('</div>\n')

    # Recommendations
    if recommendations:
        h.append('<div class="card fw">')
        h.append('<div class="ct">\U0001f4a1 \u0627\u0644\u062a\u0648\u0635\u064a\u0627\u062a \u0627\u0644\u0627\u0633\u062a\u0628\u0627\u0642\u064a\u0629 \u0627\u0644\u0645\u0628\u0646\u064a\u0629 \u0639\u0644\u0649 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a</div>')
        for rec in recommendations:
            rec_type = rec.get('type', '')
            icon = rec.get('icon', '\U0001f4cc')
            title = rec.get('title', '')
            detail = rec.get('detail', '')
            actions = rec.get('actions', [])
            type_colors = {
                '\u0627\u0633\u062a\u0628\u0627\u0642\u064a_\u0639\u0627\u062c\u0644': ('#fef2f2', '#ef4444', '#fecaca'),
                '\u062a\u062f\u062e\u0644_\u062a\u0646\u0645\u0648\u064a':   ('#fffbeb', '#f59e0b', '#fde68a'),
                '\u0627\u0633\u062a\u062b\u0645\u0627\u0631_\u0645\u064a\u0632\u0629': ('#f0fdf4', '#22c55e', '#bbf7d0'),
                '\u062a\u0639\u0632\u064a\u0632_\u0645\u0633\u062a\u0645\u0631':  ('#eff6ff', '#3b82f6', '#bfdbfe'),
            }
            bg, co, border = type_colors.get(rec_type, ('#f9fafb', '#6b7280', '#e5e7eb'))
            h.append(f'<div style="background:{bg};border:1px solid {border};border-radius:10px;padding:14px 16px;margin-bottom:12px;border-right:4px solid {co}">')
            h.append(f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">')
            h.append(f'<span style="font-size:18px">{icon}</span>')
            h.append(f'<strong style="font-size:13px;color:#1a1a2e">{title}</strong>')
            h.append(f'<span style="margin-right:auto;background:{co};color:#fff;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700">{rec_type.replace("_"," ")}</span>')
            h.append('</div>')
            h.append(f'<div style="font-size:12px;color:#374151;line-height:1.7;margin-bottom:10px">{detail}</div>')
            if actions:
                h.append('<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:6px">')
                for act in actions:
                    h.append(f'<div style="background:rgba(255,255,255,.7);border-radius:6px;padding:6px 10px;font-size:11px;color:#1a1a2e;display:flex;align-items:flex-start;gap:6px">')
                    h.append(f'<span style="color:{co};font-weight:700;flex-shrink:0">\u25c6</span><span>{act}</span>')
                    h.append('</div>')
                h.append('</div>')
            h.append('</div>')
        h.append('</div>')

    h.append('</div>')  # end cg
    h.append('</div>')  # end tab predictive

    pred_tabs[name] = '\n'.join(h)

print(f'Predictive tabs built for {len(pred_tabs)} governorates')

# ===== Inject tabs =====
for g in data['governorates']:
    name = g['name']
    end_marker = f'<!-- END_PANEL_{name} -->'
    inject_pos = html.find(end_marker)
    if inject_pos == -1:
        print(f'  WARNING: marker not found for {name}')
        continue
    html = html[:inject_pos] + '\n' + pred_tabs[name] + '\n' + html[inject_pos:]
    print(f'  Injected predictive tab for {name}')

# ===== Build chart / JS data with CAGR projection =====
trend_chart_data = {}

TREND_COLORS_MAP = {
    '\u062a\u062d\u0633\u0646 \u0627\u0633\u062a\u0631\u0627\u062a\u064a\u062c\u064a': '#22c55e',
    '\u062a\u062d\u0633\u0646 \u062d\u0630\u0631': '#eab308',
    '\u0641\u062c\u0648\u0629 \u062d\u0631\u062c\u0629': '#f97316',
    '\u062a\u0631\u0627\u062c\u0639 \u062a\u0646\u0645\u0648\u064a': '#ef4444',
}

for g in data['governorates']:
    name = g['name']
    gov_pred = pred['governorates'].get(name, {})
    indicators = gov_pred.get('indicators', {})
    years_hist_all = pred.get('years', [])

    ind_list = []
    for ind_key, ind in indicators.items():
        raw_values = ind.get('values', {})
        cur = ind.get('current', 0) or 0
        nat = ind.get('national_avg', 0) or 0
        lb = ind.get('lower_better', False)

        # Historical series
        hist_years  = sorted(yr for yr in years_hist_all if raw_values.get(yr) is not None)
        hist_values = [raw_values[yr] for yr in hist_years]

        # CAGR
        local_cagr = compute_cagr(raw_values)
        nat_cagr = nat_cagrs.get(ind_key, 0)

        # Previous value for classification
        prev_val = cur
        if len(hist_years) >= 2:
            prev_val = raw_values.get(hist_years[-2], cur)
        ind['prev_value'] = prev_val

        # Classify
        cls_result = classify_national_approach(ind, local_cagr, nat_cagr)
        cls_label = cls_result[0]
        cls_color = cls_result[2] if len(cls_result) > 2 else '#6b7280'
        reach_yrs = cls_result[3] if len(cls_result) > 3 else None

        # Build CAGR-based forecast: N_FORECAST years from last historical year
        last_hist_yr = int(hist_years[-1]) if hist_years else 2024
        fore_start = last_hist_yr + 1
        fore_years = list(range(fore_start, fore_start + N_FORECAST))
        fore_values = predict_values(cur, local_cagr, N_FORECAST)

        conf_high = [round(v * 1.10, 2) if v is not None else None for v in fore_values]
        conf_low  = [round(v * 0.90, 2) if v is not None else None for v in fore_values]

        # Year to reach national
        if reach_yrs is not None and reach_yrs == 0:
            year_str = '\u0627\u0644\u0622\u0646'
        elif reach_yrs is not None and reach_yrs <= N_FORECAST:
            yr_idx = int(math.ceil(reach_yrs)) - 1
            yr_idx = max(0, min(yr_idx, N_FORECAST - 1))
            year_str = str(fore_years[yr_idx])
        else:
            year_str = '\u062e\u0627\u0631\u062c \u0627\u0644\u0646\u0637\u0627\u0642 \u0627\u0644\u062e\u0645\u0627\u0633\u064a'

        val_2031 = fore_values[-1] if fore_values else cur

        ind_list.append({
            'key':           ind_key,
            'label':         ind['label'],
            'unit':          ind['unit'],
            'sector':        ind['sector'],
            'lower_better':  lb,
            'hist_years':    [str(y) for y in hist_years],
            'hist_values':   hist_values,
            'fore_years':    [str(y) for y in fore_years],
            'fore_values':   fore_values,
            'conf_high':     conf_high,
            'conf_low':      conf_low,
            'current':       cur,
            'national_avg':  nat,
            'gap':           ind.get('gap', 0),
            'new_class':     cls_label,
            'new_color':     cls_color,
            'reach_year':    year_str,
            'val_2031':      val_2031,
            'cagr':          round(local_cagr * 100, 2),
        })

    trend_chart_data[name] = {'indicators': ind_list}

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

_trend_json = json.dumps(trend_chart_data, ensure_ascii=False)

PRED_JS = (
    "\n// ===== PREDICTIVE MODULE (CAGR + National Approach) =====\n"
    "const TREND_DATA = " + _trend_json + ";\n\n"

    "function switchTrendIndicator(name) {\n"
    "  var sel = document.getElementById('ind-select-' + name);\n"
    "  if (!sel) return;\n"
    "  var idx = parseInt(sel.value) || 0;\n"
    "  var td = TREND_DATA[name];\n"
    "  if (!td || !td.indicators || !td.indicators[idx]) return;\n"
    "  buildSingleTrendChart(name, idx);\n"
    "  updateIndDetail(name, idx);\n"
    "}\n\n"

    "function buildSingleTrendChart(name, idx) {\n"
    "  var td = TREND_DATA[name];\n"
    "  var ind = td.indicators[idx];\n"
    "  var canvasId = 'trend-chart-' + name;\n"
    "  var canvas = document.getElementById(canvasId);\n"
    "  if (!canvas) { console.warn('canvas not found:', canvasId); return; }\n"
    "  if (charts[canvasId]) charts[canvasId].destroy();\n\n"

    "  var histYears  = ind.hist_years  || [];\n"
    "  var histValues = ind.hist_values || [];\n"
    "  var foreYears  = ind.fore_years  || [];\n"
    "  var foreValues = ind.fore_values || [];\n"
    "  var confHigh   = ind.conf_high   || [];\n"
    "  var confLow    = ind.conf_low    || [];\n\n"

    "  var foreOnly = foreYears.filter(function(yr){ return histYears.indexOf(yr) < 0; });\n"
    "  var allYears = histYears.concat(foreOnly);\n\n"

    "  var histData = allYears.map(function(yr){\n"
    "    var i = histYears.indexOf(yr); return i >= 0 ? histValues[i] : null;\n"
    "  });\n"
    "  var foreData = allYears.map(function(yr){\n"
    "    var i = foreYears.indexOf(yr); return i >= 0 ? foreValues[i] : null;\n"
    "  });\n"
    "  var confHighData = allYears.map(function(yr){\n"
    "    var i = foreYears.indexOf(yr); return i >= 0 ? confHigh[i] : null;\n"
    "  });\n"
    "  var confLowData = allYears.map(function(yr){\n"
    "    var i = foreYears.indexOf(yr); return i >= 0 ? confLow[i] : null;\n"
    "  });\n\n"

    "  var mainColor = ind.new_color || '#1a3a5c';\n"
    "  var foreColor = '#8b5cf6';\n\n"

    "  // Add national average line data\n"
    "  var natAvg = ind.national_avg;\n"
    "  var natLineData = allYears.map(function(){ return natAvg; });\n\n"

    "  charts[canvasId] = new Chart(canvas, {\n"
    "    type: 'line',\n"
    "    data: { labels: allYears, datasets: [\n"
    "      { label:'\u062d\u062f \u0623\u0639\u0644\u0649', data:confHighData, borderColor:'transparent', backgroundColor:foreColor+'22', fill:1, pointRadius:0, tension:0.3, order:4 },\n"
    "      { label:'\u062d\u062f \u0623\u062f\u0646\u0649', data:confLowData,  borderColor:'transparent', backgroundColor:'transparent', fill:false, pointRadius:0, tension:0.3, order:4 },\n"
    "      { label:'\u0627\u0644\u062a\u0648\u0642\u0639 CAGR', data:foreData,\n"
    "        borderColor:foreColor, backgroundColor:'transparent', borderWidth:2.5, borderDash:[8,4],\n"
    "        pointRadius:foreData.map(function(v,i){ return (v!==null && foreOnly.indexOf(allYears[i])>=0)?5:0; }),\n"
    "        pointStyle:'rectRot', pointBackgroundColor:foreColor, pointBorderColor:'#fff', pointBorderWidth:1.5,\n"
    "        tension:0.3, fill:false, order:2 },\n"
    "      { label:'\u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u0641\u0639\u0644\u064a\u0629', data:histData,\n"
    "        borderColor:mainColor, backgroundColor:mainColor+'15', borderWidth:3,\n"
    "        pointRadius:histData.map(function(v){ return v!==null?5:0; }),\n"
    "        pointStyle:'circle', pointBackgroundColor:mainColor, pointBorderColor:'#fff', pointBorderWidth:2,\n"
    "        tension:0.3, fill:false, order:1 },\n"
    "      { label:'\u0627\u0644\u0645\u062a\u0648\u0633\u0637 \u0627\u0644\u0648\u0637\u0646\u064a', data:natLineData,\n"
    "        borderColor:'#ef4444', backgroundColor:'transparent', borderWidth:2, borderDash:[4,4],\n"
    "        pointRadius:0, tension:0, fill:false, order:3 }\n"
    "    ]},\n"
    "    options: {\n"
    "      responsive:true, maintainAspectRatio:false,\n"
    "      interaction:{mode:'index',intersect:false},\n"
    "      plugins:{\n"
    "        legend:{position:'bottom',labels:{font:{family:'Tahoma',size:11},boxWidth:14,padding:14,\n"
    "          filter:function(item){return item.text.indexOf('\u062d\u062f \u0623')<0;}}},\n"
    "        tooltip:{rtl:true,titleFont:{family:'Tahoma',size:12},bodyFont:{family:'Tahoma',size:11},\n"
    "          callbacks:{\n"
    "            title:function(items){return '\u0633\u0646\u0629 '+items[0].label;},\n"
    "            label:function(ctx){\n"
    "              if(ctx.dataset.label.indexOf('\u062d\u062f \u0623')>=0) return null;\n"
    "              var v=ctx.raw; if(v===null||v===undefined) return null;\n"
    "              var s='';\n"
    "              if(ctx.dataset.label==='\u0627\u0644\u062a\u0648\u0642\u0639 CAGR' && foreOnly.indexOf(ctx.label)>=0) s=' \u2605 \u0645\u062a\u0648\u0642\u0639';\n"
    "              return ' '+ctx.dataset.label+': '+parseFloat(v).toFixed(1)+' '+ind.unit+s;\n"
    "            }\n"
    "          }\n"
    "        }\n"
    "      },\n"
    "      scales:{\n"
    "        x:{ticks:{font:{family:'Tahoma',size:10}},grid:{color:'#f0f0f0'}},\n"
    "        y:{ticks:{font:{family:'Tahoma',size:10},callback:function(v){return parseFloat(v).toFixed(1)+' '+ind.unit;}},grid:{color:'#f0f0f0'}}\n"
    "      }\n"
    "    },\n"
    "    plugins:[{\n"
    "      id:'fz_'+canvasId,\n"
    "      afterDraw:function(chart){\n"
    "        if(!foreOnly.length) return;\n"
    "        var c2=chart.ctx, xa=chart.scales.x;\n"
    "        var fi=allYears.indexOf(foreOnly[0]); if(fi<0) return;\n"
    "        var xs=xa.getPixelForValue(fi-0.5), xe=chart.chartArea.right;\n"
    "        c2.save();\n"
    "        c2.fillStyle=foreColor+'0d';\n"
    "        c2.fillRect(xs,chart.chartArea.top,xe-xs,chart.chartArea.bottom-chart.chartArea.top);\n"
    "        c2.beginPath(); c2.moveTo(xs,chart.chartArea.top); c2.lineTo(xs,chart.chartArea.bottom);\n"
    "        c2.strokeStyle=foreColor+'aa'; c2.lineWidth=1.5; c2.setLineDash([5,3]); c2.stroke();\n"
    "        c2.fillStyle=foreColor; c2.font='bold 10px Tahoma'; c2.textAlign='center'; c2.setLineDash([]);\n"
    "        c2.fillText('\u2190 \u062a\u0648\u0642\u0639', xs+(xe-xs)/2, chart.chartArea.top+14);\n"
    "        c2.restore();\n"
    "      }\n"
    "    }]\n"
    "  });\n"
    "}\n\n"

    "function updateIndDetail(name, idx) {\n"
    "  var td=TREND_DATA[name], ind=td.indicators[idx];\n"
    "  var el=document.getElementById('ind-detail-'+name);\n"
    "  if(!el||!ind) return;\n"
    "  var nc=ind.new_class||'', nco=ind.new_color||'#6b7280';\n"
    "  var gs=ind.gap>0?'+':'', gc=ind.gap>0?'#22c55e':(ind.gap<0?'#ef4444':'#6b7280');\n"
    "  var cur=ind.current, v31=ind.val_2031;\n"
    "  var fmt=function(v){return(v!==null&&v!==undefined)?parseFloat(v).toFixed(1):'N/A';};\n"
    "  var el2=document.getElementById('el2-'+name);\n"
    "  el.innerHTML='<div style=\"font-weight:700;color:#1a3a5c;font-size:13px;margin-bottom:10px;padding-bottom:8px;border-bottom:2px solid #e5e7eb\">'+ind.label+'</div>'\n"
    "    +'<div style=\"display:flex;flex-direction:column;gap:8px\">'\n"
    "    +'<div style=\"display:flex;justify-content:space-between\"><span style=\"color:#6b7280\">\u0627\u0644\u0642\u0637\u0627\u0639</span><span style=\"font-weight:600;color:#1a3a5c\">'+ind.sector+'</span></div>'\n"
    "    +'<div style=\"display:flex;justify-content:space-between\"><span style=\"color:#6b7280\">\u0627\u0644\u0642\u064a\u0645\u0629 \u0627\u0644\u062d\u0627\u0644\u064a\u0629</span><span style=\"font-weight:700;font-size:14px;color:#1a3a5c\">'+fmt(cur)+' '+ind.unit+'</span></div>'\n"
    "    +'<div style=\"display:flex;justify-content:space-between\"><span style=\"color:#6b7280\">\u0627\u0644\u0645\u062a\u0648\u0633\u0637 \u0627\u0644\u0648\u0637\u0646\u064a</span><span style=\"font-weight:600;color:#6b7280\">'+fmt(ind.national_avg)+' '+ind.unit+'</span></div>'\n"
    "    +'<div style=\"display:flex;justify-content:space-between\"><span style=\"color:#6b7280\">\u0627\u0644\u0641\u062c\u0648\u0629</span><span style=\"font-weight:700;color:'+gc+'\">'+gs+fmt(ind.gap)+' '+ind.unit+'</span></div>'\n"
    "    +'<div style=\"display:flex;justify-content:space-between\"><span style=\"color:#6b7280\">\u0645\u0639\u062f\u0644 \u0627\u0644\u0646\u0645\u0648 (CAGR)</span><span style=\"font-weight:700;color:#1a3a5c\">'+(ind.cagr>0?'+':'')+fmt(ind.cagr)+'%</span></div>'\n"
    "    +'<div style=\"display:flex;justify-content:space-between\"><span style=\"color:#6b7280\">\u062a\u0648\u0642\u0639 2031</span><span style=\"font-weight:700;color:'+nco+'\">'+fmt(v31)+' '+ind.unit+'</span></div>'\n"
    "    +'<div style=\"display:flex;justify-content:space-between\"><span style=\"color:#6b7280\">\u0633\u0646\u0629 \u0627\u0644\u0648\u0635\u0648\u0644</span><span style=\"font-weight:600;font-size:11px;color:#6b7280\">'+ind.reach_year+'</span></div>'\n"
    "    +'<div style=\"display:flex;justify-content:space-between;align-items:center\"><span style=\"color:#6b7280\">\u062a\u0642\u064a\u064a\u0645 \u0627\u0644\u0627\u062a\u062c\u0627\u0647</span>'\n"
    "    +'<span style=\"background:'+nco+'18;color:'+nco+';padding:2px 10px;border-radius:10px;font-size:11px;font-weight:700;border:1px solid '+nco+'40\">'+nc+'</span></div>'\n"
    "    +'<div style=\"background:#f0f4ff;border-radius:6px;padding:8px 10px;margin-top:4px;font-size:10px;color:#6b7280;line-height:1.6\"><strong style=\"color:#1a3a5c\">\u0645\u0644\u0627\u062d\u0638\u0629:</strong> \u0627\u0644\u062a\u0648\u0642\u0639 \u0645\u0628\u0646\u064a \u0639\u0644\u0649 \u0645\u0639\u062f\u0644 \u0627\u0644\u0646\u0645\u0648 \u0627\u0644\u0645\u0631\u0643\u0628 (CAGR) \u0644\u0644\u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u062a\u0627\u0631\u064a\u062e\u064a\u0629. \u0627\u0644\u0642\u064a\u0645 \u0627\u0644\u0641\u0639\u0644\u064a\u0629 \u0642\u062f \u062a\u062e\u062a\u0644\u0641 \u0628\u0646\u0627\u0621\u064b \u0639\u0644\u0649 \u0627\u0644\u0633\u064a\u0627\u0633\u0627\u062a.</div>'\n"
    "    +'</div>';\n"
    "  var be=document.getElementById('ind-badge-'+name);\n"
    "  if(be){\n"
    "    var lb=ind.lower_better?'<span style=\"background:#fef3c7;color:#92400e;padding:4px 10px;border-radius:20px;font-size:10px;font-weight:600\">\u2193 \u0627\u0644\u0623\u0642\u0644 \u0623\u0641\u0636\u0644</span>':'<span style=\"background:#dcfce7;color:#166534;padding:4px 10px;border-radius:20px;font-size:10px;font-weight:600\">\u2191 \u0627\u0644\u0623\u0639\u0644\u0649 \u0623\u0641\u0636\u0644</span>';\n"
    "    be.innerHTML='<span style=\"background:'+nco+'18;color:'+nco+';padding:4px 12px;border-radius:20px;font-size:11px;font-weight:700;border:1px solid '+nco+'40\">'+nc+'</span>'\n"
    "      +'<span style=\"background:#f0f4ff;color:#1a3a5c;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;border:1px solid #c7d2fe\">\u0627\u0644\u0648\u062d\u062f\u0629: '+ind.unit+'</span>'+lb;\n"
    "  }\n"
    "}\n\n"

    "var _origBCP = buildCharts;\n"
    "buildCharts = function(name) {\n"
    "  _origBCP(name);\n"
    "  var sel = document.getElementById('ind-select-' + name);\n"
    "  if (!sel) return;\n"
    "  if (sel.options.length === 0) {\n"
    "    var td = TREND_DATA[name];\n"
    "    if (td && td.indicators) {\n"
    "      td.indicators.forEach(function(ind, i) {\n"
    "        var opt = document.createElement('option');\n"
    "        opt.value = i;\n"
    "        opt.textContent = ind.label + ' (' + ind.unit + ')';\n"
    "        sel.appendChild(opt);\n"
    "      });\n"
    "    }\n"
    "  }\n"
    "  switchTrendIndicator(name);\n"
    "};\n"
)

html = html.replace('</script>\n</body>', PRED_JS + '\n</script>\n</body>', 1)
open('src/index.html', 'w', encoding='utf-8').write(html)

import os
size = os.path.getsize('src/index.html')
print(f'\nPredictive module (CAGR + National Approach) injected. Final size: {size/1024:.1f} KB')
