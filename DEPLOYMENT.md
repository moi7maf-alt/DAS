# دليل النشر — نظام التحليل التنموي للمحافظات الأردنية
## Deployment Guide — JLDA Developmental Analysis System

**الإصدار:** 1.0 | **التصنيف:** للاستخدام الداخلي | **تاريخ:** مايو 2026

---

## 1. نظرة عامة على المشروع

نظام ويب متكامل لتحليل الفجوات التنموية في المحافظات الأردنية الـ12، يشمل:

- **لوحة تحليل (Dashboard):** مؤشرات مركبة، رسوم بيانية، تحليل قطاعي، فجوات تنموية
- **خطة استراتيجية:** رؤية ورسالة، SWOT، أهداف ذكية، مؤشرات أداء، مخاطر
- **مشاريع مقترحة:** 10 مشاريع مخصصة لكل محافظة
- **موازنة:** تحليل مالي ونفقات قطاعية
- **تحليل تنبؤي:** اتجاهات مستقبلية بناءً على CAGR
- **موائمة:** توائم المشاريع مع الاستراتيجيات الوطنية
- **شات تنموي:** مستشار ذكي للرد على أسئلة التنمية
- **رفع وتحليل ملفات:** يحلل Excel/CSV/PDF فورياً مع تحليل AI خلفي

### العمارة التقنية

```
┌──────────────────────┐     ┌─────────────────────┐     ┌──────────┐
│   متصفح المستخدم     │────▶│   Python HTTP Server  │────▶│  Ollama  │
│   (Chrome / Edge)    │     │   (ai_server.py)      │     │ AI Model │
│                      │◀────│   Port 5000           │◀────│qwen2.5   │
└──────────────────────┘     └─────────────────────┘     └──────────┘
                                     │
                                     ▼
                           ┌─────────────────────┐
                           │   ملفات ثابتة        │
                           │   *.html, *.json     │
                           │   (مبنية مسبقاً)     │
                           └─────────────────────┘
```

- **الواجهة الأمامية:** HTML/CSS/JavaScript ثابت (ملف index.html ~2.4MB)
- **الخادم:** Python HTTP Server (`ai_server.py`) — مسؤول عن التوثيق، رفع الملفات، تحليل AI، الشات
- **AI:** Ollama محلي مع نموذج `qwen2.5:3b` للتحليل والشات
- **البيانات:** ملفات JSON مبنية مسبقاً بواسطة `run_all.py`

---

## 2. متطلبات التشغيل

### سيرفر الإنتاج (وزارة الداخلية)

| المتطلب | المواصفات الدنيا | الموصى به |
|---------|-----------------|-----------|
| نظام التشغيل | Windows Server 2019+ أو Ubuntu 22.04+ | Windows Server 2022 |
| المعالج | 4 أنوية x86_64 | 8+ أنوية |
| الذاكرة | 8 GB RAM | 16 GB RAM |
| المساحة التخزينية | 10 GB | 20 GB (SSD) |
| Python | 3.9+ | 3.11+ |
| Ollama | v0.3+ | الأحدث |
| المتصفح (للمستخدم) | Chrome 90+ / Edge 90+ | Chrome 120+ |

### جهاز التطوير (لتحديث البيانات)

| المتطلب | المواصفات |
|---------|-----------|
| نظام التشغيل | Windows 10/11 أو Linux |
| Python | 3.9+ مع pip |
| حزمة Python | pandas, openpyxl, numpy, PyPDF2 |

---

## 3. هيكل المجلدات

