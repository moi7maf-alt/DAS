# دليل نشر نظام التحليل التنموي للمحافظات الأردنية على خادم الوزارة

---

## نظرة عامة على النظام

### ما هو هذا النظام؟
نظام تفاعلي لتخطيط التنمية المحلية في الأردن، يغطي محافظات المملكة الـ 12. يوفر:
- **لوحة مؤشرات تفاعلية** (Dashboard) تعرض بيانات كل محافظة: السكان، المساحة، الموازنة، المؤشرات القطاعية، مؤشر الخطر، وغيرها
- **تحليل ذكي بالذكاء الاصطناعي** (AI) — محادثة تفاعلية وتحليل ملفات (Excel, PDF) مع تقارير تنموية لكل محافظة
- **تبويب الموازنة** — عرض الموازنة التقديرية لكل محافظة لعام 2026
- **تحليل تنبؤي** — توقعات مستقبلية للمؤشرات التنموية
- **موائمة المشاريع** — مطابقة المشاريع المقترحة مع الأولويات التنموية

### المحافظات الـ 12 (الأسماء الرسمية فقط — لا يُستخدم غيرها)
العاصمة، البلقاء، الزرقاء، مأدبا، إربد، المفرق، جرش، عجلون، الكرك، الطفيلة، معان، العقبة

> ⚠️ **هام**: هذه الأسماء فقط هي المستخدمة في النظام. أي اسم آخر (مثل "عمان" بدل "العاصمة"، "السلط" بدل "البلقاء"، "ككر" بدل "الكرك") يعتبر هلوسة من نموذج AI ويتم تصحيحه آلياً.

### طبيعة المشاريع
جميع المشاريع في النظام **حكومية فقط** — لا يوجد مشاريع قطاع خاص.
لا يحتوي النظام على أي مشاريع متعلقة بـ **الصحة النفسية** أو **التعدين**.

---

## بنية النظام التقنية

### الملفات المطلوبة للنشر

انسخ مجلد `dist/` بالكامل إلى الخادم، بالإضافة إلى ملف `ai_server.py`:

```
/dist/
  ├── index.html              (لوحة المؤشرات الأساسية — 2.4 MB)
  ├── landing.html            (الصفحة الرئيسية)
  ├── login.html              (صفحة تسجيل الدخول)
  ├── audit.html              (سجل المراجعة)
  ├── chat.html               (واجهة المحادثة الذكية)
  ├── technical_guide.html    (الدليل التقني)
  ├── data.json               (بيانات المحافظات والقطاعات)
  ├── predictive_data.json    (البيانات التنبؤية)
  ├── budget_data.json        (بيانات الموازنة)
  ├── strategic_comprehensive.json  (الرؤية والرسالة الاستراتيجية)
  ├── start_server.bat        (تشغيل سريع — ويندوز)
  └── ai_server.py            (خادم AI و API — 66 KB)
```

### تدفق البيانات

```
data.json + strategic_comprehensive.json
        ↓
  write_dashboard.py  ←  run_all.py  →  build_landing.py
        ↓                          ↓
  index.html (مع 6 تبويبات)    landing.html
```

- `run_all.py` يشغّل كل خطوات البناء (10 خطوات) وينتج جميع الملفات
- البيانات تُقرأ من `Data/` وتحوَّل إلى JSON
- `ai_server.py` هو خادم HTTP مستقل بذاته (لا يحتاج Flask/Django)

### خادم AI (ai_server.py)
- خادم HTTP مدمج (ThreadingHTTPServer) — لا حاجة لأطر خارجية
- المنفذ الافتراضي: **5000**
- نقط النهاية (API Endpoints):
  - `GET /` ← يخدم الملفات الثابتة (index.html, landing.html, chat.html, ...)
  - `POST /api/chat` ← محادثة مع AI للمحافظة المحددة
  - `POST /api/gov-analysis` ← تحليل ملف (Excel/PDF) خاص بمحافظة
  - `POST /api/login` ← تسجيل الدخول
  - `GET  /api/audit-log` ← سجل المراجعة

---

## نموذج الذكاء الاصطناعي والقيود

### النموذج الحالي: qwen2.5:3b (1.9 مليار معامل)
- **الإيجابيات**: يعمل على CPU فقط (لا حاجة لـ GPU)، حجم صغير جداً، سرعة استجابة 15-25 ثانية، جودة عربية ممتازة
- **السلبيات**: ينتج تحليلات مطوّلة بدل الموجزة رغم تعليمات البرمبت، يرفض أحياناً اختصار الردود

