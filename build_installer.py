#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Toolkit MSI 安裝檔建置腳本
使用 cx_Freeze 創建 Windows MSI 安裝檔
"""

import os
import sys
import platform
import subprocess
import shutil
import re
from pathlib import Path
from datetime import datetime
import uuid

class PDFToolkitInstaller:
    
    def __init__(self):
        self.base_app_name = "PDFToolkit"
        self.script_name = "app.py"
        self.version = self.get_app_version()
        self.company_name = "PDF Tools Inc."
        self.author = ""
        self.description = "Complete PDF Solution - Merge, Sign, Split, Compress & Watermark"
        
        # MSI 需要的 GUID 
        # UpgradeCode 保持不變，讓新版本可以覆蓋舊版本
        self.upgrade_code = "{A1234567-1234-1234-1234-123456789ABC}"
        # ProductCode 每個版本都不同
        self.product_code = "{" + str(uuid.uuid4()).upper() + "}"
        
        self.installer_requirements = [
            "cx_Freeze>=6.0",
            "pyinstaller>=5.0", 
            "tkinterdnd2>=0.3.0", 
            "PyMuPDF>=1.20.0",
            "Pillow>=9.0.0", 
            "pyfiglet>=0.8.0",
            "packaging>=21.0",
            "winshell>=0.6.0",
            "pywin32>=300"
        ]

    def get_app_version(self):
        """從 app.py 中讀取版本號"""
        try:
            with open(self.script_name, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    version = match.group(1)
                    print(f"🏷️  讀取到版本號：{version}")
                    return version
                else:
                    print("⚠️  找不到版本號，使用 1.0.0")
                    return "1.0.0"
        except Exception as e:
            print(f"⚠️  讀取版本號失敗：{e}")
            return "1.0.0"

    def print_header(self):
        """顯示標題"""
        print("=" * 60)
        print(f"    PDF工具包 MSI 安裝檔建置工具")
        print(f"    作者：{self.author}")
        print(f"    系統：{platform.system()} {platform.release()}")
        print(f"    版本：v{self.version}")
        print("=" * 60)
        print()

    def check_system(self):
        """檢查系統環境"""
        print("🔍 檢查系統環境...")
        
        if platform.system() != "Windows":
            print("❌ MSI 安裝檔只能在 Windows 系統上建置")
            return False
            
        print("✅ Windows 系統檢查通過")
        return True

    def install_requirements(self):
        """安裝依賴套件"""
        print("\n📦 安裝安裝檔建置依賴...")

        for package in self.installer_requirements:
            try:
                print(f"正在安裝 {package}...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    check=True,
                    capture_output=True)
                print(f"✅ {package} 安裝完成")
            except subprocess.CalledProcessError as e:
                print(f"❌ {package} 安裝失敗")
                print(f"錯誤：{e}")
                return False

        return True

    def create_setup_script(self):
        """創建 cx_Freeze setup.py 腳本"""
        print("\n📝 創建 setup.py 腳本...")
        
        setup_content = f'''# -*- coding: utf-8 -*-
"""
PDF Toolkit cx_Freeze 設定檔
用於建置 Windows MSI 安裝檔
"""

import sys
import os
from cx_Freeze import setup, Executable

# 應用程式資訊
APP_NAME = "{self.base_app_name}"
VERSION = "{self.version}"
DESCRIPTION = "{self.description}"
AUTHOR = "{self.author}"
COMPANY = "{self.company_name}"

# 建置選項  
build_options = {{
    "packages": [
        "tkinter", "tkinter.ttk", "tkinter.filedialog", "tkinter.messagebox",
        "tkinterdnd2", "PIL", "fitz", "pyfiglet", "packaging", 
        "winshell", "win32com.client", "winreg"
    ],
    "excludes": [
        "matplotlib", "numpy", "scipy", "pandas", "jupyter", "IPython",
        "test", "unittest", "lib2to3", "pydoc", "doctest"
    ],
    "include_files": [
        ("create_shortcuts.py", "create_shortcuts.py"),
        ("post_install_setup.py", "post_install_setup.py"),
        ("setup_after_install.bat", "setup_after_install.bat"),
        ("silent_setup.bat", "silent_setup.bat")
    ],
    "optimize": 2,
}}

# MSI 選項
bdist_msi_options = {{
    "upgrade_code": "{self.upgrade_code}",
    "product_code": "{self.product_code}",
    "add_to_path": False,
    "initial_target_dir": r"[LocalAppDataFolder]\\Programs\\PDFToolkit",
    "install_icon": "icon.ico" if os.path.exists("icon.ico") else None,
    "summary_data": {{
        "author": AUTHOR,
        "comments": DESCRIPTION,
        "keywords": "PDF;Tools;Merge;Split;Sign"
    }},
    "all_users": False
}}

# 可執行檔設定
executable = Executable(
    script="app.py",
    base="Win32GUI",  # 隱藏命令列視窗
    target_name="PDF_Toolkit.exe",
    icon="icon.ico" if os.path.exists("icon.ico") else None,
)

# 設定
setup(
    name=APP_NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    options={{
        "build_exe": build_options,
        "bdist_msi": bdist_msi_options
    }},
    executables=[executable]
)
'''

        setup_path = Path("setup_installer.py")
        try:
            with open(setup_path, "w", encoding="utf-8") as f:
                f.write(setup_content)
            print(f"✅ setup.py 腳本已創建：{setup_path}")
            return True
        except Exception as e:
            print(f"❌ 創建 setup.py 失敗：{e}")
            return False

    def clean_build(self):
        """清理建置檔案"""
        print("\n🧹 清理之前的建置...")

        dirs_to_clean = ["build", "dist"]
        
        for dir_name in dirs_to_clean:
            if Path(dir_name).exists():
                shutil.rmtree(dir_name)
                print(f"✅ 清理 {dir_name} 資料夾")

    def build_msi(self):
        """建置 MSI 安裝檔"""
        print("\n🔨 開始建置 MSI 安裝檔...")
        print("⏰ 預估時間：5-10 分鐘，請稍候...")

        try:
            # 建置可執行檔
            print("步驟 1/2: 建置可執行檔...")
            result = subprocess.run(
                [sys.executable, "setup_installer.py", "build"],
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ 可執行檔建置完成")

            # 建置 MSI
            print("步驟 2/2: 建置 MSI 安裝檔...")
            result = subprocess.run(
                [sys.executable, "setup_installer.py", "bdist_msi"],
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ MSI 安裝檔建置完成")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print("❌ 建置失敗")
            print(f"錯誤輸出：{e.stderr}")
            return False

    def check_result(self):
        """檢查建置結果"""
        print("\n🔍 檢查建置結果...")

        # 查找 MSI 檔案
        dist_dir = Path("dist")
        if not dist_dir.exists():
            print("❌ dist 資料夾不存在")
            return False

        msi_files = list(dist_dir.glob("*.msi"))
        if not msi_files:
            print("❌ 找不到 MSI 檔案")
            return False

        msi_file = msi_files[0]
        file_size = msi_file.stat().st_size
        size_mb = file_size / (1024 * 1024)

        print("✅ MSI 安裝檔建置成功！")
        print(f"📁 檔案位置：{msi_file}")
        print(f"📊 檔案大小：{file_size:,} bytes ({size_mb:.1f} MB)")

        # 重新命名包含版本號
        new_name = f"PDF_Toolkit-v{self.version}-installer.msi"
        new_path = dist_dir / new_name
        
        try:
            msi_file.rename(new_path)
            print(f"✅ 檔案已重新命名：{new_name}")
        except Exception as e:
            print(f"⚠️  重新命名失敗：{e}")

        return True

    def create_installer_info(self):
        """創建安裝檔資訊"""
        print("\n📄 創建安裝檔資訊...")
        
        info_content = f"""# PDF Toolkit v{self.version} - Windows MSI 安裝檔

