#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 合併工具跨平台打包腳本
支援 Windows, macOS, Linux
"""

import os
import sys
import platform
import subprocess
import shutil
import re
import zipfile
from datetime import datetime
from pathlib import Path


class PDFToolkitBuilder:

    def __init__(self):
        self.base_app_name = "PDFToolkit"
        self.script_name = "app.py"
        self.system = platform.system()
        self.version = self.get_app_version()
        self.app_name = f"{self.base_app_name}-v{self.version}" if self.version else self.base_app_name
        self.requirements = [
            "pyinstaller>=5.0", "tkinterdnd2>=0.3.0", "PyMuPDF>=1.20.0",
            "Pillow>=9.0.0", "pyfiglet>=0.8.0"
        ]

    def get_app_version(self):
        """從 app.py 中讀取版本號"""
        try:
            with open(self.script_name, 'r', encoding='utf-8') as f:
                content = f.read()
                # 尋找 APP_VERSION = "x.x.x" 的模式
                match = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    version = match.group(1)
                    print(f"🏷️  讀取到版本號：{version}")
                    return version
                else:
                    print("⚠️  找不到版本號，使用預設名稱")
                    return None
        except Exception as e:
            print(f"⚠️  讀取版本號失敗：{e}")
            return None

    def print_header(self):
        """顯示標題"""
        print("=" * 60)
        print(f"    PDF工具包 ({self.base_app_name}) 跨平台打包工具")
        print("    作者：選我正解")
        print(f"    系統：{self.system} {platform.release()}")
        if self.version:
            print(f"    版本：v{self.version}")
            print(f"    輸出檔案：{self.app_name}")
        print("=" * 60)
        print()

    def check_python(self):
        """檢查 Python 版本"""
        version = sys.version_info
        print(f"🐍 Python 版本：{version.major}.{version.minor}.{version.micro}")

        if version < (3, 7):
            print("❌ 錯誤：需要 Python 3.7 或更新版本")
            return False

        print("✅ Python 版本符合要求")
        return True

    def check_files(self):
        """檢查必要檔案"""
        print("\n🔍 檢查必要檔案...")

        if not Path(self.script_name).exists():
            print(f"❌ 找不到 {self.script_name}")
            return False

        print(f"✅ 找到 {self.script_name}")

        # 檢查圖示檔案
        if Path("create_icon.py").exists():
            print("✅ 找到圖示生成腳本")
        else:
            print("⚠️  找不到圖示生成腳本")

        return True

    def install_requirements(self):
        """安裝依賴套件"""
        print("\n📦 安裝依賴套件...")

        # 升級 pip
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
                capture_output=True)
            print("✅ pip 已升級")
        except subprocess.CalledProcessError:
            print("⚠️  pip 升級失敗，繼續進行...")

        # 安裝套件
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
                print(f"錯誤：{e}")
                return False

        return True

    def create_icon(self):
        """創建圖示"""
        print("\n🎨 處理應用程式圖示...")

        icon_file = "icon.ico" if self.system == "Windows" else "icon.png"

        if Path(icon_file).exists():
            print(f"✅ 圖示檔案已存在：{icon_file}")
            return icon_file

        if Path("create_icon.py").exists():
            try:
                subprocess.run([sys.executable, "create_icon.py"], check=True)
                if Path(icon_file).exists():
                    print(f"✅ 圖示創建成功：{icon_file}")
                    return icon_file
            except subprocess.CalledProcessError:
                print("⚠️  圖示創建失敗")

        print("⚠️  將使用預設圖示")
        return None

    def clean_build(self):
        """清理建置檔案"""
        print("\n🧹 清理之前的建置...")

        dirs_to_clean = ["build", "dist", "__pycache__"]
        files_to_clean = ["*.spec"]

        for dir_name in dirs_to_clean:
            if Path(dir_name).exists():
                shutil.rmtree(dir_name)
                print(f"✅ 清理 {dir_name} 資料夾")

        # 清理 spec 檔案
        for spec_file in Path(".").glob("*.spec"):
            spec_file.unlink()
            print(f"✅ 清理 {spec_file}")

    def build_executable(self):
        """建置可執行檔"""
        print("\n🔨 開始打包...")
        print("⏰ 預估時間：3-5 分鐘，請稍候...")

        # 基本參數
        cmd = [
            sys.executable, "-m", "PyInstaller", "--onefile", "--windowed",
            f"--name={self.app_name}", "--clean", "--noconfirm"
        ]
        
        # 添加隱藏導入（用於確保必要模組被包含）
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
                # 使用正確的路徑分隔符
                separator = ";" if self.system == "Windows" else ":"
                cmd.extend(["--add-data", f"{fonts_path}{separator}pyfiglet/fonts"])
                print(f"✅ 添加pyfiglet字體路徑：{fonts_path}")
        except Exception as e:
            print(f"⚠️  無法找到pyfiglet字體：{e}")
            print("   這可能會導致字體相關功能無法使用")

        # 系統特定參數
        if self.system == "Windows":
            if Path("icon.ico").exists():
                cmd.append("--icon=icon.ico")
        elif self.system == "Darwin":  # macOS
            if Path("icon.png").exists():
                cmd.append("--icon=icon.png")
            cmd.append("--osx-bundle-identifier=com.pdftools.merger")

        # 排除不必要的模組（保守排除，只排除確定不需要的）
        exclude_modules = [
            "matplotlib", "numpy", "scipy", "pandas", "jupyter", "IPython",
            "test", "unittest", "tkinter.test", "lib2to3", "pydoc", "doctest"
        ]

        for module in exclude_modules:
            cmd.extend(["--exclude-module", module])

        # 添加主腳本
        cmd.append(self.script_name)

        print(f"執行指令：{' '.join(cmd[:5])} ... (共 {len(cmd)} 個參數)")

        try:
            result = subprocess.run(cmd,
                                    check=True,
                                    capture_output=True,
                                    text=True)
            print("✅ 打包命令執行完成")
            return True
        except subprocess.CalledProcessError as e:
            print("❌ 打包失敗")
            print(f"錯誤輸出：{e.stderr}")
            return False

    def check_result(self):
        """檢查建置結果"""
        print("\n🔍 檢查建置結果...")

        dist_dir = Path("dist")
        if not dist_dir.exists():
            print("❌ dist 資料夾不存在")
            return False

        # 查找可執行檔
        executable_extensions = [".exe", ""] if self.system == "Windows" else [
            "", ".app"
        ]
        executable_path = None

        for ext in executable_extensions:
            potential_path = dist_dir / f"{self.app_name}{ext}"
            if potential_path.exists():
                executable_path = potential_path
                break

        if not executable_path:
            print("❌ 找不到可執行檔")
            return False

        # 顯示檔案資訊
        file_size = executable_path.stat().st_size
        size_mb = file_size / (1024 * 1024)

        print("✅ 打包成功！")
        print(f"📁 檔案位置：{executable_path}")
        print(f"📊 檔案大小：{file_size:,} bytes ({size_mb:.1f} MB)")

        return True

    def create_readme(self):
        """創建使用說明"""
        print("\n📄 創建使用說明...")

        version_info = f" v{self.version}" if self.version else ""
        
        readme_content = f"""# PDF工具包 (PDFToolkit{version_info})

