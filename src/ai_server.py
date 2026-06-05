"""
ai_server.py
Serves the Dashboard + Auth + File Upload + AI Analysis.
Run: python src/ai_server.py
Open: http://localhost:5000
"""

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json, urllib.request, urllib.error, os, sys, uuid, shutil, io, csv, re, threading, datetime
try: import openpyxl
except: openpyxl = None
try: import PyPDF2
except: PyPDF2 = None

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"
PORT = 5000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
UPLOAD_DIR = os.path.join(SRC, "uploads")
AUDIT_LOG = os.path.join(SRC, "audit.log")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Check AI availability at startup
AI_AVAILABLE = False
try:
    req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
    with urllib.request.urlopen(req, timeout=3) as resp:
        tags = json.loads(resp.read().decode('utf-8'))
        models = [m.get('name', '') for m in tags.get('models', [])]
        AI_AVAILABLE = any(MODEL in m for m in models)
except Exception:
    AI_AVAILABLE = False


def log_audit(event, username, name, details="", ip="0.0.0.0"):
    """Write an audit entry to audit.log."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] [{ip}] [{username}] [{event}] {name} {details}\n"
    try:
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass

# In-memory sessions
_sessions = {}
# Analysis results store (request_id -> result)
_analysis_results = {}
_USERS = {
    "admin": {"password": "admin123", "name": "مدير النظام", "role": "admin", "gov": None},
    "user": {"password": "user123", "name": "موظف تنمية محلية", "role": "user", "gov": None},
    # Arabic usernames (original)
    "العاصمة": {"password": "a1b2c3", "name": "موظف العاصمة", "role": "gov_user", "gov": "العاصمة"},
    "البلقاء": {"password": "a1b2c3", "name": "موظف البلقاء", "role": "gov_user", "gov": "البلقاء"},
    "الزرقاء": {"password": "a1b2c3", "name": "موظف الزرقاء", "role": "gov_user", "gov": "الزرقاء"},
    "مأدبا":   {"password": "a1b2c3", "name": "موظف مأدبا",   "role": "gov_user", "gov": "مأدبا"},
    "إربد":    {"password": "a1b2c3", "name": "موظف إربد",    "role": "gov_user", "gov": "إربد"},
    "المفرق":  {"password": "a1b2c3", "name": "موظف المفرق",  "role": "gov_user", "gov": "المفرق"},
    "جرش":     {"password": "a1b2c3", "name": "موظف جرش",     "role": "gov_user", "gov": "جرش"},
    "عجلون":   {"password": "a1b2c3", "name": "موظف عجلون",   "role": "gov_user", "gov": "عجلون"},
    "الكرك":   {"password": "a1b2c3", "name": "موظف الكرك",   "role": "gov_user", "gov": "الكرك"},
    "الطفيلة": {"password": "a1b2c3", "name": "موظف الطفيلة", "role": "gov_user", "gov": "الطفيلة"},
    "معان":    {"password": "a1b2c3", "name": "موظف معان",    "role": "gov_user", "gov": "معان"},
    "العقبة":  {"password": "a1b2c3", "name": "موظف العقبة",  "role": "gov_user", "gov": "العقبة"},
    # English usernames (added)
    "amman.gov":   {"password": "a1b2c3", "name": "موظف العاصمة", "role": "gov_user", "gov": "العاصمة"},
    "balqa.gov":   {"password": "a1b2c3", "name": "موظف البلقاء", "role": "gov_user", "gov": "البلقاء"},
    "zarqa.gov":   {"password": "a1b2c3", "name": "موظف الزرقاء", "role": "gov_user", "gov": "الزرقاء"},
    "madaba.gov":  {"password": "a1b2c3", "name": "موظف مأدبا",   "role": "gov_user", "gov": "مأدبا"},
    "irbid.gov":   {"password": "a1b2c3", "name": "موظف إربد",    "role": "gov_user", "gov": "إربد"},
    "mafraq.gov":  {"password": "a1b2c3", "name": "موظف المفرق",  "role": "gov_user", "gov": "المفرق"},
    "jerash.gov":  {"password": "a1b2c3", "name": "موظف جرش",     "role": "gov_user", "gov": "جرش"},
    "ajloun.gov":  {"password": "a1b2c3", "name": "موظف عجلون",   "role": "gov_user", "gov": "عجلون"},
    "karak.gov":   {"password": "a1b2c3", "name": "موظف الكرك",   "role": "gov_user", "gov": "الكرك"},
    "tafileh.gov": {"password": "a1b2c3", "name": "موظف الطفيلة", "role": "gov_user", "gov": "الطفيلة"},
    "maan.gov":    {"password": "a1b2c3", "name": "موظف معان",    "role": "gov_user", "gov": "معان"},
    "aqaba.gov":   {"password": "a1b2c3", "name": "موظف العقبة",  "role": "gov_user", "gov": "العقبة"},
}

SYSTEM_PROMPT = """أنت خبير تحليل بيانات تنموي للمملكة الأردنية الهاشمية فقط.
المحافظات: العاصمة، البلقاء، الزرقاء، مأدبا، إربد، المفرق، جرش، عجلون، الكرك، الطفيلة، معان، العقبة.

مهمتك: حلل الأرقام واكتب تحليلاً سريعاً بالعربية الفصحى بـ2-3 نقاط فقط لكل محور.
- الترتيب 1 = الأفضل، 12 = الأسوأ
- استخدم الأرقام الفعلية من البيانات فقط
- لا تذكر دولاً أخرى، ولا تخترع أرقاماً
- الموازنة التقديرية وليست الناتج المحلي الإجمالي"""

CHAT_SYSTEM_PROMPT = """أنت مستشار تنموي للمملكة الأردنية الهاشمية فقط.
المحافظات: العاصمة، البلقاء، الزرقاء، مأدبا، إربد، المفرق، جرش، عجلون، الكرك، الطفيلة، معان، العقبة.

