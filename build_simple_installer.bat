@echo off
chcp 65001 >nul
echo ==========================================
echo   PDF Toolkit 簡化安裝檔建置工具
echo   建立便攜版 + NSIS 安裝檔
echo ==========================================
echo.

echo 🔍 檢查 Python 環境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 找不到 Python，請確認已安裝 Python 3.7+
    pause
    exit /b 1
)

echo ✅ Python 環境正常
echo.

echo 🔨 開始建置...
python build_simple_installer.py

if errorlevel 1 (
    echo ❌ 建置失敗
    pause
    exit /b 1
)

echo.
echo 🎉 建置完成！
echo.
echo 📋 說明：
echo ✅ 便攜版：無需安裝，直接執行
echo ✅ 安裝檔：需要 NSIS，更適合企業環境
echo.
echo 💡 如需建立 NSIS 安裝檔，請下載：
echo    https://nsis.sourceforge.io/Download
echo.

pause