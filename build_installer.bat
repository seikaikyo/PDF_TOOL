@echo off
chcp 65001 >nul
echo ==========================================
echo   PDF Toolkit MSI 安裝檔建置工具
echo   一鍵建置 Windows MSI 安裝檔
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

echo 📦 安裝建置依賴...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ 依賴安裝失敗
    pause
    exit /b 1
)

echo ✅ 依賴安裝完成
echo.

echo 🔨 開始建置 MSI 安裝檔...
python build_installer.py

if errorlevel 1 (
    echo ❌ 建置失敗
    pause
    exit /b 1
)

echo.
echo 🎉 建置完成！MSI 安裝檔位於 dist/ 資料夾
echo.
echo 📋 接下來可以：
echo 1. 在乾淨環境測試 MSI 安裝
echo 2. 檢查企業防毒軟體相容性  
echo 3. 分發給使用者
echo.

pause