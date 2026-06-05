# -*- coding: utf-8 -*-
# inject_alignment.py — موائمة المشاريع (منهجية التقييم الرباعي الجديدة)

import json, os, sys
import re as _re
sys.stdout.reconfigure(encoding='utf-8')

data   = json.load(open('src/data.json',            encoding='utf-8'))
pred   = json.load(open('src/predictive_data.json', encoding='utf-8'))
budget = json.load(open('src/budget_data.json',     encoding='utf-8'))
html   = open('src/index.html', encoding='utf-8').read()

# ===== Sector categories (for step 1: sector weight) =====
SECTOR_CAT = {
    # Sovereign (50 pts) — الخدمات الكبرى ذات الأولوية الوطنية
    'التعليم':         'sovereign',
    'الصحة':           'sovereign',
    'البنية التحتية':  'sovereign',
    'المياه والصرف الصحي': 'sovereign',
    'الزراعة':         'sovereign',
    # Support (30 pts)
    'الثقافة':         'support',
    # Complementary (15 pts)
    'السياحة':         'complementary',
    # Support (30 pts)
    'التنمية الاجتماعية':'support',
}
CAT_POINTS = {'sovereign':50, 'support':30, 'complementary':15}
CAT_LABELS = {'sovereign':'سيادي','support':'مساند','complementary':'تكميلي'}

# ===== STEP 1: Add tab button (skip if already exists) =====
for g in data['governorates']:
    name = g['name']
    btn = f'onclick="switchTab(\'{name}\',\'alignment\')"'
    if btn in html:
        continue
    old = f'onclick="switchTab(\'{name}\',\'predictive\')">🔮 التحليل التنبؤي</button>'
    new = (f'onclick="switchTab(\'{name}\',\'predictive\')">🔮 التحليل التنبؤي</button>\n'
           f'<button class="tb" onclick="switchTab(\'{name}\',\'alignment\')">🎯 موائمة المشاريع</button>')
    html = html.replace(old, new)
print('Tab buttons injected')

# ===== Project suggestion templates =====
PROJECT_GAP_TEMPLATES = {
    'التعليم': [
        ('مركز التدريب المهني والتقني', 'رفع كفاءة مخرجات التعليم المهني لتقليل الفجوة مع احتياجات سوق العمل المحلي'),
        ('برنامج محو الأمية الرقمية', 'تمكين المواطنين من المهارات الرقمية الأساسية لتحسين فرص التوظيف'),
        ('مبادرة دعم التعليم المجتمعي', 'برامج تقوية ودعم للطلبة في المناطق الأقل حظاً لرفع نسب النجاح'),
    ],
    'الصحة': [
        ('مستشفى تخصصي', 'تغطية الفجوة في الخدمات الصحية التخصصية وتقليل الحاجة للسفر للمراكز الرئيسية'),
        ('برنامج عيادات متنقلة', 'سد الفجوة في وصول الخدمات الصحية الأساسية للمناطق النائية والمهمشة'),
        ('مركز الطوارئ والإسعاف', 'تطوير خدمات الطوارئ الطبية وتقليل زمن الاستجابة للحالات الحرجة'),
    ],
    'الزراعة': [
        ('مشروع استصلاح الأراضي الزراعية', 'معالجة تدهور الأراضي ورفع الإنتاجية الزراعية في المناطق المتأثرة'),
        ('مركز الإرشاد الزراعي', 'نقل التقنيات الحديثة للمزارعين لسد الفجوة في الممارسات الزراعية'),
        ('محطة أبحاث زراعية', 'تطوير أصناف محسنة من المحاصيل تتناسب مع الظروف المناخية للمحافظة'),
    ],
    'السياحة': [
        ('مشروع تطوير المواقع السياحية', 'استثمار المواقع غير المستغلة لتنشيط القطاع السياحي'),
        ('برنامج التسويق السياحي', 'الترويج للمقومات السياحية المحلية لجذب الزوار والمستثمرين'),
        ('مهرجان سياحي موسمي', 'تنظيم فعاليات سياحية دورية تستقطب الزوار وتنشط الحركة الاقتصادية'),
    ],
    'البنية التحتية': [
        ('شبكة طرق داخلية', 'تأهيل شبكات الطرق في المناطق المتضررة لتحسين الربط والوصول'),
        ('مشروع إنارة عامة ذكية', 'تطوير البنية التحتية للإنارة بخفض استهلاك الطاقة وتحسين الأمن'),
        ('حدائق ومنتزهات عامة', 'إنشاء مساحات خضراء ومرافق عامة لتحسين جودة الحياة'),
    ],
    'المياه والصرف الصحي': [
        ('محطة معالجة مياه', 'سد الفجوة في خدمات المياه عبر إنشاء محطة معالجة تخدم المناطق المحرومة'),
        ('شبكة صرف صحي', 'توسيع شبكات الصرف الصحي في التجمعات السكانية غير المخدومة'),
        ('خزانات مياه استراتيجية', 'إنشاء خزانات تجميع مياه لضمان التزويد في أوقات الذروة والجفاف'),
    ],
    'الثقافة': [
        ('مركز ثقافي مجتمعي', 'توفير فضاء ثقافي للشباب لتعزيز المشاركة المجتمعية والأنشطة الإبداعية'),
        ('برنامج دعم التراث المحلي', 'الحفاظ على التراث الثقافي غير المادي وتعزيز الهوية المحلية'),
        ('نادي الشباب والرياضة', 'إنشاء مرافق رياضية وشبابية لاستثمار طاقات الشباب بشكل إيجابي'),
    ],
    'التنمية الاجتماعية': [
        ('برنامج دعم الأسر المنتجة', 'تمكين الأسر المستفيدة من المعونات للتحول إلى أسر منتجة عبر التدريب والتمويل'),
        ('مركز التمكين الاجتماعي', 'تقديم خدمات الاستشارة والتدريب والتأهيل للأسر المحتاجة للخروج من دائرة الفقر'),
        ('نظام إدارة الحالة للأسر المحتاجة', 'تطوير قاعدة بيانات ذكية لمتابعة وتقييم احتياجات الأسر المتلقية للمعونات'),
    ],
}

