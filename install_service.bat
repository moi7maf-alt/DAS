@echo off
cd /d "%~dp0"

:: طلب صلاحية المسؤول تلقائياً (Administrator)
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo طلب صلاحية المسؤول...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ====================================
echo  تثبيت نظام التخطيط التنموي كخدمة
echo ====================================
echo.

:: التأكد من أن الملفات موجودة
if not exist "ai_server.py" (
    echo [خطأ] لا يوجد ملف ai_server.py في هذا المجلد
    echo تأكد من تشغيل هذا الملف من داخل مجلد المشروع
    pause
    exit /b 1
)

:: التأكد من وجود Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [خطأ] Python غير مثبت على هذا الجهاز
    echo الرجاء تثبيت Python من https://python.org
    pause
    exit /b 1
)

:: تثبيت المكتبات الإضافية
echo جاري تثبيت المكتبات الإضافية...
pip install openpyxl PyPDF2 >nul 2>&1

:: حذف المهمة القديمة إن وجدت
schtasks /delete /tn "JLDashboard" /f >nul 2>&1

:: إنشاء مهمة في جدول المهام لتشغيل الخادم تلقائياً عند بدء تشغيل Windows
:: تعمل تحت حساب النظام (SYSTEM) وبصلاحية عالية
schtasks /create /tn "JLDashboard" /sc ONSTART /delay 0000:30 /rl HIGHEST /ru SYSTEM /tr "'%CD%\start_daemon.vbs'" /f

if %errorlevel% equ 0 (
    echo.
    echo ✅ تم تثبيت الخدمة بنجاح!
    echo.
    echo - سيبدأ الخادم تلقائياً عند تشغيل Windows (بعد 30 ثانية)
    echo - المنفذ: http://localhost:5000
    echo.
    echo لتشغيل الخادم الآن بدون إعادة تشغيل:
    echo   انقر مرتين على start_server.bat
    echo.
    echo لإلغاء التثبيت:
    echo   انقر مرتين على uninstall_service.bat
) else (
    echo.
    echo [خطأ] فشل تثبيت الخدمة. حاول تشغيل هذا الملف كمسؤول.
)

pause
