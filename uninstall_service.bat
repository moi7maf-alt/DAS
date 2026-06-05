@echo off
cd /d "%~dp0"

:: طلب صلاحية المسؤول تلقائياً
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ====================================
echo  إلغاء تثبيت خدمة النظام
echo ====================================
schtasks /delete /tn "JLDashboard" /f >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ تم إلغاء تثبيت الخدمة بنجاح
) else (
    echo الخدمة غير مثبتة أصلاً
)
pause
