# landing v8 — Auth-aware
import json
data = json.load(open('src/data.json', encoding='utf-8'))
total_pop = sum(g['population'] for g in data['governorates'])

gov_icons = {'العاصمة':'🏛️','البلقاء':'🌊','الزرقاء':'🏭','مأدبا':'🕌','إربد':'🎓','المفرق':'🛤️','جرش':'🏛','عجلون':'🌲','الكرك':'🏰','الطفيلة':'⚡','معان':'🌟','العقبة':'⚓'}

gov_scores = []
for g in data['governorates']:
    name = g['name']
    avg = g['composite_index']
    gov_scores.append({'name': name, 'avg': round(avg, 1), 'population': g['population'], 'budget': g['budget_2026'], 'area': g['area'], 'icon': gov_icons.get(name, '📍')})
gov_scores.sort(key=lambda x: -x['avg'])

MOI_LOGO = "https://www.moi.gov.jo/ebv4.0/root_storage/en/eb_homepage/logoen.png"

# JavaScript text constants (avoid Python unicode escape issues)
JS_LOGIN = '\\u{1F4CA} \\u062A\\u0633\\u062C\\u064A\\u0644 \\u0627\\u0644\\u062F\\u062E\\u0648\\u0644'
JS_GOV = '\\u{1F3D4} \\u0645\\u062D\\u0627\\u0641\\u0638\\u0629 '
JS_GLOBE = '\\u{1F30D} \\u062C\\u0645\\u064A\\u0639 \\u0627\\u0644\\u0645\\u062D\\u0627\\u0641\\u0638\\u0627\\u062A'
JS_CHART = '\\u{1F4CA} '
JS_DASH_ADMIN = '\\u{1F4CA} \\u0627\\u0644\\u062F\\u062E\\u0648\\u0644 \\u0625\\u0644\\u0649 \\u0627\\u0644\\u0645\\u0646\\u0635\\u0629 \\u0627\\u0644\\u062A\\u062D\\u0644\\u064A\\u0644\\u064A\\u0629'
JS_BOARD = '\\u{1F4CA} \\u0644\\u0648\\u062D\\u0629 \\u0627\\u0644\\u0628\\u064A\\u0627\\u0646\\u0627\\u062A'
JS_PORTAL = '\\u{1F4CA} \\u0627\\u0644\\u062F\\u062E\\u0648\\u0644 \\u0625\\u0644\\u0649 \\u0627\\u0644\\u0645\\u0646\\u0635\\u0629'