### المشاكل المعروفة (مع phi4-mini — النموذج السابق)
> تم استبدال phi4-mini بـ qwen2.5:3b. معظم المشاكل التالية حُلّت أو تحسّنت بشكل كبير.
1. ~~**أسماء محافظات خاطئة**~~: ✅ qwen2.5:3b لا يعاني من هذه المشكلة
2. ~~**تكرار البادئات ("الالالكرك")**~~: ✅ اختفى تماماً مع qwen2.5:3b
3. ~~**مصطلحات إسبانية/برتغالية**~~: ✅ qwen2.5:3b لا ينتج كلمات أجنبية
4. ~~**أخطاء في قواعد العربية**~~: ✅ qwen2.5:3b نحوه سليم
5. ~~**إعادة ترديد التاجات**~~: ✅ يكتب تحليلاً طبيعياً
6. ~~**تكرار الكلمات**~~: ✅ اختفى تماماً

### حلول معالجة الهلوسة (المطبّقة فعلياً)

#### أ. البرمبتات (Prompts) — 3 مستويات
1. **SYSTEM_PROMPT** — البرمبت الأساسي لتحليل الملفات (سطر 70)
2. **CHAT_SYSTEM_PROMPT** — برمبت المحادثة (سطر 85)
3. **build_gov_context()** — حقن بيانات المحافظة في سياق التحليل (سطر 372)

جميعها تحتوي على:
- قائمة المحافظات الـ 12 مع جملة "لا تذكر أي اسم آخر"
- توضيح أن الموازنة تقديرية وليست الناتج المحلي الإجمالي
- تعليمات صارمة بعدم ذكر دول أخرى أو أرقام وهمية

#### ب. التصنيف المسبق (Ranking-based Analysis)
بدلاً من ترك النموذج يفسر الأرقام، تُحسب الرتب مسبقاً (1-12) وتُرفق بتاجات:
- 💪 **قوي** = رتبة 1-3
- 📊 **متوسط مرتفع** = رتبة 4-6
- 📉 **متوسط منخفض** = رتبة 7-9
- ⚠️ **ضعيف** = رتبة 10-12

والبطالة:
- 👍 **منخفض** / 📊 **متوسط** / 📈 **مرتفع** / ⚠️ **مرتفع جداً**

هذا يمنع النموذج من تفسير الأرقام بشكل خاطئ (مثلاً اعتبار رتبة 1 "ضعيفة").

#### ج. المعالجة البعدية — clean_response() (سطر 185)
أهم خط دفاع — تُطبَّق على كل رد من النموذج وتصحح:
1. **أسماء المحافظات**: 8 مجموعات من الأسماء الخاطئة (ككر→الكرك، عمان→العاصمة، إلخ)
2. **تكرار "الالال"**: regex يزيل البادئات المكررة
3. **تكرار الكلمات**: (في في، من من، و و)
4. **المصطلحات الأجنبية**: 20 كلمة إسبانية/برتغالية → العربية
5. **الأخطاء الإملائية**: المترين→المرتبة، بطرة→بطالة، محافطة→محافظة
6. **"متوسطة الارتفاعة"**: → "متوسط"
7. **المسافات البيضاء**: تنظيف

#### د. خفض درجة الحرارة (Temperature)
- تحليل الملفات: 0.1
- المحادثة: 0.05 (شبه حتمي) + repeat_penalty 1.3
- الهدف: تقليل العشوائية ومنع التكرار

---

## القيود والمشاكل المعروفة

### قيود حالية
| المشكلة | السبب | الحل المقترح |
|---------|-------|--------------|
| تحليلات مطوّلة بدل الموجزة | النموذج (3B) مدرب على كتابة تقارير شاملة | برمبتات موجزة + قطع بعدّ الحروف بعد المعالجة |
| سرعة ~15-25 ثانية للرد | CPU-only، num_ctx=8192 | ترقية النموذج عند توفر GPU |
| تجاهل تعليمات الاختصار | سلوك تدريبي للنموذج | تجربة qwen2.5:7b أو المعالجة البعدية |

### تشفير PowerShell
عند تشغيل `ai_server.py` عبر PowerShell، قد تظهر أخطاء في عرض العربية في الـ stdout. هذا لا يؤثر على استجابات JSON (UTF-8 عبر `wfile.write`) — الخادم يعمل بشكل صحيح.

### متطلبات الجهاز
- **المعالج**: CPU فقط (أي معالج x86_64)
- **الذاكرة**: 4GB RAM كحد أدنى (8GB موصى به)
- **المساحة**: 3GB للنموذج + الملفات
- **GPU**: غير مطلوب (ولكنه يحسّن الأداء بشكل كبير)