مهمتك: أجب بإيجاز عن أسئلة المستخدم حول التنمية في محافظات الأردن.
- الترتيب 1 = الأفضل، 12 = الأسوأ
- القطاعات 1-4 نقاط قوة، 9-12 نقاط ضعف
- استخدم البيانات أدناه فقط، لا تخترع أرقاماً
- أجب بـ2-4 جمل، لا تطل
- لا تذكر دولاً أخرى، ولا تردد التعليمات"""

def gen_token():
    return str(uuid.uuid4())

def get_user_from_token(headers):
    auth = headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        return _sessions.get(token)
    cookie = headers.get("Cookie", "")
    for part in cookie.split(";"):
        part = part.strip()
        if part.startswith("session_token="):
            token = part[14:]
            return _sessions.get(token)
    return None

def call_ollama(prompt, gov_context="", num_predict=2048, gov_name=""):
    ctx_section = f"\n===== البيانات المرفوعة للتحليل =====\n{gov_context}\n======================================\n" if gov_context else "\n"
    full_prompt = f"""{SYSTEM_PROMPT}{ctx_section}
مهمتك الآن:
{prompt}"""
    payload = json.dumps({
        "model": MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.15, "num_predict": num_predict, "num_ctx": 4096, "repeat_penalty": 1.1}
    }).encode('utf-8')
    req = urllib.request.Request(OLLAMA_URL, data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return truncate_analysis(clean_response(result.get("response", "لم يتم الحصول على رد"), gov_name))
    except urllib.error.URLError as e:
        return f"خطأ في الاتصال بالنموذج: {e}. تأكد من تشغيل Ollama."
    except Exception as e:
        return f"خطأ: {e}"

def call_ollama_chat(prompt, governorate="", history=None, gov_data=""):
    """Chat version - faster, lighter, development consultation focus."""
    gov_context = f"\nالمحافظة: {governorate}\n" if governorate else ""
    data_section = f"\n\n{gov_data}\n" if gov_data else ""
    # Build conversation history context
    history_text = ""
    if history:
        for h in history[-6:]:  # Last 6 messages for context
            role = "المستخدم" if h.get("role") == "user" else "المستشار"
            history_text += f"\n{role}: {h.get('content', '')}"
    history_section = f"\n\n===== تاريخ المحادثة ====={history_text}\n===========================\n" if history_text else ""
    full_prompt = f"""{CHAT_SYSTEM_PROMPT}{gov_context}{data_section}{history_section}

