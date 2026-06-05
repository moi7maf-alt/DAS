# inject

import json, sys
sys.stdout.reconfigure(encoding='utf-8')

bd = json.load(open('src/budget_data.json', encoding='utf-8'))
data = json.load(open('src/data.json', encoding='utf-8'))
plans = json.load(open('src/strategic_plans.json', encoding='utf-8'))

html = open('src/index.html', encoding='utf-8').read()

PACKAGES = bd['packages']
PKG_COLORS = {
    'البنية التحتية': '#8b5cf6',
    'الخدمات': '#3b82f6',
    'الإنتاج': '#22c55e'
}
PKG_ICONS = {
    'البنية التحتية': '🏗️',
    'الخدمات': '🏥',
    'الإنتاج': '🌾'
}

# ===== STEP 1: Add budget tab button to each panel =====
# Budget tab comes after advantages tab
for g in data['governorates']:
    name = g['name']
    old_tab = f'onclick="switchTab(\'{name}\',\'strategy\',this)">🎯 الخطة الاستراتيجية</button>'
    new_tab = (f'onclick="switchTab(\'{name}\',\'strategy\',this)">🎯 الخطة الاستراتيجية</button>\n'
               f'<button class="tb" onclick="switchTab(\'{name}\',\'budget\')">💰 توجيه الموازنة</button>')
    html = html.replace(old_tab, new_tab)

print('Tab buttons injected')

# ===== STEP 2: Build budget tab content for each gov =====
budget_tabs_html = {}

