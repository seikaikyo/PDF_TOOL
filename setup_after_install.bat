@echo off
chcp 65001 >nul
title PDF Toolkit 安裝後設定

echo ==========================================
echo   PDF Toolkit 安裝後設定
echo ==========================================
echo.

REM 獲取當前目錄
set "INSTALL_DIR=%~dp0"

echo 📁 安裝目錄: %INSTALL_DIR%
echo.

REM 檢查 Python 是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 不可用，使用手動設定模式
    goto manual_setup
)

echo ✅ Python 可用，開始自動設定...
echo.

REM 執行 Python 設定腳本
python "%INSTALL_DIR%post_install_setup.py" "%INSTALL_DIR%"

if errorlevel 1 (
    echo.
    echo ❌ 自動設定失敗，請手動完成設定
    goto manual_setup
)

echo.
echo 🎉 設定完成！
goto end

:manual_setup
echo.
echo 📋 手動設定步驟：
echo 1. 在開始功能表搜尋 "PDF Toolkit"
echo 2. 右鍵點擊程式 → 釘選到開始功能表
echo 3. 如需桌面捷徑，請手動建立
echo.
echo 💡 提示：程式已安裝在 %INSTALL_DIR%
echo.

:end
echo.
echo 按任意鍵結束...
pause >nul