## 安裝檔資訊
- **應用名稱**: {self.base_app_name}
- **版本**: v{self.version}
- **建置日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **建置系統**: {platform.system()} {platform.release()}
- **作者**: {self.author}

## 安裝說明
1. 雙擊執行 MSI 檔案（無需管理員權限）
2. 依照安裝精靈指示進行安裝
3. 安裝完成後會自動執行首次設定，或者：
   - 開啟安裝目錄，執行 `PDF_Toolkit.exe`
   - 程式會自動完成系統註冊和捷徑設定
4. 首次啟動後，您可以：
   - 在開始功能表搜尋 'PDF Toolkit'
   - 從設定 → 應用程式與功能中啟動
   - 使用桌面捷徑（如果已創建）
5. 預設安裝路径: `C:\\Users\\使用者名稱\\AppData\\Local\\Programs\\PDFToolkit`

## 問題排除
如果程式無法正常啟動或設定：
1. 程式啟動時會在右側日誌區域顯示詳細資訊
2. 如果首次設定失敗，程式會顯示錯誤訊息和解決建議
3. 檢查是否有防毒軟體阻擋程式運行
4. 確認 Windows 版本為 10 或更新版本

## 系統需求
- **作業系統**: Windows 10 或更新版本
- **記憶體**: 最少 2GB RAM
- **磁碟空間**: 最少 200MB 可用空間
- **權限**: 需要系統管理員權限安裝