PROJECT_OPP_TEMPLATES = {
    'التعليم': [
        ('مركز التميز التربوي', 'الاستفادة من الأداء التعليمي المتميز في بناء مركز إقليمي للتدريب والتأهيل'),
        ('منصة التعليم الذكي', 'تطوير بنية تعليمية رقمية تستثمر الكوادر التعليمية المتميزة في المحافظة'),
        ('برنامج المنح الدراسية', 'دعم الطلاب المتفوقين للدراسة في التخصصات النوعية المطلوبة'),
    ],
    'الصحة': [
        ('مركز الطب الوقائي', 'الاستثمار في القطاع الصحي المتطور لتعزيز الوقاية وتقليل الأعباء العلاجية المستقبلية'),
        ('مشروع السياحة العلاجية', 'استغلال الميزة التنافسية في الخدمات الصحية لجذب السياحة العلاجية'),
        ('بنك الدم المركزي', 'إنشاء مركز متقدم للتبرع بالدم وخدمات نقل الدم'),
    ],
    'الزراعة': [
        ('سوق المنتجات الزراعية', 'إنشاء سوق مركزي للمنتجات الزراعية يستفيد من فائض الإنتاج المحلي'),
        ('مركز التصنيع الغذائي', 'إضافة قيمة للمنتجات الزراعية عبر التصنيع والتعبئة والتغليف'),
        ('مشروع الزراعة المحمية', 'تطوير بيوت بلاستيكية وزراعات محمية لزيادة الإنتاج'),
    ],
    'السياحة': [
        ('مشروع الضيافة الريفية', 'تطوير تجربة سياحية فريدة تستثمر المقومات الطبيعية والتراثية'),
        ('مركز الزوار', 'إنشاء مركز استقبال سياحي يقدم خدمات متكاملة للسياح'),
        ('مسارات سياحية بيئية', 'تطوير مسارات للمشي والرحلات البيئية تستهدف سياح المغامرات'),
    ],
    'البنية التحتية': [
        ('البنية التحتية الخضراء', 'تطوير بنية تحتية صديقة للبيئة تستثمر الموقع الجغرافي المتميز'),
        ('مركز الخدمات اللوجستية', 'إنشاء مركز لوجستي يستفيد من موقع المحافظة الاستراتيجي'),
        ('مشروع المدن الذكية', 'تطبيق حلول المدن الذكية في إدارة المرافق والخدمات'),
    ],
    'المياه والصرف الصحي': [
        ('نظام حصاد مياه الأمطار', 'استثمار الموارد المائية المتاحة عبر أنظمة حصاد وتخزين ذكية'),
        ('مشروع إعادة استخدام المياه', 'استغلال المياه المعالجة في الأغراض الزراعية والصناعية'),
        ('محطة تحلية مياه', 'إنشاء محطة تحلية لتوفير مصادر مائية إضافية'),
    ],
    'الثقافة': [
        ('مهرجان التراث المحلي', 'تنظيم مهرجان سنوي للتراث والثقافة يستقطب الزوار ويعزز الاقتصاد المحلي'),
        ('مركز الإبداع الشبابي', 'مساحة للإبداع والابتكار تستثمر طاقات الشباب في مجالات الفنون والتقنية'),
        ('متحف المحافظة', 'إنشاء متحف يوثق تاريخ وتراث المحافظة ويعزز الهوية المحلية'),
    ],
    'التنمية الاجتماعية': [
        ('برنامج الشمول المالي للأسر', 'توفير خدمات مالية رقمية للأسر المستفيدة لتعزيز الاستقرار الاقتصادي'),
        ('مبادرة التكافل المجتمعي', 'إطلاق منصة للتبرع والتكافل تربط المتبرعين بالأسر المحتاجة بشفافية'),
        ('مركز التدخل المبكر', 'تقديم خدمات الكشف والتدخل المبكر للمشاكل الاجتماعية قبل تفاقمها'),
    ],
}

def calc_project_score(sec, gap_val):
    """Calculate alignment score assuming optimal inputs (maintenance, governorate, v.high density, >10 jobs)."""
    cat = SECTOR_CAT.get(sec, 'support')
    secPts = CAT_POINTS[cat]
    gapPct = gap_val / 100.0  # gap is stored as percentage
    gapPts = 25 if gapPct > 0.20 else (15 if gapPct >= 0.10 else 5)
    raw = (secPts/50)*0.25 + (gapPts/25)*0.25 + (20/20)*0.20 + (10/10)*0.10 + (10/10)*0.10 + (10/10)*0.10
    return round(raw * 100)

def gen_project_cards(gov_name, secs):
    """Generate 10 gap + 10 opportunity project cards — data-driven per governorate."""
    ALL_SECS = list(PROJECT_GAP_TEMPLATES.keys())
    scores = {s: d['score'] for s, d in secs.items()}
    gaps  = {s: d.get('gap', 0) for s, d in secs.items()}

    def pick_projects(templates, sectors, max_n, score_fn):
        """Pick up to max_n projects from given sectors, cycling through templates."""
        used = set()
        result = []
        ti = 0
        while len(result) < max_n and ti < 3:
            for sec in sectors:
                tmpls = templates.get(sec, [])
                if ti < len(tmpls):
                    nm, jst = tmpls[ti]
                    key = sec + '|' + nm
                    if key not in used:
                        used.add(key)
                        result.append((score_fn(sec), sec, nm, jst))
                        if len(result) >= max_n:
                            break
            ti += 1
        return result

    # Gap projects: ONLY sectors with positive gaps (underperforming)
    pos_gap_secs = sorted(
        [s for s in ALL_SECS if gaps.get(s, 0) > 0],
        key=lambda s: -gaps[s]
    )
    # Opportunity projects: ONLY top 5 sectors by score (best performing)
    top5_secs = sorted(ALL_SECS, key=lambda s: -scores.get(s, 0))[:5]

    def gap_score(sec): return calc_project_score(sec, gaps.get(sec, 0))
    def opp_score(sec): return scores.get(sec, 0)

    gap_cards = pick_projects(PROJECT_GAP_TEMPLATES, pos_gap_secs, 10, gap_score)
    opp_cards = pick_projects(PROJECT_OPP_TEMPLATES, top5_secs, 10, opp_score)
    return gap_cards, opp_cards

