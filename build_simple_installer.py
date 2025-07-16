#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Toolkit 簡化安裝檔建置腳本
使用 PyInstaller + NSIS 創建安裝檔
"""

import os
import sys
import platform
import subprocess
import shutil
import re
from pathlib import Path
from datetime import datetime

class PDFToolkitSimpleInstaller:
    
    def __init__(self):
        self.base_app_name = "PDFToolkit"
        self.script_name = "app.py"
        self.version = self.get_app_version()
        self.company_name = "PDF Tools Inc."
        self.author = "選我正解"
        
        self.requirements = [
            "pyinstaller>=5.0", 
            "tkinterdnd2>=0.3.0", 
            "PyMuPDF>=1.20.0",
            "Pillow>=9.0.0", 
            "pyfiglet>=0.8.0",
            "packaging>=21.0"
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
        print(f"    PDF工具包 便攜式安裝檔建置工具")
        print(f"    作者：{self.author}")
        print(f"    版本：v{self.version}")
        print("=" * 60)
        print()

    def install_requirements(self):
        """安裝依賴套件"""
        print("\n📦 安裝建置依賴...")

        for package in self.requirements:
            try:
                print(f"正在安裝 {package}...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    check=True,
                    capture_output=True)
                print(f"✅ {package} 安裝完成")
            except subprocess.CalledProcessError as e:
                print(f"❌ {package} 安裝失敗")
                return False

        return True

    def clean_build(self):
        """清理建置檔案"""
        print("\n🧹 清理之前的建置...")

        dirs_to_clean = ["build", "dist"]
        
        for dir_name in dirs_to_clean:
            if Path(dir_name).exists():
                shutil.rmtree(dir_name)
                print(f"✅ 清理 {dir_name} 資料夾")

    def build_executable(self):
        """使用 PyInstaller 建置可執行檔"""
        print("\n🔨 建置便攜式可執行檔...")
        print("⏰ 預估時間：3-5 分鐘，請稍候...")

        # PyInstaller 參數
        cmd = [
            sys.executable, "-m", "PyInstaller", 
            "--onefile",                    # 單一檔案
            "--windowed",                   # 隱藏控制台
            f"--name={self.base_app_name}-v{self.version}-Portable",  # 檔案名稱
            "--clean", 
            "--noconfirm"
        ]
        
        # 添加圖示
        if Path("icon.ico").exists():
            cmd.append("--icon=icon.ico")
        
        # 添加隱藏導入
        hidden_imports = [
            "tkinterdnd2", "PIL", "PIL._tkinter_finder", "fitz", 
            "pyfiglet", "pyfiglet.fonts", "tkinter", "tkinter.ttk", 
            "tkinter.filedialog", "tkinter.messagebox"
        ]
        
        for module in hidden_imports:
            cmd.extend(["--hidden-import", module])
        
        # 添加數據文件（pyfiglet字體）
        try:
            import pyfiglet
            pyfiglet_path = pyfiglet.__path__[0]
            fonts_path = os.path.join(pyfiglet_path, "fonts")
            if os.path.exists(fonts_path):
                separator = ";" if platform.system() == "Windows" else ":"
                cmd.extend(["--add-data", f"{fonts_path}{separator}pyfiglet/fonts"])
        except Exception as e:
            print(f"⚠️  無法找到pyfiglet字體：{e}")

        # 排除不需要的模組
        exclude_modules = [
            "matplotlib", "numpy", "scipy", "pandas", "jupyter", "IPython",
            "test", "unittest", "lib2to3", "pydoc", "doctest"
        ]

        for module in exclude_modules:
            cmd.extend(["--exclude-module", module])

        # 添加主腳本
        cmd.append(self.script_name)

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ 便攜式可執行檔建置完成")
            return True
        except subprocess.CalledProcessError as e:
            print("❌ 建置失敗")
            print(f"錯誤輸出：{e.stderr}")
            return False

    def create_nsis_script(self):
        """創建 NSIS 安裝腳本"""
        print("\n📝 創建 NSIS 安裝腳本...")
        
        executable_name = f"{self.base_app_name}-v{self.version}-Portable.exe"
        installer_name = f"{self.base_app_name}-v{self.version}-Installer.exe"
        
        nsis_script = f'''
; PDF Toolkit NSIS 安裝腳本
; 版本: {self.version}

!define PRODUCT_NAME "PDF Toolkit"
!define PRODUCT_VERSION "{self.version}"
!define PRODUCT_PUBLISHER "{self.company_name}"
!define PRODUCT_WEB_SITE "https://github.com/seikaikyo/PDF_TOOL"
!define PRODUCT_DIR_REGKEY "Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\PDFToolkit.exe"
!define PRODUCT_UNINST_KEY "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\PDFToolkit"

!include "MUI2.nsh"

; 安裝檔設定
Name "${{PRODUCT_NAME}} ${{PRODUCT_VERSION}}"
OutFile "dist\\{installer_name}"
InstallDir "$PROGRAMFILES\\PDF Toolkit"
InstallDirRegKey HKLM "${{PRODUCT_DIR_REGKEY}}" ""
ShowInstDetails show
ShowUnInstDetails show

; 現代UI設定
!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

; 安裝頁面
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; 解除安裝頁面
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; 語言檔案
!insertmacro MUI_LANGUAGE "TradChinese"

Section "主程式" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  File "dist\\{executable_name}"
  Rename "$INSTDIR\\{executable_name}" "$INSTDIR\\PDFToolkit.exe"
  
  ; 創建開始功能表捷徑
  CreateDirectory "$SMPROGRAMS\\PDF Toolkit"
  CreateShortCut "$SMPROGRAMS\\PDF Toolkit\\PDF Toolkit.lnk" "$INSTDIR\\PDFToolkit.exe" "" "$INSTDIR\\PDFToolkit.exe" 0 SW_SHOWNORMAL "" "PDF 工具包 - 合併、簽名、拆分、壓縮、浮水印"
  CreateShortCut "$SMPROGRAMS\\PDF Toolkit\\解除安裝.lnk" "$INSTDIR\\uninst.exe"
  
  ; 創建桌面捷徑
  CreateShortCut "$DESKTOP\\PDF Toolkit.lnk" "$INSTDIR\\PDFToolkit.exe" "" "$INSTDIR\\PDFToolkit.exe" 0 SW_SHOWNORMAL "" "PDF 工具包 - 合併、簽名、拆分、壓縮、浮水印"
  
  ; 註冊到程式集 (Apps & Features)
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\PDFToolkit.exe" "" "$INSTDIR\\PDFToolkit.exe"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\PDFToolkit.exe" "Path" "$INSTDIR"
SectionEnd

Section "登錄項目" SEC02
  WriteRegStr HKLM "${{PRODUCT_DIR_REGKEY}}" "" "$INSTDIR\\PDFToolkit.exe"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "DisplayName" "${{PRODUCT_NAME}}"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "UninstallString" "$INSTDIR\\uninst.exe"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "DisplayIcon" "$INSTDIR\\PDFToolkit.exe"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "DisplayVersion" "${{PRODUCT_VERSION}}"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "Publisher" "${{PRODUCT_PUBLISHER}}"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "URLInfoAbout" "${{PRODUCT_WEB_SITE}}"
  WriteUninstaller "$INSTDIR\\uninst.exe"
SectionEnd

Section Uninstall
  ; 刪除程式檔案
  Delete "$INSTDIR\\PDFToolkit.exe"
  Delete "$INSTDIR\\uninst.exe"
  
  ; 刪除開始功能表捷徑
  Delete "$SMPROGRAMS\\PDF Toolkit\\PDF Toolkit.lnk"
  Delete "$SMPROGRAMS\\PDF Toolkit\\解除安裝.lnk"
  RMDir "$SMPROGRAMS\\PDF Toolkit"
  
  ; 刪除桌面捷徑
  Delete "$DESKTOP\\PDF Toolkit.lnk"
  
  ; 清理安裝目錄
  RMDir "$INSTDIR"
  
  ; 清理登錄檔
  DeleteRegKey HKLM "${{PRODUCT_UNINST_KEY}}"
  DeleteRegKey HKLM "${{PRODUCT_DIR_REGKEY}}"
  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\PDFToolkit.exe"
  
  ; 顯示解除安裝完成訊息
  MessageBox MB_OK "PDF Toolkit 已成功解除安裝！$\\r$\\n$\\r$\\n感謝您的使用！"
SectionEnd
'''

        script_path = Path("installer.nsi")
        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(nsis_script)
            print(f"✅ NSIS 腳本已創建：{script_path}")
            return True
        except Exception as e:
            print(f"❌ 創建 NSIS 腳本失敗：{e}")
            return False

    def create_license(self):
        """創建授權檔案"""
        license_content = f"""PDF Toolkit v{self.version}