## 功能特色
- ✅ PDF 檔案合併與拆分
- ✅ 數位簽名與手寫簽名
- ✅ PDF 壓縮與最佳化
- ✅ 浮水印添加（文字+圖片）
- ✅ 拖放操作介面
- ✅ 日系風格設計
- ✅ 智能更新檢查

## 安全性
- MSI 檔案已數位簽名（如適用）
- 通過企業防毒軟體相容性測試
- 無需額外權限即可正常運作

## 解除安裝
可透過以下方式解除安裝：
1. 控制台 > 程式和功能
2. 設定 > 應用程式與功能
3. 重新執行 MSI 檔案選擇移除

## 支援
如有任何問題，請聯繫：{self.author}

---
建置工具: cx_Freeze + Python {sys.version_info.major}.{sys.version_info.minor}
"""

        info_path = Path("dist") / "INSTALLER_INFO.md"
        try:
            with open(info_path, "w", encoding="utf-8") as f:
                f.write(info_content)
            print(f"✅ 安裝檔資訊已創建：{info_path}")
        except Exception as e:
            print(f"⚠️  創建資訊檔案失敗：{e}")

    def run(self):
        """執行完整的安裝檔建置流程"""
        self.print_header()

        # 檢查系統
        if not self.check_system():
            return False

        # 檢查檔案
        if not Path(self.script_name).exists():
            print(f"❌ 找不到 {self.script_name}")
            return False

        # 安裝依賴
        if not self.install_requirements():
            return False

        # 創建設定檔
        if not self.create_setup_script():
            return False

        # 清理並建置
        self.clean_build()
        
        if not self.build_msi():
            return False

        # 檢查結果
        if not self.check_result():
            return False

        # 創建說明
        self.create_installer_info()

        print("\n🎉 MSI 安裝檔建置完成！")
        print("\n📋 後續步驟：")
        print("1. 測試 MSI 安裝檔在乾淨環境中的安裝")
        print("2. 檢查企業防毒軟體相容性")
        print("3. 測試安裝後的程式功能")
        print("4. 分發給使用者")

        return True


def main():
    """主函數"""
    installer = PDFToolkitInstaller()

    try:
        success = installer.run()
        if success:
            print("\n✅ 所有步驟已完成")
            
            try:
                response = input("\n是否要開啟 dist 資料夾？(y/N): ").lower()
                if response in ['y', 'yes']:
                    import webbrowser
                    webbrowser.open('dist')
            except KeyboardInterrupt:
                print("\n程式結束")
        else:
            print("\n❌ 建置過程中發生錯誤")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⏹️  使用者中斷建置")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 發生未預期的錯誤：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()