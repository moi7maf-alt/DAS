# solutions tab

import json

data = json.load(open('src/data.json', encoding='utf-8'))
plans = json.load(open('src/strategic_plans.json', encoding='utf-8'))

# ===== SOLUTIONS LIBRARY =====
# الهيكل الجديد: تقليدي + ذكي + نماذج دول لكل قطاع
# traditional: حلول تقليدية مجربة قابلة للتنفيذ في الأردن
# smart: حلول ذكية مبتكرة تناسب الواقع الأردني
# examples: نماذج من دول نجحت
LOCAL_SOLUTIONS = {
    'التعليم': {
        'traditional': [
            {'t': 'برنامج الحوافز المالية للأسر', 'd': 'منح شهرية للأسر المعرضة للتسرب مشروطة بحضور الأبناء المدرسي 85%. مطبق في برنامج معونة الأسرة الأردني ويمكن توسيعه.'},
            {'t': 'شراكة الجامعات والمدارس', 'd': 'طلاب الجامعات يعملون كمرشدين أكاديميين في المدارس مقابل ساعات معتمدة. يستفيد الطرفان ويقلل التسرب.'},
            {'t': 'فصول مسائية للمتسربين والكبار', 'd': 'فصول بعد الظهر في المدارس الحكومية تستوعب المتسربين والعمال الكبار. تجربة ناجحة في محافظات أردنية عدة.'},
        ],
        'smart': [
            {'t': 'منصة تعلم ذكي محلية', 'd': 'تطبيق أردني يقدم دروساً مسجلة بأصوات معلمين متميزين لكل طالب في المملكة. يعمل بدون إنترنت عبر تحميل مسبق.'},
            {'t': 'الفصل المعكوس بالمحتوى المحلي', 'd': 'الطالب يشاهد الدرس فيديو في البيت، والفصل للتطبيق والنقاش. يرفع معدلات الفهم 28% ويقلل الرسوب.'},
            {'t': 'حافلة التعليم المتنقلة', 'd': 'حافلة مجهزة بتقنيات تعليمية تصل للقرى النائية أسبوعياً. تناسب محافظات البادية والمناطق الجبلية.'},
        ],
        'examples': [
            {'c': 'فنلندا', 't': 'معلم الحي المتنقل', 'r': 'رفع الالتحاق 18% في 4 سنوات'},
            {'c': 'البرازيل', 't': 'المنحة المشروطة Bolsa Família', 'r': 'خفض التسرب 36% في 5 سنوات'},
            {'c': 'إستونيا', 't': 'المدرسة الرقمية الكاملة', 'r': 'الأولى في أوروبا في مهارات الرياضيات'},
        ],
        'advanced': [
            {'t': 'مركز التميز التعليمي الإقليمي', 'd': 'تحويل المحافظة لمرجع تعليمي يستقطب الطلاب من المحافظات المجاورة ويصدّر الكفاءات التعليمية.'},
        ],
    },
    'الصحة': {
        'traditional': [
            {'t': 'برنامج الصحة المجتمعية المحلية', 'd': 'تدريب 50 مرشداً صحياً من أبناء كل قرية للكشف المبكر والتطعيم والتوعية. تكلفة منخفضة وأثر واسع.'},
            {'t': 'شراكة المستشفيات الخاصة والحكومية', 'd': 'اتفاقيات لتقديم خدمات متخصصة بأسعار مدعومة لأبناء المحافظة في المستشفيات الخاصة.'},
            {'t': 'عيادات متنقلة للمناطق النائية', 'd': 'سيارات مجهزة بمعدات طبية أساسية تزور القرى البعيدة أسبوعياً. تقلل الحاجة للسفر للمدينة.'},
        ],
        'smart': [
            {'t': 'التيليميديسين المحلي', 'd': 'شاشات في المراكز الصحية الريفية تربط المريض بأطباء متخصصين في عمّان. تقلل الحاجة للسفر 70%.'},
            {'t': 'تطبيق الصحة الذكي للمواطن', 'd': 'تطبيق يتيح حجز المواعيد ومتابعة الملف الصحي وتلقي تذكيرات الدواء. يخفف الضغط على المراكز الصحية.'},
            {'t': 'الدرونز الطبية للمناطق الجبلية', 'd': 'طائرات مسيّرة توصل الأدوية والمستلزمات الطبية للقرى الجبلية النائية في وقت قياسي.'},
        ],
        'examples': [
            {'c': 'رواندا', 't': 'Zipline للدرونز الطبية', 'r': 'خفض وفيات الأمهات 88%'},
            {'c': 'كوبا', 't': 'طبيب الحي المقيم', 'r': 'مؤشرات صحية تفوق دولاً أغنى بـ 10 أضعاف'},
            {'c': 'الهند', 't': 'eSanjeevani للتيليميديسين', 'r': '100 مليون استشارة طبية'},
        ],
        'advanced': [
            {'t': 'مركز الصحة الوقائية الإقليمي', 'd': 'استثمار التفوق الصحي بإنشاء مركز إقليمي للطب الوقائي يخدم المحافظات المجاورة ويستقطب السياحة الصحية.'},
        ],
    },
    'الزراعة': {
        'traditional': [
            {'t': 'تعاونيات الزراعة التعاقدية', 'd': 'عقود مسبقة مع شركات الغذاء لضمان تسويق المحاصيل قبل الزراعة. تحمي المزارع من تقلبات الأسعار.'},
            {'t': 'مراكز التجميع والتبريد المشتركة', 'd': 'مستودعات تبريد مشتركة تموّلها الدولة وتديرها التعاونيات. تخفض هدر الخضروات من 40% إلى 8%.'},
            {'t': 'برنامج الإرشاد الزراعي الميداني', 'd': 'مرشدون زراعيون يزورون المزارعين ميدانياً ويقدمون توصيات مخصصة لكل مزرعة. يرفع الإنتاجية 20%.'},
        ],
        'smart': [
            {'t': 'الزراعة الدقيقة بأجهزة الاستشعار', 'd': 'أجهزة استشعار في التربة ترسل بيانات الرطوبة والمغذيات للمزارع على هاتفه. تقلل استهلاك المياه 40%.'},
            {'t': 'منصة التسويق الزراعي الرقمي', 'd': 'تطبيق يربط المزارعين مباشرة بالمستهلكين والمطاعم دون وسطاء. يرفع دخل المزارع 30%.'},
            {'t': 'الزراعة العمودية في البيوت المحمية', 'd': 'إنتاج الخضروات في مستودعات مضاءة بـ LED بدون تربة. إنتاجية أعلى بـ 95% أقل مياهاً. مناسب للمناطق الجافة.'},
        ],
        'examples': [
            {'c': 'اليابان', 't': 'الزراعة الدقيقة بالاستشعار', 'r': 'رفع إنتاجية الأرز 35%'},
            {'c': 'كينيا', 't': 'M-Farm للتسويق الرقمي', 'r': 'رفع دخل المزارع 30%'},
            {'c': 'نيوزيلندا', 't': 'العلامة التجارية الجغرافية المحمية', 'r': 'بيع المنتجات بـ 3 أضعاف السعر العالمي'},
        ],
        'advanced': [
            {'t': 'مركز التصدير الزراعي الإقليمي', 'd': 'استثمار الإنتاج الزراعي المتميز بإنشاء مركز تصدير إقليمي مع تسجيل علامة جغرافية محمية للمنتجات المحلية.'},
        ],
    },
    'السياحة': {
        'traditional': [
            {'t': 'مهرجانات الهوية المحلية الموسمية', 'd': 'مهرجانات سنوية تبرز الموروث الثقافي والمنتجات المحلية والطعام التقليدي. تجذب آلاف الزوار وتخلق دخلاً موسمياً.'},
            {'t': 'شبكة المرشدين السياحيين المحليين', 'd': 'تدريب وتوظيف شباب المحافظة كمرشدين سياحيين معتمدين. يخلق وظائف ويحسن تجربة الزائر.'},
            {'t': 'تطوير مسارات سياحية مترابطة', 'd': 'ربط المواقع الأثرية والطبيعية بمسارات واضحة مع لافتات ومرافق. يطيل مدة إقامة الزائر.'},
        ],
        'smart': [
            {'t': 'تطبيق AR لإحياء المواقع الأثرية', 'd': 'تطبيق يُعيد بناء المواقع الأثرية افتراضياً على هاتف الزائر. يحوّل أي موقع أثري لتجربة سينمائية تفاعلية.'},
            {'t': 'قرى الإقامة الأصيلة', 'd': 'السياح يقيمون في بيوت الأسر المحلية ويعيشون حياتهم اليومية. يخلق دخلاً لـ 500 أسرة في كل قرية.'},
            {'t': 'منصة الحجز السياحي المحلية', 'd': 'منصة رقمية تجمع كل المنشآت السياحية في المحافظة وتتيح الحجز المباشر. تقلل الاعتماد على وسطاء خارجيين.'},
        ],
        'examples': [
            {'c': 'اليابان', 't': 'Minpaku قرى الإقامة الأصيلة', 'r': '4 مليار دولار سنوياً'},
            {'c': 'بيرو', 't': 'AR لماتشو بيتشو', 'r': 'رفع الإيرادات 40%'},
            {'c': 'إيطاليا', 't': 'مهرجانات الطعام المحلي', 'r': '500,000 زائر لمهرجان واحد'},
        ],
        'advanced': [
            {'t': 'مركز المؤتمرات والفعاليات الإقليمي', 'd': 'تحويل المحافظة لوجهة للمؤتمرات والفعاليات الإقليمية. يجني 30% من الإيرادات السياحية في دبي.'},
        ],
    },
    'البنية التحتية': {
        'traditional': [
            {'t': 'صيانة الطرق بالمقاولين المحليين', 'd': 'برنامج تأهيل مقاولين محليين لصيانة الطرق الريفية بتكلفة أقل 30% من المقاولين الخارجيين.'},
            {'t': 'مشاركة المجتمع في بناء الطرق', 'd': 'مجتمعات ريفية تشارك في بناء طرقها مقابل أجر يومي من الحكومة. يخلق وظائف ويبني البنية التحتية معاً.'},
            {'t': 'تحسين الإضاءة في الطرق الريفية', 'd': 'إضاءة الطرق الريفية بألواح شمسية. تقلل الحوادث الليلية 60% وتوفر تكاليف الكهرباء.'},
        ],
        'smart': [
            {'t': 'الكابلكار للقرى الجبلية', 'd': 'تلفريك يربط القرى الجبلية بالمراكز الحضرية بدل الطرق المكلفة. يخفض وقت التنقل من 90 دقيقة إلى 10 دقائق.'},
            {'t': 'تطبيق النقل المشترك الريفي', 'd': 'تطبيق يربط سكان القرى لمشاركة رحلات السيارات. يخفض تكلفة التنقل 50% ويعمل بدون إنترنت.'},
            {'t': 'منصة الإبلاغ عن مشاكل الطرق', 'd': 'تطبيق يتيح للمواطنين الإبلاغ عن حفر وأعطال الطرق بصورة فورية. يسرّع الصيانة ويوفر التكاليف.'},
        ],
        'examples': [
            {'c': 'كولومبيا', 't': 'كابلكار ميديين للأحياء الجبلية', 'r': 'خفض وقت التنقل من 90 إلى 10 دقائق'},
            {'c': 'رواندا', 't': 'الطرق الذكية بالطاقة الشمسية', 'r': '2,000 كم بتكلفة 20% من الشبكة الكهربائية'},
            {'c': 'سنغافورة', 't': 'المدينة الذكية المتكاملة', 'r': 'توفير 20% من تكاليف الصيانة'},
        ],
        'advanced': [
            {'t': 'مركز اللوجستيات الإقليمي', 'd': 'استثمار شبكة الطرق المتقدمة بإنشاء مركز لوجستي يخدم المحافظات المجاورة ويستقطب الاستثمارات.'},
        ],
    },
    'المياه والصرف الصحي': {
        'traditional': [
            {'t': 'حملات ترشيد استهلاك المياه', 'd': 'برنامج توعية مجتمعي مع حوافز للأسر الموفرة للمياه. يخفض الاستهلاك 15-20% بتكلفة منخفضة.'},
            {'t': 'تأهيل شبكات المياه القديمة', 'd': 'استبدال الأنابيب المتهالكة لتقليل الفاقد. الأردن يفقد 40% من المياه في الشبكات القديمة.'},
            {'t': 'خزانات المجتمع المشتركة', 'd': 'خزانات مياه مشتركة تُبنى وتُدار من المجتمع بدعم حكومي. تضمن الأمن المائي في انقطاعات الشبكة.'},
        ],
        'smart': [
            {'t': 'إعادة استخدام مياه الصرف الصحي للري', 'd': 'معالجة مياه الصرف الصحي وتوجيهها للري الزراعي. الأردن يُعيد 50% فقط ويمكن رفعها لـ 80%.'},
            {'t': 'حصاد مياه الأمطار من الأسطح', 'd': 'أنظمة حصاد مياه الأمطار على مستوى الأحياء مع خزانات مجتمعية ذكية. تغطي 25% من الاحتياجات.'},
            {'t': 'أجهزة استشعار تسرب المياه الذكية', 'd': 'أجهزة تكتشف تسرب المياه في الشبكات فوراً وترسل تنبيهاً للصيانة. تقلل الفاقد 30%.'},
        ],
        'examples': [
            {'c': 'سنغافورة', 't': 'NEWater إعادة استخدام 90% من مياه الصرف', 'r': 'تغطي 40% من الاحتياجات المائية'},
            {'c': 'المغرب', 't': 'الصرف الصحي اللامركزي للقرى', 'r': 'رفع التغطية من 28% إلى 72% في 8 سنوات'},
            {'c': 'أستراليا', 't': 'حصاد مياه الأمطار الحضري', 'r': 'تغطية 25% من الاحتياجات المنزلية'},
        ],
        'advanced': [
            {'t': 'نموذج الكفاءة المائية الوطني', 'd': 'تحويل تجربة المحافظة في ترشيد المياه لنموذج يُعمم وطنياً ويُصدَّر إقليمياً.'},
        ],
    },
    'الثقافة': {
        'traditional': [
            {'t': 'تفعيل الجمعيات الخيرية والثقافية', 'd': 'برنامج دعم وتأهيل الجمعيات لتوسيع خدماتها المجتمعية وتحسين حوكمتها.'},
            {'t': 'مراكز الشباب المتعددة الخدمات', 'd': 'مراكز تجمع التدريب المهني والرياضة والفنون والإرشاد النفسي تحت سقف واحد. تكلفة أقل من مرافق منفصلة.'},
            {'t': 'مهرجانات التراث المحلي السنوية', 'd': 'مهرجانات تبرز الموروث الثقافي والحرف التقليدية والطعام المحلي. تخلق دخلاً وتعزز الهوية.'},
        ],
        'smart': [
            {'t': 'الأرشيف الرقمي للتراث الشفهي', 'd': 'تسجيل القصص والأغاني والحكايات من كبار السن رقمياً. يحفظ الهوية ويخلق محتوى سياحياً فريداً.'},
            {'t': 'المتحف الرقمي المجتمعي', 'd': 'أرشفة رقمية للتراث المحلي وإتاحته عبر تطبيق تفاعلي للأجيال القادمة.'},
            {'t': 'مراكز الإبداع الشبابي', 'd': 'مساحات عمل مشتركة للشباب المبدع في الفنون والتكنولوجيا والحرف. تحوّل الإبداع لمصدر دخل.'},
        ],
        'examples': [
            {'c': 'اليابان', 't': 'إحياء القرى المهجورة بالفن (Naoshima)', 'r': '700,000 زائر سنوياً لقرية صيد مهجورة'},
            {'c': 'إيرلندا', 't': 'الأرشيف الرقمي للتراث الشفهي', 'r': '50,000 ساعة من التراث محفوظة'},
            {'c': 'كولومبيا', 't': 'مراكز الشباب المتعددة الخدمات', 'r': 'خفض جرائم الشباب 80% في ميديين'},
        ],
        'advanced': [
            {'t': 'عاصمة الثقافة الإقليمية', 'd': 'استثمار الرصيد الثقافي لاستضافة فعاليات ثقافية إقليمية وبناء صناعة محتوى رقمي يُسوّق للعالم.'},
        ],
    },
}