## 版本資訊
- 應用版本：{self.version if self.version else "未知"}
- 檔案名稱：{self.app_name}
- 建立時間：{platform.node()} - {sys.version}
- 作業系統：{platform.system()} {platform.release()}
- 處理器：{platform.processor()}

## 功能特色
- ✅ 多個 PDF 檔案合併
- ✅ 拖曳調整頁面順序  
- ✅ 直覺的圖形化介面
- ✅ 支援拖放操作
- ✅ 即時預覽功能
- ✅ PDF 數位簽名編輯
- ✅ 手寫簽名功能
- ✅ 圖片簽名上傳
- ✅ 文字插入與編輯
- ✅ PDF 拆分功能
- ✅ PDF 壓縮功能
- ✅ PDF 浮水印功能 (文字 + 圖片)
- ✅ 日系配色設計
- ✅ 智能多源更新檢查

## 使用方法
1. 執行程式
2. 拖放或選擇 PDF 檔案
3. 選擇功能（合併/簽名/拆分/壓縮/浮水印）
4. 根據功能進行相應操作
5. 選擇儲存位置

## 系統需求
- Python 3.7+ (開發環境)
- 記憶體：2GB 以上
- 磁碟空間：100MB 以上

## 技術資訊
- GUI 框架：Tkinter (日系配色設計)
- PDF 處理：PyMuPDF (fitz)
- 圖像處理：Pillow (PIL)
- 打包工具：PyInstaller
- 更新系統：多源智能檢查 (GitLab + GitHub)