for g in data['governorates']:
    name = g['name']
    gov_bd = bd['governorates'].get(name, {})
    alloc = gov_bd.get('allocation_pct', {})
    justifications = gov_bd.get('justifications', {})
    gap_details = gov_bd.get('gap_details', {})
    budget_2026 = g['budget_2026']
    sectors = g['sectors']

    h = []
    h.append(f'<div class="tc" id="tab-{name}-budget">')

    # Description banner
    h.append(f'''<div style="background:linear-gradient(135deg,#fffbeb,#fef3c7);border-radius:10px;padding:14px 18px;margin-bottom:16px;border-right:4px solid #c8a84b;display:flex;gap:12px;align-items:flex-start">
<span style="font-size:20px">💰</span>
<div>
<div style="font-size:13px;font-weight:700;color:#92400e;margin-bottom:4px">توجيه الموازنة — ما الهدف من هذا التبويب؟</div>
<div style="font-size:12px;color:#374151;line-height:1.7">يساعدك هذا التبويب على <strong>توزيع الموازنة الرأسمالية المحلية</strong> على أفضل وجه بناءً على الفجوات التنموية الفعلية. أدخل سقف الموازنة المتاح وسيقترح النظام التوزيع الأمثل على ثلاث حزم قطاعية مع مبررات مستندة للبيانات. يُستخدم كأداة دعم لصانع القرار عند إعداد الموازنات السنوية.</div>
</div>
</div>''')

    # Budget input card
    h.append('<div class="cg">')
    h.append('<div class="card fw">')
    h.append('<div class="ct">💰 توجيه الموازنة المحلية — أدخل سقف الموازنة</div>')
    h.append(f'''
<div style="background:linear-gradient(135deg,#f0f4ff,#e8f0fe);border-radius:12px;padding:20px;margin-bottom:16px;border:1px solid #c7d2fe">
  <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
    <div style="flex:1;min-width:200px">
      <label style="font-size:12px;font-weight:700;color:#1a3a5c;display:block;margin-bottom:6px">سقف الموازنة (دينار أردني)</label>
      <input type="number" id="budget-input-{name}" value="{int(budget_2026)}"
        style="width:100%;padding:10px 14px;border:2px solid #c7d2fe;border-radius:8px;font-size:15px;font-weight:700;color:#1a3a5c;direction:ltr;text-align:left"
        onchange="updateBudget('{name}')" oninput="updateBudget('{name}')">
      <div style="font-size:11px;color:#6b7280;margin-top:4px">الموازنة الرأسمالية 2026: {int(budget_2026):,} د.أ</div>
    </div>
    <button onclick="updateBudget('{name}')"
      style="background:linear-gradient(135deg,#1a3a5c,#2a5298);color:#fff;border:none;padding:12px 28px;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer">
      ⚡ احسب التوزيع الأمثل
    </button>
  </div>
</div>
''')
    h.append('</div>')  # end card

    # Package cards
    for pkg_key, pkg in PACKAGES.items():
        pct = alloc.get(pkg_key, 33.3)
        color = PKG_COLORS.get(pkg_key, '#6b7280')
        icon = PKG_ICONS.get(pkg_key, '📦')
        just = justifications.get(pkg_key, '')
        pkg_sectors = pkg['sectors']

        h.append(f'<div class="card" id="pkg-card-{name}-{pkg_key}">')
        h.append(f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">')
        h.append(f'<div class="ct" style="margin-bottom:0">{icon} {pkg["name"]}</div>')
        h.append(f'<div style="font-size:22px;font-weight:800;color:{color}" id="pkg-pct-{name}-{pkg_key}">{pct}%</div>')
        h.append('</div>')

        # Amount display
        h.append(f'<div style="background:{color}15;border-radius:8px;padding:10px 14px;margin-bottom:12px;border-right:4px solid {color}">')
        h.append(f'<div style="font-size:11px;color:#6b7280;margin-bottom:2px">المبلغ المقترح</div>')
        h.append(f'<div style="font-size:18px;font-weight:700;color:{color}" id="pkg-amt-{name}-{pkg_key}">{int(budget_2026 * pct / 100):,} د.أ</div>')
        h.append('</div>')

        # Progress bar
        h.append(f'<div style="height:10px;background:#e5e7eb;border-radius:5px;overflow:hidden;margin-bottom:12px">')
        h.append(f'<div id="pkg-bar-{name}-{pkg_key}" style="height:100%;width:{pct}%;background:{color};border-radius:5px;transition:width .6s ease"></div>')
        h.append('</div>')

        # Sectors in package
        h.append('<div style="margin-bottom:10px">')
        for sec in pkg_sectors:
            if sec in sectors:
                sec_data = sectors[sec]
                gap = sec_data['gap']
                status = sec_data['status']
                s_cls = 's-adv' if status == 'متقدم' else ('s-beh' if status == 'متأخر' else 's-avg')
                gap_sign = '+' if gap > 0 else ''
                h.append(f'<div style="display:flex;justify-content:space-between;font-size:11px;padding:3px 0;border-bottom:1px dashed #e5e7eb">')
                h.append(f'<span>{sec}</span>')
                h.append(f'<span><span class="sb {s_cls}">{status}</span> <span style="font-weight:700">{gap_sign}{gap:.1f}</span></span>')
                h.append('</div>')
        h.append('</div>')

        # Justification
        h.append(f'<div style="background:#f8fafc;border-radius:6px;padding:8px 10px;font-size:11px;color:#374151;line-height:1.6;border-right:3px solid {color}">')
        h.append(f'<strong>المبرر:</strong> {just}')
        h.append('</div>')

        h.append('</div>')  # end card

    # Pie chart card
    h.append('<div class="card">')
    h.append('<div class="ct">🥧 توزيع الموازنة على الحزم</div>')
    h.append(f'<div class="ch"><canvas id="budget-pie-{name}"></canvas></div>')
    h.append('</div>')

    # Detailed breakdown table card
    h.append('<div class="card fw">')
    h.append('<div class="ct">📋 جدول التوزيع التفصيلي</div>')
    h.append(f'<table class="pt" id="budget-table-{name}"><tr><th>الحزمة القطاعية</th><th>القطاعات المشمولة</th><th>النسبة</th><th>المبلغ (د.أ)</th><th>الأولوية</th></tr>')
    for pkg_key, pkg in PACKAGES.items():
        pct = alloc.get(pkg_key, 33.3)
        color = PKG_COLORS.get(pkg_key, '#6b7280')
        icon = PKG_ICONS.get(pkg_key, '📦')
        behind_count = sum(1 for s in pkg['sectors'] if s in sectors and sectors[s]['status'] == 'متأخر')
        priority = 'عالية 🔴' if behind_count >= 2 else ('متوسطة 🟡' if behind_count == 1 else 'تعزيز 🟢')
        h.append(f'<tr>')
        h.append(f'<td><strong style="color:{color}">{icon} {pkg["name"]}</strong></td>')
        h.append(f'<td style="font-size:11px">{" | ".join(pkg["sectors"])}</td>')
        h.append(f'<td id="tbl-pct-{name}-{pkg_key}" style="font-weight:700;color:{color}">{pct}%</td>')
        h.append(f'<td id="tbl-amt-{name}-{pkg_key}" style="font-weight:700">{int(budget_2026 * pct / 100):,}</td>')
        h.append(f'<td>{priority}</td>')
        h.append('</tr>')
    h.append('</table></div>')

    h.append('</div>')  # end cg
    h.append('</div>')  # end tab budget

    budget_tabs_html[name] = '\n'.join(h)

print('Budget tab HTML built for', len(budget_tabs_html), 'governorates')

# ===== STEP 3: Inject budget tabs before closing panel div =====
for g in data['governorates']:
    name = g['name']
    # Find the end of advantages tab and inject budget tab before panel close
    old_end = f'</div>\n</div>\n'  # end tab advantages + end panel
    # More specific: find the advantages tab end for this panel
    adv_end = f'</div>\n</div>\n</div>\n</div>\n'  # end cg + end tab advantages + end panel

    # Use a unique marker: the panel closing div
    panel_close = f'</div>\n\n</div>\n'

    # Inject budget tab using END_PANEL marker
    end_marker = f'<!-- END_PANEL_{name} -->'
    inject_pos = html.find(end_marker)
    if inject_pos == -1:
        print(f'WARNING: end marker not found for {name}')
        continue

    # Inject budget tab BEFORE this marker
    html = html[:inject_pos] + '\n' + budget_tabs_html[name] + '\n' + html[inject_pos:]
    print(f'  Injected budget tab for {name}')

print('All budget tabs injected')

# ===== STEP 4: Inject Budget JS before </script> =====
BUDGET_JS = """
// ===== BUDGET MODULE =====
const BUDGET_DATA = """ + json.dumps(bd, ensure_ascii=False) + """;

function updateBudget(name) {
  const input = document.getElementById('budget-input-' + name);
  if (!input) return;
  const total = parseFloat(input.value) || 0;
  const govBd = BUDGET_DATA.governorates[name];
  if (!govBd) return;
  const alloc = govBd.allocation_pct;
  const pkgs = Object.keys(alloc);

  pkgs.forEach(pkg => {
    const pct = alloc[pkg];
    const amt = Math.round(total * pct / 100);

    const pctEl = document.getElementById('pkg-pct-' + name + '-' + pkg);
    const amtEl = document.getElementById('pkg-amt-' + name + '-' + pkg);
    const barEl = document.getElementById('pkg-bar-' + name + '-' + pkg);
    const tblPct = document.getElementById('tbl-pct-' + name + '-' + pkg);
    const tblAmt = document.getElementById('tbl-amt-' + name + '-' + pkg);

    if (pctEl) pctEl.textContent = pct + '%';
    if (amtEl) amtEl.textContent = amt.toLocaleString('ar-JO') + ' د.أ';
    if (barEl) barEl.style.width = pct + '%';
    if (tblPct) tblPct.textContent = pct + '%';
    if (tblAmt) tblAmt.textContent = amt.toLocaleString('ar-JO');
  });

  // Update pie chart
  buildBudgetPie(name, total, alloc);
}

function buildBudgetPie(name, total, alloc) {
  const canvasId = 'budget-pie-' + name;
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const pkgs = Object.keys(alloc);
  const labels = pkgs.map(p => {
    const icons = {'البنية التحتية':'🏗️','الخدمات':'🏥','الإنتاج':'🌾'};
    return (icons[p]||'') + ' ' + p;
  });
  const values = pkgs.map(p => alloc[p]);
  const colors = ['#8b5cf6','#3b82f6','#22c55e'];
  const amounts = pkgs.map(p => Math.round(total * alloc[p] / 100));

  if (charts[canvasId]) charts[canvasId].destroy();
  charts[canvasId] = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        borderWidth: 3,
        borderColor: '#fff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {position: 'bottom', labels: {font: {family: 'Tahoma', size: 12}, padding: 16}},
        tooltip: {
          callbacks: {
            label: ctx => {
              const amt = amounts[ctx.dataIndex];
              return ctx.label + ': ' + ctx.raw + '% (' + amt.toLocaleString('ar-JO') + ' د.أ)';
            }
          }
        }
      }
    }
  });
}

// Override buildCharts to also build budget pie when on budget tab
const _origBuildCharts = buildCharts;
buildCharts = function(name) {
  _origBuildCharts(name);
  const input = document.getElementById('budget-input-' + name);
  if (input) {
    const govBd = BUDGET_DATA.governorates[name];
    if (govBd) buildBudgetPie(name, parseFloat(input.value)||0, govBd.allocation_pct);
  }
};
"""

# Inject before closing </script>
html = html.replace('</script>\n</body>', BUDGET_JS + '\n</script>\n</body>')

# Save
open('src/index.html', 'w', encoding='utf-8').write(html)
print('Budget module injected successfully!')
print('Final HTML size:', round(len(html)/1024, 1), 'KB')
