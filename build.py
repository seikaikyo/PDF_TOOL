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
from pathlib import Path


class PDFToolkitBuilder:

    def __init__(self):
        self.app_name = "PDF合併工具"
        self.script_name = "app.py"
        self.system = platform.system()
        self.requirements = [
            "pyinstaller>=5.0", "tkinterdnd2>=0.3.0", "PyMuPDF>=1.20.0",
            "Pillow>=9.0.0", "pyfiglet>=0.8.0"
        ]

    def print_header(self):
        """顯示標題"""
        print("=" * 50)
        print(f"    {self.app_name} 跨平台打包工具")
        print("    作者：選我正解")
        print(f"    系統：{self.system} {platform.release()}")
        print("=" * 50)
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

        # 系統特定參數
        if self.system == "Windows":
            if Path("icon.ico").exists():
                cmd.append("--icon=icon.ico")
        elif self.system == "Darwin":  # macOS
            if Path("icon.png").exists():
                cmd.append("--icon=icon.png")
            cmd.append("--osx-bundle-identifier=com.pdftools.merger")

        # 排除不必要的模組
        exclude_modules = [
            "matplotlib", "numpy", "scipy", "pandas", "jupyter", "IPython",
            "setuptools", "distutils", "email", "html", "http", "urllib",
            "xml", "test", "unittest", "sqlite3", "tkinter.test", "lib2to3",
            "pydoc"
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

        readme_content = f"""# {self.app_name}

## 系統資訊
- 建立時間：{platform.node()} - {sys.version}
- 作業系統：{platform.system()} {platform.release()}
- 處理器：{platform.processor()}

## 功能特色
- ✅ 多個 PDF 檔案合併
- ✅ 拖曳調整頁面順序  
- ✅ 直覺的圖形化介面
- ✅ 支援拖放操作
- ✅ 即時預覽功能
- ✅ PDF 簽名編輯

## 使用方法
1. 執行程式
2. 拖放或選擇 PDF 檔案
3. 調整頁面順序
4. 點擊合併按鈕
5. 選擇儲存位置

## 系統需求
- Python 3.7+ (開發環境)
- 記憶體：2GB 以上
- 磁碟空間：100MB 以上

## 技術資訊
- GUI 框架：Tkinter
- PDF 處理：PyMuPDF
- 圖像處理：Pillow
- 打包工具：PyInstaller

## 作者
選我正解

---
Generated by PDF Toolkit Builder
"""

        readme_path = Path("dist") / "README.md"
        try:
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme_content)
            print(f"✅ 使用說明已創建：{readme_path}")
        except Exception as e:
            print(f"⚠️  創建說明檔案失敗：{e}")

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

        print("\n🎉 建置完成！")
        print("\n📋 後續步驟：")
        print("1. 測試可執行檔功能")
        print("2. 檢查在不同環境下的相容性")
        print("3. 準備分發套件")

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