## 配色設計
基於日本傳統色彩（nipponcolors.com 和 irocore.com）：
- 淡雪色 (AWAYUKI) - 主背景
- 白茶色 (SHIRACHA) - 面板背景  
- 瑠璃色 (RURI) - 信息色
- 常磐色 (TOKIWA) - 成功色
- 柿色 (KAKI) - 浮水印按鈕

## 作者
選我正解

---
Generated by PDF Toolkit Builder v{self.version if self.version else "unknown"}
Build Date: {platform.node()}
"""

        readme_path = Path("dist") / "README.md"
        try:
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme_content)
            print(f"✅ 使用說明已創建：{readme_path}")
        except Exception as e:
            print(f"⚠️  創建說明檔案失敗：{e}")

    def create_release_package(self):
        """創建發布包"""
        print("\n📦 創建發布包...")
        
        if not self.version:
            print("⚠️  沒有版本號，跳過創建發布包")
            return False
            
        try:
            # 創建發布包名稱
            package_name = f"{self.base_app_name}-v{self.version}-{self.system.lower()}"
            if self.system == "Windows":
                package_name += ".zip"
            else:
                package_name += ".tar.gz"
            
            package_path = Path("releases") / package_name
            
            # 創建 releases 目錄
            package_path.parent.mkdir(exist_ok=True)
            
            if self.system == "Windows":
                # 創建 ZIP 檔案
                with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # 添加可執行檔
                    for item in Path("dist").iterdir():
                        if item.is_file():
                            zipf.write(item, item.name)
                            print(f"  添加：{item.name}")
            else:
                # 創建 TAR.GZ 檔案
                import tarfile
                with tarfile.open(package_path, 'w:gz') as tarf:
                    for item in Path("dist").iterdir():
                        if item.is_file():
                            tarf.add(item, item.name)
                            print(f"  添加：{item.name}")
            
            file_size = package_path.stat().st_size
            size_mb = file_size / (1024 * 1024)
            
            print(f"✅ 發布包創建成功：{package_path}")
            print(f"📊 包大小：{file_size:,} bytes ({size_mb:.1f} MB)")
            
            return True
            
        except Exception as e:
            print(f"❌ 創建發布包失敗：{e}")
            return False

    def run(self):
        """執行完整的建置流程"""
        self.print_header()

        # 檢查環境
        if not self.check_python():
            return False

        if not self.check_files():
            return False

        # 安裝依賴
        if not self.install_requirements():
            return False

        # 準備檔案
        self.create_icon()
        self.clean_build()

        # 建置
        if not self.build_executable():
            return False

        # 檢查結果
        if not self.check_result():
            return False

        # 創建說明
        self.create_readme()
        
        # 創建發布包
        self.create_release_package()

        print("\n🎉 建置完成！")
        print(f"\n📁 輸出檔案：{self.app_name}")
        if self.version:
            print(f"🏷️  版本標籤：v{self.version}")
        print("\n📋 後續步驟：")
        print("1. 測試可執行檔功能")
        print("2. 檢查在不同環境下的相容性")
        print("3. 上傳 releases/ 中的檔案到 GitLab/GitHub")
        print("4. 測試多源更新功能")

        return True


def main():
    """主函數"""
    builder = PDFToolkitBuilder()

    try:
        success = builder.run()
        if success:
            print("\n✅ 所有步驟已完成")

            # 詢問是否開啟資料夾
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
