@echo off
chcp 65001 >nul
echo.
echo ==========================================
echo    環境診斷工具
echo ==========================================
echo.

echo 🔍 檢查 Python 環境...
python --version
echo.

echo 🔍 檢查已安裝的套件...
python -c "
import sys
print('Python 路徑:', sys.executable)
print()

packages = ['PyInstaller', 'tkinterdnd2', 'fitz', 'PIL', 'pyfiglet', 'pathlib']
for pkg in packages:
    try:
        if pkg == 'fitz':
            import fitz
            print(f'✅ {pkg}: {fitz.version}')
        elif pkg == 'PIL':
            import PIL
            print(f'✅ {pkg}: {PIL.__version__}')
        elif pkg == 'pathlib':
            import pathlib
            print(f'⚠️  {pkg}: 存在（這可能造成問題）')
        else:
            module = __import__(pkg)
            version = getattr(module, '__version__', 'Unknown')
            print(f'✅ {pkg}: {version}')
    except ImportError:
        print(f'❌ {pkg}: 未安裝')
    except Exception as e:
        print(f'⚠️  {pkg}: {e}')
"

echo.
echo 🔍 檢查檔案...
if exist "app.py" (
    echo ✅ app.py 存在
) else (
    echo ❌ app.py 不存在
)

if exist "icon.ico" (
    echo ✅ icon.ico 存在
) else (
    echo ⚠️  icon.ico 不存在
)

if exist "dist" (
    echo 📁 dist 資料夾內容：
    dir "dist" /b
) else (
    echo ❌ dist 資料夾不存在
)

echo.
echo 📋 診斷完成！
pause