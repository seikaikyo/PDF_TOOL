# -*- coding: utf-8 -*-
"""
PDF Toolkit cx_Freeze 設定檔
用於建置 Windows MSI 安裝檔
"""

import sys
import os
from cx_Freeze import setup, Executable

# 應用程式資訊
APP_NAME = "PDFToolkit"
VERSION = "4.2.1"
DESCRIPTION = "Complete PDF Solution - Merge, Sign, Split, Compress & Watermark"
AUTHOR = ""
COMPANY = "PDF Tools Inc."

# 建置選項  
build_options = {
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
}

# MSI 選項
bdist_msi_options = {
    "upgrade_code": "{A1234567-1234-1234-1234-123456789ABC}",
    "product_code": "{4DFF20AF-EAB1-4B95-9F52-820DA874DB18}",
    "add_to_path": False,
    "initial_target_dir": r"[LocalAppDataFolder]\Programs\PDFToolkit",
    "install_icon": "icon.ico" if os.path.exists("icon.ico") else None,
    "summary_data": {
        "author": AUTHOR,
        "comments": DESCRIPTION,
        "keywords": "PDF;Tools;Merge;Split;Sign"
    },
    "all_users": False,
    "data": {
        "CustomAction": [
            ("PostInstallSetup", 18, "TARGETDIR", "[TARGETDIR]silent_setup.bat")
        ],
        "InstallExecuteSequence": [
            ("PostInstallSetup", None, "NOT Installed")
        ]
    }
}

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
    options={
        "build_exe": build_options,
        "bdist_msi": bdist_msi_options
    },
    executables=[executable]
)