سؤال المستخدم:
{prompt}"""
    payload = json.dumps({
        "model": MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.15, "num_predict": 512, "num_ctx": 4096, "repeat_penalty": 1.15}
    }).encode('utf-8')
    req = urllib.request.Request(OLLAMA_URL, data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return clean_response(result.get("response", "لم يتم الحصول على رد"), governorate)
    except urllib.error.URLError as e:
        return f"خطأ في الاتصال بالنموذج: {e}"
    except Exception as e:
        return f"خطأ: {e}"

def clean_response(text, gov_name=""):
    """Fix common Arabic spelling/encoding artifacts and hallucinated names from phi4-mini."""
    if not text:
        return text
    if text.startswith('\ufeff'):
        text = text[1:]
    import re
    # Remove CJK characters + CJK symbols (。，、％) + fullwidth forms
    text = re.sub(r'[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef\u3400-\u4dbf\uf900-\ufaff]', '', text)
    # Fix repeated words (phi4-mini common artifact)
    text = re.sub(r'\b(في|من|على|إلى|عن|مع|و)\s+\1\b', r'\1', text)
    text = re.sub(r'\b(و)\s+(و)\s+', r'\1 ', text)
    # Governorate name hallucinations — run BEFORE الالال cleanup
    # because short forms like "كرك" match as substrings of "الكرك"
    all_govs = {
        'العاصمة': ['عمّان', 'عمان', 'الالالعاصمة', 'العاصمة عمّان'],
        'البلقاء': ['السلط'],
        'مأدبا': ['مادبا'],
        'إربد': ['اربد', 'أربد'],
        'الكرك': ['ككر', 'كركك', 'كرك', 'كراك', 'الالالكرك', 'كرك الكرك'],
        'المفرق': ['المفراق', 'مفرق'],
        'الطفيلة': ['طفيلة'],
        'العقبة': ['العقبه'],
    }
    for correct, wrong_list in all_govs.items():
        for wrong in wrong_list:
            text = text.replace(wrong, correct)
    # If the expected governorate is completely absent, try to force-fix
    if gov_name and gov_name not in text:
        for wrong, correct_list in all_govs.items():
            if wrong == gov_name:
                continue
            for w in correct_list + [wrong]:
                if w in text:
                    text = text.replace(w, gov_name, 1)
                    break
    # Rank/spelling hallucinations
    replacements = {
        'بطرة': 'بطالة', 'بطالت': 'بطالة',
        'محافطة': 'محافظة', 'محافظه': 'محافظة',
        'سياستي': 'سياسي',
        'الاردن': 'الأردن',
        ' residents': ' السكان',
        'Residents': 'السكان',
        'نسبتي': 'نسبة',
        'المترين': 'المرتبة', 'المتر': 'المرتبة',
    }
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)
    # Fix "متوسطة الارتفاعة/الارتفاع" → "متوسط"
    text = re.sub(r'متوسطة?\s*الارتفا[عق]ة?', 'متوسط', text)
    # Fix broken rank patterns: "- المترين 5" or standalone "المترين 5"
    text = re.sub(r'(^|[\n\-–—])\s*المترين\s*\d+', '', text)
    # Remove raw emoji tags that the model echoes back (💪 📊 ⚠️)
    # These are meaningful, let's keep them but clean surrounding text
    # Remove stray non-Arabic characters/words
    foreign_words = {
        'tecnológicas?': 'التكنولوجية', 'tecnológicos?': 'التكنولوجية',
        'tecnológic[ao]s?': 'التكنولوجية',
        'aguas?': 'المياه', 'soluciones?': 'حلول',
        'implementación': 'تنفيذ', 'digitales?': 'الرقمية',
        'proyectos?': 'مشاريع', 'capacitación': 'تدريب',
        'infraestructura': 'البنية التحتية', 'agrícolas?': 'الزراعية',
        'desarrollo': 'تطوير', 'gestión': 'إدارة',
        'recursos': 'موارد', 'sector': 'قطاع',
        'económico': 'اقتصادي', 'económicos?': 'اقتصادية',
        'sociales?': 'اجتماعية', 'sistema': 'نظام',
        'gobierno': 'حكومة', 'políticas?': 'سياسات',
    }
    for pattern, replacement in foreign_words.items():
        text = re.sub(r'\b' + pattern + r'\b', replacement, text, flags=re.IGNORECASE)
    # Fix "الالال" repeated prefix LAST — name_map can add ال to already-correct names
    text = re.sub(r'(ال){2,}', 'ال', text)
    # Strip echoed instructions — put specific patterns BEFORE general ones
    echo_patterns = [
        r'لا تذكر[^.]*\.',  # "لا تذكر أي دولة أخرى..." (must be before تذكر)
        r'لا تخترع[^.]*\.',
        r'لا تقل[^.]*\.',
        r'لا تستخدم[^.]*\.',
        r'تذكر:?[^.]*\.',  # "تذكر: اسم المحافظة الصحيح..."
        r'اسم المحافظة[^.]*\.',
        r'الاسم المدخل[^.]*\.',
        r'إذا ورد[^.]*\.',
        r'هذه بيانات حقيقية[^.]*\.',
        r'المحافظات الأردنية هي فقط[^.]*\.',
        r'التزم بهذه[^.]*\.',
        r'قدم تحليلك[^.]*\.',
    ]
    for pat in echo_patterns:
        text = re.sub(pat, '', text)
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    # Clean numeric artifacts from CJK removal (e.g. "18.0%8" → "18.0%")
    text = re.sub(r'%\d(?![.\d%])', '%', text)
    # Clean double percent signs
    text = text.replace('%%', '%')
    return text.strip()

def truncate_analysis(text, max_chars=800):
    """Post-processing truncation for AI analysis brevity enforcement.
    Extracts 3 sections (نقاط قوة, نقاط ضعف, فرص) with 2-3 bullets each,
    then hard-cuts at max_chars as final safety."""
    if not text or len(text) <= max_chars:
        return text
    sections = {
        'قوة': re.compile(r'(?:نقاط\s*)?(?:القوة|قوة)', re.UNICODE),
        'ضعف': re.compile(r'(?:نقاط\s*)?(?:الضعف|ضعف)', re.UNICODE),
        'فرص': re.compile(r'(?:ال)?فرص(?:\s*التنموية|\s*تطوير)?', re.UNICODE),
        'توصيات': re.compile(r'(?:ال)?توصيات', re.UNICODE),
    }
    lines = text.split('\n')
    result_lines = []
    current_section = None
    section_counts = {k: 0 for k in sections}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        for key, pat in sections.items():
            if pat.search(stripped):
                current_section = key
                result_lines.append(stripped)
                section_counts[key] = 0
                break
        else:
            if current_section and section_counts.get(current_section, 0) < 3:
                if stripped.startswith('-') or stripped.startswith('•') or stripped.startswith('*') or stripped[0].isdigit():
                    result_lines.append(stripped)
                    section_counts[current_section] = section_counts.get(current_section, 0) + 1
    extracted = '\n'.join(result_lines)
    if len(extracted) > 100:
        return extracted[:max_chars]
    return text[:max_chars]


def read_file_content(file_path, filename=""):
    ext = os.path.splitext(filename)[1].lower()
    try:
        if ext == ".csv":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read(50000)
        elif ext in (".xlsx", ".xls"):
            if not openpyxl: return "[مكتبة openpyxl غير متوفرة]"
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            rows = []
            for sheet in wb.worksheets:
                rows.append(f"=== ورقة: {sheet.title} ===")
                for i, row in enumerate(sheet.iter_rows(values_only=True)):
                    if i > 200: break
                    rows.append(",".join(str(c) if c is not None else "" for c in row))
            wb.close()
            return "\n".join(rows[:5000])
        elif ext == ".pdf":
            if not PyPDF2: return "[مكتبة PyPDF2 غير متوفرة]"
            text = ""
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    if i > 20: break
                    text += page.extract_text() + "\n"
            return text[:50000]
        else:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read(50000)
    except Exception as e:
        return f"[خطأ في قراءة الملف: {e}]"

def analyze_file(file_path, filename, service_type, governorate, description):
    content = read_file_content(file_path, filename)
    stats = compute_data_stats(content)
    report = generate_report(stats, service_type, governorate, description)
    return report

def generate_report(stats, service_type, governorate, description):
    """Concise analysis: key gaps → deviations → recommendations."""
    lines = []
    na = stats.get("numeric_analysis", {})
    cols = stats.get("column_names", [])
    num_rows = stats.get("num_rows", 0)

    lines.append(f"📊 {num_rows} محافظة، {len(cols)} مؤشر")
    lines.append("")

    if not na:
        lines.append("لا توجد أرقام كافية للتحليل.")
        return "\n".join(lines)

    # ---- ترتيب المؤشرات حسب الفجوة ----
    sorted_cols = sorted(na.items(), key=lambda x: abs(float(x[1].get("gap", 0) or 0)), reverse=True)

    # ---- التحليل: أعلى/أدنى + الانحراف عن المتوسط ----
    lines.append("🔍 تحليل المؤشرات")
    for col_name, col_data in sorted_cols:
        max_v = col_data.get("max", "")
        min_v = col_data.get("min", "")
        max_r = col_data.get("max_row", "")
        min_r = col_data.get("min_row", "")
        gap = col_data.get("gap", "")
        avg = col_data.get("avg", "")
        try:
            dev_high = round(float(max_v) - float(avg), 1)
            dev_low = round(float(avg) - float(min_v), 1)
        except:
            dev_high = dev_low = ""
        lines.append(f"• {col_name}: الأعلى {max_v} ({max_r}) بزيادة {dev_high} عن المتوسط {avg}، الأدنى {min_v} ({min_r}) بأقل {dev_low} عن المتوسط")
    lines.append("")

    # ---- أبرز العلاقات (أكثر 4) ----
    if len(na) >= 2:
        col_names_list = list(na.keys())
        found = set()
        rels = []
        for i in range(len(col_names_list)):
            for j in range(i+1, len(col_names_list)):
                c1 = na[col_names_list[i]]
                c2 = na[col_names_list[j]]
                if c1.get("max_row") == c2.get("max_row") and c1.get("max_row"):
                    r = f"• {c1['max_row']} تتصدر في '{col_names_list[i]}' و'{col_names_list[j]}'"
                    if r not in found: rels.append(r); found.add(r)
                if c1.get("min_row") == c2.get("min_row") and c1.get("min_row"):
                    r = f"• {c1['min_row']} الأدنى في '{col_names_list[i]}' و'{col_names_list[j]}'"
                    if r not in found: rels.append(r); found.add(r)
        if rels:
            lines.append("🔗 العلاقات")
            lines.extend(rels[:4])
            lines.append("")

    # ---- تدخلات مطلوبة (المحافظات المتأخرة) ----
    lines.append("💡 تدخلات تنموية مطلوبة")
    interventions = []
    for col_name, col_data in sorted_cols:
        min_r = col_data.get("min_row", "")
        min_v = col_data.get("min", "")
        avg = col_data.get("avg", "")
        max_r = col_data.get("max_row", "")
        max_v = col_data.get("max", "")
        if min_r and min_v is not None:
            interventions.append(f"• {min_r}: رفع {col_name} من {min_v} إلى المتوسط {avg}")
        if max_r and max_v is not None and max_r != min_r:
            interventions.append(f"• {max_r}: الاستفادة من ريادتها في {col_name} ({max_v}) لنقل التجربة")
        if len(interventions) >= 8:
            break
    lines.extend(interventions[:6])
    lines.append("")

    # ---- خلاصة الأولويات ----
    gov_count = {}
    for col_name, col_data in na.items():
        min_r = col_data.get("min_row", "")
        if min_r:
            gov_count[min_r] = gov_count.get(min_r, 0) + 1
    if gov_count:
        top = max(gov_count, key=gov_count.get)
        lines.append(f"🔴 الأولوية: {top} الأكثر حاجة للتدخل ({gov_count[top]} مؤشر)")

    return "\n".join(lines)

    if description:
        lines.append(f"هذا التحليل تم استناداً إلى طلب المستخدم: {description}")

    return "\n".join(lines)

def compute_data_stats(content):
    """Extract statistics from tabular data. Handles sheet markers and mixed content."""
    raw_lines = [l.strip() for l in content.split("\n") if l.strip()]
    # Filter out non-data lines (sheet markers, separators, empty metadata)
    data_lines = [l for l in raw_lines if not l.startswith("===") and not l.startswith("---") and not l.startswith("***")]
    if not data_lines:
        return {"error": "لا توجد بيانات", "num_rows": 0, "column_names": [], "numeric_analysis": {}}
    headers = [h.strip() for h in data_lines[0].split(",")]
    rows = []
    gov_name_map = {
        'عمان': 'العاصمة', 'عمّان': 'العاصمة', 'العاصمة عمان': 'العاصمة', 'العاصمة عمّان': 'العاصمة',
        'اربد': 'إربد', 'أربد': 'إربد',
        'مادبا': 'مأدبا',
        'الكرك': 'الكرك', 'ككر': 'الكرك',
        'المفراق': 'المفرق',
        'طفيلة': 'الطفيلة',
        'العقبه': 'العقبة',
        'السلط': 'البلقاء',
    }
    for line in data_lines[1:]:
        vals = [v.strip() for v in line.split(",")]
        if len(vals) >= len(headers):
            vals[0] = gov_name_map.get(vals[0], vals[0])
            rows.append(vals[:len(headers)])
    num_cols = len(headers)
    numeric_cols = {}
    for ci in range(num_cols):
        col_vals = []
        for row in rows:
            try:
                v = float(row[ci].replace("%", "").replace(",", "").replace(" ", ""))
                col_vals.append(v)
            except:
                pass
        if len(col_vals) >= 2:  # Need at least 2 values for meaningful stats
            h = headers[ci]
            numeric_cols[h] = {
                "max": max(col_vals),
                "min": min(col_vals),
                "avg": round(sum(col_vals) / len(col_vals), 1),
                "gap": round(max(col_vals) - min(col_vals), 1),
                "max_row": rows[col_vals.index(max(col_vals))][0] if col_vals and len(rows) > 0 else "",
                "min_row": rows[col_vals.index(min(col_vals))][0] if col_vals and len(rows) > 0 else ""
            }
    return {
        "num_rows": len(rows),
        "num_columns": num_cols,
        "column_names": headers,
        "numeric_analysis": numeric_cols,
        "first_row_sample": rows[0] if rows else []
    }

def build_gov_context(gov_name):
    """Build structured context string for AI analysis from existing dashboard data, with rankings."""
    try:
        data_path = os.path.join(SRC, "data.json")
        strat_path = os.path.join(SRC, "strategic_comprehensive.json")
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        govs = data.get("governorates", [])
        gov = None
        for g in govs:
            if g.get("name") == gov_name:
                gov = g
                break
        if not gov:
            return f"خطأ: لم يتم العثور على محافظة {gov_name}"

        # Collect all governorates data for ranking
        all_composites = []
        all_sectors = {}
        all_unemp = []
        for g in govs:
            gname = g.get("name", "")
            all_composites.append((gname, g.get("composite_index", 0)))
            sr = g.get("sectors", {})
            for s_name, s_data in sr.items():
                score = s_data.get("score", 0) if isinstance(s_data, dict) else (float(s_data) if s_data else 0)
                all_sectors.setdefault(s_name, []).append((gname, score))
            ue = g.get("contextual_drivers", {}).get("unemployment_rate", 1)
            all_unemp.append((gname, ue))

        def rank_of(item, lst):
            """Rank: 1 = best (highest score OR lowest unemployment)."""
            sorted_lst = sorted(lst, key=lambda x: -x[1])
            for i, (name, _) in enumerate(sorted_lst):
                if name == item:
                    return i + 1
            return len(lst)

        def rev_rank_of(item, lst):
            """Reverse rank: 1 = lowest value (for unemployment where lower is better)."""
            sorted_lst = sorted(lst, key=lambda x: x[1])
            for i, (name, _) in enumerate(sorted_lst):
                if name == item:
                    return i + 1
            return len(lst)

        sectors_raw = gov.get("sectors", {})
        sectors = {}
        if isinstance(sectors_raw, dict):
            for s_name, s_data in sectors_raw.items():
                score = s_data.get("score", 0) if isinstance(s_data, dict) else (float(s_data) if s_data else 0)
                sectors[s_name] = score
        else:
            sectors = {}

        comp_index = gov.get('composite_index', 0)
        comp_rank = rank_of(gov_name, all_composites)

        context = f"""===== تحليل تنموي شامل لمحافظة: {gov_name} =====