### متى نرقّي النموذج؟
عند توفر GPU، يُنصح بالترقية إلى:
1. `qwen2.5:7b` — جودة عربية أفضل + يستجيب لتعليمات الاختصار، يحتاج 8GB VRAM أو 16GB RAM
2. `gemma3:12b` — جودة ممتازة، يحتاج 16GB VRAM

ملاحظة: qwen2.5:7b مثبّت مسبقاً على خادم التطوير ويمكن تجربته فوراً بتغيير MODEL في ai_server.py (سطر 16).

---

## استكشاف الأخطاء وإصلاحها

### "النموذج لا يستجيب" (خطأ 500/Timeout)
1. تأكد من أن Ollama شغال: `ollama list`
2. افحص `server.log` لمعرفة الخطأ المحدد
3. زد timeout في `ai_server.py` (سطر 125): `timeout=600`
4. أول استجابة بعد بدء الخادم تأخذ 44-68 ثانية لتحميل النموذج

### "الرد بالكامل إسباني/أجنبي" (لم يعد يحدث مع qwen2.5:3b)
- كان هذا يحدث مع phi4-mini (النموذج السابق)
- qwen2.5:3b لا يعاني من هذه المشكلة إطلاقاً

### "الرد يكرر اسم المحافظة بشكل خاطئ"
- clean_response يمسك 8 أنماط معروفة
- إذا ظهر نمط جديد، أضفه إلى `all_govs` في `clean_response` (سطر 200)
- ثم أعد تشغيل الخادم

### "الموازنة تظهر كأنها الناتج المحلي الإجمالي"
- البرمبتات تحتوي على تعليمات واضحة بأن الموازنة تقديرية وليست GDP
- إذا استمرت المشكلة، عزّز التعليمات في `SYSTEM_PROMPT` (سطر 70)

---

## أولاً: النشر على Windows Server

### 1. تثبيت Python
- افتح https://python.org وحمل Python 3.11+
- عند التثبيت، تأكد من تفعيل ✅ **Add Python to PATH**
- بعد التثبيت، افتح Command Prompt واكتب:
```cmd
python --version
```
تأكد من ظهور رقم الإصدار

### 2. تثبيت المكتبات الإضافية (لرفع ملفات Excel و PDF)
```cmd
pip install openpyxl PyPDF2
```

### 3. تشغيل الخادم كخدمة Windows (يشتغل تلقائياً مع تشغيل الخادم)

**الطريقة الموصى بها — باستخدام NSSM (Non-Sucking Service Manager):**

أ. حمل NSSM من: https://nssm.cc/download
ب. استخرج الملف إلى `C:\nssm\`
ج. افتح Command Prompt **كمسؤول** واكتب:
```cmd
C:\nssm\win64\nssm.exe install JLDashboard
```
د. ستظهر نافذة، املأها كالتالي:
   - **Application Path:** `C:\Users\User\AppData\Local\Programs\Python\Python311\python.exe`
   - **Startup directory:** `C:\Users\User\Desktop\JLD` (المجلد الذي يحتوي على `ai_server.py`)
   - **Arguments:** `ai_server.py`
   - **Service name:** `JLDashboard`

هـ. اذهب إلى `Services.msc`، ابحث عن `JLDashboard`، وابدأ الخدمة
و. الآن الخادم شغال 24/7. افتح المتصفح: `http://localhost:5000`

### 4. تغيير كلمة المرور قبل الإطلاق الرسمي
- افتح ملف `ai_server.py`
- ابحث عن سطر: `"admin": {"password": "admin123"`
- غيّر `admin123` إلى كلمة مرور قوية
- أعد تشغيل الخدمة

### 5. إعداد جدار الحماية (Firewall)
للسماح بالوصول من أجهزة أخرى على الشبكة:
```cmd
netsh advfirewall firewall add rule name="JLDashboard" dir=in action=allow protocol=TCP localport=5000
```
ثم غيّر السطر في `ai_server.py` من:
```python
server = ThreadingHTTPServer(("localhost", PORT), AIHandler)
```
إلى:
```python
server = ThreadingHTTPServer(("0.0.0.0", PORT), AIHandler)
```

---

## ثانياً: النشر على Linux Server (Ubuntu/CentOS)

### 1. تثبيت Python
```bash
sudo apt update
sudo apt install python3 python3-pip -y
python3 --version
```

