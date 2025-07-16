#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Toolkit 捷徑創建工具
提供圖形界面讓用戶選擇是否創建桌面和開始功能表捷徑
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import threading

def create_shortcuts(desktop=True, start_menu=True):
    """創建桌面和開始功能表捷徑"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        # 獲取安裝路徑
        import os
        username = os.getenv('USERNAME')
        install_path = rf"C:\Users\{username}\AppData\Local\Programs\PDFToolkit"
        exe_path = os.path.join(install_path, "PDF_Toolkit.exe")
        
        if not os.path.exists(exe_path):
            return False, f"找不到執行檔：{exe_path}"
        
        shell = Dispatch('WScript.Shell')
        created = []
        
        # 創建桌面捷徑
        if desktop:
            try:
                desktop_path = winshell.desktop()
                desktop_shortcut = os.path.join(desktop_path, "PDF Toolkit.lnk")
                
                shortcut = shell.CreateShortCut(desktop_shortcut)
                shortcut.Targetpath = exe_path
                shortcut.WorkingDirectory = install_path
                shortcut.Description = "PDF Toolkit - Complete PDF Solution"
                if os.path.exists(os.path.join(install_path, "icon.ico")):
                    shortcut.IconLocation = os.path.join(install_path, "icon.ico")
                shortcut.save()
                
                created.append("桌面捷徑")
            except Exception as e:
                return False, f"創建桌面捷徑失敗：{e}"
        
        # 創建開始功能表捷徑
        if start_menu:
            try:
                start_menu_path = winshell.start_menu()
                start_shortcut = os.path.join(start_menu_path, "PDF Toolkit.lnk")
                
                shortcut2 = shell.CreateShortCut(start_shortcut)
                shortcut2.Targetpath = exe_path
                shortcut2.WorkingDirectory = install_path
                shortcut2.Description = "PDF Toolkit - Complete PDF Solution"
                if os.path.exists(os.path.join(install_path, "icon.ico")):
                    shortcut2.IconLocation = os.path.join(install_path, "icon.ico")
                shortcut2.save()
                
                created.append("開始功能表捷徑")
            except Exception as e:
                return False, f"創建開始功能表捷徑失敗：{e}"
        
        return True, f"成功創建：{', '.join(created)}"
        
    except ImportError:
        return False, "缺少必要的模組 (winshell, pywin32)"
    except Exception as e:
        return False, f"創建捷徑失敗：{e}"

class ShortcutDialog:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDF Toolkit - 捷徑設定")
        self.root.geometry("400x250")
        self.root.resizable(False, False)
        
        # 設定視窗置中
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (250 // 2)
        self.root.geometry(f"400x250+{x}+{y}")
        
        self.setup_ui()
        
    def setup_ui(self):
        # 標題
        title_label = tk.Label(
            self.root, 
            text="PDF Toolkit 安裝完成！", 
            font=("Microsoft YaHei", 14, "bold"),
            fg="#2c3e50"
        )
        title_label.pack(pady=20)
        
        # 說明文字
        desc_label = tk.Label(
            self.root,
            text="您想要在哪裡創建程式捷徑？",
            font=("Microsoft YaHei", 10),
            fg="#34495e"
        )
        desc_label.pack(pady=10)
        
        # 選項框架
        options_frame = tk.Frame(self.root)
        options_frame.pack(pady=20)
        
        # 桌面捷徑選項
        self.desktop_var = tk.BooleanVar(value=True)
        desktop_cb = tk.Checkbutton(
            options_frame,
            text="🖥️  桌面捷徑",
            variable=self.desktop_var,
            font=("Microsoft YaHei", 10)
        )
        desktop_cb.pack(anchor="w", pady=5)
        
        # 開始功能表選項
        self.start_menu_var = tk.BooleanVar(value=True)
        start_menu_cb = tk.Checkbutton(
            options_frame,
            text="📋  開始功能表",
            variable=self.start_menu_var,
            font=("Microsoft YaHei", 10)
        )
        start_menu_cb.pack(anchor="w", pady=5)
        
        # 按鈕框架
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        # 創建按鈕
        create_btn = tk.Button(
            button_frame,
            text="創建捷徑",
            command=self.create_shortcuts,
            bg="#3498db",
            fg="white",
            font=("Microsoft YaHei", 10),
            padx=20,
            pady=8
        )
        create_btn.pack(side="left", padx=10)
        
        # 跳過按鈕
        skip_btn = tk.Button(
            button_frame,
            text="跳過",
            command=self.skip,
            bg="#95a5a6",
            fg="white",
            font=("Microsoft YaHei", 10),
            padx=20,
            pady=8
        )
        skip_btn.pack(side="left", padx=10)
        
    def create_shortcuts(self):
        """創建選中的捷徑"""
        desktop = self.desktop_var.get()
        start_menu = self.start_menu_var.get()
        
        if not desktop and not start_menu:
            messagebox.showwarning("提示", "請至少選擇一個捷徑選項")
            return
        
        # 顯示進度
        progress_window = tk.Toplevel(self.root)
        progress_window.title("創建中...")
        progress_window.geometry("300x100")
        progress_window.resizable(False, False)
        
        # 置中
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (300 // 2)
        y = (progress_window.winfo_screenheight() // 2) - (100 // 2)
        progress_window.geometry(f"300x100+{x}+{y}")
        
        progress_label = tk.Label(progress_window, text="正在創建捷徑...")
        progress_label.pack(pady=30)
        
        def create_in_thread():
            success, message = create_shortcuts(desktop, start_menu)
            progress_window.destroy()
            
            if success:
                messagebox.showinfo("成功", f"✅ {message}")
            else:
                messagebox.showerror("錯誤", f"❌ {message}")
            
            self.root.quit()
        
        threading.Thread(target=create_in_thread, daemon=True).start()
        
    def skip(self):
        """跳過創建捷徑"""
        self.root.quit()
    
    def run(self):
        """運行對話框"""
        self.root.mainloop()

if __name__ == "__main__":
    # 檢查是否有命令行參數
    if len(sys.argv) > 1 and sys.argv[1] == "--silent":
        # 靜默模式，創建所有捷徑
        success, message = create_shortcuts(True, True)
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            sys.exit(1)
    else:
        # 圖形界面模式
        try:
            dialog = ShortcutDialog()
            dialog.run()
        except Exception as e:
            # 如果圖形界面失敗，詢問是否使用命令行模式
            print(f"圖形界面啟動失敗：{e}")
            response = input("是否要創建桌面和開始功能表捷徑？(y/N): ").lower()
            if response in ['y', 'yes']:
                success, message = create_shortcuts(True, True)
                if success:
                    print(f"✅ {message}")
                else:
                    print(f"❌ {message}")
                    sys.exit(1)