البيانات الأساسية (ملاحظة: الموازنة التقديرية أدناه هي موازنة المحافظة المخصصة من الحكومة لعام 2026، وليست الناتج المحلي الإجمالي):
- عدد السكان: {gov.get('population', 0):,} نسمة
- المساحة: {gov.get('area', 0):,} كم²
- موازنة 2026 (تقديرية): {gov.get('budget_2026', 0):,} دينار أردني
- المؤشر المركب: {comp_index:.1f} من 100 (المرتبة {comp_rank} من 12)

درجات القطاعات (من 100) وترتيبها بين المحافظات الـ12:\n"""
        sorted_sectors = sorted(sectors.items(), key=lambda x: -x[1])
        for s_name, s_score in sorted_sectors:
            s_rank = rank_of(gov_name, all_sectors.get(s_name, []))
            if s_rank <= 3:
                tag = "💪 قوي"
            elif s_rank <= 6:
                tag = "📊 متوسط مرتفع"
            elif s_rank <= 9:
                tag = "📉 متوسط منخفض"
            else:
                tag = "⚠️ ضعيف"
            context += f"- {s_name}: {s_score:.1f} (المرتبة {s_rank} من 12) — {tag}\n"

        context += f"\nأعلى قطاعين: {', '.join(s for s, _ in sorted_sectors[:2])}\n"
        context += f"أدنى قطاعين: {', '.join(s for s, _ in sorted_sectors[-2:])}\n"

        # Add contextual drivers with ranking
        cd = gov.get("contextual_drivers", {})
        if cd:
            context += "\nالمؤشرات السياقية:\n"
            for k, v in cd.items():
                if k == "unemployment_rate":
                    ue_rank = rev_rank_of(gov_name, all_unemp)
                    if ue_rank <= 3:
                        ue_tag = "👍 منخفضة (جيد)"
                    elif ue_rank <= 6:
                        ue_tag = "📊 متوسطة"
                    elif ue_rank <= 9:
                        ue_tag = "📈 مرتفعة"
                    else:
                        ue_tag = "⚠️ مرتفعة جداً"
                    context += f"- معدل البطالة: {v*100:.1f}% (الترتيب: {ue_rank} من 12) — {ue_tag}\n"
                else:
                    context += f"- {k}: {v}\n"

        # Add competitive advantages
        ca = gov.get("competitive_advantages", [])
        if ca:
            context += f"\nالمزايا التنافسية: {'، '.join(ca)}\n"

        # Add strategic data
        if os.path.exists(strat_path):
            with open(strat_path, "r", encoding="utf-8") as f:
                strat = json.load(f)
            gov_strat = strat.get(gov_name, {})
            if gov_strat:
                context += f"\nالخطط الاستراتيجية:\n"
                plans = gov_strat.get("strategic_plans", [])
                for p in plans[:5]:
                    context += f"- {p.get('name', '')}: {p.get('objective', '')}\n"

        context += f"""
