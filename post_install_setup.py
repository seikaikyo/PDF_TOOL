#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Toolkit 安裝後自動設定腳本
在 MSI 安裝完成後自動執行，完成應用程式註冊和捷徑創建
"""

import os
import sys
import subprocess
import time
import winreg
import tkinter as tk
from tkinter import messagebox
import traceback

def get_install_path():
    """獲取安裝路徑"""
    try:
        # 從環境變數或參數獲取安裝路徑
        install_path = os.getenv('MSIEXEC_INSTALL_PATH')
        if install_path and os.path.exists(install_path):
            return install_path
        
        # 從命令列參數獲取
        if len(sys.argv) > 1:
            install_path = sys.argv[1]
            if os.path.exists(install_path):
                return install_path
        
        # 嘗試從當前目錄獲取
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(os.path.join(current_dir, "PDF_Toolkit.exe")):
            return current_dir
        
        # 嘗試從用戶AppData目錄獲取
        username = os.getenv('USERNAME')
        appdata_path = rf"C:\Users\{username}\AppData\Local\Programs\PDFToolkit"
        if os.path.exists(appdata_path):
            return appdata_path
        
        return None
        
    except Exception as e:
        print(f"獲取安裝路徑失敗：{e}")
        return None

def register_application(install_path):
    """註冊應用程式到系統"""
    try:
        exe_path = os.path.join(install_path, "PDF_Toolkit.exe")
        if not os.path.exists(exe_path):
            print(f"找不到執行檔：{exe_path}")
            return False
        
        # 註冊應用程式路徑
        app_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\PDF_Toolkit.exe"
        
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, app_key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, exe_path)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, install_path)
        
        print("✅ 應用程式路徑註冊完成")
        
        # 註冊卸載資訊
        uninstall_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\PDFToolkit"
        
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, uninstall_key_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "PDF Toolkit")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "4.2.1")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "PDF Toolkit")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_path)
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{exe_path}" --uninstall')
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, exe_path)
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        
        print("✅ 卸載資訊註冊完成")
        return True
        
    except Exception as e:
        print(f"❌ 註冊應用程式失敗：{e}")
        return False

def create_shortcuts(install_path):
    """創建桌面和開始功能表捷徑"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        exe_path = os.path.join(install_path, "PDF_Toolkit.exe")
        if not os.path.exists(exe_path):
            print(f"找不到執行檔：{exe_path}")
            return False
        
        shell = Dispatch('WScript.Shell')
        
        # 創建開始功能表捷徑
        start_menu = winshell.start_menu()
        start_shortcut = os.path.join(start_menu, "PDF Toolkit.lnk")
        
        shortcut = shell.CreateShortCut(start_shortcut)
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = install_path
        shortcut.Description = "PDF Toolkit - Complete PDF Solution"
        
        # 設定圖示
        icon_path = os.path.join(install_path, "icon.ico")
        if os.path.exists(icon_path):
            shortcut.IconLocation = icon_path
        
        shortcut.save()
        print("✅ 開始功能表捷徑已創建")
        
        return True
        
    except Exception as e:
        print(f"❌ 創建捷徑失敗：{e}")
        return False

def ask_desktop_shortcut(install_path, silent=False):
    """詢問用戶是否創建桌面捷徑"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        # 檢查桌面是否已有捷徑
        desktop = winshell.desktop()
        desktop_shortcut = os.path.join(desktop, "PDF Toolkit.lnk")
        
        if os.path.exists(desktop_shortcut):
            return True
        
        # 靜默模式：不創建桌面捷徑，讓程式自己處理
        if silent:
            return True
        
        # 創建簡單的對話框
        root = tk.Tk()
        root.withdraw()  # 隱藏主視窗
        
        result = messagebox.askyesno(
            "PDF Toolkit 安裝完成",
            "🎉 PDF Toolkit 已成功安裝！\n\n" +
            "程式已經可以在開始功能表中找到。\n" +
            "是否要在桌面創建捷徑？",
            icon='question'
        )
        
        root.destroy()
        
        if result:
            exe_path = os.path.join(install_path, "PDF_Toolkit.exe")
            shell = Dispatch('WScript.Shell')
            
            shortcut = shell.CreateShortCut(desktop_shortcut)
            shortcut.Targetpath = exe_path
            shortcut.WorkingDirectory = install_path
            shortcut.Description = "PDF Toolkit - Complete PDF Solution"
            
            # 設定圖示
            icon_path = os.path.join(install_path, "icon.ico")
            if os.path.exists(icon_path):
                shortcut.IconLocation = icon_path
            
            shortcut.save()
            print("✅ 桌面捷徑已創建")
            
            # 顯示完成訊息
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(
                "設定完成",
                "✅ PDF Toolkit 設定完成！\n\n" +
                "現在您可以：\n" +
                "• 從桌面捷徑啟動\n" +
                "• 在開始功能表搜尋 'PDF Toolkit'\n" +
                "• 在設定→應用程式與功能中找到程式"
            )
            root.destroy()
        
        return True
        
    except Exception as e:
        print(f"❌ 桌面捷徑處理失敗：{e}")
        return False

def main():
    """主要安裝後設定流程"""
    # 檢查是否為靜默模式
    silent = "--silent" in sys.argv
    
    if not silent:
        print("PDF Toolkit 安裝後設定")
        print("=" * 40)
    
    # 等待安裝完成
    time.sleep(1)
    
    # 獲取安裝路徑
    install_path = get_install_path()
    if not install_path:
        if not silent:
            print("❌ 無法確定安裝路徑")
        return False
    
    if not silent:
        print(f"📁 安裝路徑：{install_path}")
    
    success_count = 0
    total_tasks = 3
    
    # 1. 註冊應用程式
    if not silent:
        print("\n1. 註冊應用程式到系統...")
    if register_application(install_path):
        success_count += 1
    
    # 2. 創建開始功能表捷徑
    if not silent:
        print("\n2. 創建開始功能表捷徑...")
    if create_shortcuts(install_path):
        success_count += 1
    
    # 3. 詢問桌面捷徑
    if not silent:
        print("\n3. 設定桌面捷徑...")
    if ask_desktop_shortcut(install_path, silent):
        success_count += 1
    
    if not silent:
        print(f"\n✅ 設定完成 ({success_count}/{total_tasks} 項目成功)")
    
    if success_count == total_tasks:
        if not silent:
            print("🎉 PDF Toolkit 已完全設定完成！")
        return True
    else:
        if not silent:
            print("⚠️ 部分設定可能未成功，程式仍可正常使用")
        return False

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 安裝後設定失敗：{e}")
        traceback.print_exc()
        
        # 顯示錯誤訊息給用戶
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "安裝設定", 
                f"自動設定遇到問題：{e}\n\n" +
                "程式已安裝完成，但可能需要手動創建捷徑。\n" +
                "您可以在開始功能表搜尋程式位置。"
            )
            root.destroy()
        except:
            pass
    
    # 等待用戶確認（如果是手動執行）
    if len(sys.argv) <= 1:
        input("\n按 Enter 鍵結束...")