```
JLD/
├── ACCOUNTS.md                  ← حسابات المستخدمين
├── DEPLOYMENT.md                ← هذا الملف
├── src/                         ← مجلد المصدر الرئيسي
│   ├── ai_server.py             ★ خادم Python (القلب النابض)
│   ├── index.html               ★ الصفحة الرئيسية للداشبورد (~2.4MB)
│   ├── landing.html             ★ صفحة الهبوط
│   ├── login.html               ★ صفحة تسجيل الدخول
│   ├── chat.html                ★ صفحة الشات التنموي
│   ├── upload.html              ★ صفحة رفع وتحليل الملفات
│   ├── technical_guide.html     ← الدليل التقني (HTML)
│   ├── data.json                ← بيانات المحافظات
│   ├── strategic_plans.json     ← الخطط الاستراتيجية
│   ├── strategic_comprehensive.json  ← الخطط الشاملة (مع SWOT)
│   ├── budget_data.json         ← بيانات الموازنة
│   ├── predictive_data.json     ← بيانات التنبؤات
│   ├── write_dashboard.py       ← بناء الداشبورد
│   ├── generate_data.py         ← معالجة البيانات الخام
│   ├── generate_comprehensive.py ← بناء الخطط الشاملة
│   ├── build_*.py               ← سكريبتات بناء مختلفة
│   ├── inject_*.py              ← سكريبتات حقن تبويبات
│   ├── run_all.py               ★ سكريبت البناء الشامل
│   └── build_landing.py         ← بناء صفحة الهبوط
├── Data/                        ← مجلد البيانات الخام (Excel)
│   └── input/
└── uploads/                     ← مجلد الملفات المرفوعة (يتولد تلقائياً)
```

### شرح الملفات الأساسية

| الملف | الوظيفة | ملاحظات |
|-------|---------|---------|
| `ai_server.py` | خادم HTTP متكامل: توثيق، رفع، تحليل، شات، خدمة ملفات | **الملف الوحيد الذي يحتاج تشغيل مستمر** |
| `index.html` | لوحة التحكم الرئيسية (3 تبويبات لكل محافظة) | يُبنى بواسطة `write_dashboard.py` |
| `landing.html` | الصفحة الرئيسية قبل الدخول | يُبنى بواسطة `build_landing.py` |
| `login.html` | صفحة تسجيل الدخول | ملف ثابت لا يتغير |
| `chat.html` | صفحة المستشار التنموي الذكي | ملف ثابت لا يتغير |
| `upload.html` | صفحة رفع وتحليل الملفات | ملف ثابت لا يتغير |
| `run_all.py` | سكريبت بناء شامل (10 خطوات) | يُشغّل على جهاز التطوير فقط |

> **ملاحظة مهمة:** الملفات الثابتة (`index.html`, `landing.html`, `*.json`) تُبنى على جهاز التطوير ثم تُرفع للسيرفر. أما `ai_server.py` فيُشغّل على السيرفر نفسه.

---

## 4. التثبيت على سيرفر الوزارة (للمبرمج المستلم)

### 4.1 تنزيل المشروع

```bash
# عبر Git (إن وجد)
git clone <رابط المستودع> C:\JLD

# أو نسخ المجلد من USB / شبكة داخلية
copy D:\JLD C:\JLD
```

### 4.2 تثبيت Python