==========
أنت خبير تنمية محلية للمملكة الأردنية الهاشمية فقط.
المحافظة التي تحللها: ({gov_name}).
الترتيب: 1 = الأفضل، 12 = الأسوأ. القطاعات 1-4 قوة، 9-12 ضعف.

أعط تحليلاً سريعاً بـ2-3 نقاط فقط لكل قسم:

**نقاط القوة**: 2-3 جمل (القطاعات الأعلى ترتيباً والمزايا التنافسية)
**نقاط الضعف**: 2-3 جمل (القطاعات الأدنى ترتيباً والتحديات)
**الفرص التنموية**: 2-3 جمل (فرص التطوير بناءً على الفجوات)

ملاحظات: الموازنة تقديرية وليست GDP. استخدم الأرقام الفعلية من البيانات فقط. لا تذكر دولاً أخرى."""
        return context
    except Exception as e:
        return f"خطأ في بناء السياق: {e}"


def build_chat_gov_data(gov_name):
    """Build structured numeric data context for chat about a specific governorate, with rankings."""
    try:
        data_path = os.path.join(SRC, "data.json")
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        govs = data.get("governorates", [])
        gov = None
        for g in govs:
            if g.get("name") == gov_name:
                gov = g
                break
        if not gov:
            return ""
        # Collect all governorates sector scores for ranking
        all_sectors = {}  # sector_name -> [(gov_name, score)]
        all_composites = []  # [(gov_name, composite_index)]
        for g in govs:
            gname = g.get("name", "")
            sr = g.get("sectors", {})
            for s_name, s_data in sr.items():
                score = s_data.get("score", 0) if isinstance(s_data, dict) else (float(s_data) if s_data else 0)
                all_sectors.setdefault(s_name, []).append((gname, score))
            all_composites.append((gname, g.get("composite_index", 0)))
        # Rank helper: higher score = rank 1
        def rank_in(item, lst):
            sorted_lst = sorted(lst, key=lambda x: -x[1])
            for i, (name, _) in enumerate(sorted_lst):
                if name == item:
                    return i + 1
            return len(lst)

        sectors_raw = gov.get("sectors", {})
        sectors = []
        for s_name, s_data in sectors_raw.items():
            score = s_data.get("score", 0) if isinstance(s_data, dict) else (float(s_data) if s_data else 0)
            rank = rank_in(gov_name, all_sectors.get(s_name, []))
            sectors.append((s_name, score, rank))
        sectors.sort(key=lambda x: -x[1])

        cd = gov.get("contextual_drivers", {})
        lines = [f"===== بيانات محافظة: {gov_name} ====="]
        lines.append(f"- عدد السكان: {gov.get('population', 0):,} نسمة")
        lines.append(f"- المساحة: {gov.get('area', 0):,} كم²")
        lines.append(f"- موازنة 2026 (تقديرية): {gov.get('budget_2026', 0):,} دينار أردني")
        comp_index = gov.get('composite_index', 0)
        comp_rank = rank_in(gov_name, all_composites)
        lines.append(f"- المؤشر المركب: {comp_index:.1f} من 100 (المرتبة {comp_rank} من 12)")
        lines.append("")
        lines.append("درجات القطاعات (من 100) وترتيبها بين المحافظات الـ12:")
        for s_name, s_score, s_rank in sectors:
            if s_rank <= 3:
                tag = "💪 قوي"
            elif s_rank <= 6:
                tag = "📊 متوسط مرتفع"
            elif s_rank <= 9:
                tag = "📉 متوسط منخفض"
            else:
                tag = "⚠️ ضعيف"
            lines.append(f"  {s_name}: {s_score:.1f} (المرتبة {s_rank} من 12) — {tag}")
        if cd:
            # Rank contextual drivers too
            all_cd = {}  # driver_name -> [(gov_name, value)]
            for g in govs:
                gname = g.get("name", "")
                gcd = g.get("contextual_drivers", {})
                for k, v in gcd.items():
                    all_cd.setdefault(k, []).append((gname, v))
            lines.append("")
            lines.append("المؤشرات السياقية:")
            for k, v in cd.items():
                label = k
                if k == "unemployment_rate":
                    label = "معدل البطالة"
                    r = rank_in(gov_name, all_cd.get(k, []))
                    if r >= 10:
                        tag = "👍 منخفض"
                    elif r >= 7:
                        tag = "📊 متوسط"
                    elif r >= 4:
                        tag = "📈 مرتفع"
                    else:
                        tag = "⚠️ مرتفع جداً"
                    lines.append(f"  {label}: {v*100:.1f}% (المرتبة {r} من 12) — {tag}")
                elif "pct" in k:
                    r = rank_in(gov_name, all_cd.get(k, []))
                    pmap = {"refugee_pct": "نسبة اللاجئين", "low_income_pct": "نسبة الدخل المنخفض", "medium_income_pct": "نسبة الدخل المتوسط", "high_income_pct": "نسبة الدخل المرتفع", "aid_recipient_pct": "نسبة متلقي المساعدات"}
                    label = pmap.get(k, k)
                    lines.append(f"  {label}: {v:.1f}% (المرتبة {r} من 12)")
                elif "income" in k:
                    r = rank_in(gov_name, all_cd.get(k, []))
                    label = "متوسط دخل الفرد"
                    lines.append(f"  {label}: {v:.1f} دينار (المرتبة {r} من 12)")
                elif "density" in k or k == "population_density":
                    r = rank_in(gov_name, all_cd.get(k, []))
                    lines.append(f"  الكثافة السكانية: {v:.1f} نسمة/كم² (المرتبة {r} من 12)")
                elif "econ_participation" in k:
                    r = rank_in(gov_name, all_cd.get(k, []))
                    label = "مشاركة اقتصادية" if "total" in k else "مشاركة اقتصادية (إناث)"
                    lines.append(f"  {label}: {v:.1f}% (المرتبة {r} من 12)")
                elif k == "refugee_count":
                    r = rank_in(gov_name, all_cd.get(k, []))
                    lines.append(f"  عدد اللاجئين: {v:,.0f} (المرتبة {r} من 12)")
                elif isinstance(v, (int, float)):
                    r = rank_in(gov_name, all_cd.get(k, []))
                    lines.append(f"  {label}: {v} (المرتبة {r} من 12)")
                else:
                    lines.append(f"  {label}: {v}")
        # Add competitive advantages
        ca = gov.get("competitive_advantages", [])
        if ca:
            lines.append("")
            lines.append(f"المزايا التنافسية: {'، '.join(ca[:3])}")
        # Add strategic context from strategic_comprehensive.json
        try:
            strat_path = os.path.join(SRC, "strategic_comprehensive.json")
            if os.path.exists(strat_path):
                with open(strat_path, "r", encoding="utf-8") as f:
                    strat = json.load(f)
                gov_strat = strat.get(gov_name, {})
                if gov_strat:
                    intro = gov_strat.get("introduction", "")
                    if intro:
                        lines.append("")
                        lines.append(f"الوصف الاستراتيجي: {intro.replace('<br>', '. ')[:300]}")
        except Exception:
            pass
        lines.append("")
        return "\n".join(lines)
    except Exception:
        return ""

MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
}

PROTECTED_PAGES = ['/index.html', '/upload.html', '/chat.html', '/audit.html']

class AIHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def serve_static(self, path):
        if path == "/" or path == "":
            path = "/landing.html"
        # Strip query string for file serving
        clean_path = path.split("?")[0]
        user = get_user_from_token(self.headers)
        if clean_path in PROTECTED_PAGES and not user:
            self.send_response(302)
            self.send_header("Location", "/login.html")
            self.end_headers()
            return
        for base in [SRC, ROOT]:
            file_path = os.path.join(base, clean_path.lstrip("/"))
            if os.path.isfile(file_path):
                ext = os.path.splitext(file_path)[1]
                ctype = MIME_TYPES.get(ext, 'application/octet-stream')
                try:
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(data)
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(f"Error: {e}".encode('utf-8'))
                return
        self.send_response(404)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"404 Not Found")

    def do_GET(self):
        if self.path == "/health":
            user = get_user_from_token(self.headers)
            try:
                urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
                status = {"status": "ok", "model": MODEL, "ollama": "running", "user": user}
            except:
                status = {"status": "ok", "ollama": "not running", "user": user}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(status, ensure_ascii=False).encode('utf-8'))
            return
        if self.path == "/api/ai-status":
            alive = False
            try:
                req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    tags = json.loads(resp.read().decode('utf-8'))
                    models = [m.get('name', '') for m in tags.get('models', [])]
                    alive = any(MODEL in m for m in models)
            except Exception:
                alive = False
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"available": alive, "model": MODEL if alive else None}, ensure_ascii=False).encode('utf-8'))
            return
        if self.path == "/api/me":
            user = get_user_from_token(self.headers)
            if user:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"authenticated": True, "name": user["name"], "role": user["role"], "gov": user.get("gov")}, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"authenticated": False}).encode())
            return

        # --- AUDIT LOG (admin only) ---
        if self.path == "/api/audit-log":
            user = get_user_from_token(self.headers)
            if not user or user["role"] != "admin":
                self.send_response(403)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"message": "غير مصرح - صلاحية مدير النظام فقط"}).encode('utf-8'))
                return
            entries = []
            if os.path.exists(AUDIT_LOG):
                with open(AUDIT_LOG, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            entries.append(line)
            entries.reverse()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"entries": entries}, ensure_ascii=False).encode('utf-8'))
            return

        # --- POLL ANALYSIS RESULT (GET) ---
        if self.path.startswith("/api/analysis-result/"):
            rid = self.path.split("/")[-1]
            result = _analysis_results.get(rid, {})
            if not result:
                meta_path = os.path.join(UPLOAD_DIR, f"req_{rid}", "meta.json")
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                        result = {
                            "status": meta.get("status", "unknown"),
                            "analysis": meta.get("analysis", ""),
                            "ai_status": meta.get("ai_status", "unknown"),
                            "ai_analysis": meta.get("ai_analysis", None)
                        }
                        _analysis_results[rid] = result
                    except:
                        result = {"status": "error", "analysis": "خطأ في قراءة النتيجة", "ai_status": "unknown", "ai_analysis": None}
                else:
                    result = {"status": "unknown", "analysis": "", "ai_status": "unknown", "ai_analysis": None}
            status = result.get("status", "unknown")
            ai_status = result.get("ai_status", "unknown")
            analysis = result.get("analysis", "")
            ai_analysis = result.get("ai_analysis", None)
            if status == "completed":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "completed",
                    "analysis": analysis,
                    "ai_status": ai_status,
                    "ai_analysis": ai_analysis
                }, ensure_ascii=False).encode('utf-8'))
            elif status == "error":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "analysis": result.get("analysis", "حدث خطأ في التحليل"),
                    "ai_status": ai_status,
                    "ai_analysis": ai_analysis
                }, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "processing"}, ensure_ascii=False).encode('utf-8'))
            return

        self.serve_static(self.path)

    def do_DELETE(self):
        # --- CLEAR AUDIT LOG (admin only) ---
        if self.path == "/api/audit-log":
            user = get_user_from_token(self.headers)
            if not user or user["role"] != "admin":
                self.send_response(403)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"message": "غير مصرح"}).encode('utf-8'))
                return
            try:
                open(AUDIT_LOG, "w", encoding="utf-8").close()
                log_audit("AUDIT_CLEAR", user["username"], user["name"], "مسح سجل التدقيق", ip=self.client_address[0])
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"message": "تم مسح السجل"}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
            return
        self.send_response(405)
        self.end_headers()

    def do_POST(self):
        # --- LOGIN ---
        if self.path == "/api/login":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode('utf-8-sig'))
            username = body.get("username", "")
            password = body.get("password", "")
            user_info = _USERS.get(username)
            ip = self.client_address[0]
            if user_info and user_info["password"] == password:
                token = gen_token()
                _sessions[token] = {"name": user_info["name"], "role": user_info["role"], "username": username, "gov": user_info.get("gov")}
                log_audit("LOGIN_OK", username, user_info["name"], ip=ip)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"token": token, "name": user_info["name"], "role": user_info["role"], "gov": user_info.get("gov")}, ensure_ascii=False).encode('utf-8'))
            else:
                log_audit("LOGIN_FAIL", username, "محاولة دخول فاشلة", ip=ip)
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"message": "اسم المستخدم أو كلمة المرور غير صحيحة"}).encode())
            return

        # --- LOGOUT ---
        if self.path == "/api/logout":
            auth = self.headers.get("Authorization", "")
            user = get_user_from_token(self.headers)
            if auth.startswith("Bearer "):
                token = auth[7:]
                _sessions.pop(token, None)
            if user:
                log_audit("LOGOUT", user["username"], user["name"], ip=self.client_address[0])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"message": "تم تسجيل الخروج"}).encode())
            return

        # --- GOVERNORATE AI ANALYSIS (uses existing dashboard data) ---
        if self.path == "/api/gov-analysis":
            try:
                user = get_user_from_token(self.headers)
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                body = json.loads(raw.decode('utf-8'))
                gov_name = body.get("governorate", "")
                if not gov_name:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "يرجى تحديد اسم المحافظة"}).encode())
                    return
                gov_context = build_gov_context(gov_name)
                if gov_context.startswith("خطأ"):
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": gov_context}).encode())
                    return
                ai_result = call_ollama(gov_context, "", num_predict=1024, gov_name=gov_name)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"response": ai_result, "governorate": gov_name}, ensure_ascii=False).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode('utf-8'))
                return

        # --- ANALYSIS REQUEST (file upload + background AI analysis) ---
        if self.path == "/api/analysis-request":
            user = get_user_from_token(self.headers)
            if not user:
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"message": "الرجاء تسجيل الدخول أولاً"}).encode())
                return
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Expecting multipart/form-data"}).encode())
                return
            form_data = {}
            file_data = None
            filename = "uploaded_file.bin"
            boundary = content_type.split("boundary=")[1].strip()
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            parts = raw.split(b"--" + boundary.encode())
            for part in parts:
                if b"Content-Disposition" not in part:
                    continue
                header_end = part.find(b"\r\n\r\n")
                if header_end == -1:
                    continue
                headers_raw = part[:header_end].decode('utf-8', errors='replace')
                body_part = part[header_end + 4:]
                if body_part.endswith(b"\r\n"):
                    body_part = body_part[:-2]
                if body_part.endswith(b"--"):
                    body_part = body_part[:-2]
                if body_part.endswith(b"\r\n"):
                    body_part = body_part[:-2]
                m = re.search(r'filename="([^"]*)"', headers_raw)
                if m:
                    filename = m.group(1)
                if 'name="file"' in headers_raw:
                    file_data = body_part
                elif 'name="serviceType"' in headers_raw:
                    form_data["serviceType"] = body_part.decode('utf-8', errors='replace')
                elif 'name="governorate"' in headers_raw:
                    form_data["governorate"] = body_part.decode('utf-8', errors='replace')
                elif 'name="description"' in headers_raw:
                    form_data["description"] = body_part.decode('utf-8', errors='replace')
            if not file_data:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"message": "لم يتم رفع ملف"}).encode())
                return
            request_id = str(uuid.uuid4())[:8]
            req_dir = os.path.join(UPLOAD_DIR, f"req_{request_id}")
            os.makedirs(req_dir, exist_ok=True)
            file_path = os.path.join(req_dir, filename)
            with open(file_path, "wb") as f:
                f.write(file_data)
            log_audit("FILE_UPLOAD", user["username"], user["name"],
                      f"ملف: {filename} | محافظة: {form_data.get('governorate', '')} | نوع: {form_data.get('serviceType', 'تحليل تنموي شامل')}",
                      ip=self.client_address[0])
            # Save metadata with pending status
            _analysis_results[request_id] = {"status": "processing", "analysis": None}
            meta = {
                "request_id": request_id,
                "user": user["username"],
                "user_name": user["name"],
                "service_type": form_data.get("serviceType", ""),
                "governorate": form_data.get("governorate", ""),
                "description": form_data.get("description", ""),
                "file_path": file_path,
                "filename": filename,
                "status": "processing",
            }
            with open(os.path.join(req_dir, "meta.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            # Start background analysis
            svc_type = form_data.get("serviceType", "")
            gov_val = form_data.get("governorate", "")
            desc = form_data.get("description", "")
            t = threading.Thread(target=self._run_analysis, args=(request_id, file_path, filename, svc_type, gov_val, desc), daemon=True)
            t.start()
            # Run instant Python analysis immediately
            instant_analysis = analyze_file(file_path, filename, svc_type, gov_val, desc)
            _analysis_results[request_id] = {"status": "completed", "analysis": instant_analysis, "ai_status": "pending", "ai_analysis": None}
            req_dir_meta = os.path.join(UPLOAD_DIR, f"req_{request_id}", "meta.json")
            if os.path.exists(req_dir_meta):
                with open(req_dir_meta, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                meta["status"] = "completed"
                meta["analysis"] = instant_analysis
                meta["ai_status"] = "pending"
                meta["ai_analysis"] = None
                with open(req_dir_meta, "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "message": "تم التحليل",
                "request_id": request_id,
                "status": "completed",
                "analysis": instant_analysis,
                "ai_status": "pending"
            }, ensure_ascii=False).encode('utf-8'))
            return

        # --- AI CHAT ---
        if self.path == "/ai" or self.path == "/api/chat":
            if not AI_AVAILABLE:
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"response": "🧠 المساعد الذكي غير متاح حالياً. يرجى تشغيل Ollama لتفعيل هذه الخدمة."}, ensure_ascii=False).encode('utf-8'))
                return
            user = get_user_from_token(self.headers)
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode('utf-8-sig'))
            prompt = body.get("prompt", "") or body.get("message", "")
            governorate = body.get("governorate", "")
            history = body.get("history", [])
            if not governorate and user and user.get("gov"):
                governorate = user["gov"]
            gov_data = build_chat_gov_data(governorate) if governorate else ""
            response = call_ollama_chat(prompt, governorate, history, gov_data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"response": response}, ensure_ascii=False).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

    def _run_analysis(self, request_id, file_path, filename, service_type, governorate, description):
        """Background AI analysis. Feeds clean statistics to model with strong context."""
        try:
            content = read_file_content(file_path, filename)
            stats = compute_data_stats(content)
            stats_summary = generate_report(stats, service_type, governorate, description)
            na = stats.get("numeric_analysis", {})
            # If no numeric columns found, skip AI analysis entirely
            if not na:
                msg = "⚠️ لم يتم العثور على أعمدة رقمية كافية في الملف المرفوع لإجراء تحليل الذكاء الاصطناعي. تأكد من أن الملف يحتوي على بيانات رقمية (أعداد) بتنسيق CSV أو Excel."
                req_dir = os.path.join(UPLOAD_DIR, f"req_{request_id}")
                meta_path = os.path.join(req_dir, "meta.json")
                if os.path.exists(meta_path):
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    meta["ai_status"] = "skipped"
                    meta["ai_analysis"] = msg
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump(meta, f, ensure_ascii=False, indent=2)
                existing = _analysis_results.get(request_id, {})
                existing["ai_status"] = "skipped"
                existing["ai_analysis"] = msg
                _analysis_results[request_id] = existing
                return
            stats_json = ""
            for col, d in na.items():
                stats_json += f"  - {col}: الأعلى={d['max']} ({d['max_row']}), الأدنى={d['min']} ({d['min_row']}), المتوسط={d['avg']}, الفجوة={d['gap']}\n"
            ai_prompt = f"""أنت خبير تخطيط تنموي. حلل الأرقام أدناه للمحافظات الأردنية.