# ===== VISION 2033 SOLUTIONS =====
VISION_2033 = [
    {
        'pillar': 'الاقتصاد الرقمي',
        'icon': '💻',
        'color': '#3b82f6',
        'solutions': [
            {'title': 'مناطق التقنية المحلية', 'desc': 'إنشاء حاضنات تقنية في كل محافظة لدعم الشركات الناشئة الرقمية وفق أهداف رؤية 2033 لرفع مساهمة الاقتصاد الرقمي'},
            {'title': 'التحول الرقمي للخدمات الحكومية المحلية', 'desc': 'رقمنة كافة خدمات مجلس المحافظة وربطها بمنصة الحكومة الرقمية الوطنية'},
            {'title': 'برنامج المهارات الرقمية للشباب', 'desc': 'تدريب 1000 شاب سنوياً على مهارات الاقتصاد الرقمي بالتنسيق مع وزارة الاقتصاد الرقمي'},
        ]
    },
    {
        'pillar': 'الطاقة المتجددة',
        'icon': '⚡',
        'color': '#f59e0b',
        'solutions': [
            {'title': 'مشاريع الطاقة الشمسية المجتمعية', 'desc': 'تركيب ألواح شمسية على المباني الحكومية والمدارس لتحقيق هدف رؤية 2033 برفع حصة الطاقة المتجددة إلى 31%'},
            {'title': 'مجمعات الطاقة الريفية', 'desc': 'توليد الطاقة محلياً في القرى النائية وتصدير الفائض للشبكة الوطنية'},
        ]
    },
    {
        'pillar': 'السياحة المستدامة',
        'icon': '🌿',
        'color': '#22c55e',
        'solutions': [
            {'title': 'مسارات السياحة البيئية الوطنية', 'desc': 'ربط المحافظة بالمسار السياحي الوطني المندرج ضمن رؤية 2033 لمضاعفة إيرادات السياحة'},
            {'title': 'شهادة الاستدامة السياحية', 'desc': 'تأهيل المنشآت السياحية للحصول على شهادات الاستدامة الدولية'},
        ]
    },
    {
        'pillar': 'التعليم والتدريب المهني',
        'icon': '🎓',
        'color': '#8b5cf6',
        'solutions': [
            {'title': 'مراكز التدريب المهني المتخصصة', 'desc': 'إنشاء مراكز تدريب مهني تلبي احتياجات سوق العمل المستقبلي وفق خارطة الوظائف في رؤية 2033'},
            {'title': 'برنامج التعليم المزدوج', 'desc': 'شراكات بين المدارس والشركات لتطبيق نموذج التعليم المزدوج الألماني'},
        ]
    },
    {
        'pillar': 'الصحة والاقتصاد الصحي',
        'icon': '🏥',
        'color': '#ef4444',
        'solutions': [
            {'title': 'السياحة الصحية المحلية', 'desc': 'تطوير خدمات صحية متخصصة تستقطب المرضى من المحافظات المجاورة وتساهم في الاقتصاد الصحي'},
            {'title': 'الصحة الرقمية', 'desc': 'تطبيق منظومة الصحة الرقمية الوطنية محلياً لتحسين الكفاءة وتقليل التكاليف'},
        ]
    },
    {
        'pillar': 'الزراعة الحديثة والأمن الغذائي',
        'icon': '🌾',
        'color': '#10b981',
        'solutions': [
            {'title': 'الزراعة الدقيقة بالبيانات', 'desc': 'استخدام أجهزة الاستشعار والبيانات لتحسين الإنتاجية الزراعية وتقليل الهدر وفق أهداف الأمن الغذائي في رؤية 2033'},
            {'title': 'سلاسل القيمة الزراعية', 'desc': 'ربط المزارعين بالصناعات التحويلية الغذائية لرفع القيمة المضافة المحلية'},
        ]
    },
]