# ===== STEP 2: Build alignment data (scores + gaps + national_avgs only) =====
align_data = {}
for g in data['governorates']:
    name = g['name']
    secs = g['sectors']
    align_data[name] = {
        'sector_scores':   {s: round(d['score'], 2)       for s, d in secs.items()},
        'sector_gaps':     {s: round(d['gap'], 2)         for s, d in secs.items()},
        'national_avgs':   {s: round(d['national_avg'],2) for s, d in secs.items()},
        'sector_status':   {s: d['status']                for s, d in secs.items()},
    }
print(f'Alignment data built for {len(align_data)} governorates')

# ===== STEP 3: Build HTML tab per governorate =====
tabs = {}
for g in data['governorates']:
    name = g['name']
    h = []
    h.append(f'<div class="tc no-print" id="tab-{name}-alignment">')
    h.append(f'''<div style="background:linear-gradient(135deg,#fefce8,#fef9c3);border-radius:10px;padding:14px 18px;margin-bottom:16px;border-right:4px solid #eab308;display:flex;gap:12px;align-items:flex-start">
<span style="font-size:20px">🧮</span>
<div>
<div style="font-size:13px;font-weight:700;color:#713f12;margin-bottom:4px">موائمة المشاريع — منهجية تقييم كمية (6 معايير)</div>
<div style="font-size:12px;color:#374151;line-height:1.8">يعتمد التقييم على <strong>معادلة كمية</strong> تربط المشروع المقترح بواقع المحافظة عبر 6 معايير مرجحة: وزن القطاع، الفجوة التنموية، نوع المشروع، النطاق المكاني، الكثافة السكانية، والأثر التشغيلي.</div>
</div>
</div>''')
    h.append('<div class="cg">')

    # Input form
    h.append(f'''<div class="card fw">
<div class="ct">📝 بيانات المشاريع المقترحة</div>
<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin-bottom:10px">
  <div>
    <label style="font-size:12px;font-weight:700;color:#1a3a5c;display:block;margin-bottom:5px">اسم المشروع <span style="color:#ef4444">*</span></label>
    <input type="text" id="proj-name-{name}" placeholder="مثال: مركز تدريب مهني"
      style="width:100%;padding:9px 12px;border:2px solid #e5e7eb;border-radius:8px;font-size:13px;font-family:Tahoma,Arial;color:#1a3a5c"
      oninput="clearAlignResult('{name}')">
  </div>
  <div>
    <label style="font-size:12px;font-weight:700;color:#1a3a5c;display:block;margin-bottom:5px">القطاع المستهدف <span style="color:#ef4444">*</span></label>
    <select id="proj-sector-{name}"
      style="width:100%;padding:9px 12px;border:2px solid #e5e7eb;border-radius:8px;font-size:13px;font-family:Tahoma,Arial;color:#1a3a5c;background:#fff"
      onchange="clearAlignResult('{name}')">
      <option value="">-- اختر القطاع --</option>
      <option value="التعليم">التعليم</option>
      <option value="الصحة">الصحة</option>
      <option value="الزراعة">الزراعة</option>
      <option value="السياحة">السياحة</option>
      <option value="البنية التحتية">البنية التحتية</option>
      <option value="المياه والصرف الصحي">المياه والصرف الصحي</option>
      <option value="الثقافة">الثقافة</option>
      <option value="التنمية الاجتماعية">التنمية الاجتماعية</option>
    </select>
  </div>
  <div>
    <label style="font-size:12px;font-weight:700;color:#1a3a5c;display:block;margin-bottom:5px">نوع المشروع <span style="color:#ef4444">*</span></label>
    <select id="proj-type-{name}"
      style="width:100%;padding:9px 12px;border:2px solid #e5e7eb;border-radius:8px;font-size:13px;font-family:Tahoma,Arial;color:#1a3a5c;background:#fff"
      onchange="clearAlignResult('{name}')">
      <option value="">-- اختر نوع المشروع --</option>
      <option value="20" selected>صيانة وتأهيل</option>
      <option value="18">طوارئ</option>
      <option value="15">رأسمالي إنشائي</option>
      <option value="12">شراء وتوريد مواد</option>
      <option value="10">شراء خدمات</option>
      <option value="8">تقنية وتحول رقمي</option>
    </select>
  </div>
  <div>
    <label style="font-size:12px;font-weight:700;color:#1a3a5c;display:block;margin-bottom:5px">النطاق المكاني <span style="color:#ef4444">*</span></label>
    <select id="proj-scope-{name}"
      style="width:100%;padding:9px 12px;border:2px solid #e5e7eb;border-radius:8px;font-size:13px;font-family:Tahoma,Arial;color:#1a3a5c;background:#fff"
      onchange="clearAlignResult('{name}')">
      <option value="">-- اختر النطاق المكاني --</option>
      <option value="10" selected>مركز المحافظة (يخدم كافة المناطق)</option>
      <option value="7">لواء</option>
      <option value="4">قضاء</option>
      <option value="2">تجمع سكاني محدد</option>
    </select>
  </div>
  <div>
    <label style="font-size:12px;font-weight:700;color:#1a3a5c;display:block;margin-bottom:5px">الكثافة السكانية <span style="color:#ef4444">*</span></label>
    <select id="proj-density-{name}"
      style="width:100%;padding:9px 12px;border:2px solid #e5e7eb;border-radius:8px;font-size:13px;font-family:Tahoma,Arial;color:#1a3a5c;background:#fff"
      onchange="clearAlignResult('{name}')">
      <option value="">-- اختر الكثافة السكانية --</option>
      <option value="10" selected>عالية جداً</option>
      <option value="8">عالية</option>
      <option value="5">متوسطة</option>
      <option value="2">متدنية</option>
    </select>
  </div>
  <div>
    <label style="font-size:12px;font-weight:700;color:#1a3a5c;display:block;margin-bottom:5px">الأثر التشغيلي (فرص العمل) <span style="color:#ef4444">*</span></label>
    <select id="proj-employ-{name}"
      style="width:100%;padding:9px 12px;border:2px solid #e5e7eb;border-radius:8px;font-size:13px;font-family:Tahoma,Arial;color:#1a3a5c;background:#fff"
      onchange="clearAlignResult('{name}')">
      <option value="">-- اختر الأثر التشغيلي --</option>
      <option value="10" selected>أكثر من 10 فرص عمل مستدامة</option>
      <option value="5">أقل من 10 فرص عمل مستدامة</option>
      <option value="0">لا يوجد فرص عمل جديدة</option>
    </select>
  </div>
</div>
<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
  <button onclick="evalProject('{name}')"
    style="background:linear-gradient(135deg,#1a3a5c,#2a5298);color:#fff;border:none;padding:11px 28px;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:8px;box-shadow:0 4px 12px rgba(26,58,92,.3)">
    ⚡ احسب درجة الموائمة
  </button>
  <button onclick="resetAlign('{name}')"
    style="background:#f0f4ff;border:1px solid #c7d2fe;border-radius:8px;padding:11px 20px;font-size:13px;font-weight:600;cursor:pointer;color:#1a3a5c">
    🔄 مسح
  </button>
  <span id="align-err-{name}" style="font-size:12px;color:#ef4444;display:none">⚠️ يرجى إدخال اسم المشروع والقطاع ونوع المشروع والنطاق المكاني والكثافة السكانية</span>
</div>
</div>''')

    # Result area
    h.append(f'<div id="align-res-{name}" style="display:none" class="fw"></div>')

    # Methodology guide
    h.append(f'''<div class="card fw">
<div class="ct">📖 منهجية التقييم الكمي</div>
<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px">
  <div style="background:#fef2f2;border-radius:8px;padding:10px;border-right:3px solid #ef4444">
    <div style="font-size:11px;font-weight:700;color:#991b1b">① وزن القطاع (0.25)</div>
    <div style="font-size:10px;color:#374151;line-height:1.5">سيادي 50ن، مساند 30ن، تكميلي 15ن.</div>
  </div>
  <div style="background:#fffbeb;border-radius:8px;padding:10px;border-right:3px solid #f59e0b">
    <div style="font-size:11px;font-weight:700;color:#92400e">② الفجوة التنموية (0.25)</div>
    <div style="font-size:10px;color:#374151;line-height:1.5">(الوطني-المحافظة)÷الوطني. >20%=25ن، 10%-20%=15ن، <10%=5ن.</div>
  </div>
  <div style="background:#ecfeff;border-radius:8px;padding:10px;border-right:3px solid #06b6d4">
    <div style="font-size:11px;font-weight:700;color:#155e75">③ نوع المشروع (0.20)</div>
    <div style="font-size:10px;color:#374151;line-height:1.5">صيانة 20ن، طوارئ 18ن، إنشائي 15ن، توريد 12ن، خدمات 10ن، تقنية 8ن.</div>
  </div>
  <div style="background:#f0fdf4;border-radius:8px;padding:10px;border-right:3px solid #22c55e">
    <div style="font-size:11px;font-weight:700;color:#166534">④ النطاق المكاني (0.10)</div>
    <div style="font-size:10px;color:#374151;line-height:1.5">مركز محافظة 10ن، لواء 7ن، قضاء 4ن، تجمع محدد 2ن.</div>
  </div>
  <div style="background:#fff7ed;border-radius:8px;padding:10px;border-right:3px solid #f97316">
    <div style="font-size:11px;font-weight:700;color:#9a3412">⑤ الكثافة السكانية (0.10)</div>
    <div style="font-size:10px;color:#374151;line-height:1.5">عالية جداً 10ن، عالية 8ن، متوسطة 5ن، متدنية 2ن.</div>
  </div>
  <div style="background:#f5f3ff;border-radius:8px;padding:10px;border-right:3px solid #8b5cf6">
    <div style="font-size:11px;font-weight:700;color:#5b21b6">⑥ الأثر التشغيلي (0.10)</div>
    <div style="font-size:10px;color:#374151;line-height:1.5">>10 فرص 10ن، <10 فرص 5ن، لا يوجد 0ن.</div>
  </div>
</div>
<div style="margin-top:10px;background:#f8fafc;border-radius:8px;padding:10px 14px;font-size:12px;color:#1a3a5c;direction:ltr;text-align:center;font-weight:700">
  الموائمة = (القطاعx0.25)+(الفجوةx0.25)+(نوع المشروعx0.20)+(النطاقx0.10)+(الكثافةx0.10)+(التشغيلx0.10)
</div>
</div>''')

    # Suggested projects (removed per user request)

    h.append('</div>')  # end cg
    h.append('</div>')  # end tab
    tabs[name] = '\n'.join(h)