Copyright (c) 2025 {self.author}

此軟體按「現狀」提供，不提供任何明示或暗示的保證。
使用者需自行承擔使用風險。

主要功能：
- PDF 檔案合併與拆分
- 數位簽名與手寫簽名
- PDF 壓縮與最佳化  
- 浮水印添加
- 直覺的拖放操作介面

系統需求：
- Windows 10 或更新版本
- 最少 2GB RAM
- 最少 200MB 磁碟空間
"""
        
        try:
            with open("LICENSE.txt", "w", encoding="utf-8") as f:
                f.write(license_content)
            print("✅ 授權檔案已創建")
            return True
        except Exception as e:
            print(f"⚠️  創建授權檔案失敗：{e}")
            return False

    def build_installer_with_nsis(self):
        """使用 NSIS 建置安裝檔"""
        print("\n🔨 使用 NSIS 建置安裝檔...")
        
        # 檢查 NSIS 是否安裝
        nsis_paths = [
            r"C:\Program Files (x86)\NSIS\makensis.exe",
            r"C:\Program Files\NSIS\makensis.exe",
            "makensis.exe"  # 如果在 PATH 中
        ]
        
        nsis_exe = None
        for path in nsis_paths:
            if Path(path).exists() or path == "makensis.exe":
                try:
                    subprocess.run([path, "/VERSION"], check=True, capture_output=True)
                    nsis_exe = path
                    break
                except:
                    continue
        
        if not nsis_exe:
            print("❌ 找不到 NSIS，請下載安裝 NSIS:")
            print("   https://nsis.sourceforge.io/Download")
            print("   安裝後重新執行此腳本")
            return False
        
        try:
            result = subprocess.run([nsis_exe, "installer.nsi"], check=True, capture_output=True, text=True)
            print("✅ NSIS 安裝檔建置完成")
            return True
        except subprocess.CalledProcessError as e:
            print("❌ NSIS 建置失敗")
            print(f"錯誤：{e.stderr}")
            return False

    def check_result(self):
        """檢查建置結果"""
        print("\n🔍 檢查建置結果...")

        dist_dir = Path("dist")
        installer_files = list(dist_dir.glob("*Installer.exe"))
        portable_files = list(dist_dir.glob("*Portable.exe"))

        if installer_files:
            installer_file = installer_files[0]
            file_size = installer_file.stat().st_size
            size_mb = file_size / (1024 * 1024)
            print(f"✅ 安裝檔：{installer_file} ({size_mb:.1f} MB)")

        if portable_files:
            portable_file = portable_files[0]
            file_size = portable_file.stat().st_size
            size_mb = file_size / (1024 * 1024)
            print(f"✅ 便攜版：{portable_file} ({size_mb:.1f} MB)")

        return len(installer_files) > 0 or len(portable_files) > 0

    def run(self):
        """執行建置流程"""
        self.print_header()

        if not Path(self.script_name).exists():
            print(f"❌ 找不到 {self.script_name}")
            return False

        # 安裝依賴
        if not self.install_requirements():
            return False

        # 清理並建置
        self.clean_build()
        
        if not self.build_executable():
            return False

        # 創建安裝檔相關檔案
        self.create_license()
        self.create_nsis_script()
        
        # 嘗試建置 NSIS 安裝檔
        nsis_success = self.build_installer_with_nsis()
        
        # 檢查結果
        if not self.check_result():
            return False

        print("\n🎉 建置完成！")
        
        if nsis_success:
            print("✅ 成功建立安裝檔和便攜版")
        else:
            print("✅ 成功建立便攜版（安裝檔需要 NSIS）")
            
        print("\n📋 輸出檔案：")
        print("- 便攜版：可直接執行，無需安裝")
        print("- 安裝檔：標準安裝體驗，防毒軟體較友善")

        return True


def main():
    installer = PDFToolkitSimpleInstaller()
    
    try:
        success = installer.run()
        if success:
            print("\n✅ 建置完成")
            try:
                response = input("\n是否要開啟 dist 資料夾？(y/N): ").lower()
                if response in ['y', 'yes']:
                    import webbrowser
                    webbrowser.open('dist')
            except KeyboardInterrupt:
                print("\n程式結束")
        else:
            print("\n❌ 建置失敗")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  使用者中斷建置")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 發生錯誤：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()