HTML = '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>نظام التحليل التنموي للمحافظات الأردنية — DAS</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',Tahoma,Arial,sans-serif;background:#f5f6fa;color:#1a1a2e;direction:rtl}
@keyframes fadeUp{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
.anim{animation:fadeUp .7s ease-out forwards;opacity:0}
.anim-d2{animation-delay:.2s}
.anim-d4{animation-delay:.4s}
.nav{background:#fff;padding:0 40px;display:flex;align-items:center;justify-content:space-between;height:64px;border-bottom:1px solid #e5e7eb;position:sticky;top:0;z-index:100}
.nav-brand{display:flex;align-items:center;gap:10px}
.nav-icon{width:34px;height:34px;background:linear-gradient(135deg,#1a3a5c,#2a5298);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:17px;color:#fff}
.nav-title{font-size:14px;font-weight:700;color:#1a3a5c}
.nav-sub{font-size:10px;color:#9ca3af}
.nav-btn{background:#1a3a5c;color:#fff;border:none;padding:8px 22px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;text-decoration:none;transition:all .2s}
.nav-btn:hover{background:#2a5298}
.hero{background:linear-gradient(160deg,#0d2137,#1a3a5c 60%,#1e4976);color:#fff;padding:64px 40px 56px;text-align:center;position:relative;overflow:hidden}
.hero::after{content:"";position:absolute;bottom:0;left:0;right:0;height:50px;background:#f5f6fa;clip-path:ellipse(60% 100% at 50% 100%)}
.hero-tag{display:inline-block;background:rgba(200,168,75,.15);border:1px solid rgba(200,168,75,.4);color:#c8a84b;padding:4px 16px;border-radius:20px;font-size:11px;font-weight:600;margin-bottom:12px}
.hero h1{font-size:38px;font-weight:800;line-height:1.25;margin-bottom:8px}
.hero .gold{color:#c8a84b}
.hero p{font-size:14px;opacity:.85;max-width:520px;margin:0 auto 20px;line-height:1.8}
.hero-btns{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
.btn-gold{background:linear-gradient(135deg,#c8a84b,#e8c96b);color:#1a3a5c;border:none;padding:10px 24px;border-radius:8px;font-size:13px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:6px;box-shadow:0 4px 16px rgba(200,168,75,.3);transition:all .2s}
.btn-gold:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(200,168,75,.4)}
.stats{display:flex;justify-content:center;padding:20px 40px;background:#fff;gap:0;border-bottom:1px solid #e5e7eb;flex-wrap:wrap}
.stat{text-align:center;padding:0 28px;border-left:1px solid #e5e7eb}
.stat:last-child{border-left:none}
.stat-n{font-size:22px;font-weight:800;color:#1a3a5c}
.stat-l{font-size:10px;color:#9ca3af;margin-top:2px}
.cta{text-align:center;padding:48px 40px;max-width:600px;margin:0 auto}
.cta h2{font-size:26px;font-weight:800;color:#1a3a5c;margin-bottom:6px}
.cta p{font-size:13px;color:#9ca3af;line-height:1.7;margin-bottom:16px}
.footer{background:#0d2137;color:#fff;padding:20px 40px;border-top:3px solid #c8a84b}
.ft-inner{display:flex;align-items:center;justify-content:space-between;max-width:1200px;margin:0 auto;flex-wrap:wrap;gap:10px}
.ft-left{display:flex;align-items:center;gap:10px}
.ft-left img{height:32px;filter:brightness(1.2)}
.ft-text{font-size:10px;opacity:.6;text-align:center}
.ft-copy{font-size:9px;opacity:.45}
@media(max-width:768px){
.nav{padding:0 16px}
.hero{padding:40px 16px 32px}
.hero h1{font-size:26px}
.stats{padding:12px 8px}
.stat{padding:0 12px}
.cta{padding:32px 16px}
.footer{padding:16px}
.ft-inner{flex-direction:column;text-align:center}
}
</style>
</head>
<body>

<div class="nav">
  <div class="nav-brand">
    <img src="''' + MOI_LOGO + '''" alt="وزارة الداخلية" style="height:52px;width:auto" onerror="this.style.display='none'">
    <div>
      <div class="nav-title">نظام التحليل التنموي للمحافظات الأردنية</div>
      <div class="nav-sub">Developmental Analysis System (DAS)</div>
    </div>
  </div>
  <a id="navBtn" href="login.html" class="nav-btn">📊 تسجيل الدخول</a>
</div>

<div class="hero">
  <div id="topBar" style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:24px">
    <div id="guestBtns" style="display:flex;gap:10px">
      <a href="login.html" class="btn-gold">📊 تسجيل الدخول</a>
      <a href="chat.html" class="btn-gold" style="background:linear-gradient(135deg,#7c3aed,#a78bfa);box-shadow:0 4px 16px rgba(124,58,237,.3)">🧠 المساعد الذكي</a>
    </div>
    <div id="userBtns" style="display:none">
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <div style="background:rgba(200,168,75,.15);border:1px solid rgba(200,168,75,.4);border-radius:10px;padding:8px 18px;text-align:center">
          <div style="font-size:10px;opacity:.7">مرحباً</div>
          <div style="font-size:15px;font-weight:800" id="userDisplay">مدير النظام</div>
          <div style="font-size:10px;opacity:.6" id="govDisplay">🌍 جميع المحافظات</div>
        </div>
        <a href="index.html" class="btn-gold" id="dashBtn" style="font-size:12px;padding:8px 18px">📊 المنصة التحليلية</a>
        <a href="chat.html" class="btn-gold" style="font-size:12px;padding:8px 18px;background:linear-gradient(135deg,#7c3aed,#a78bfa);box-shadow:0 4px 16px rgba(124,58,237,.3)">🧠 المساعد الذكي</a>
        <a href="audit.html" class="btn-gold audit-btn" style="display:none;font-size:12px;padding:8px 18px;background:linear-gradient(135deg,#dc2626,#ef4444);box-shadow:0 4px 16px rgba(220,38,38,.3)">🔍 سجل التدقيق</a>
      </div>
    </div>
  </div>
  <div class="hero-tag">🏛️ المملكة الأردنية الهاشمية — 12 محافظة</div>
  <h1>نظام التحليل التنموي<br><span class="gold">للمحافظات الأردنية</span></h1>
  <div style="font-size:18px;opacity:.85;margin-bottom:18px;letter-spacing:1px">Developmental Analysis System <span style="color:#c8a84b;font-weight:700">(DAS)</span></div>
  <p>منظومة متكاملة لتحليل الفجوات التنموية، تصنيف المحافظات، وتوجيه الموارد بدقة — مدعومة بالبيانات الرسمية والذكاء الاصطناعي</p>
</div>
<script>
if (localStorage.getItem('user_role') === 'admin') {
  document.querySelectorAll('.audit-btn').forEach(function(b){b.style.display = '';});
}
</script>

<div class="stats anim anim-d2">
  <div class="stat"><div class="stat-n">12</div><div class="stat-l">محافظة</div></div>
  <div class="stat"><div class="stat-n">8</div><div class="stat-l">قطاع تنموي</div></div>
  <div class="stat"><div class="stat-n">''' + f"{total_pop:,}" + '''</div><div class="stat-l">نسمة</div></div>
  <div class="stat"><div class="stat-n">240+</div><div class="stat-l">مشروع مقترح</div></div>
</div>

<!-- Governorate ranking cards -->
<div style="max-width:1200px;margin:0 auto;padding:32px 40px">
<h2 style="font-size:20px;font-weight:800;color:#1a3a5c;margin-bottom:16px">🏆 ترتيب المحافظات حسب معدل التنمية</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px">'''

for i, g in enumerate(gov_scores):
    rank = i + 1
    color = '#16a34a' if g['avg'] >= 55 else ('#2563eb' if g['avg'] >= 35 else ('#d97706' if g['avg'] >= 25 else '#dc2626'))
    medal = '🥇' if rank == 1 else ('🥈' if rank == 2 else ('🥉' if rank == 3 else ''))
    HTML += f'''<div style="background:#fff;border-radius:10px;padding:14px;box-shadow:0 1px 6px rgba(0,0,0,.06);text-align:center;border-top:3px solid {color}">
<div style="font-size:22px">{g['icon']}</div>
<div style="font-size:11px;font-weight:700;color:#1a3a5c;margin:4px 0">{g['name']}</div>
<div style="font-size:18px;font-weight:800;color:{color}">{g['avg']}<span style="font-size:11px;color:#9ca3af">/100</span></div>
<div style="font-size:10px;color:#9ca3af">{medal} المرتبة {rank}</div>
</div>'''

HTML += '''</div>
</div>

<div class="cta anim">
  <h2>ابدأ التخطيط التنموي الآن</h2>
  <p>حلل وضع كل محافظة، اكتشف الفجوات، وابنِ خططاً استراتيجية مبنية على بيانات حقيقية</p>
  <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
    <a id="ctaBtn" href="login.html" class="btn-gold" style="display:inline-flex">📊 الدخول إلى المنصة ←</a>
    <a href="chat.html" class="btn-gold" style="display:inline-flex;background:linear-gradient(135deg,#7c3aed,#a78bfa);box-shadow:0 4px 16px rgba(124,58,237,.3)">🧠 المساعد الذكي</a>
    <a href="audit.html" class="btn-gold audit-btn2" style="display:none;background:linear-gradient(135deg,#dc2626,#ef4444);box-shadow:0 4px 16px rgba(220,38,38,.3)">🔍 سجل التدقيق</a>
  </div>
</div>
<script>
if (localStorage.getItem('user_role') === 'admin') {
  document.querySelectorAll('.audit-btn2').forEach(function(b){b.style.display = '';});
}
</script>

<footer class="footer">
  <div class="ft-inner">
    <div class="ft-left">
      <img src="''' + MOI_LOGO + '''" alt="وزارة الداخلية" style="height:48px;width:auto" onerror="this.style.display='none'" loading="lazy">
      <div>
        <div style="font-size:11px;font-weight:700;color:#c8a84b">وزارة الداخلية الأردنية</div>
        <div style="font-size:9px;opacity:.55">مديرية التنمية المحلية</div>
      </div>
    </div>
    <div class="ft-text">نظام التحليل التنموي للمحافظات الأردنية — بيانات رسمية محدّثة</div>
    <div class="ft-copy">&copy; 2026 جميع الحقوق محفوظة</div>
  </div>
</footer>

<script>
(async function() {
  const token = localStorage.getItem('session_token');
  const navBtn = document.getElementById('navBtn');
  const guestBtns = document.getElementById('guestBtns');
  const userBtns = document.getElementById('userBtns');
  const userDisplay = document.getElementById('userDisplay');
  const govDisplay = document.getElementById('govDisplay');
  const ctaBtn = document.getElementById('ctaBtn');
  const dashBtn = document.getElementById('dashBtn');

  if (!token) {
    navBtn.href = 'login.html';
    navBtn.textContent = '📊 تسجيل الدخول';
    return;
  }

  try {
    const resp = await fetch('/api/me', {
      headers: {'Authorization': 'Bearer ' + token}
    });
    const data = await resp.json();

    if (!data.authenticated) {
      localStorage.removeItem('session_token');
      navBtn.href = 'login.html';
      navBtn.textContent = '📊 تسجيل الدخول';
      return;
    }

    guestBtns.style.display = 'none';
    userBtns.style.display = 'flex';

    userDisplay.textContent = data.name;
    if (data.gov) {
      govDisplay.textContent = '🏔 محافظة ' + data.gov;
      dashBtn.textContent = '📊 الدخول إلى لوحة ' + data.gov;
      dashBtn.href = '/index.html?gov=' + encodeURIComponent(data.gov);
    } else {
      govDisplay.textContent = '🌍 جميع المحافظات';
      dashBtn.textContent = '📊 الدخول إلى المنصة التحليلية';
    }

    navBtn.href = 'index.html';
    navBtn.textContent = '📊 لوحة البيانات';
    ctaBtn.href = 'index.html';
    ctaBtn.textContent = '📊 الدخول إلى المنصة';
  } catch(e) {
    navBtn.href = 'login.html';
    navBtn.textContent = '📊 تسجيل الدخول';
  }
})();
</script>
</body>
</html>'''

open('src/landing.html', 'w', encoding='utf-8').write(HTML)
print('Landing page v8 built: src/landing.html (Auth-aware)')