print('Solutions library loaded')
print(f'  Local solutions: {len(LOCAL_SOLUTIONS)} sectors')
print(f'  Vision 2033 pillars: {len(VISION_2033)}')

# ===== BUILD SOLUTIONS TAB HTML PER GOVERNORATE =====
html = open('src/index.html', encoding='utf-8').read()

# Add tab button — solutions comes after budget tab
for g in data['governorates']:
    name = g['name']
    old_btn = f'onclick="switchTab(\'{name}\',\'budget\')">💰 توجيه الموازنة</button>'
    new_btn = (f'onclick="switchTab(\'{name}\',\'budget\')">💰 توجيه الموازنة</button>\n'
               f'<button class="tb" onclick="switchTab(\'{name}\',\'solutions\')">🚀 الحلول الذكية</button>')
    html = html.replace(old_btn, new_btn)

print('Solutions tab buttons injected')

solutions_tabs = {}

for g in data['governorates']:
    name = g['name']
    sectors = g['sectors']

    h = []
    h.append(f'<div class="tc" id="tab-{name}-solutions">')
    h.append(f'''<div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border-radius:10px;padding:14px 18px;margin-bottom:16px;border-right:4px solid #22c55e;display:flex;gap:12px;align-items:flex-start">
<span style="font-size:20px">🚀</span>
<div>
<div style="font-size:13px;font-weight:700;color:#166534;margin-bottom:4px">الحلول الذكية — ما الهدف من هذا التبويب؟</div>
<div style="font-size:12px;color:#374151;line-height:1.7">يقدم هذا التبويب <strong>قائمتين من الحلول التنموية</strong>: الأولى حلول محلية ذكية وتقليدية مصممة خصيصاً لفجوات هذه المحافظة، والثانية حلول وطنية منسجمة مع <strong>رؤية التحديث الاقتصادي الأردني 2033</strong>. كل حل مبرر بالبيانات الفعلية ومصنف حسب نوعه (ذكي/تقليدي) ليسهل على صانع القرار الاختيار والتنفيذ.</div>
</div>
</div>''')
    h.append('<div class="cg">')

    # ===== SECTION 1: LOCAL SOLUTIONS =====
    h.append('<div class="card fw">')
    h.append('<div class="ct">🏘️ الحلول المحلية الذكية — مبنية على فجوات المحافظة الفعلية</div>')

    # Show solutions for sectors with negative gap
    behind_sectors = [(s, d) for s, d in sectors.items() if d['status'] == 'متأخر']
    advanced_sectors = [(s, d) for s, d in sectors.items() if d['status'] == 'متقدم']

    def render_sector_solutions(h, sec_name, sec_data, is_behind):
        if sec_name not in LOCAL_SOLUTIONS:
            return
        sec_sols = LOCAL_SOLUTIONS[sec_name]
        gap   = sec_data['gap']
        score = sec_data['score']
        border_color = '#fecaca' if is_behind else '#bbf7d0'
        header_bg    = '#fef2f2' if is_behind else '#f0fdf4'
        header_color = '#c62828' if is_behind else '#2e7d32'
        gap_label    = f'النقاط: {score:.1f} | الفجوة: {gap:.1f}' if is_behind else f'الفجوة: +{gap:.1f} ✅'

        h.append(f'<div style="margin-bottom:18px;border:1px solid {border_color};border-radius:12px;overflow:hidden">')
        h.append(f'<div style="background:{header_bg};padding:10px 16px;display:flex;justify-content:space-between;align-items:center">')
        h.append(f'<strong style="color:{header_color};font-size:13px">قطاع {sec_name}</strong>')
        h.append(f'<span style="font-size:11px;color:{header_color}">{gap_label}</span>')
        h.append('</div>')
        h.append('<div style="padding:14px">')

        # --- Traditional solutions ---
        trad = sec_sols.get('traditional', [])
        if trad:
            h.append('<div style="margin-bottom:12px">')
            h.append('<div style="font-size:12px;font-weight:700;color:#374151;margin-bottom:8px;display:flex;align-items:center;gap:6px;padding:5px 10px;background:#f1f5f9;border-radius:6px">🔧 الحلول التقليدية</div>')
            h.append('<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:8px">')
            for sol in trad:
                h.append('<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:11px;border-right:3px solid #64748b">')
                h.append(f'<strong style="font-size:12px;color:#1a3a5c;display:block;margin-bottom:5px">{sol["t"]}</strong>')
                h.append(f'<div style="font-size:11px;color:#374151;line-height:1.6">{sol["d"]}</div>')
                h.append('</div>')
            h.append('</div></div>')

        # --- Smart solutions ---
        smart = sec_sols.get('smart', [])
        if smart:
            h.append('<div style="margin-bottom:12px">')
            h.append('<div style="font-size:12px;font-weight:700;color:#1e40af;margin-bottom:8px;display:flex;align-items:center;gap:6px;padding:5px 10px;background:#eff6ff;border-radius:6px">💡 الحلول الذكية</div>')
            h.append('<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:8px">')
            for sol in smart:
                h.append('<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:11px;border-right:3px solid #3b82f6">')
                h.append(f'<strong style="font-size:12px;color:#1a3a5c;display:block;margin-bottom:5px">{sol["t"]}</strong>')
                h.append(f'<div style="font-size:11px;color:#374151;line-height:1.6">{sol["d"]}</div>')
                h.append('</div>')
            h.append('</div></div>')

        # --- Country examples ---
        examples = sec_sols.get('examples', [])
        if examples:
            h.append('<div>')
            h.append('<div style="font-size:12px;font-weight:700;color:#92400e;margin-bottom:8px;display:flex;align-items:center;gap:6px;padding:5px 10px;background:#fef3c7;border-radius:6px">🌍 نماذج من دول نجحت</div>')
            h.append('<div style="display:flex;flex-wrap:wrap;gap:8px">')
            for ex in examples:
                h.append(f'<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:8px 12px;flex:1;min-width:180px">')
                h.append(f'<div style="font-size:11px;font-weight:700;color:#92400e;margin-bottom:3px">{ex["c"]} — {ex["t"]}</div>')
                h.append(f'<div style="font-size:11px;color:#374151">{ex["r"]}</div>')
                h.append('</div>')
            h.append('</div></div>')

        h.append('</div></div>')  # end padding + card

    if behind_sectors:
        h.append('<div style="margin-bottom:20px">')
        h.append('<div style="font-size:13px;font-weight:700;color:#c62828;margin-bottom:12px;display:flex;align-items:center;gap:6px">⚠️ حلول لمعالجة الفجوات التنموية</div>')
        for sec_name, sec_data in behind_sectors:
            render_sector_solutions(h, sec_name, sec_data, True)
        h.append('</div>')

    if advanced_sectors:
        h.append('<div style="margin-bottom:8px">')
        h.append('<div style="font-size:13px;font-weight:700;color:#2e7d32;margin-bottom:12px;display:flex;align-items:center;gap:6px">🚀 حلول لتعزيز الميزة التنافسية</div>')
        for sec_name, sec_data in advanced_sectors:
            if sec_name not in LOCAL_SOLUTIONS:
                continue
            adv = LOCAL_SOLUTIONS[sec_name].get('advanced', [])
            if not adv:
                continue
            gap = sec_data['gap']
            h.append(f'<div style="margin-bottom:12px;border:1px solid #bbf7d0;border-radius:10px;overflow:hidden">')
            h.append(f'<div style="background:#f0fdf4;padding:10px 14px;display:flex;justify-content:space-between;align-items:center">')
            h.append(f'<strong style="color:#2e7d32;font-size:13px">قطاع {sec_name}</strong>')
            h.append(f'<span style="font-size:11px;color:#2e7d32">الفجوة: +{gap:.1f} ✅</span>')
            h.append('</div>')
            h.append('<div style="padding:12px;display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px">')
            for sol in adv:
                h.append('<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:12px;border-right:3px solid #22c55e">')
                h.append(f'<strong style="font-size:12px;color:#1a3a5c;display:block;margin-bottom:6px">{sol["t"]}</strong>')
                h.append(f'<div style="font-size:11px;color:#374151;line-height:1.6">{sol["d"]}</div>')
                h.append('</div>')
            h.append('</div></div>')
        h.append('</div>')

    h.append('</div>')  # end card

    # ===== SECTION 2: VISION 2033 =====
    h.append('<div class="card fw">')
    h.append('''<div class="ct">🇯🇴 الحلول المنسجمة مع رؤية التحديث الاقتصادي الأردني 2033</div>
<div style="background:linear-gradient(135deg,#1a3a5c,#2a5298);border-radius:10px;padding:14px 18px;margin-bottom:16px;color:#fff;font-size:12px;line-height:1.8">
  <strong style="color:#c8a84b">رؤية التحديث الاقتصادي 2033</strong> تهدف إلى مضاعفة الناتج المحلي الإجمالي، خلق 1,000,000 فرصة عمل، ورفع نسبة مشاركة المرأة في سوق العمل إلى 36%. الحلول أدناه تربط أولويات المحافظة بالأهداف الوطنية.
</div>''')

    h.append('<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px">')
    for pillar in VISION_2033:
        color = pillar['color']
        h.append(f'<div style="border:1px solid {color}30;border-radius:10px;overflow:hidden">')
        h.append(f'<div style="background:{color};color:#fff;padding:10px 14px;display:flex;align-items:center;gap:8px">')
        h.append(f'<span style="font-size:18px">{pillar["icon"]}</span>')
        h.append(f'<strong style="font-size:13px">{pillar["pillar"]}</strong>')
        h.append('</div>')
        h.append('<div style="padding:12px">')
        for sol in pillar['solutions']:
            h.append(f'<div style="margin-bottom:10px;padding-bottom:10px;border-bottom:1px dashed #e5e7eb">')
            h.append(f'<div style="font-size:12px;font-weight:700;color:#1a3a5c;margin-bottom:4px">◆ {sol["title"]}</div>')
            h.append(f'<div style="font-size:11px;color:#374151;line-height:1.6">{sol["desc"]}</div>')
            h.append('</div>')
        h.append('</div></div>')
    h.append('</div>')
    h.append('</div>')  # end card

    # ===== SECTION 3: GLOBAL INSPIRATIONS =====
    h.append('<div class="card fw">')
    h.append('''<div class="ct">🌍 تجارب دولية إضافية ملهمة — أفكار غير تقليدية نجحت</div>
<div style="background:linear-gradient(135deg,#f0f4ff,#e8f0fe);border-radius:8px;padding:12px 16px;margin-bottom:14px;font-size:12px;color:#374151;line-height:1.8;border-right:3px solid #1a3a5c">
  <strong style="color:#1a3a5c">لماذا نتعلم من تجارب الآخرين؟</strong> الأفكار الناجحة لا تعرف حدوداً — ما نجح في رواندا أو كولومبيا أو اليابان يمكن تكييفه للواقع الأردني بتكلفة أقل وخبرة مثبتة.
</div>
<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px">''')

    GLOBAL_INSPIRATIONS = [
        {'country': '🇷🇼 رواندا', 'color': '#22c55e', 'title': 'التحول من الفقر للنمو في 20 عاماً',
         'idea': 'رواندا رفعت دخل الفرد 6 أضعاف بين 2000-2020 عبر: حوكمة نظيفة، تقنية في كل قرية، وسياحة بيئية. الدرس: الإرادة السياسية + البيانات = تحول حقيقي.'},
        {'country': '🇨🇴 كولومبيا', 'color': '#3b82f6', 'title': 'ميديين — من أخطر مدينة لنموذج عالمي',
         'idea': 'ميديين تحوّلت من أعنف مدينة في العالم لمدينة مبتكرة بجائزة دولية. السر: تلفريك للأحياء الفقيرة + مكتبات في الأحياء الهشة + مراكز شباب متعددة الخدمات.'},
        {'country': '🇧🇷 البرازيل', 'color': '#f59e0b', 'title': 'كوريتيبا — المدينة التي حلّت مشاكلها بالإبداع',
         'idea': 'كوريتيبا حلّت مشكلة النفايات بمبادلتها بطعام وتذاكر باص. حلّت الفيضانات بحدائق بدل قنوات. الدرس: الحلول الإبداعية أرخص وأكثر استدامة من الحلول التقليدية.'},
        {'country': '🇰🇪 كينيا', 'color': '#8b5cf6', 'title': 'M-Pesa — الثورة المالية من الهاتف',
         'idea': 'كينيا حوّلت 80% من سكانها لمستخدمي خدمات مالية عبر الهاتف بدون بنوك. M-Pesa تُعالج 50% من الناتج المحلي. الدرس: التقنية البسيطة تُحدث ثورة اقتصادية.'},
        {'country': '🇪🇪 إستونيا', 'color': '#06b6d4', 'title': 'الحكومة الرقمية الكاملة',
         'idea': 'إستونيا رقمنت 99% من خدماتها الحكومية. المواطن يُنجز كل معاملاته في 5 دقائق. وفّرت 2% من الناتج المحلي سنوياً. الدرس: الرقمنة ليست رفاهية بل ضرورة اقتصادية.'},
        {'country': '🇲🇦 المغرب', 'color': '#f97316', 'title': 'نموذج التنمية الريفية المتكاملة',
         'idea': 'المغرب طوّر 35,000 قرية بمشروع واحد متكامل: طرق + كهرباء + ماء + مدارس + مراكز صحية. الدرس: التنمية المتكاملة أفضل من مشاريع منفصلة.'},
    ]

    for ins in GLOBAL_INSPIRATIONS:
        h.append(f'<div style="background:#f8fafc;border-radius:10px;padding:14px;border:1px solid #e5e7eb;border-top:3px solid {ins["color"]}">')
        h.append(f'<div style="font-size:13px;font-weight:700;color:{ins["color"]};margin-bottom:4px">{ins["country"]} — {ins["title"]}</div>')
        h.append(f'<div style="font-size:11px;color:#374151;line-height:1.7">{ins["idea"]}</div>')
        h.append('</div>')

    h.append('</div>')
    h.append('</div>')  # end card

    h.append('</div>')  # end cg
    h.append('</div>')  # end tab solutions

    solutions_tabs[name] = '\n'.join(h)

print(f'Solutions tabs built for {len(solutions_tabs)} governorates')

# ===== INJECT TABS =====
for g in data['governorates']:
    name = g['name']
    end_marker = f'<!-- END_PANEL_{name} -->'
    inject_pos = html.find(end_marker)
    if inject_pos == -1:
        print(f'  WARNING: end marker not found for {name}')
        continue
    html = html[:inject_pos] + '\n' + solutions_tabs[name] + '\n' + html[inject_pos:]
    print(f'  Injected solutions tab for {name}')

open('src/index.html', 'w', encoding='utf-8').write(html)
import os
size = os.path.getsize('src/index.html')
print(f'\nSolutions module injected. Final size: {size/1024:.1f} KB')
