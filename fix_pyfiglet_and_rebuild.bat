@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo.
echo ==========================================
echo    PDF 合併工具 pyfiglet 問題自動修復
echo ==========================================
echo.

echo 🔍 檢測到的問題：
echo   - pyfiglet 字體檔案未包含在 EXE 中
echo   - 執行時無法載入字體導致程式崩潰
echo.

echo 🔧 修復方案：修改程式碼添加錯誤處理
echo.

:: 檢查 app.py 是否存在
if not exist "app.py" (
    echo ❌ 找不到 app.py 檔案！
    pause
    exit /b 1
)

:: 備份原始檔案
echo 📋 備份原始檔案...
copy "app.py" "app_backup.py" >nul
echo ✅ 備份完成：app_backup.py

:: 創建修復腳本
echo 🛠️ 創建修復腳本...
(
echo import re
echo.
echo # 讀取 app.py 檔案
echo with open('app.py', 'r', encoding='utf-8'^) as f:
echo     content = f.read(^)
echo.
echo # 找到並替換 figlet_format 的部分
echo old_pattern = '''title_text = figlet_format("PDF TOOLKIT", font="slant"^)
echo         title_label = tk.Label(content_frame,
echo                                text=title_text,
echo                                bg=self.colors['bg_panel'],
echo                                fg=self.colors['info'],
echo                                font=("Courier", 8^),
echo                                justify="center"^)'''
echo.
echo new_pattern = '''# ASCII 標題（置中） - 添加錯誤處理
echo         try:
echo             title_text = figlet_format("PDF TOOLKIT", font="slant"^)
echo             title_font = ("Courier", 8^)
echo         except Exception as e:
echo             # 如果 pyfiglet 失敗，使用普通文字
echo             title_text = "PDF TOOLKIT"
echo             title_font = ("Arial", 24, "bold"^)
echo             print(f"pyfiglet 載入失敗，使用普通文字：{e}"^)
echo.
echo         title_label = tk.Label(content_frame,
echo                                text=title_text,
echo                                bg=self.colors['bg_panel'],
echo                                fg=self.colors['info'],
echo                                font=title_font,
echo                                justify="center"^)'''
echo.
echo # 進行替換
echo if 'figlet_format("PDF TOOLKIT", font="slant"^)' in content:
echo     # 使用更寬鬆的匹配模式
echo     pattern = r'title_text = figlet_format\("PDF TOOLKIT", font="slant"\^).*?justify="center"\^)'
echo     replacement = '''# ASCII 標題（置中） - 添加錯誤處理
echo         try:
echo             title_text = figlet_format("PDF TOOLKIT", font="slant"^)
echo             title_font = ("Courier", 8^)
echo         except Exception as e:
echo             # 如果 pyfiglet 失敗，使用普通文字
echo             title_text = "PDF TOOLKIT"
echo             title_font = ("Arial", 24, "bold"^)
echo             print(f"pyfiglet 載入失敗，使用普通文字：{e}"^)
echo.
echo         title_label = tk.Label(content_frame,
echo                                text=title_text,
echo                                bg=self.colors['bg_panel'],
echo                                fg=self.colors['info'],
echo                                font=title_font,
echo                                justify="center"^)'''
echo     
echo     content = re.sub(pattern, replacement, content, flags=re.DOTALL^)
echo     
echo     # 寫回檔案
echo     with open('app.py', 'w', encoding='utf-8'^) as f:
echo         f.write(content^)
echo     
echo     print("✅ 修復完成！"^)
echo else:
echo     print("⚠️  找不到需要修復的代碼段，可能已經修復過了"^)
) > fix_code.py

:: 執行修復
echo 🔧 執行代碼修復...
python fix_code.py

:: 清理修復腳本
del fix_code.py

echo.
echo 📦 重新打包程式...
echo.

:: 清理舊的建置檔案
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del "*.spec"

:: 重新打包
echo 使用修復後的代碼重新打包...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name="PDFMerger_Fixed" ^
    --icon=icon.ico ^
    --exclude-module=matplotlib ^
    --exclude-module=numpy ^
    --exclude-module=scipy ^
    --exclude-module=pandas ^
    --clean ^
    --noconfirm ^
    app.py

echo.

:: 檢查結果
if exist "dist\PDFMerger_Fixed.exe" (
    echo ✅ 修復和重新打包成功！
    echo.
    echo 📁 新的可執行檔：dist\PDFMerger_Fixed.exe
    echo 📋 原始檔案備份：app_backup.py
    echo.
    
    :: 顯示檔案大小
    for %%i in ("dist\PDFMerger_Fixed.exe") do (
        set "file_size=%%~zi"
        set /a "size_mb=!file_size! / 1024 / 1024"
        echo 📊 檔案大小：!file_size! bytes (約 !size_mb! MB)
    )
    
    echo.
    echo 🎉 問題已修復！主要改進：
    echo   ✅ 添加了 pyfiglet 錯誤處理
    echo   ✅ 如果字體載入失敗會使用普通文字
    echo   ✅ 程式不會再因為字體問題而崩潰
    echo.
    
    :: 詢問是否測試
    set /p "test_run=是否要測試執行修復後的程式？(Y/N): "
    if /i "!test_run!"=="Y" (
        echo.
        echo 🧪 啟動測試...
        start "" "dist\PDFMerger_Fixed.exe"
    )
    
    :: 詢問是否開啟資料夾
    set /p "open_folder=是否要開啟 dist 資料夾？(Y/N): "
    if /i "!open_folder!"=="Y" (
        explorer "dist"
    )
    
) else (
    echo ❌ 重新打包失敗！
    echo.
    echo 🔍 可能的原因：
    echo   1. Python 環境問題
    echo   2. 依賴套件缺失
    echo   3. 磁碟空間不足
    echo.
    echo 💡 嘗試手動修復：
    echo   1. 檢查 app_backup.py 是否正常
    echo   2. 比較 app.py 與 app_backup.py 的差異
    echo   3. 手動執行：python app.py 檢查是否有語法錯誤
)

echo.
echo 📋 修復程序完成！
pause