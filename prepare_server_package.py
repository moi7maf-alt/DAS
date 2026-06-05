# -*- coding: utf-8 -*-
"""
prepare_server_package.py — إصلاح الحزمة للنشر على سيرفر مستقل

الاستخدام:
    python prepare_server_package.py

ينشئ مجلد server_package/ يحتوي على:
- dist/ الموقع الثابت
- src/ جميع سكريبتات البناء وملفات البيانات
- requirements.txt
- ملفات الوثائق الداعمة
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'src')
DIST = os.path.join(ROOT, 'dist')
PACKAGE = os.path.join(ROOT, 'server_package')

ROOT_FILES = [
    'deploy.py',
    'HOW_TO_ADD_DATA.md',
    'requirements.txt',
    'SECURE_DEPLOYMENT.md',
    '.gitignore',
]

EXCLUDE_ROOT_DIRS = {
    'venv',
    'venv_packages',
    '__pycache__',
    '.git',
    'server_package',
}

EXCLUDE_SRC_DIRS = {
    '__pycache__',
}


def run_deploy():
    print('> تشغيل deploy.py لإنشاء dist/ ...')
    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, 'deploy.py')],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
    )
    if result.returncode != 0:
        print('خطأ أثناء تشغيل deploy.py:')
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError('deploy.py فشل')
    print('✅ تم إنشاء dist/ بنجاح.')


def copy_file(src_path, dst_path):
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    shutil.copy2(src_path, dst_path)


def copy_tree(src_dir, dst_dir, ignore_dirs=None):
    if os.path.exists(dst_dir):
        shutil.rmtree(dst_dir)
    def _ignore(directory, contents):
        ignored = []
        for name in contents:
            if ignore_dirs and name in ignore_dirs:
                ignored.append(name)
        return ignored
    shutil.copytree(src_dir, dst_dir, ignore=shutil.ignore_patterns(*ignore_dirs) if ignore_dirs else None)


def build_package():
    if not os.path.exists(SRC):
        raise FileNotFoundError('مجلد src/ غير موجود.')

    run_deploy()

    if os.path.exists(PACKAGE):
        shutil.rmtree(PACKAGE)
    os.makedirs(PACKAGE)

    print(f'> نسخ الملفات إلى {PACKAGE} ...')
    for fname in ROOT_FILES:
        src_path = os.path.join(ROOT, fname)
        if os.path.exists(src_path):
            dst_path = os.path.join(PACKAGE, fname)
            copy_file(src_path, dst_path)
            print(f'  - {fname}')

    print('> نسخ src/ ...')
    copy_tree(SRC, os.path.join(PACKAGE, 'src'), ignore_dirs=EXCLUDE_SRC_DIRS)

    print('> نسخ dist/ ...')
    copy_tree(DIST, os.path.join(PACKAGE, 'dist'))

    package_readme = os.path.join(PACKAGE, 'README.md')
    with open(package_readme, 'w', encoding='utf-8') as f:
        f.write(f"""# حزمة الاستضافة المستقلة

تم إنشاء هذه الحزمة بواسطة `prepare_server_package.py` في {datetime.now().strftime('%Y-%m-%d %H:%M')}.

## الهدف
هذه الحزمة مخصصة للنشر على سيرفر مستقل.

## المحتويات
- `dist/` — ملفات الموقع الثابت.
- `src/` — ملفات البناء والبيانات.
- `requirements.txt` — متطلبات Python للبناء.
- `SECURE_DEPLOYMENT.md` — توصيات الأمان.

## تعليمات سريعة
1. انسخ محتويات `dist/` إلى مجلد الجذر للموقع على السيرفر.
2. إن كنت تريد تحديث البيانات لاحقاً، ثبّت متطلبات Python ثم شغّل `python src/run_all.py`.
""")

    print('✅ تم إعداد الحزمة بنجاح.')
    print(f'  مجلد الحزمة: {PACKAGE}')
    print('  يمكنك الآن رفع محتويات server_package/ أو استخدام dist/ مباشرة.')


if __name__ == '__main__':
    try:
        build_package()
    except Exception as exc:
        print('❌ حدث خطأ:')
        print(str(exc))
        sys.exit(1)