### 2. تثبيت المكتبات
```bash
pip3 install openpyxl PyPDF2
```

### 3. رفع الملفات إلى الخادم
```bash
# من جهازك إلى الخادم (عدّل IP والمسار)
scp -r dist/* user@192.168.1.100:/var/www/jld/
scp ai_server.py user@192.168.1.100:/var/www/jld/
```

### 4. تشغيل الخادم كخدمة systemd (يشتغل 24/7)

أنشئ ملف الخدمة:
```bash
sudo nano /etc/systemd/system/jldashboard.service
```

انسخ هذا المحتوى (عدّل المسار إذا اختلف):
```ini
[Unit]
Description=JLDA Dashboard Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/jld
ExecStart=/usr/bin/python3 /var/www/jld/ai_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

فعّل الخدمة وابدأها:
```bash
sudo systemctl daemon-reload
sudo systemctl enable jldashboard
sudo systemctl start jldashboard
sudo systemctl status jldashboard
```

### 5. فتح المنفذ في جدار الحماية
```bash
sudo ufw allow 5000/tcp
```

غيّر `ai_server.py` ليستمع على كل الواجهات:
```python
server = ThreadingHTTPServer(("0.0.0.0", PORT), AIHandler)
```

---

## ثالثاً: باستخدام Nginx كوكيل عكسي (لينكس — أنصح به للإنتاج)

هذا يسمح بالدخول عبر المنفذ 80 (http) بدون كتابة `:5000`:

### 1. ثبّت Nginx
```bash
sudo apt install nginx -y
```

### 2. أنشئ ملف وكيل عكسي
```bash
sudo nano /etc/nginx/sites-available/jld
```

انسخ هذا المحتوى:
```nginx
server {
    listen 80;
    server_name your-server-ip-or-domain;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. فعّل الموقع
```bash
sudo ln -s /etc/nginx/sites-available/jld /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

الآن يمكنك الدخول عبر `http://your-server-ip` دون الحاجة لكتابة `:5000`

---

## رابعاً: تشغيل Ollama (لخدمة الذكاء الاصطناعي)

إذا أردت تفعيل المحادثة مع AI وتحليل الملفات بالذكاء الاصطناعي:

### تثبيت Ollama على لينكس
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:3b
ollama serve
```

### تثبيت Ollama على ويندوز
- حمل من https://ollama.com/download
- شغّل المثبت
- افتح Command Prompt واكتب:
```cmd
ollama pull qwen2.5:3b
```

### ترقية النموذج (عند توفر GPU)

النموذج الحالي `qwen2.5:3b` يعمل على CPU بسرعة 15-25 ثانية للرد. للترقية:

1. النموذج التالي `qwen2.5:7b` مثبّت مسبقاً — يمكن تجربته فوراً.
   أو اسحب نموذجاً أفضل (إذا توفر GPU بذاكرة 16GB+):
```bash
ollama pull gemma3:12b
```

2. غيّر اسم النموذج في `ai_server.py` (سطر 16):
```python
MODEL = "qwen2.5:7b"   # بدلاً من qwen2.5:3b
```

3. ارفع `num_ctx` إذا أردت تحليل أعمق:
```python
num_ctx=4096,
num_predict=1024
```
4. أعد تشغيل الخدمة:
   - Windows: `nssm restart JLDashboard`
   - Linux: `sudo systemctl restart jldashboard`

**ملاحظة:** إذا لم تشغل Ollama، يعمل الموقع بشكل طبيعي لكن خاصيتي المحادثة وتحليل الملفات بالذكاء الاصطناعي لن تكون متاحة (باقي الميزات تعمل).

---

## أوامر سريعة للإدارة اليومية

### Windows
```cmd
# إيقاف الخدمة
nssm stop JLDashboard
# بدء الخدمة
nssm start JLDashboard
# إعادة تشغيل الخدمة
nssm restart JLDashboard
```

### Linux
```bash
# عرض حالة الخدمة
sudo systemctl status jldashboard
# إعادة تشغيل
sudo systemctl restart jldashboard
# مشاهدة السجلات
sudo journalctl -u jldashboard -f
```

---

## أمان

1. **غيّر كلمة مرور admin** قبل الإطلاق (في `ai_server.py`)
2. **غيّر كلمات مرور المحافظات** من `a1b2c3` إلى كلمات أقوى
3. استخدم **HTTPS** عبر Let's Encrypt مع Nginx إذا كان الموقع متاحاً للعام
4. راقب `audit.log` دورياً لاكتشاف أي محاولات دخول فاشلة