print(f'Alignment tabs built for {len(tabs)} governorates')

# ===== STEP 4: Inject tabs (skip if already injected) =====
for g in data['governorates']:
    name = g['name']
    if f'id="tab-{name}-alignment"' in html:
        print(f'  Skipped (exists): {name}')
        continue
    marker = f'<!-- END_PANEL_{name} -->'
    pos = html.find(marker)
    if pos == -1:
        print(f'  WARNING: marker not found for {name}')
        continue
    html = html[:pos] + '\n' + tabs[name] + '\n' + html[pos:]
    print(f'  Injected: {name}')
print('All tabs injected')

# ===== STEP 5: Build JS data =====
align_json = json.dumps(align_data, ensure_ascii=False)

# ===== STEP 6: Build JS engine =====
JS = (
    "\n// ===== ALIGNMENT MODULE =====\n"
    "var ALIGN_DATA=" + align_json + ";\n"
    "var SECTOR_CAT={" + ','.join(
        json.dumps(k)+':'+json.dumps(v) for k,v in SECTOR_CAT.items()
    ) + "};\n"
    "var CAT_POINTS={'sovereign':50,'support':30,'complementary':15};\n"
    "var CAT_LABELS={'sovereign':'سيادي','support':'مساند','complementary':'تكميلي'};\n"
    "\n"
    "function clearAlignResult(n){\n"
    "  var e=document.getElementById('align-res-'+n);\n"
    "  if(e)e.style.display='none';\n"
    "  var r=document.getElementById('align-err-'+n);\n"
    "  if(r)r.style.display='none';\n"
    "}\n"
    "\n"
    "function resetAlign(n){\n"
    "  ['proj-name-','proj-sector-'].forEach(function(id){var e=document.getElementById(id+n);if(e)e.value='';});\n"
    "  var t=document.getElementById('proj-type-'+n);if(t)t.value='20';\n"
    "  var s=document.getElementById('proj-scope-'+n);if(s)s.value='10';\n"
    "  var d=document.getElementById('proj-density-'+n);if(d)d.value='10';\n"
    "  var e=document.getElementById('proj-employ-'+n);if(e)e.value='10';\n"
    "  clearAlignResult(n);\n"
    "}\n"
    "\n"
    "function evalProject(name){\n"
    "  try {\n"
    "  var pn=((document.getElementById('proj-name-'+name)||{}).value||'').trim();\n"
    "  var sec=(document.getElementById('proj-sector-'+name)||{}).value||'';\n"
    "  var projTypePts=parseFloat((document.getElementById('proj-type-'+name)||{}).value)||0;\n"
    "  var scopePts=parseFloat((document.getElementById('proj-scope-'+name)||{}).value)||0;\n"
    "  var densityPts=parseFloat((document.getElementById('proj-density-'+name)||{}).value)||0;\n"
    "  var employPts=parseFloat((document.getElementById('proj-employ-'+name)||{}).value)||0;\n"
    "  var errEl=document.getElementById('align-err-'+name);\n"
    "  if(!pn||!sec||!projTypePts||!scopePts||!densityPts){if(errEl)errEl.style.display='inline';return;}\n"
    "  if(errEl)errEl.style.display='none';\n"
    "  var ad=ALIGN_DATA[name];if(!ad)return;\n"
    "\n"
    "  // (1) Sector weight (0.25)\n"
    "  var cat=SECTOR_CAT[sec]||'support';\n"
    "  var secPts=CAT_POINTS[cat];\n"
    "  var secLabel=CAT_LABELS[cat];\n"
    "  var secCalc='قطاع '+secLabel+' = '+secPts+' نقطة';\n"
    "\n"
    "  // (2) Gap coefficient (0.25)\n"
    "  var ssc=(ad.sector_scores||{})[sec]||0;\n"
    "  var nav=(ad.national_avgs||{})[sec]||0;\n"
    "  var gapVal=(ad.sector_gaps||{})[sec]||0;\n"
    "  var gapPct=nav>0?(nav-ssc)/nav:0;\n"
    "  var gapPts;\n"
    "  var gapCalc;\n"
    "  if(gapPct>0.20){gapPts=25;gapCalc='('+nav.toFixed(1)+'-'+ssc.toFixed(1)+')/'+nav.toFixed(1)+'='+(gapPct*100).toFixed(1)+'% > 20% → 25 نقطة';}\n"
    "  else if(gapPct>=0.10){gapPts=15;gapCalc='('+nav.toFixed(1)+'-'+ssc.toFixed(1)+')/'+nav.toFixed(1)+'='+(gapPct*100).toFixed(1)+'% (10%-20%) → 15 نقطة';}\n"
    "  else{gapPts=5;gapCalc='('+nav.toFixed(1)+'-'+ssc.toFixed(1)+')/'+nav.toFixed(1)+'='+(gapPct*100).toFixed(1)+'% < 10% → 5 نقاط';}\n"
    "  var gapLabel=gapPts>=25?'أولوية حرجة':gapPts>=15?'أولوية متوسطة':'أولوية منخفضة';\n"
    "\n"
    "  // (3) Project type (0.20) — from user input\n"
    "  var projTypeLabels={'20':'صيانة وتأهيل','18':'طوارئ','15':'رأسمالي إنشائي','12':'شراء وتوريد مواد','10':'شراء خدمات','8':'تقنية وتحول رقمي'};\n"
    "  var projTypeLabel=projTypeLabels[String(projTypePts)]||'صيانة وتأهيل';\n"
    "\n"
    "  // (4) Spatial scope (0.10) — from user input\n"
    "  var scopeLabels={'10':'مركز المحافظة','7':'لواء','4':'قضاء','2':'تجمع سكاني محدد'};\n"
    "  var scopeLabel=scopeLabels[String(scopePts)]||'مركز المحافظة';\n"
    "\n"
    "  // (5) Population density (0.10) — from user input\n"
    "  var densityLabels={'10':'عالية جداً','8':'عالية','5':'متوسطة','2':'متدنية'};\n"
    "  var densityLabel=densityLabels[String(densityPts)]||'عالية جداً';\n"
    "\n"
    "  // (6) Employment impact (0.10) — from user input\n"
    "  var employLabels={'10':'أكثر من 10 فرص عمل','5':'أقل من 10 فرص عمل','0':'لا يوجد فرص عمل جديدة'};\n"
    "  var employLabel=employLabels[String(employPts)]||'أكثر من 10 فرص عمل';\n"
    "\n"
    "  // Final alignment — normalized to 0-1 scale per criterion (6 criteria)\n"
    "  var finalRaw = (secPts/50)*0.25 + (gapPts/25)*0.25 + (projTypePts/20)*0.20 + (scopePts/10)*0.10 + (densityPts/10)*0.10 + (employPts/10)*0.10;\n"
    "  var finalPct = Math.round(finalRaw * 100);\n"
    "  var formula = '('+secPts+'/50x0.25)+('+gapPts+'/25x0.25)+('+projTypePts+'/20x0.20)+('+scopePts+'/10x0.10)+('+densityPts+'/10x0.10)+('+employPts+'/10x0.10)='+finalPct+'%';\n"
    "\n"
    "  // Classification\n"
    "  var cls,clr,bg,icn,isStrategic=false;\n"
    "  if(cat==='sovereign'&&finalPct>80){cls='مشروع استراتيجي واجب التنفيذ';clr='#1a3a5c';bg='#eef2ff';icn='🏆';isStrategic=true;}\n"
    "  else if(finalPct>=70){cls='مواءمة عالية جداً';clr='#166534';bg='#f0fdf4';icn='🟢';}\n"
    "  else if(finalPct>=55){cls='مواءمة عالية';clr='#1e40af';bg='#eff6ff';icn='🔵';}\n"
    "  else if(finalPct>=40){cls='مواءمة متوسطة';clr='#92400e';bg='#fffbeb';icn='🟡';}\n"
    "  else if(finalPct>=25){cls='مواءمة ضعيفة';clr='#6b7280';bg='#f9fafb';icn='⚪';}\n"
    "  else{cls='مواءمة ضعيفة جداً';clr='#991b1b';bg='#fef2f2';icn='🔴';}\n"
    "\n"
    "  // Table rows\n"
    "  var rows=[\n"
    "    {c:'وزن القطاع',v:secLabel+' ('+secPts+'ن)',m:secCalc,r:(secPts/50).toFixed(3),w:'0.25',wr:((secPts/50)*0.25).toFixed(3)},\n"
    "    {c:'الفجوة التنموية',v:gapLabel,m:gapCalc,r:(gapPts/25).toFixed(3),w:'0.25',wr:((gapPts/25)*0.25).toFixed(3)},\n"
    "    {c:'نوع المشروع',v:projTypeLabel,m:'إدخال المستخدم',r:(projTypePts/20).toFixed(3),w:'0.20',wr:((projTypePts/20)*0.20).toFixed(3)},\n"
    "    {c:'النطاق المكاني',v:scopeLabel,m:'إدخال المستخدم',r:(scopePts/10).toFixed(3),w:'0.10',wr:((scopePts/10)*0.10).toFixed(3)},\n"
    "    {c:'الكثافة السكانية',v:densityLabel,m:'إدخال المستخدم',r:(densityPts/10).toFixed(3),w:'0.10',wr:((densityPts/10)*0.10).toFixed(3)},\n"
    "    {c:'الأثر التشغيلي',v:employLabel,m:'إدخال المستخدم',r:(employPts/10).toFixed(3),w:'0.10',wr:((employPts/10)*0.10).toFixed(3)},\n"
    "  ];\n"
    "\n"
    "  var tbl='<table style=\"width:100%;border-collapse:collapse;font-size:12px;direction:rtl\">'\n"
    "    +'<thead><tr style=\"background:#1a3a5c;color:#fff\">'\n"
    "    +'<th style=\"padding:8px 6px;text-align:right\">المعيار</th>'\n"
    "    +'<th style=\"padding:8px 6px;text-align:center\">التصنيف</th>'\n"
    "    +'<th style=\"padding:8px 6px;text-align:center\">طريقة الاحتساب</th>'\n"
    "    +'<th style=\"padding:8px 6px;text-align:center\">النقاط</th>'\n"
    "    +'<th style=\"padding:8px 6px;text-align:center\">الوزن</th>'\n"
    "    +'<th style=\"padding:8px 6px;text-align:center\">المرجح</th>'\n"
    "    +'</tr></thead><tbody>'\n"
    "    +rows.map(function(r,i){\n"
    "      var bg2=i%2===0?'#f8fafc':'#fff';\n"
    "      return '<tr style=\"background:'+bg2+'\">'\n"
    "        +'<td style=\"padding:7px 6px;text-align:right;font-weight:600;color:#1a3a5c\">'+r.c+'</td>'\n"
    "        +'<td style=\"padding:7px 6px;text-align:center;color:#374151\">'+r.v+'</td>'\n"
    "        +'<td style=\"padding:7px 6px;text-align:center;font-size:11px;color:#6b7280;direction:ltr\">'+r.m+'</td>'\n"
    "        +'<td style=\"padding:7px 6px;text-align:center;font-weight:700;color:#1a3a5c\">'+r.r+'</td>'\n"
    "        +'<td style=\"padding:7px 6px;text-align:center;color:#6b7280\">'+r.w+'</td>'\n"
    "        +'<td style=\"padding:7px 6px;text-align:center;font-weight:700;color:'+(parseFloat(r.wr)>0.08?'#166534':'#92400e')+'\">'+r.wr+'</td>'\n"
    "        +'</tr>';\n"
    "    }).join('')+\n"
    "    '<tr style=\"background:#1a3a5c10;font-weight:800\">'+\n"
    "    '<td colspan=\"4\" style=\"padding:9px 6px;text-align:left;color:#1a3a5c\">درجة الموائمة النهائية</td>'+\n"
    "    '<td style=\"padding:9px 6px;text-align:center;color:#1a3a5c\">1.00</td>'+\n"
    "    '<td style=\"padding:9px 6px;text-align:center;color:'+clr+';font-size:15px\">'+finalPct+'%</td>'\n"
    "    +'</tr>'\n"
    "    +'</tbody></table>';\n"
    "\n"
    "  // Interpretation\n"
    "  var interp='';\n"
    "  interp+='<p>حصل المشروع <strong>\"'+pn+'\"</strong> على درجة موائمة <strong>'+finalPct+'%</strong> ('+cls+') في محافظة <strong>'+name+'</strong>.</p>';\n"
    "  if(isStrategic)interp+='<p style=\"background:#eef2ff;border-radius:6px;padding:8px 12px;border-right:3px solid #1a3a5c;font-size:12px;font-weight:700;color:#1a3a5c\">🏆 هذا المشروع سيادي استراتيجي وتجاوزت درجته 80% — يُصنف كمشروع واجب التنفيذ ضمن خطة التنمية المحلية.</p>';\n"
    "  interp+='<p><strong>تحليل النتائج:</strong></p><ul>';\n"
    "  if(cat==='sovereign')interp+='<li>القطاع سيادي — المشروع يستهدف قطاعاً ذا أولوية وطنية عليا ('+sec+').</li>';\n"
    "  else if(cat==='support')interp+='<li>القطاع مساند — المشروع يدعم قطاعاً تنموياً مسانداً ('+sec+') ويسهم في تحقيق التوازن التنموي.</li>';\n"
    "  else interp+='<li>القطاع تكميلي — المشروع في قطاع تكميلي ('+sec+') وله أثر محدود على الأولويات الوطنية.</li>';\n"
    "  if(gapPts>=25)interp+='<li>الفجوة التنموية حرجة — الفجوة بين أداء المحافظة والمعدل الوطني تتجاوز 20%. المشروع يسد فجوة حقيقية وملحة.</li>';\n"
    "  else if(gapPts>=15)interp+='<li>الفجوة التنموية متوسطة — الفجوة بين 10% و20%. المشروع يعزز الأداء القطاعي بشكل ملموس.</li>';\n"
    "  else interp+='<li>الفجوة التنموية منخفضة — أداء المحافظة قريب من المعدل الوطني (أقل من 10% فجوة). الأولوية للقطاعات الأخرى.</li>';\n"
    "  if(projTypePts>=18)interp+='<li>نوع المشروع — مشروع صيانة أو طوارئ يحافظ على استدامة الأصول ويجنب المخاطر.</li>';\n"
    "  else if(projTypePts>=15)interp+='<li>نوع المشروع — مشروع رأسمالي إنشائي يؤسس أصولاً دائمة.</li>';\n"
    "  else interp+='<li>نوع المشروع — مشروع توريد أو خدمات أو تقنية بأثر رأسمالي محدود.</li>';\n"
    "  if(scopePts>=10)interp+='<li>النطاق المكاني — المشروع يخدم كافة مناطق المحافظة (نطاق شامل).</li>';\n"
    "  else if(scopePts>=7)interp+='<li>النطاق المكاني — المشروع يخدم نطاق لواء.</li>';\n"
    "  else if(scopePts>=4)interp+='<li>النطاق المكاني — المشروع يخدم نطاق قضاء.</li>';\n"
    "  else interp+='<li>النطاق المكاني — المشروع يخدم تجمعاً سكانياً محدداً.</li>';\n"
    "  if(densityPts>=10)interp+='<li>الكثافة السكانية — المنطقة ذات كثافة عالية جداً تخدم أكبر عدد من المواطنين.</li>';\n"
    "  else if(densityPts>=8)interp+='<li>الكثافة السكانية — منطقة ذات كثافة عالية.</li>';\n"
    "  else if(densityPts>=5)interp+='<li>الكثافة السكانية — منطقة ذات كثافة متوسطة.</li>';\n"
    "  else interp+='<li>الكثافة السكانية — منطقة ذات كثافة متدنية مع تواجد سكاني مشتت.</li>';\n"
    "  if(employPts>=10)interp+='<li>الأثر التشغيلي — المشروع يخلق أكثر من 10 فرص عمل مستدامة.</li>';\n"
    "  else if(employPts>=5)interp+='<li>الأثر التشغيلي — المشروع يخلق أقل من 10 فرص عمل مستدامة.</li>';\n"
    "  else interp+='<li>الأثر التشغيلي — المشروع لا يخلق فرص عمل جديدة (خدمي بحت).</li>';\n"
    "  interp+='</ul>';\n"
    "\n"
    "  // Strengths / Weaknesses\n"
    "  var strengths=[],weaknesses=[];\n"
    "  if(cat==='sovereign')strengths.push('قطاع سيادي ذو أولوية وطنية');\n"
    "  if(gapPts>=25)strengths.push('يسد فجوة تنموية حرجة تتجاوز 20%');\n"
    "  else if(gapPts>=15)strengths.push('يعالج فجوة تنموية متوسطة');\n"
    "  if(projTypePts>=18)strengths.push('صيانة أو طوارئ — يحافظ على الأصول ويجنب المخاطر');\n"
    "  else if(projTypePts>=15)strengths.push('استثمار رأسمالي دائم');\n"
    "  if(scopePts>=10)strengths.push('يخدم كافة المحافظة — نطاق شامل');\n"
    "  else if(scopePts>=7)strengths.push('يخدم نطاق لواء');\n"
    "  if(densityPts>=10)strengths.push('منطقة كثافة عالية جداً — يخدم عدداً كبيراً من المواطنين');\n"
    "  else if(densityPts>=8)strengths.push('منطقة كثافة عالية');\n"
    "  if(employPts>=10)strengths.push('يخلق أكثر من 10 فرص عمل مستدامة');\n"
    "  else if(employPts>=5)strengths.push('يخلق فرص عمل محدودة');\n"
    "  if(cat!=='sovereign')weaknesses.push('القطاع غير سيادي (أولوية تنموية أقل)');\n"
    "  if(gapPts<15)weaknesses.push('فجوة تنموية منخفضة — القطاع لا يعاني من تأخر كبير');\n"
    "  if(projTypePts<15)weaknesses.push('نوع المشروع — أثر رأسمالي محدود (توريد/خدمات/تقنية)');\n"
    "  if(scopePts<7)weaknesses.push('النطاق المكاني محدود (قضاء أو تجمع محدد)');\n"
    "  if(densityPts<8)weaknesses.push('الكثافة السكانية متوسطة أو متدنية');\n"
    "  if(employPts<5)weaknesses.push('لا يخلق فرص عمل جديدة');\n"
    "  if(weaknesses.length===0&&strengths.length>1)weaknesses.push('لا توجد محدّدات جوهرية — المشروع ذو موائمة جيدة');\n"
    "\n"
    "  var sw='<div style=\"display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px\">';\n"
    "  sw+='<div style=\"background:#f0fdf4;border-radius:8px;padding:10px 14px;border-right:3px solid #22c55e\">';\n"
    "  sw+='<div style=\"font-size:12px;font-weight:700;color:#166534;margin-bottom:6px\">✅ نقاط القوة</div>';\n"
    "  sw+=(strengths.length?strengths.map(function(s){return '<div style=\"font-size:11px;color:#374151;padding:3px 0\">● '+s+'</div>';}).join(''):'<div style=\"font-size:11px;color:#6b7280\">لا توجد نقاط قوة بارزة</div>');\n"
    "  sw+='</div>';\n"
    "  sw+='<div style=\"background:#fef2f2;border-radius:8px;padding:10px 14px;border-right:3px solid #ef4444\">';\n"
    "  sw+='<div style=\"font-size:12px;font-weight:700;color:#991b1b;margin-bottom:6px\">⚠️ المحددات</div>';\n"
    "  sw+=(weaknesses.length?weaknesses.map(function(w){return '<div style=\"font-size:11px;color:#374151;padding:3px 0\">● '+w+'</div>';}).join(''):'<div style=\"font-size:11px;color:#6b7280\">لا توجد محدّدات جوهرية</div>');\n"
    "  sw+='</div></div>';\n"
    "\n"
    "  // Summary\n"
    "  var summary='';\n"
    "  if(isStrategic)summary='المشروع <strong>\"'+pn+'\"</strong> مشروع سيادي استراتيجي تجاوزت درجة مواءمته 80%. يُوصى بإدراجه فوراً في خطة التنمية المحلية كمشروع واجب التنفيذ.';\n"
    "  else if(finalPct>=55)summary='المشروع يتمتع بموائمة عالية مع احتياجات محافظة '+name+'. يلامس أولويات تنموية حقيقية ويُوصى بإدراجه في خطة التنمية.';\n"
    "  else if(finalPct>=40)summary='المشروع يتمتع بموائمة متوسطة. يمكن تحسين درجته عبر اختيار قطاع سيادي أو استهداف مناطق أكثر احتياجاً.';\n"
    "  else summary='المشروع ذو موائمة منخفضة مع واقع المحافظة. يُنصح بإعادة تقييم أولويات المشروع أو توجيهه لقطاع أكثر احتياجاً.';\n"
    "\n"
    "  // ===== Render =====\n"
    "  var rEl=document.getElementById('align-res-'+name);\n"
    "  if(!rEl)return;\n"
    "  rEl.innerHTML='<div class=\"cg\">'\n"
    "    +'<div class=\"card\" style=\"text-align:center;padding:20px\">'\n"
    "    +'<div class=\"ct\">🎯 نتيجة الموائمة التنموية — '+pn+'</div>'\n"
    "    +'<div style=\"font-size:64px;font-weight:800;color:'+clr+';line-height:1.1\">'+finalPct+'<span style=\"font-size:28px\">%</span></div>'\n"
    "    +'<div style=\"font-size:13px;color:#6b7280;margin-bottom:12px\">من 100</div>'\n"
    "    +'<div style=\"background:'+bg+';border-radius:10px;padding:10px 18px;margin-bottom:10px;border:2px solid '+clr+'40;display:inline-block\">'\n"
    "    +'<span style=\"font-size:15px;font-weight:800;color:'+clr+'\">'+icn+' '+cls+'</span>'\n"
    "    +'</div>'\n"
    "    +'<div style=\"height:12px;background:#e5e7eb;border-radius:6px;overflow:hidden;max-width:400px;margin:0 auto\">'\n"
    "    +'<div style=\"height:100%;width:'+finalPct+'%;background:'+clr+';border-radius:6px;transition:width 1s ease\"></div>'\n"
    "    +'</div>'\n"
    "    +'<div style=\"font-size:11px;color:#6b7280;margin-top:8px\">القطاع: <strong>'+sec+'</strong> | المحافظة: <strong>'+name+'</strong></div>'\n"
    "    +'</div>'\n"
    "    // Detailed table\n"
    "    +'<div class=\"card\"><div class=\"ct\">📊 جدول الحسابات التفصيلية</div>'+tbl+'</div>'\n"
    "    // Formula\n"
    "    +'<div class=\"card\" style=\"background:#f8fafc\">'\n"
    "    +'<div class=\"ct\" style=\"font-size:12px\">🧮 المعادلة النهائية</div>'\n"
    "    +'<div style=\"font-size:12px;color:#1a3a5c;direction:ltr;text-align:center;font-weight:600;padding:6px;font-family:Consolas,monospace\">'+formula+'</div>'\n"
    "    +'</div>'\n"
    "    // Interpretation\n"
    "    +'<div class=\"card\"><div class=\"ct\">📝 التفسير التحليلي للنتيجة</div>'\n"
    "    +'<div style=\"font-size:12px;color:#374151;line-height:1.9\">'+interp+'</div>'\n"
    "    +sw+'</div>'\n"
    "    // Summary\n"
    "    +'<div class=\"card\" style=\"background:linear-gradient(135deg,#eff6ff,#dbeafe);border-right:4px solid #1a3a5c\">'\n"
    "    +'<div class=\"ct\" style=\"color:#1a3a5c\">📌 الخلاصة</div>'\n"
    "    +'<div style=\"font-size:12px;color:#374151;line-height:1.9\">'+summary+'</div>'\n"
    "    +'</div>'\n"
    "    // Scale explanation\n"
    "    +'<div class=\"card\" style=\"background:#f9fafb\">'\n"
    "    +'<div class=\"ct\" style=\"font-size:12px;color:#374151\">📖 شرح مقياس الموائمة التنموية</div>'\n"
    "    +'<div style=\"font-size:11px;color:#374151;line-height:1.9\">'\n"
    "    +'<ul style=\"margin:0;padding-right:18px\">'\n"
    "    +'<li>يعتمد المقياس على تحليل الفجوات التنموية الفعلية المستخرجة من بيانات محافظة '+name+'.</li>'\n"
    "    +'<li>ارتفاع الدرجة يعني ارتفاع توافق المشروع مع أولويات المحافظة التنموية بناءً على 6 معايير مرجحة.</li>'\n"
    "    +'<li>الأوزان: القطاع (25%)، الفجوة (25%)، نوع المشروع (20%)، النطاق (10%)، الكثافة (10%)، التشغيل (10%).</li>'\n"
    "    +'<li>المشاريع السيادية التي تتجاوز 80% تُصنف كمشاريع استراتيجية واجبة التنفيذ.</li>'\n"
    "    +'<li>الهدف من المقياس هو دعم ترتيب أولويات المشاريع بشكل موضوعي وقابل للتفسير.</li>'\n"
    "    +'</ul>'\n"
    "    +'</div>'\n"
    "    +'</div>'\n"
    "    +'</div>';\n"
    "  rEl.style.display='block';\n"
    "  setTimeout(function(){rEl.scrollIntoView({behavior:'smooth',block:'start'});},100);\n"
    "  }catch(e){console.error('Alignment eval error:',e)}\n"
    "}\n"
)

# ===== STEP 7: Inject JS and save =====
html = _re.sub(r'\n// ===== ALIGNMENT MODULE =====.*?(?=\n</script>\n</body>)', '', html, flags=_re.DOTALL)
html = html.replace('</script>\n</body>', JS + '\n</script>\n</body>', 1)
open('src/index.html', 'w', encoding='utf-8').write(html)

size = os.path.getsize('src/index.html')
print(f'Alignment module complete. Final size: {size/1024:.1f} KB')
