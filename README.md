# نظام التحليل التنموي للمحافظات الأردنية
## المحافظات الأردنية الاثنتا عشرة

**تاريخ البناء:** 2026-06-06 02:46
**الجهة:** وزارة الداخلية الأردنية — مديرية التنمية المحلية

---

## ملفات الموقع

| الملف | الوصف | الحجم |
|-------|-------|-------|
| `index.html` | لوحة المؤشرات التفاعلية | 2.4 MB |
| `landing.html` | الصفحة الرئيسية | 17 KB |
| `login.html` | صفحة تسجيل الدخول | 8 KB |
| `chat.html` | المستشار التنموي الذكي | 12 KB |
| `upload.html` | رفع وتحليل الملفات | 14 KB |
| `audit.html` | سجل المراجعة | 8 KB |
| `technical_guide.html` | الدليل التقني | 58 KB |
| `data.json` | بيانات المحافظات والقطاعات | 57 KB |
| `budget_data.json` | بيانات الموازنة | 27 KB |
| `predictive_data.json` | البيانات التنبؤية | 276 KB |
| `strategic_comprehensive.json` | الخطط الاستراتيجية الشاملة | 257 KB |
| `strategic_plans.json` | الخطط الاستراتيجية (اختياري) | 38 KB |

**الحجم الإجمالي:** 3.1 MB

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
© 2026 وزارة الداخلية الأردنية — مديرية التنمية المحلية
