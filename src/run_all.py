"""
run_all.py — سكريبت التشغيل الموحد
يبني النظام كاملاً بخطوة واحدة بالترتيب الصحيح.

الاستخدام:
    python src/run_all.py

الخطوات:
    1. generate_data.py      → src/data.json
    2. generate_comprehensive.py → src/strategic_comprehensive.json
    3. build_budget.py       → src/budget_data.json
    4. build_predictive2.py  → src/predictive_data.json
    5. write_dashboard.py    → src/index.html (الهيكل الأساسي)
    6. inject_budget.py      → يضيف تبويب الموازنة
    7. inject_solutions.py   → يضيف تبويب الحلول الذكية
    8. inject_predictive.py  → يضيف تبويب التحليل التنبؤي
    9. inject_alignment.py   → يضيف تبويب موائمة المشاريع
   10. inject_ai.py          → يضيف تبويب تقرير المحافظة
   11. build_landing.py      → src/landing.html
   12. build_guide.py        → src/technical_guide.html
"""

import subprocess
import sys
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# Fix console encoding for Arabic/emoji output
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add local packages folder to path if it exists
_local_pkgs = os.path.join(ROOT, 'venv_packages')
if os.path.isdir(_local_pkgs) and _local_pkgs not in sys.path:
    sys.path.insert(0, _local_pkgs)

STEPS = [
    ("generate_data.py",             "معالجة البيانات → data.json"),
    ("generate_comprehensive.py",    "بناء البيانات الاستراتيجية الشاملة → strategic_comprehensive.json"),
    ("build_budget.py",              "بناء بيانات الموازنة → budget_data.json"),
    ("build_predictive2.py",         "بناء البيانات التنبؤية → predictive_data.json"),
    ("write_dashboard.py",           "بناء الهيكل الأساسي → index.html"),
    ("inject_budget.py",             "حقن تبويب الموازنة"),
    # ("inject_solutions.py",       # محذوف - مشاريع مقترحة + الحلول الذكية
    ("inject_predictive.py",         "حقن تبويب التحليل التنبؤي"),
    # ("inject_trends.py",          # محذوف - اتجاهات القطاعات
    # ("inject_ai.py",               # محذوف - تقرير المحافظة
    ("inject_alignment.py",        "حقن تبويب موائمة المشاريع"),
    # ("inject_spatial_services.py", # صفحة منفصلة - spatial.html
    ("build_landing.py",             "بناء الصفحة الرئيسية → landing.html"),
    ("build_guide.py",               "بناء الدليل التقني → technical_guide.html"),
]

def get_python_exe():
    """Return the best Python executable — prefer 3.11 if available."""
    import shutil
    # Try py launcher with 3.11 first
    py = shutil.which('py')
    if py:
        try:
            r = subprocess.run([py, '-3.11', '-c', 'import sys; print(sys.version)'],
                               capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return [py, '-3.11']
        except Exception:
            pass
    # Fall back to current interpreter
    return [sys.executable]


PYTHON_CMD = get_python_exe()


def run_step(script, desc, step_num, total):
    print(f"\n{'='*60}")
    print(f"[{step_num}/{total}] {desc}")
    print(f"{'='*60}")
    t0 = time.time()

    # Build environment with local packages path
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    local_pkgs = os.path.join(ROOT, 'venv_packages')
    if os.path.isdir(local_pkgs):
        existing = env.get('PYTHONPATH', '')
        env['PYTHONPATH'] = local_pkgs + (os.pathsep + existing if existing else '')

    result = subprocess.run(
        PYTHON_CMD + [f"src/{script}"],
        capture_output=False,
        text=True,
        env=env
    )
    elapsed = time.time() - t0
    if result.returncode != 0:
        print(f"\n❌ فشل: {script} (كود الخطأ: {result.returncode})")
        return False
    print(f"\n✅ اكتمل في {elapsed:.1f}s")
    return True

def main():
    print("=" * 60)
    print("  نظام التحليل التنموي للمحافظات الأردنية — بناء شامل")
    print("  DAS (Developmental Analysis System) — Build Pipeline")
    print("=" * 60)
    print(f"  المجلد: {ROOT}")
    print(f"  الخطوات: {len(STEPS)}")

    t_start = time.time()
    failed = []

    for i, (script, desc) in enumerate(STEPS, 1):
        script_path = os.path.join("src", script)
        if not os.path.exists(script_path):
            print(f"\n⚠️  [{i}/{len(STEPS)}] تخطي: {script} (غير موجود)")
            continue
        ok = run_step(script, desc, i, len(STEPS))
        if not ok:
            failed.append(script)
            print(f"\n⛔ توقف البناء بسبب خطأ في: {script}")
            print("   راجع رسالة الخطأ أعلاه وأصلح المشكلة ثم أعد التشغيل.")
            sys.exit(1)

    total_time = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"  ✅ اكتمل البناء بنجاح في {total_time:.1f}s")
    print(f"  📄 الملفات الناتجة:")
    for f in ["src/index.html", "src/landing.html", "src/technical_guide.html",
              "src/data.json", "src/budget_data.json", "src/predictive_data.json"]:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(f"     {f} ({size/1024:.0f} KB)")
    print("=" * 60)

if __name__ == "__main__":
    main()