1. حمّل Python 3.11+ من [python.org](https://python.org)
2. شغّل المثبّت → تأكد من تفعيل **"Add Python to PATH"**
3. افتح Command Prompt وتحقق:
   ```cmd
   python --version
   pip --version
   ```

### 4.3 تثبيت المكتبات

```cmd
cd C:\JLD
pip install pandas openpyxl numpy PyPDF2
```

### 4.4 تثبيت Ollama

1. حمّل من [ollama.com/download](https://ollama.com/download)
2. شغّل المثبّت
3. افتح Command Prompt واسحب النموذج:

```cmd
ollama pull qwen2.5:3b
```

> **ملاحظة:** النموذج (`qwen2.5:3b`) حجمه ~1.9GB. إذا عندك سيرفر أقوى (16GB+ RAM، GPU)، استخدم `qwen2.5:7b` بدلاً منه (أدق ولكن أبطأ 3× تقريباً).

### 4.5 التأكد من اشتغال Ollama

```cmd
ollama list
```
يجب أن يظهر `qwen2.5:3b` في القائمة.

### 4.6 تشغيل خادم التطبيقات

```cmd
cd C:\JLD
python src/ai_server.py
```

يجب أن تشاهد رسالة تفيد أن السيرفر شغال على `http://localhost:5000`.

**ملاحظة:** هذا الأمر يجب أن يبقى شغال باستمرار. لإيقافه: `Ctrl + C`.

### 4.7 تشغيل السيرفر كخدمة خلفية (Windows)

لتشغيل السيرفر في الخلفية بدون نافذة:

```powershell
# PowerShell (تشغيل)
Start-Process -WindowStyle Hidden -FilePath python -ArgumentList "src/ai_server.py" -WorkingDirectory "C:\JLD"

# PowerShell (إيقاف)
Get-Process -Name python | Where-Object { $_.MainWindowTitle -eq '' } | Stop-Process -Force
```

### 4.8 تشغيل السيرفر كخدمة (Linux)

```bash
# تثبيت systemd service
sudo nano /etc/systemd/system/jld.service
```

المحتوى:
```ini
[Unit]
Description=JLDA Development Planning Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/JLD/src/ai_server.py
WorkingDirectory=/opt/JLD
Restart=always
User=www-data
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable jld
sudo systemctl start jld
sudo systemctl status jld
```

### 4.9 التحقق من أن كل شيء شغال

افتح المتصفح على: `http://localhost:5000/health`

الرد المتوقع:
```json
{"status": "ok", "model": "qwen2.5:3b", "ollama": "running", "user": null}
```

ثم افتح `http://localhost:5000` — يجب أن تشاهد صفحة الهبوط.

---

## 5. تجهيز البيانات وبناء الملفات الثابتة

هذه الخطوة تتم على **جهاز التطوير** (وليس السيرفر).

### 5.1 تحضير البيانات الخام

ضع ملفات Excel في المجلد:
```
Data/input/
├── indicator.xlsx
├── budget.xlsx
├── trends_raw.xlsx
├── refugee.xlsx
└── ... (بقية ملفات البيانات)
```

### 5.2 تشغيل البناء الشامل

```cmd
cd C:\JLD
python src/run_all.py
```

هذا الأمر يشغّل 10 خطوات تباعاً:
1. معالجة البيانات ← `data.json`
2. بناء الخطط الاستراتيجية الشاملة ← `strategic_comprehensive.json`
3. بناء بيانات الموازنة ← `budget_data.json`
4. بناء البيانات التنبؤية ← `predictive_data.json`
5. بناء الهيكل الأساسي ← `index.html`
6. حقن تبويب الموازنة
7. حقن تبويب التحليل التنبؤي
8. حقن تبويب موائمة المشاريع
9. بناء الصفحة الرئيسية ← `landing.html`
10. بناء الدليل التقني ← `technical_guide.html`

### 5.3 رفع الملفات للسيرفر

بعد انتهاء البناء، انسخ هذه الملفات إلى **سيرفر الإنتاج**:

```
src/index.html
src/landing.html
src/login.html
src/chat.html
src/upload.html
src/data.json
src/strategic_plans.json
src/strategic_comprehensive.json
src/budget_data.json
src/predictive_data.json
```

ضعها في نفس مسار `ai_server.py` على السيرفر (مثال: `C:\JLD\src\`).

---

## 6. إعداد IIS (اختياري — للاستخدام الإنتاجي)

إذا كنت تريد استخدام IIS كـ **Reverse Proxy** لخادم Python:

### 6.1 تثبيت IIS

من Server Manager → Add Roles and Features → تفعيل Web Server (IIS).

### 6.2 تثبيت Application Request Routing (ARR)

1. حمّل ARR من Microsoft
2. شغّل المثبّت
3. افتح IIS Manager →双击 **Application Request Routing Cache**
4. من الـ Actions panel، اختر **Server Proxy Settings** → فعّل **Enable proxy**

### 6.3 إضافة Reverse Proxy Rule

1. افتح IIS Manager
2. اختر الموقع الافتراضي (Default Web Site)
3. من الـ Actions، اختر **Add Application**
4. اسم التطبيق: `jld` (أو حسب الرغبة)
5. المسار الفيزيائي: `C:\JLD\src`
6. افتح **URL Rewrite** ← Add Rule ← Reverse Proxy
7. الخادم الخلفي: `localhost:5000`

الآن الموقع متاح على: `http://YOUR_SERVER_IP/jld/`

### 6.4 إعداد HTTPS

1. احصل على شهادة SSL من Let's Encrypt أو مديرية تكنولوجيا المعلومات
2. في IIS، اربط الشهادة بالموقع
3. فعّل redirect HTTP → HTTPS

---

## 7. إدارة النموذج (Ollama)

### النماذج المتاحة

| النموذج | الحجم | السرعة | جودة العربية | متى تستخدم |
|---------|-------|--------|-------------|------------|
| `qwen2.5:3b` | 1.9 GB | ⚡ سريع | 👍 جيدة | الإنتاج (الموصى به) |
| `qwen2.5:7b` | 4.7 GB | 🐢 بطيء 3× | 👌 ممتازة | سيرفر قوي GPU |
| `phi4-mini` | 2.5 GB | ⚡ سريع | 👎 ضعيفة | لا تستخدم (عربية رديئة) |
| `aya:8b` | 4.8 GB | 🐢 بطيء | 🌟 ممتازة جداً | سيرفر قوي (مستقبلاً) |

### تغيير النموذج

1. افتح `src/ai_server.py`
2. ابحث عن `MODEL = "qwen2.5:3b"` (سطر 16)
3. غيّر إلى النموذج المطلوب
4. اسحب النموذج: `ollama pull <اسم النموذج>`
5. أعد تشغيل السيرفر

### ضبط سرعة الرد

في `call_ollama_chat()` (سطر 117-122):
- `num_predict: 800` — عدد الكلمات المولّدة (أقل = أسرع)
- `temperature: 0.3` — التحكم في الإبداعية (أقل = أدق)
- `num_ctx: 4096` — طول السياق

في `call_ollama()` للتحليل:
- `num_predict: 1200` — أكثر للتحليل العميق
- `timeout: 300` — 5 دقائق كحد أقصى

---

## 8. استكشاف الأخطاء الشائعة

### السيرفر لا يشتغل

```
خطأ: [Errno 10048] Address already in use
```
**الحل:** المنفذ 5000 مشغول. غيّر المنفذ في `ai_server.py` (سطر `PORT = 5000`).

```
خطأ في الاتصال بالنموذج: تأكد من تشغيل Ollama
```
**الحل:** السيرفر شغال لكن Ollama لا. شغّل `ollama serve` في نافذة منفصلة.

### العربية مشوهة

```
????? ???? ??? ?????? ??
```
**الحل:** تأكد من أن شاشة الـ terminal تدعم UTF-8. شغّل:
```cmd
chcp 65001
```

### الملفات المرفوعة لا تظهر

التأكد من وجود المجلد `uploads/` داخل `src/`:
```cmd
mkdir src\uploads
```

### الخطط الاستراتيجية لا تظهر (تبويب استراتيجية فارغ)

```
strategic_comprehensive.json
```
تأكد من وجود الملف. إذا كان محذوفاً:
```cmd
python src/generate_comprehensive.py
```

### بعد تحديث البيانات، التغييرات لا تظهر

1. شغّل `python src/run_all.py`
2. انسخ الملفات المبنية حديثاً للسيرفر
3. أعد تحميل الصفحة (`Ctrl + F5` للـ Hard Refresh)

---

## 9. أوامر سريعة

| المهمة | الأمر |
|--------|-------|
| تشغيل السيرفر | `python src/ai_server.py` |
| بناء كل الملفات | `python src/run_all.py` |
| سحب نموذج Ollama | `ollama pull qwen2.5:3b` |
| اختبار Ollama | `curl http://localhost:11434/api/generate -d "{\"model\":\"qwen2.5:3b\",\"prompt\":\"مرحبا\"}"` |
| التحقق من الصحة | `curl http://localhost:5000/health` |
| إيقاف السيرفر (Windows) | `Get-Process -Name python \| Stop-Process -Force` |
| إيقاف السيرفر (Linux) | `sudo systemctl stop jld` |

---

## 10. جهات الاتصال

| المسؤول | المهمة |
|---------|--------|
 | المطور الأصلي | استفسارات تقنية، تطوير، إضافة ميزات |
| مدير النظام | صيانة السيرفر، نسخ احتياطي، أمان |
| مدير التنمية المحلية | تحديث البيانات، مراجعة الخطط |

---

*نظام التحليل التنموي للمحافظات الأردنية*
*المملكة الأردنية الهاشمية — وزارة الداخلية — مديرية التنمية المحلية*
*مايو 2026*
