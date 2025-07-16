#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Toolkit 自動啟動設定
創建一個一次性的自動啟動項目，讓程式在安裝後自動執行首次設定
"""

import os
import sys
import winreg
import subprocess

def create_oneshot_autostart():
    """創建一次性自動啟動項目"""
    try:
        # 獲取當前執行檔路徑
        if getattr(sys, 'frozen', False):
            current_exe = sys.executable
        else:
            current_exe = os.path.abspath(__file__)
        
        # 獲取 PDF Toolkit 執行檔路徑
        current_dir = os.path.dirname(current_exe)
        pdf_toolkit_exe = os.path.join(current_dir, "PDF_Toolkit.exe")
        
        if not os.path.exists(pdf_toolkit_exe):
            print(f"找不到 PDF Toolkit 執行檔：{pdf_toolkit_exe}")
            return False
        
        # 創建自動啟動項目
        autostart_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, autostart_key, 0, winreg.KEY_SET_VALUE) as key:
            # 創建一個一次性啟動項目
            winreg.SetValueEx(key, "PDFToolkit_FirstSetup", 0, winreg.REG_SZ, 
                            f'"{pdf_toolkit_exe}" --first-setup')
        
        print("✅ 已創建一次性自動啟動項目")
        print("📝 系統將在下次重新啟動時自動執行首次設定")
        return True
        
    except Exception as e:
        print(f"❌ 創建自動啟動項目失敗：{e}")
        return False

def remove_oneshot_autostart():
    """移除一次性自動啟動項目"""
    try:
        autostart_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, autostart_key, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, "PDFToolkit_FirstSetup")
                print("✅ 已移除一次性自動啟動項目")
            except FileNotFoundError:
                print("📝 自動啟動項目不存在")
        
        return True
        
    except Exception as e:
        print(f"❌ 移除自動啟動項目失敗：{e}")
        return False

def main():
    """主函數"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--remove":
            remove_oneshot_autostart()
        elif sys.argv[1] == "--create":
            create_oneshot_autostart()
        else:
            print("用法：")
            print("  create_autostart.py --create    # 創建自動啟動")
            print("  create_autostart.py --remove    # 移除自動啟動")
    else:
        print("PDF Toolkit 自動啟動設定工具")
        print("=" * 40)
        
        choice = input("選擇操作 (1:創建自動啟動, 2:移除自動啟動): ")
        
        if choice == "1":
            create_oneshot_autostart()
        elif choice == "2":
            remove_oneshot_autostart()
        else:
            print("無效的選擇")

if __name__ == "__main__":
    main()