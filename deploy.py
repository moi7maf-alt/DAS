# -*- coding: utf-8 -*-
"""
deploy.py — سكريبت النشر
يجمع ملفات الموقع في مجلد dist/ جاهز للرفع على الاستضافة.

الاستخدام:
    python deploy.py

الناتج:
    dist/
    ├── index.html
    ├── landing.html
    └── technical_guide.html
"""

import os
import sys
import shutil
import hashlib
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT  = os.path.dirname(os.path.abspath(__file__))
SRC   = os.path.join(ROOT, 'src')
DIST  = os.path.join(ROOT, 'dist')

# الملفات المطلوبة للنشر فقط
DEPLOY_FILES = [
    'index.html',
    'landing.html',
    'login.html',
    'chat.html',
    'upload.html',
    'audit.html',
    'technical_guide.html',
    'data.json',
    'budget_data.json',
    'predictive_data.json',
    'strategic_comprehensive.json',
]

# ملفات اختيارية — تُنسخ إن وُجدت
OPTIONAL_FILES = [
    'report.html',
    'strategic_plans.json',
]

def file_hash(path):
    """MD5 hash لمقارنة الملفات."""
    h = hashlib.md5()
    with open(path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()

def format_size(bytes_val):
    """تنسيق حجم الملف."""
    if bytes_val >= 1024 * 1024:
        return f'{bytes_val / (1024*1024):.1f} MB'
    return f'{bytes_val / 1024:.0f} KB'

def main():
    print('=' * 60)
    print('  نظام التحليل التنموي للمحافظات الأردنية — سكريبت النشر')
    print('  DAS (Developmental Analysis System) — Deploy Script')
    print('=' * 60)
    print(f'  المصدر: {SRC}')
    print(f'  الهدف:  {DIST}')
    print()

    # ===== التحقق من وجود ملفات المصدر =====
    print('[ 1/4 ] التحقق من ملفات المصدر...')
    missing = []
    for fname in DEPLOY_FILES:
        src_path = os.path.join(SRC, fname)
        if not os.path.exists(src_path):
            missing.append(fname)
        else:
            size = os.path.getsize(src_path)
            print(f'  ✅ {fname} ({format_size(size)})')

    if missing:
        print()
        print('❌ ملفات مفقودة — شغّل run_all.py أولاً:')
        for f in missing:
            print(f'   - {f}')
        print()
        print('   python src/run_all.py')
        return

    # ===== إنشاء مجلد dist =====
    print()
    print('[ 2/4 ] إنشاء مجلد dist/...')
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
        print('  🗑️  حُذف dist/ القديم')
    os.makedirs(DIST)
    print(f'  📁 تم إنشاء: {DIST}')

    # ===== نسخ الملفات =====
    print()
    print('[ 3/4 ] نسخ الملفات...')
    total_size = 0
    copied = []

    for fname in DEPLOY_FILES + OPTIONAL_FILES:
        src_path = os.path.join(SRC, fname)
        dst_path = os.path.join(DIST, fname)
        if not os.path.exists(src_path):
            continue
        shutil.copy2(src_path, dst_path)
        size = os.path.getsize(dst_path)
        total_size += size
        copied.append((fname, size))
        print(f'  📄 {fname:<30} {format_size(size):>8}')

    # ===== إنشاء ملف README =====
    print()
    print('[ 4/4 ] إنشاء ملف README...')
    DESC_MAP = {
        "index.html":"لوحة المؤشرات التفاعلية",
        "landing.html":"الصفحة الرئيسية",
        "login.html":"صفحة تسجيل الدخول",
        "chat.html":"المستشار التنموي الذكي",
        "upload.html":"رفع وتحليل الملفات",
        "audit.html":"سجل المراجعة",
        "technical_guide.html":"الدليل التقني",
        "data.json":"بيانات المحافظات والقطاعات",
        "budget_data.json":"بيانات الموازنة",
        "predictive_data.json":"البيانات التنبؤية",
        "strategic_comprehensive.json":"الخطط الاستراتيجية الشاملة",
        "report.html":"تقرير (اختياري)",
        "strategic_plans.json":"الخطط الاستراتيجية (اختياري)",
    }
    table_rows = '\n'.join([f'| `{f}` | {DESC_MAP.get(f, f)} | {format_size(s)} |' for f, s in copied])
    readme_content = f"""# نظام التحليل التنموي للمحافظات الأردنية
## المحافظات الأردنية الاثنتا عشرة

**تاريخ البناء:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**الجهة:** وزارة الداخلية الأردنية — مديرية التنمية المحلية

---

## ملفات الموقع

| الملف | الوصف | الحجم |
|-------|-------|-------|
{table_rows}

**الحجم الإجمالي:** {format_size(total_size)}

---

## طريقة النشر

### IIS (Windows Server)
1. افتح IIS Manager
2. أنشئ موقعاً جديداً أو Virtual Directory
3. انسخ محتويات هذا المجلد إلى مجلد الموقع
4. تأكد أن `index.html` هو الملف الافتراضي (Default Document)
5. أضف MIME type: `.json` → `application/json` (إن لزم)

### Apache / Nginx (Linux)
```bash
sudo cp -r dist/* /var/www/html/jlda/
sudo chown -R www-data:www-data /var/www/html/jlda/
sudo chmod -R 755 /var/www/html/jlda/
```

### Netlify / GitHub Pages
ارفع محتويات هذا المجلد مباشرة.

---

## ملاحظات
- الموقع **Static** بالكامل — لا يحتاج قاعدة بيانات
- الرسوم البيانية تحتاج اتصال إنترنت لتحميل Chart.js من CDN
- تبويب **"تقرير المحافظة"** يحتاج تشغيل `python src/ai_server.py` محلياً
- باقي التبويبات الـ 8 تعمل بدون إنترنت أو خادم إضافي

---
© {datetime.now().year} وزارة الداخلية الأردنية — مديرية التنمية المحلية
"""
    readme_path = os.path.join(DIST, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f'  📝 README.md')

    # ===== ملخص =====
    print()
    print('=' * 60)
    print(f'  ✅ اكتمل النشر بنجاح')
    print(f'  📁 المجلد: {DIST}')
    print(f'  📄 الملفات: {len(copied)} ملف')
    print(f'  💾 الحجم الإجمالي: {format_size(total_size)}')
    print()
    print('  الخطوة التالية:')
    print(f'  انسخ محتويات مجلد dist/ إلى السيرفر')
    print('=' * 60)

    # ===== فتح المجلد في Explorer =====
    try:
        os.startfile(DIST)
    except Exception:
        pass

if __name__ == '__main__':
    main()