تعليمات:
- لا تعيد كتابة الأرقام. حلل مباشرة.
- لا تفترض أن المؤشر المرتفع = نجاح أو المنخفض = فشل. فسره ضمن سياق المحافظة.
- عند المقارنة، استخدم مقارنات نسبية: اذكر الفجوة عن المتوسط، وليس القيم المطلقة فقط.
- عند اكتشاف مؤشر سلبي، لا تفترض فشلاً تنموياً — قد يكون بسبب ضغط سكاني أو مركزية خدمات.
- قدم 2-3 توصيات استراتيجية بصيغة: الإجراء + المحافظة + الرقم المبرر.

لكل مؤشر: اذكر أعلى/أدنى قيمة وانحرافهما عن المتوسط. ثم حلل: ماذا تعني هذه النتائج؟ وما المخاطر؟ وما الأولويات؟

في النهاية: صنف كل محافظة ظهرت في التحليل ضمن:
• متقدمة / مستقرة / فرص نمو / ضغوط تنموية / تحتاج تدخلات مركزة

===== الأرقام =====
{stats_json}
==========================
- الأرقام أعلاه هي المصدر الوحيد للأرقام — لا تخترع أي رقم
- لا تخترع مؤشرات ولا أسماء محافظات غير واردة
- الموازنة تقديرية وليست ناتجاً محلياً"""
            ai_analysis = call_ollama(ai_prompt, "", num_predict=4096)
            req_dir = os.path.join(UPLOAD_DIR, f"req_{request_id}")
            meta_path = os.path.join(req_dir, "meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                meta["ai_status"] = "completed" if ai_analysis and "خطأ" not in ai_analysis[:10] else "error"
                meta["ai_analysis"] = ai_analysis
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
            existing = _analysis_results.get(request_id, {})
            existing["ai_status"] = meta["ai_status"]
            existing["ai_analysis"] = ai_analysis
            _analysis_results[request_id] = existing
        except Exception as e:
            req_dir = os.path.join(UPLOAD_DIR, f"req_{request_id}")
            meta_path = os.path.join(req_dir, "meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                meta["ai_status"] = "error"
                meta["ai_analysis"] = f"حدث خطأ في تحليل الذكاء الاصطناعي: {e}"
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)

    def log_message(self, format, *args):
        print(f"[AI Server] {args[0]} {args[1]}")

if __name__ == "__main__":
    status = "ONLINE" if AI_AVAILABLE else "OFFLINE — اشغل Ollama أولاً"
    print(f"Starting Dashboard + Auth + Upload Server on port {PORT}...")
    print(f"Model: {MODEL} ({status})")
    print(f"Default users: admin/admin123, user/user123")
    print(f"Open: http://localhost:{PORT}")
    if not AI_AVAILABLE:
        print(f"WARNING: الموقع يعمل لكن خدمات الذكاء الاصطناعي غير متاحة حتى يتم تشغيل Ollama")
    server = ThreadingHTTPServer(("localhost", PORT), AIHandler)
    server.serve_forever()
