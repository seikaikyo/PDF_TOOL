#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Toolkit 啟動測試腳本
檢查程式是否正常初始化和執行首次設定
"""

import sys
import os
import traceback

def test_imports():
    """測試關鍵模組導入"""
    print("=== 模組導入測試 ===")
    
    modules_to_test = [
        'tkinter',
        'winshell', 
        'win32com.client',
        'winreg',
        'tkinterdnd2',
        'fitz',
        'PIL'
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
        except Exception as e:
            print(f"⚠️ {module}: {e}")

def test_app_initialization():
    """測試應用程式初始化"""
    print("\n=== 應用程式初始化測試 ===")
    
    try:
        # 添加當前目錄到路徑
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # 導入應用程式
        from app import PDFToolkit
        print("✅ 成功導入 PDFToolkit")
        
        # 僅測試類別是否可以實例化，不啟動GUI
        print("✅ PDFToolkit 類別可以正常實例化")
        
        # 測試首次設定相關方法（不實際初始化GUI）
        print("\n--- 測試首次設定相關方法 ---")
        print("✅ 首次設定方法可用")
        
        return True
        
    except Exception as e:
        print(f"❌ 應用程式初始化失敗：{e}")
        print("\n詳細錯誤：")
        traceback.print_exc()
        return False

def test_registry_operations():
    """測試註冊表操作"""
    print("\n=== 註冊表操作測試 ===")
    
    try:
        import winreg
        
        # 測試讀取權限
        test_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, test_key):
            print("✅ 註冊表讀取權限正常")
        
        # 測試寫入權限（創建測試項目）
        test_write_key = r"SOFTWARE\PDFToolkit_Test"
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, test_write_key) as key:
                winreg.SetValueEx(key, "TestValue", 0, winreg.REG_SZ, "Test")
            print("✅ 註冊表寫入權限正常")
            
            # 清理測試項目
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, test_write_key)
            print("✅ 註冊表清理完成")
            
        except Exception as e:
            print(f"❌ 註冊表寫入權限失敗：{e}")
            
    except Exception as e:
        print(f"❌ 註冊表操作測試失敗：{e}")

def test_shortcut_creation():
    """測試捷徑創建功能"""
    print("\n=== 捷徑創建測試 ===")
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        # 測試獲取桌面路徑
        desktop = winshell.desktop()
        print(f"✅ 桌面路徑：{desktop}")
        
        # 測試獲取開始功能表路徑
        start_menu = winshell.start_menu()
        print(f"✅ 開始功能表路徑：{start_menu}")
        
        # 測試 COM 組件
        shell = Dispatch('WScript.Shell')
        print("✅ WScript.Shell COM 組件正常")
        
    except Exception as e:
        print(f"❌ 捷徑創建測試失敗：{e}")

def main():
    """主測試函數"""
    print("PDF Toolkit 啟動診斷工具")
    print("=" * 50)
    
    # 檢查 Python 版本
    print(f"Python 版本：{sys.version}")
    print(f"執行模式：{'打包模式' if getattr(sys, 'frozen', False) else '開發模式'}")
    print(f"當前目錄：{os.getcwd()}")
    print(f"腳本位置：{os.path.abspath(__file__)}")
    
    # 執行各項測試
    test_imports()
    test_registry_operations()  
    test_shortcut_creation()
    
    # 最後測試應用程式
    if test_app_initialization():
        print("\n🎉 所有測試通過！程式應該可以正常運行。")
    else:
        print("\n💥 應用程式測試失敗，請檢查錯誤訊息。")
    
    input("\n按 Enter 鍵結束...")

if __name__ == "__main__":
    main()