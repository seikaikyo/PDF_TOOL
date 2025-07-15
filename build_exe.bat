@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo.
echo ==========================================
echo    PDF 合併工具 問題修復 + 重新打包
echo    作者：
echo ==========================================
echo.

:: 步驟1：修復 pathlib 衝突
echo 🔧 步驟1：修復 pathlib 套件衝突...
echo.
echo 正在卸載衝突的 pathlib 套件...
python -m pip uninstall pathlib -y
if errorlevel 1 (
    echo ⚠️  pathlib 套件可能已經不存在，繼續進行...
) else (
    echo ✅ pathlib 衝突套件已移除
)
echo.

:: 步驟2：清理 Python 快取
echo 🧹 步驟2：清理 Python 快取...
if exist "__pycache__" (
    rmdir /s /q "__pycache__"
    echo ✅ 清理 __pycache__ 資料夾
)

for /d %%d in (*__pycache__*) do (
    rmdir /s /q "%%d"
    echo ✅ 清理 %%d 資料夾
)
echo.

:: 步驟3：重新安裝乾淨的依賴
echo 📦 步驟3：重新安裝依賴套件...
echo.

echo 升級 pip...
python -m pip install --upgrade pip

echo.
echo 安裝核心依賴...
set "core_packages=pyinstaller>=5.0 tkinterdnd2>=0.3.0 PyMuPDF>=1.23.0 Pillow>=9.0.0 pyfiglet>=0.8.0"
for %%p in (%core_packages%) do (
    echo 正在安裝 %%p...
    python -m pip install "%%p" --upgrade --force-reinstall
    if errorlevel 1 (
        echo ❌ %%p 安裝失敗
        pause
        exit /b 1
    )
    echo ✅ %%p 安裝完成
)
echo.

:: 步驟4：驗證安裝
echo 🔍 步驟4：驗證套件安裝...
python -c "import PyInstaller; print('✅ PyInstaller:', PyInstaller.__version__)"
python -c "import tkinterdnd2; print('✅ tkinterdnd2: OK')"
python -c "import fitz; print('✅ PyMuPDF:', fitz.version)"
python -c "import PIL; print('✅ Pillow:', PIL.__version__)"
python -c "import pyfiglet; print('✅ pyfiglet: OK')"
echo.

:: 步驟5：清理舊的建置檔案
echo 🧹 步驟5：清理舊的建置檔案...
if exist "build" (
    rmdir /s /q "build"
    echo ✅ 清理 build 資料夾
)
if exist "dist" (
    rmdir /s /q "dist"
    echo ✅ 清理 dist 資料夾
)
if exist "*.spec" (
    del "*.spec"
    echo ✅ 清理 spec 檔案
)
echo.

:: 步驟6：創建圖示（如果需要）
if not exist "icon.ico" (
    echo 🎨 步驟6：創建應用程式圖示...
    if exist "create_icon.py" (
        python create_icon.py
        if exist "icon.ico" (
            echo ✅ 圖示創建成功
        )
    )
)

:: 步驟7：使用修正的打包指令
echo.
echo 🔨 步驟7：重新打包（使用修正的參數）...
echo 這次使用更安全的打包設定...
echo.

:: 讀取版本號
echo 🔍 讀取應用程式版本...
for /f "tokens=2 delims='" %%a in ('findstr "APP_VERSION.*=" app.py') do (
    set "app_version=%%a"
)
if defined app_version (
    echo ✅ 找到版本號: %app_version%
    set "app_name_en=PDFToolkit-v%app_version%"
    set "app_name_ch=PDF工具包-v%app_version%"
) else (
    echo ⚠️  未找到版本號，使用預設名稱
    set "app_name_en=PDFToolkit"
    set "app_name_ch=PDF工具包"
)

echo 使用檔案名稱: %app_name_en%
echo.

:: 修正的打包指令
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name="%app_name_en%" ^
    --icon=icon.ico ^
    --exclude-module=pathlib ^
    --exclude-module=matplotlib ^
    --exclude-module=numpy ^
    --exclude-module=scipy ^
    --exclude-module=pandas ^
    --exclude-module=jupyter ^
    --exclude-module=IPython ^
    --exclude-module=setuptools ^
    --exclude-module=distutils ^
    --exclude-module=email ^
    --exclude-module=html ^
    --exclude-module=http ^
    --exclude-module=urllib ^
    --exclude-module=xml ^
    --exclude-module=test ^
    --exclude-module=unittest ^
    --exclude-module=sqlite3 ^
    --clean ^
    --noconfirm ^
    --log-level=INFO ^
    app.py

echo.

:: 步驟8：檢查結果並重命名
echo 🔍 步驟8：檢查建置結果...

set "exe_path_en=dist\%app_name_en%.exe"
set "exe_path_ch=dist\%app_name_ch%.exe"

if exist "%exe_path_en%" (
    echo ✅ 打包成功！英文檔名：%exe_path_en%
    
    :: 嘗試重命名為中文檔名
    copy "%exe_path_en%" "%exe_path_ch%" >nul 2>&1
    if exist "%exe_path_ch%" (
        echo ✅ 中文檔名副本已創建：%exe_path_ch%
        echo.
        echo 📁 你現在有兩個版本：
        echo    1. %exe_path_en% （英文檔名，推薦）
        echo    2. %exe_path_ch% （中文檔名）
    ) else (
        echo ⚠️  中文檔名創建失敗，使用英文檔名版本
    )
    
    :: 顯示檔案資訊
    for %%i in ("%exe_path_en%") do (
        set "file_size=%%~zi"
        set /a "size_mb=!file_size! / 1024 / 1024"
        echo 📊 檔案大小：!file_size! bytes (約 !size_mb! MB)
    )
    
    echo.
    echo 🎉 打包完成！
    echo.
    
    :: 創建啟動腳本
    echo 📄 創建啟動腳本...
    (
        echo @echo off
        echo cd /d "%%~dp0"
        echo if exist "%app_name_en%.exe" (
        echo     start "" "%app_name_en%.exe"
        echo ^) else if exist "%app_name_ch%.exe" (
        echo     start "" "%app_name_ch%.exe"
        echo ^) else (
        echo     echo 找不到可執行檔！
        echo     pause
        echo ^)
    ) > "dist\啟動程式.bat"
    echo ✅ 啟動腳本已創建：dist\啟動程式.bat
    
    echo.
    echo 🚀 現在你可以：
    echo    1. 直接執行：%exe_path_en%
    echo    2. 使用啟動腳本：dist\啟動程式.bat
    echo    3. 分享整個 dist 資料夾給其他人
    
    :: 詢問是否開啟資料夾
    set /p "open_folder=是否要開啟 dist 資料夾？(Y/N): "
    if /i "!open_folder!"=="Y" (
        explorer "dist"
    )
    
    :: 詢問是否測試
    set /p "test_run=是否要測試執行程式？(Y/N): "
    if /i "!test_run!"=="Y" (
        echo.
        echo 🧪 啟動測試...
        start "" "%exe_path_en%"
    )
    
) else (
    echo ❌ 打包仍然失敗！
    echo.
    echo 🔍 請檢查以下項目：
    echo 1. 確認 app.py 檔案存在
    echo 2. 檢查上方是否有錯誤訊息
    echo 3. 嘗試關閉防毒軟體
    echo 4. 確保有足夠的磁碟空間
    echo 5. 以管理員身份執行此腳本
    echo.
    echo 💡 如果問題持續，可以嘗試：
    echo python -m PyInstaller --onefile --console app.py
    echo （使用控制台模式查看詳細錯誤）
)

echo.
echo 📋 修復和打包程序完成！
echo.
pause