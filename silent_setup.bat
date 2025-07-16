@echo off
REM PDF Toolkit 靜默安裝後設定
REM 在 MSI 安裝完成後自動執行

REM 獲取當前目錄
set "INSTALL_DIR=%~dp0"

REM 嘗試執行 Python 設定腳本（靜默模式）
python "%INSTALL_DIR%post_install_setup.py" "%INSTALL_DIR%" --silent >nul 2>&1

REM 如果 Python 設定失敗，嘗試直接啟動程式讓它自己設定
if errorlevel 1 (
    start "" "%INSTALL_DIR%PDF_Toolkit.exe"
)

REM 結束不顯示任何訊息
exit /b 0