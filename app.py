import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import fitz  # PyMuPDF
from PIL import Image, ImageTk, ImageDraw
try:
    from pyfiglet import figlet_format
    PYFIGLET_AVAILABLE = True
except ImportError:
    PYFIGLET_AVAILABLE = False

    def figlet_format(text, font=None):
        # 後備方案：使用簡單的ASCII藝術
        return f"""
    ┌─────────────────────────────────────┐
    │           {text}           │
    └─────────────────────────────────────┘
        """


from datetime import datetime
import threading
import traceback
import logging
import urllib.request
import urllib.parse
import json
import webbrowser
import ssl
from packaging import version

# 應用程式版本信息
APP_VERSION = "4.2.1"

# 多源更新配置 - 支援內網 GitLab 和外網 GitHub
UPDATE_SOURCES = {
    'gitlab': {
        'name': 'Internal GitLab',
        'api_url': "https://gitlab.example.com/api/v4/projects/team%2Fpdf_tool/releases?per_page=1",
        'download_url': "https://gitlab.example.com/team/pdf_tool/-/releases",
        'token': os.getenv('GITLAB_TOKEN'),
        'priority': 1  # 優先級：1=最高
    },
    'github': {
        'name': 'GitHub Public',
        'api_url': "https://api.github.com/repos/seikaikyo/PDF_TOOL/releases/latest",
        'download_url': "https://github.com/seikaikyo/PDF_TOOL/releases",
        'token': None,  # GitHub public repo 不需要 token
        'priority': 2  # 備用源
    }
}


class UpdateChecker:
    """智能多源版本更新檢查器"""

    def __init__(self, current_version, update_sources):
        self.current_version = current_version
        self.update_sources = update_sources
        self.last_successful_source = None

    def check_for_updates(self, callback=None):
        """智能多源檢查更新（在背景執行緒中）"""
        def _check():
            # 根據優先級排序更新源
            sorted_sources = sorted(self.update_sources.items(), 
                                  key=lambda x: x[1]['priority'])
            
            # 如果上次有成功的源，優先嘗試
            if self.last_successful_source and self.last_successful_source in self.update_sources:
                sorted_sources.insert(0, (self.last_successful_source, 
                                         self.update_sources[self.last_successful_source]))
            
            update_info = None
            
            for source_name, source_config in sorted_sources:
                try:
                    print(f"嘗試檢查更新源：{source_config['name']}")
                    result = self._check_single_source(source_name, source_config)
                    
                    if not result.get('error', False):
                        # 成功獲取更新信息
                        self.last_successful_source = source_name
                        result['source'] = source_config['name']
                        update_info = result
                        break
                        
                except Exception as e:
                    print(f"檢查 {source_config['name']} 失敗：{e}")
                    continue
            
            # 如果所有源都失敗
            if update_info is None:
                update_info = {
                    'error': True,
                    'message': '所有更新源都無法連接，請檢查網絡連接或稍後再試。\n'
                              '內網用戶請確認可以訪問 GitLab，\n'
                              '外網用戶請確認可以訪問 GitHub。'
                }
            
            if callback:
                callback(update_info)
        
        # 在新執行緒中執行檢查
        thread = threading.Thread(target=_check)
        thread.daemon = True
        thread.start()
    
    def _check_single_source(self, source_name, source_config):
        """檢查單個更新源"""
        try:
            # 設置請求頭
            request = urllib.request.Request(source_config['api_url'])
            request.add_header('User-Agent', 'PDF-Toolkit-App/4.2.0')
            
            # 如果有 token，添加認證頭
            if source_config.get('token'):
                if source_name == 'gitlab':
                    request.add_header('PRIVATE-TOKEN', source_config['token'])
                elif source_name == 'github':
                    request.add_header('Authorization', f"token {source_config['token']}")
            
            # 設置 SSL 上下文
            ssl_context = ssl.create_default_context()
            if source_name == 'gitlab':
                # 內部 GitLab 可能需要跳過 SSL 驗證
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            # 發送請求
            with urllib.request.urlopen(request, timeout=10, context=ssl_context) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # 根據源類型解析數據
            if source_name == 'gitlab':
                return self._parse_gitlab_response(data, source_config)
            elif source_name == 'github':
                return self._parse_github_response(data, source_config)
            else:
                return {'error': True, 'message': f'未知的更新源類型：{source_name}'}
                
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            if isinstance(e, urllib.error.HTTPError):
                if e.code == 404:
                    return {'error': True, 'message': f'{source_config["name"]} 未找到發布版本'}
                else:
                    return {'error': True, 'message': f'{source_config["name"]} API 錯誤 {e.code}'}
            else:
                return {'error': True, 'message': f'{source_config["name"]} 連接失敗：{str(e)}'}
    
    def _parse_gitlab_response(self, data, source_config):
        """解析 GitLab API 響應"""
        if isinstance(data, list) and len(data) > 0:
            latest_release = data[0]  # GitLab 按時間降序排列
            latest_version = latest_release["tag_name"].lstrip('v')
            
            if version.parse(latest_version) > version.parse(self.current_version):
                return {
                    'available': True,
                    'version': latest_version,
                    'title': latest_release.get("name", f"v{latest_version}"),
                    'description': latest_release.get("description", "新版本可用"),
                    'download_url': source_config['download_url'],
                    'date': latest_release.get("released_at", "")
                }
            else:
                return {'available': False, 'message': '您已經使用最新版本！'}
        else:
            return {'error': True, 'message': "GitLab 暫時沒有發布版本"}
    
    def _parse_github_response(self, data, source_config):
        """解析 GitHub API 響應"""
        if isinstance(data, dict) and 'tag_name' in data:
            latest_version = data["tag_name"].lstrip('v')
            
            if version.parse(latest_version) > version.parse(self.current_version):
                return {
                    'available': True,
                    'version': latest_version,
                    'title': data.get("name", f"v{latest_version}"),
                    'description': data.get("body", "新版本可用"),
                    'download_url': source_config['download_url'],
                    'date': data.get("published_at", "")
                }
            else:
                return {'available': False, 'message': '您已經使用最新版本！'}
        else:
            return {'error': True, 'message': "GitHub 暫時沒有發布版本"}


class UpdateDialog(tk.Toplevel):
    """更新對話框"""

    def __init__(self, parent, update_info):
        super().__init__(parent)
        self.parent = parent
        self.update_info = update_info
        self.setup_dialog()

    def setup_dialog(self):
        self.title("發現新版本")
        self.geometry("500x400")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")

        # 置中顯示
        self.transient(self.parent)
        self.grab_set()

        # 主框架
        main_frame = tk.Frame(self, bg="#f0f0f0", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # 標題
        title_label = tk.Label(main_frame,
                               text="🎉 發現新版本！",
                               font=("Microsoft YaHei", 16, "bold"),
                               bg="#f0f0f0",
                               fg="#2c3e50")
        title_label.pack(pady=(0, 10))

        # 版本信息
        version_frame = tk.Frame(main_frame, bg="#f0f0f0")
        version_frame.pack(fill="x", pady=(0, 15))

        current_label = tk.Label(version_frame,
                                 text=f"目前版本：v{APP_VERSION}",
                                 font=("Microsoft YaHei", 11),
                                 bg="#f0f0f0",
                                 fg="#7f8c8d")
        current_label.pack(anchor="w")

        latest_label = tk.Label(version_frame,
                                text=f"最新版本：v{self.update_info['version']}",
                                font=("Microsoft YaHei", 11, "bold"),
                                bg="#f0f0f0",
                                fg="#27ae60")
        latest_label.pack(anchor="w")

        # 更新說明
        tk.Label(main_frame,
                 text="更新內容：",
                 font=("Microsoft YaHei", 12, "bold"),
                 bg="#f0f0f0",
                 fg="#2c3e50").pack(anchor="w", pady=(10, 5))

        # 創建滾動文本框顯示更新說明
        text_frame = tk.Frame(main_frame, bg="#f0f0f0")
        text_frame.pack(fill="both", expand=True, pady=(0, 20))

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(text_frame,
                              height=8,
                              wrap="word",
                              font=("Microsoft YaHei", 10),
                              yscrollcommand=scrollbar.set,
                              bg="white",
                              fg="#2c3e50",
                              relief="solid",
                              borderwidth=1)
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        # 插入更新說明
        text_widget.insert("1.0", self.update_info['description'])
        text_widget.config(state="disabled")

        # 按鈕框架
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(fill="x")

        # 下載更新按鈕
        download_btn = tk.Button(button_frame,
                                 text="📥 下載更新",
                                 command=self.download_update,
                                 bg="#3498db",
                                 fg="white",
                                 font=("Microsoft YaHei", 11, "bold"),
                                 width=12,
                                 relief="flat",
                                 cursor="hand2")
        download_btn.pack(side="left", padx=(0, 10))

        # 稍後提醒按鈕
        later_btn = tk.Button(button_frame,
                              text="稍後提醒",
                              command=self.remind_later,
                              bg="#95a5a6",
                              fg="white",
                              font=("Microsoft YaHei", 11),
                              width=10,
                              relief="flat",
                              cursor="hand2")
        later_btn.pack(side="left", padx=(0, 10))

        # 跳過此版本按鈕
        skip_btn = tk.Button(button_frame,
                             text="跳過此版本",
                             command=self.skip_version,
                             bg="#e74c3c",
                             fg="white",
                             font=("Microsoft YaHei", 11),
                             width=12,
                             relief="flat",
                             cursor="hand2")
        skip_btn.pack(side="right")

    def download_update(self):
        """開啟下載頁面"""
        try:
            webbrowser.open(self.update_info['download_url'])
            messagebox.showinfo("提示", "已開啟下載頁面，請下載最新版本後替換現有檔案。")
        except Exception as e:
            messagebox.showerror("錯誤", f"無法開啟下載頁面：{str(e)}")
        self.destroy()

    def remind_later(self):
        """稍後提醒"""
        self.destroy()

    def skip_version(self):
        """跳過此版本"""
        # 在實際應用中，這裡可以保存跳過的版本號到設置文件
        messagebox.showinfo("提示", f"已跳過版本 v{self.update_info['version']}")
        self.destroy()


class TextInsertDialog(tk.Toplevel):
    """文字插入對話框"""

    def __init__(self, parent, colors):
        super().__init__(parent)
        self.parent = parent
        self.colors = colors
        self.result = None

        self._setup_dialog()

    def _setup_dialog(self):
        """設置對話框"""
        self.title("插入文字")
        self.geometry("400x300")
        self.resizable(False, False)
        self.configure(bg=self.colors['bg_main'])

        # 置中顯示
        self.transient(self.parent)
        self.grab_set()

        # 主框架
        main_frame = tk.Frame(self,
                              bg=self.colors['bg_main'],
                              padx=20,
                              pady=20)
        main_frame.pack(fill="both", expand=True)

        # 文字輸入區域
        tk.Label(main_frame,
                 text="輸入文字：",
                 bg=self.colors['bg_main'],
                 fg="black",
                 font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")

        self.text_entry = tk.Text(main_frame,
                                  height=3,
                                  font=("Microsoft YaHei", 11))
        self.text_entry.pack(fill="x", pady=(5, 15))
        self.text_entry.focus_set()

        # 字體設置區域
        font_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        font_frame.pack(fill="x", pady=(0, 15))

        # 字體選擇
        tk.Label(font_frame,
                 text="字體：",
                 bg=self.colors['bg_main'],
                 fg="black",
                 font=("Microsoft YaHei", 10)).pack(side="left")

        self.font_var = tk.StringVar(value="Microsoft YaHei")
        font_combo = ttk.Combobox(
            font_frame,
            textvariable=self.font_var,
            values=["Microsoft YaHei", "SimSun", "Arial"],
            state="readonly",
            width=15)
        font_combo.pack(side="left", padx=(5, 20))

        # 字體大小
        tk.Label(font_frame,
                 text="大小：",
                 bg=self.colors['bg_main'],
                 fg="black",
                 font=("Microsoft YaHei", 10)).pack(side="left")

        self.size_var = tk.StringVar(value="16")
        size_combo = ttk.Combobox(
            font_frame,
            textvariable=self.size_var,
            values=["12", "14", "16", "18", "20", "24", "28", "32"],
            state="readonly",
            width=8)
        size_combo.pack(side="left", padx=5)

        # 顏色選擇區域
        color_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        color_frame.pack(fill="x", pady=(0, 20))

        tk.Label(color_frame,
                 text="顏色：",
                 bg=self.colors['bg_main'],
                 fg="black",
                 font=("Microsoft YaHei", 10)).pack(side="left")

        self.color_var = tk.StringVar(value="black")
        colors_list = [("黑色", "black"), ("藍色", "blue"), ("紅色", "red"),
                       ("綠色", "green"), ("紫色", "purple")]

        for i, (color_name, color_value) in enumerate(colors_list):
            tk.Radiobutton(color_frame,
                           text=color_name,
                           variable=self.color_var,
                           value=color_value,
                           bg=self.colors['bg_main'],
                           fg="black",
                           font=("Microsoft YaHei", 9)).pack(side="left",
                                                             padx=5)

        # 按鈕區域
        btn_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        btn_frame.pack(fill="x")

        tk.Button(btn_frame,
                  text="確定",
                  command=self._confirm,
                  bg=self.colors['success'],
                  fg="white",
                  font=("Microsoft YaHei", 10, "bold"),
                  width=10).pack(side="right", padx=(5, 0))

        tk.Button(btn_frame,
                  text="取消",
                  command=self._cancel,
                  bg=self.colors['danger'],
                  fg="white",
                  font=("Microsoft YaHei", 10, "bold"),
                  width=10).pack(side="right")

        # 綁定Enter鍵
        self.bind('<Return>', lambda e: self._confirm())
        self.bind('<Escape>', lambda e: self._cancel())

    def _confirm(self):
        """確認插入"""
        text_content = self.text_entry.get("1.0", tk.END).strip()
        if text_content:
            self.result = {
                'text': text_content,
                'font_name': self.font_var.get(),
                'font_size': int(self.size_var.get()),
                'color': self.color_var.get()
            }
        self.destroy()

    def _cancel(self):
        """取消插入"""
        self.result = None
        self.destroy()


class PDFSplitDialog(tk.Toplevel):
    """PDF拆分對話框"""

    def __init__(self, parent, pdf_path, colors):
        super().__init__(parent)
        self.parent = parent
        self.pdf_path = pdf_path
        self.colors = colors
        self.pdf_doc = None
        # 獲取主應用程式的錯誤日誌方法
        self.main_app = None
        widget = parent
        while widget and not hasattr(widget, '_log_error'):
            widget = widget.master
        self.main_app = widget

        if self._load_pdf():
            self._setup_dialog()

    def _load_pdf(self):
        """載入PDF文件"""
        try:
            self.pdf_doc = fitz.open(self.pdf_path)
            self.total_pages = len(self.pdf_doc)
            return True
        except Exception as e:
            messagebox.showerror("錯誤", f"無法載入PDF檔案：{str(e)}")
            self.total_pages = 0
            if hasattr(self, 'pdf_doc') and self.pdf_doc:
                self.pdf_doc.close()
            self.destroy()
            return False

    def _setup_dialog(self):
        """設置對話框"""
        self.title("PDF 拆分工具")
        self.geometry("500x400")
        self.resizable(False, False)
        self.configure(bg=self.colors['bg_main'])

        # 置中顯示
        self.transient(self.parent)
        self.grab_set()

        # 主框架
        main_frame = tk.Frame(self,
                              bg=self.colors['bg_main'],
                              padx=20,
                              pady=20)
        main_frame.pack(fill="both", expand=True)

        # 標題資訊
        info_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        info_frame.pack(fill="x", pady=(0, 20))

        tk.Label(info_frame,
                 text=f"檔案：{os.path.basename(self.pdf_path)}",
                 bg=self.colors['bg_main'],
                 fg="black",
                 font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")

        tk.Label(info_frame,
                 text=f"總頁數：{self.total_pages} 頁",
                 bg=self.colors['bg_main'],
                 fg="black",
                 font=("Microsoft YaHei", 10)).pack(anchor="w")

        # 拆分選項
        options_frame = tk.LabelFrame(main_frame,
                                      text="拆分選項",
                                      bg=self.colors['bg_main'],
                                      fg="black",
                                      font=("Microsoft YaHei", 10, "bold"))
        options_frame.pack(fill="x", pady=(0, 20))

        self.split_type = tk.StringVar(value="pages")

        # 按頁數拆分
        pages_frame = tk.Frame(options_frame, bg=self.colors['bg_main'])
        pages_frame.pack(fill="x", padx=10, pady=5)

        tk.Radiobutton(pages_frame,
                       text="按頁數拆分：每",
                       variable=self.split_type,
                       value="pages",
                       bg=self.colors['bg_main'],
                       fg="black").pack(side="left")

        self.pages_per_file = tk.StringVar(value="1")
        pages_entry = tk.Entry(pages_frame,
                               textvariable=self.pages_per_file,
                               width=5)
        pages_entry.pack(side="left", padx=5)

        tk.Label(pages_frame,
                 text="頁為一個檔案",
                 bg=self.colors['bg_main'],
                 fg="black").pack(side="left")

        # 按範圍拆分
        range_frame = tk.Frame(options_frame, bg=self.colors['bg_main'])
        range_frame.pack(fill="x", padx=10, pady=5)

        tk.Radiobutton(range_frame,
                       text="按範圍拆分：",
                       variable=self.split_type,
                       value="range",
                       bg=self.colors['bg_main'],
                       fg="black").pack(side="left")

        tk.Label(range_frame, text="從第", bg=self.colors['bg_main'],
                 fg="black").pack(side="left", padx=(10, 5))

        self.start_page = tk.StringVar(value="1")
        start_entry = tk.Entry(range_frame,
                               textvariable=self.start_page,
                               width=5)
        start_entry.pack(side="left")

        tk.Label(range_frame,
                 text="頁到第",
                 bg=self.colors['bg_main'],
                 fg="black").pack(side="left", padx=5)

        self.end_page = tk.StringVar(value=str(self.total_pages))
        end_entry = tk.Entry(range_frame, textvariable=self.end_page, width=5)
        end_entry.pack(side="left")

        tk.Label(range_frame, text="頁", bg=self.colors['bg_main'],
                 fg="black").pack(side="left", padx=(5, 0))

        # 單頁提取
        single_frame = tk.Frame(options_frame, bg=self.colors['bg_main'])
        single_frame.pack(fill="x", padx=10, pady=5)

        tk.Radiobutton(single_frame,
                       text="提取單頁：第",
                       variable=self.split_type,
                       value="single",
                       bg=self.colors['bg_main'],
                       fg="black").pack(side="left")

        self.single_page = tk.StringVar(value="1")
        single_entry = tk.Entry(single_frame,
                                textvariable=self.single_page,
                                width=5)
        single_entry.pack(side="left", padx=5)

        tk.Label(single_frame, text="頁", bg=self.colors['bg_main'],
                 fg="black").pack(side="left")

        # 按鈕區域
        btn_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        btn_frame.pack(fill="x", pady=(20, 0))

        tk.Button(btn_frame,
                  text="開始拆分",
                  command=self._start_split,
                  bg=self.colors['success'],
                  fg="white",
                  font=("Microsoft YaHei", 10, "bold"),
                  width=12).pack(side="right", padx=(5, 0))

        tk.Button(btn_frame,
                  text="取消",
                  command=self.destroy,
                  bg=self.colors['danger'],
                  fg="white",
                  font=("Microsoft YaHei", 10, "bold"),
                  width=12).pack(side="right")

    def _start_split(self):
        """開始拆分PDF"""
        try:
            split_type = self.split_type.get()

            # 選擇輸出目錄
            output_dir = filedialog.askdirectory(title="選擇拆分檔案的儲存目錄")
            if not output_dir:
                return

            base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
            success_count = 0

            if split_type == "pages":
                # 按頁數拆分
                pages_per_file = int(self.pages_per_file.get())
                if pages_per_file <= 0:
                    messagebox.showerror("錯誤", "每個檔案的頁數必須大於0")
                    return

                current_page = 0
                file_index = 1

                while current_page < self.total_pages:
                    end_page = min(current_page + pages_per_file - 1,
                                   self.total_pages - 1)

                    output_path = os.path.join(
                        output_dir, f"{base_name}_part{file_index}.pdf")
                    new_doc = fitz.open()

                    for page_num in range(current_page, end_page + 1):
                        new_doc.insert_pdf(self.pdf_doc,
                                           from_page=page_num,
                                           to_page=page_num)

                    new_doc.save(output_path)
                    new_doc.close()

                    success_count += 1
                    current_page = end_page + 1
                    file_index += 1

            elif split_type == "range":
                # 按範圍拆分
                start = int(self.start_page.get()) - 1  # 轉為0-based索引
                end = int(self.end_page.get()) - 1

                if start < 0 or end >= self.total_pages or start > end:
                    messagebox.showerror(
                        "錯誤", f"頁面範圍無效，請輸入1到{self.total_pages}之間的頁數")
                    return

                output_path = os.path.join(
                    output_dir, f"{base_name}_pages{start+1}-{end+1}.pdf")
                new_doc = fitz.open()

                for page_num in range(start, end + 1):
                    new_doc.insert_pdf(self.pdf_doc,
                                       from_page=page_num,
                                       to_page=page_num)

                new_doc.save(output_path)
                new_doc.close()
                success_count = 1

            elif split_type == "single":
                # 提取單頁
                page_num = int(self.single_page.get()) - 1  # 轉為0-based索引

                if page_num < 0 or page_num >= self.total_pages:
                    messagebox.showerror("錯誤",
                                         f"頁數無效，請輸入1到{self.total_pages}之間的數字")
                    return

                output_path = os.path.join(
                    output_dir, f"{base_name}_page{page_num+1}.pdf")
                new_doc = fitz.open()
                new_doc.insert_pdf(self.pdf_doc,
                                   from_page=page_num,
                                   to_page=page_num)
                new_doc.save(output_path)
                new_doc.close()
                success_count = 1

            messagebox.showinfo(
                "完成",
                f"PDF拆分完成！\n成功創建了 {success_count} 個檔案\n儲存位置：{output_dir}")
            self.destroy()

        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的數字")
        except Exception as e:
            error_msg = f"拆分過程中發生錯誤：{str(e)}"
            if self.main_app:
                self.main_app._log_error(error_msg, e, "PDF拆分處理")
            messagebox.showerror("錯誤", error_msg)

    def destroy(self):
        """關閉對話框時清理資源"""
        if self.pdf_doc:
            self.pdf_doc.close()
        super().destroy()


class PDFCompressDialog(tk.Toplevel):
    """PDF壓縮對話框"""

    def __init__(self, parent, pdf_path, colors):
        super().__init__(parent)
        self.parent = parent
        self.pdf_path = pdf_path
        self.colors = colors
        self.pdf_doc = None
        # 獲取主應用程式的錯誤日誌方法
        self.main_app = None
        widget = parent
        while widget and not hasattr(widget, '_log_error'):
            widget = widget.master
        self.main_app = widget

        if self._load_pdf():
            self._setup_dialog()

    def _load_pdf(self):
        """載入PDF文件"""
        try:
            self.pdf_doc = fitz.open(self.pdf_path)
            self.total_pages = len(self.pdf_doc)
            self.original_size = os.path.getsize(self.pdf_path)
            return True
        except Exception as e:
            messagebox.showerror("錯誤", f"無法載入PDF檔案：{str(e)}")
            self.total_pages = 0
            self.original_size = 0
            if hasattr(self, 'pdf_doc') and self.pdf_doc:
                self.pdf_doc.close()
            self.destroy()
            return False

    def _setup_dialog(self):
        """設置對話框"""
        self.title("PDF 壓縮工具")
        self.geometry("500x550")
        self.resizable(False, False)
        self.configure(bg=self.colors['bg_main'])

        # 置中顯示
        self.transient(self.parent)
        self.grab_set()

        # 主框架
        main_frame = tk.Frame(self,
                              bg=self.colors['bg_main'],
                              padx=20,
                              pady=20)
        main_frame.pack(fill="both", expand=True)

        # 檔案資訊
        info_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        info_frame.pack(fill="x", pady=(0, 20))

        tk.Label(info_frame,
                 text=f"檔案：{os.path.basename(self.pdf_path)}",
                 bg=self.colors['bg_main'],
                 fg="black",
                 font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")

        tk.Label(info_frame,
                 text=f"總頁數：{self.total_pages} 頁",
                 bg=self.colors['bg_main'],
                 fg="black",
                 font=("Microsoft YaHei", 10)).pack(anchor="w")

        size_mb = self.original_size / (1024 * 1024)
        tk.Label(info_frame,
                 text=f"原始大小：{size_mb:.2f} MB",
                 bg=self.colors['bg_main'],
                 fg="black",
                 font=("Microsoft YaHei", 10)).pack(anchor="w")

        # 壓縮選項
        options_frame = tk.LabelFrame(main_frame,
                                      text="壓縮選項",
                                      bg=self.colors['bg_main'],
                                      fg="black",
                                      font=("Microsoft YaHei", 10, "bold"))
        options_frame.pack(fill="x", pady=(0, 20))

        # 壓縮級別
        level_frame = tk.Frame(options_frame, bg=self.colors['bg_main'])
        level_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(level_frame,
                 text="壓縮級別：",
                 bg=self.colors['bg_main'],
                 fg="black",
                 font=("Microsoft YaHei", 10)).pack(anchor="w")

        self.compress_level = tk.StringVar(value="medium")

        levels = [("輕度壓縮（保持高品質）", "light"), ("中度壓縮（平衡品質與大小）", "medium"),
                  ("高度壓縮（最小檔案大小）", "heavy")]

        for text, value in levels:
            tk.Radiobutton(level_frame,
                           text=text,
                           variable=self.compress_level,
                           value=value,
                           bg=self.colors['bg_main'],
                           fg="black").pack(anchor="w", pady=2)

        # 壓縮選項
        compress_options_frame = tk.Frame(options_frame,
                                          bg=self.colors['bg_main'])
        compress_options_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(compress_options_frame,
                 text="壓縮選項：",
                 bg=self.colors['bg_main'],
                 fg="black",
                 font=("Microsoft YaHei", 10)).pack(anchor="w")

        self.compress_images = tk.BooleanVar(value=True)
        tk.Checkbutton(compress_options_frame,
                       text="壓縮圖片",
                       variable=self.compress_images,
                       bg=self.colors['bg_main'],
                       fg="black").pack(anchor="w", pady=2)

        self.remove_objects = tk.BooleanVar(value=True)
        tk.Checkbutton(compress_options_frame,
                       text="移除不必要物件",
                       variable=self.remove_objects,
                       bg=self.colors['bg_main'],
                       fg="black").pack(anchor="w", pady=2)

        self.optimize_fonts = tk.BooleanVar(value=True)
        tk.Checkbutton(compress_options_frame,
                       text="優化字體",
                       variable=self.optimize_fonts,
                       bg=self.colors['bg_main'],
                       fg="black").pack(anchor="w", pady=2)

        # 按鈕區域（固定在底部）
        btn_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        btn_frame.pack(side="bottom", fill="x", pady=(20, 0))

        # 進度顯示（在按鈕上方）
        self.progress_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        self.progress_frame.pack(side="bottom", fill="x", pady=(10, 0))

        self.progress_label = tk.Label(self.progress_frame,
                                       text="",
                                       bg=self.colors['bg_main'],
                                       fg="black")
        self.progress_label.pack(pady=5)

        tk.Button(btn_frame,
                  text="開始壓縮",
                  command=self._start_compress,
                  bg=self.colors['success'],
                  fg="white",
                  font=("Microsoft YaHei", 10, "bold"),
                  width=12).pack(side="right", padx=(5, 0))

        tk.Button(btn_frame,
                  text="取消",
                  command=self.destroy,
                  bg=self.colors['danger'],
                  fg="white",
                  font=("Microsoft YaHei", 10, "bold"),
                  width=12).pack(side="right")

    def _start_compress(self):
        """開始壓縮PDF"""
        try:
            # 選擇輸出檔案
            base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
            output_path = filedialog.asksaveasfilename(
                title="儲存壓縮後的PDF",
                defaultextension=".pdf",
                filetypes=[("PDF 檔案", "*.pdf")],
                initialfile=f"{base_name}_compressed.pdf")

            if not output_path:
                return

            # 顯示進度
            self.progress_label.config(text="正在壓縮PDF，請稍候...")
            self.update()

            # 執行壓縮
            success = self._compress_pdf(output_path)

            if success:
                # 計算壓縮後大小
                new_size = os.path.getsize(output_path)
                new_size_mb = new_size / (1024 * 1024)
                original_size_mb = self.original_size / (1024 * 1024)
                reduction = (
                    (self.original_size - new_size) / self.original_size) * 100

                result_msg = f"""PDF壓縮完成！

原始大小：{original_size_mb:.2f} MB
壓縮後大小：{new_size_mb:.2f} MB
節省空間：{reduction:.1f}%

儲存位置：{output_path}"""

                messagebox.showinfo("完成", result_msg)
                self.destroy()

        except Exception as e:
            error_msg = f"壓縮過程中發生錯誤：{str(e)}"
            if self.main_app:
                self.main_app._log_error(error_msg, e, "PDF壓縮處理")
            messagebox.showerror("錯誤", error_msg)
            self.progress_label.config(text="")

    def _compress_pdf(self, output_path):
        """執行PDF壓縮"""
        try:
            level = self.compress_level.get()

            # 根據壓縮級別設定參數
            if level == "light":
                compression_matrix = fitz.Matrix(0.9, 0.9)  # 輕度壓縮
                garbage_level = 1
            elif level == "medium":
                compression_matrix = fitz.Matrix(0.7, 0.7)  # 中度壓縮
                garbage_level = 2
            else:  # heavy
                compression_matrix = fitz.Matrix(0.5, 0.5)  # 高度壓縮
                garbage_level = 4

            # 創建新的PDF文件
            new_doc = fitz.open()

            # 逐頁處理
            for page_num in range(self.total_pages):
                self.progress_label.config(
                    text=f"正在處理第 {page_num + 1} / {self.total_pages} 頁...")
                self.update()

                page = self.pdf_doc[page_num]

                # 如果需要壓縮圖片，重新處理頁面
                if self.compress_images.get():
                    # 獲取頁面作為圖片，使用壓縮矩陣
                    pix = page.get_pixmap(matrix=compression_matrix)
                    img_data = pix.tobytes("jpeg", jpg_quality=70)  # 使用JPEG壓縮

                    # 創建新頁面
                    new_page = new_doc.new_page(width=page.rect.width,
                                                height=page.rect.height)
                    new_page.insert_image(page.rect, stream=img_data)
                else:
                    # 直接複製頁面
                    new_doc.insert_pdf(self.pdf_doc,
                                       from_page=page_num,
                                       to_page=page_num)

            # 設定儲存參數（使用通用參數）
            save_options = {
                "deflate": True,
                "garbage": garbage_level if self.remove_objects.get() else 0,
                "clean": self.remove_objects.get()
            }

            # 儲存壓縮後的PDF
            try:
                new_doc.save(output_path, **save_options)
            except Exception as save_error:
                # 如果參數不支援，使用最簡單的保存方式
                self.progress_label.config(text="使用基本壓縮模式...")
                self.update()
                new_doc.save(output_path)

            new_doc.close()

            return True

        except Exception as e:
            error_msg = f"壓縮失敗：{str(e)}"
            if self.main_app:
                self.main_app._log_error(error_msg, e, "PDF壓縮核心處理")
            raise Exception(error_msg)

    def destroy(self):
        """關閉對話框時清理資源"""
        if self.pdf_doc:
            self.pdf_doc.close()
        super().destroy()


class PDFWatermarkDialog(tk.Toplevel):
    """PDF 浮水印對話框"""

    def __init__(self, parent, pdf_files, log_callback=None):
        super().__init__(parent)
        self.pdf_files = pdf_files
        self.log_callback = log_callback or (lambda msg, level: None)

        self.title("PDF 浮水印")
        self.geometry("500x600")
        self.resizable(False, False)
        self.configure(bg='#F8F9FA')

        # 置中顯示
        self.transient(parent)
        self.grab_set()

        # 色系配置
        self.colors = {
            'bg_main': '#F5F5F0',
            'bg_panel': '#FDFDF2',
            'primary': '#4D6FAC',
            'success': '#4A6741',
            'warning': '#D4A574',
            'danger': '#B22222',
            'fg_primary': '#2C2C2C',
            'border': '#D8D8D8'
        }

        self.setup_ui()

    def setup_ui(self):
        """設置使用者介面"""
        main_frame = tk.Frame(self, bg=self.colors['bg_main'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 標題
        title_label = tk.Label(main_frame,
                               text="PDF 浮水印設定",
                               bg=self.colors['bg_main'],
                               fg=self.colors['fg_primary'],
                               font=("Microsoft YaHei", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # 浮水印類型選擇
        type_frame = tk.LabelFrame(main_frame,
                                   text="浮水印類型",
                                   bg=self.colors['bg_panel'],
                                   fg=self.colors['fg_primary'],
                                   font=("Microsoft YaHei", 12, "bold"))
        type_frame.pack(fill="x", pady=(0, 15))

        self.watermark_type = tk.StringVar(value="text")

        tk.Radiobutton(type_frame,
                       text="文字浮水印",
                       variable=self.watermark_type,
                       value="text",
                       bg=self.colors['bg_panel'],
                       font=("Microsoft YaHei", 10),
                       command=self.on_type_change).pack(anchor="w",
                                                         padx=10,
                                                         pady=5)

        tk.Radiobutton(type_frame,
                       text="圖片浮水印",
                       variable=self.watermark_type,
                       value="image",
                       bg=self.colors['bg_panel'],
                       font=("Microsoft YaHei", 10),
                       command=self.on_type_change).pack(anchor="w",
                                                         padx=10,
                                                         pady=5)

        # 文字浮水印設定
        self.text_frame = tk.LabelFrame(main_frame,
                                        text="文字設定",
                                        bg=self.colors['bg_panel'],
                                        fg=self.colors['fg_primary'],
                                        font=("Microsoft YaHei", 12, "bold"))
        self.text_frame.pack(fill="x", pady=(0, 15))

        # 浮水印文字
        tk.Label(self.text_frame,
                 text="浮水印文字：",
                 bg=self.colors['bg_panel'],
                 fg="black",
                 font=("Microsoft YaHei", 10)).pack(anchor="w",
                                                    padx=10,
                                                    pady=(10, 5))

        self.watermark_text = tk.Entry(self.text_frame,
                                       font=("Microsoft YaHei", 10),
                                       width=40)
        self.watermark_text.pack(padx=10, pady=(0, 10))
        self.watermark_text.insert(0, "CONFIDENTIAL")

        # 字體大小
        font_size_frame = tk.Frame(self.text_frame, bg=self.colors['bg_panel'])
        font_size_frame.pack(fill="x", padx=10, pady=(0, 10))

        tk.Label(font_size_frame,
                 text="字體大小：",
                 bg=self.colors['bg_panel'],
                 fg="black",
                 font=("Microsoft YaHei", 10)).pack(side="left")

        self.font_size = tk.Scale(font_size_frame,
                                  from_=10,
                                  to=100,
                                  orient="horizontal",
                                  bg=self.colors['bg_panel'])
        self.font_size.set(36)
        self.font_size.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # 透明度
        opacity_frame = tk.Frame(self.text_frame, bg=self.colors['bg_panel'])
        opacity_frame.pack(fill="x", padx=10, pady=(0, 10))

        tk.Label(opacity_frame,
                 text="透明度：",
                 bg=self.colors['bg_panel'],
                 fg="black",
                 font=("Microsoft YaHei", 10)).pack(side="left")

        self.opacity = tk.Scale(opacity_frame,
                                from_=0.1,
                                to=1.0,
                                resolution=0.1,
                                orient="horizontal",
                                bg=self.colors['bg_panel'])
        self.opacity.set(0.3)
        self.opacity.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # 圖片浮水印設定
        self.image_frame = tk.LabelFrame(main_frame,
                                         text="圖片設定",
                                         bg=self.colors['bg_panel'],
                                         fg=self.colors['fg_primary'],
                                         font=("Microsoft YaHei", 12, "bold"))
        self.image_frame.pack(fill="x", pady=(0, 15))

        # 圖片選擇
        image_select_frame = tk.Frame(self.image_frame,
                                      bg=self.colors['bg_panel'])
        image_select_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(image_select_frame,
                  text="選擇圖片",
                  command=self.select_image,
                  bg=self.colors['primary'],
                  fg="white",
                  font=("Microsoft YaHei", 10)).pack(side="left")

        self.image_path_label = tk.Label(image_select_frame,
                                         text="未選擇圖片",
                                         bg=self.colors['bg_panel'],
                                         fg=self.colors['fg_primary'],
                                         font=("Microsoft YaHei", 9))
        self.image_path_label.pack(side="left", padx=(10, 0))

        # 位置設定
        position_frame = tk.LabelFrame(main_frame,
                                       text="位置設定",
                                       bg=self.colors['bg_panel'],
                                       fg=self.colors['fg_primary'],
                                       font=("Microsoft YaHei", 12, "bold"))
        position_frame.pack(fill="x", pady=(0, 15))

        self.position = tk.StringVar(value="center")

        positions = [("置中", "center"), ("左上角", "top-left"),
                     ("右上角", "top-right"), ("左下角", "bottom-left"),
                     ("右下角", "bottom-right")]

        pos_grid = tk.Frame(position_frame, bg=self.colors['bg_panel'])
        pos_grid.pack(padx=10, pady=10)

        for i, (text, value) in enumerate(positions):
            row = i // 3
            col = i % 3
            tk.Radiobutton(pos_grid,
                           text=text,
                           variable=self.position,
                           value=value,
                           bg=self.colors['bg_panel'],
                           font=("Microsoft YaHei", 10)).grid(row=row,
                                                              column=col,
                                                              sticky="w",
                                                              padx=10,
                                                              pady=2)

        # 按鈕區域
        btn_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        btn_frame.pack(fill="x", pady=(20, 0))

        tk.Button(btn_frame,
                  text="開始加浮水印",
                  command=self.start_watermark,
                  bg=self.colors['success'],
                  fg="white",
                  font=("Microsoft YaHei", 12, "bold"),
                  width=15).pack(side="right", padx=(5, 0))

        tk.Button(btn_frame,
                  text="取消",
                  command=self.destroy,
                  bg=self.colors['danger'],
                  fg="white",
                  font=("Microsoft YaHei", 12, "bold"),
                  width=10).pack(side="right")

        # 初始化顯示
        self.on_type_change()

    def on_type_change(self):
        """切換浮水印類型時的處理"""
        if self.watermark_type.get() == "text":
            self.text_frame.pack(fill="x", pady=(0, 15))
            self.image_frame.pack_forget()
        else:
            self.text_frame.pack_forget()
            self.image_frame.pack(fill="x", pady=(0, 15))

    def select_image(self):
        """選擇浮水印圖片"""
        file_path = filedialog.askopenfilename(
            title="選擇浮水印圖片",
            filetypes=[("圖片檔案", "*.png *.jpg *.jpeg *.gif *.bmp"),
                       ("PNG 檔案", "*.png"), ("JPEG 檔案", "*.jpg *.jpeg"),
                       ("所有檔案", "*.*")])

        if file_path:
            self.image_path = file_path
            filename = os.path.basename(file_path)
            self.image_path_label.config(text=filename)
        else:
            self.image_path = None
            self.image_path_label.config(text="未選擇圖片")

    def start_watermark(self):
        """開始加浮水印"""
        try:
            if not self.pdf_files:
                messagebox.showwarning("警告", "請先載入 PDF 檔案")
                return

            # 驗證設定
            if self.watermark_type.get() == "text":
                if not self.watermark_text.get().strip():
                    messagebox.showwarning("警告", "請輸入浮水印文字")
                    return
            else:
                if not hasattr(self, 'image_path') or not self.image_path:
                    messagebox.showwarning("警告", "請選擇浮水印圖片")
                    return

            # 選擇輸出目錄
            output_dir = filedialog.askdirectory(title="選擇浮水印檔案的儲存目錄")
            if not output_dir:
                return

            success_count = 0

            for pdf_file in self.pdf_files:
                try:
                    input_path = pdf_file['path']
                    base_name = os.path.splitext(
                        os.path.basename(input_path))[0]
                    output_path = os.path.join(output_dir,
                                               f"{base_name}_watermarked.pdf")

                    self.apply_watermark(input_path, output_path)
                    success_count += 1
                    self.log_callback(f"已完成：{os.path.basename(output_path)}",
                                      "success")

                except Exception as e:
                    error_msg = f"處理 {pdf_file['name']} 失敗：{str(e)}"
                    self.log_callback(error_msg, "error")
                    print(f"詳細錯誤：{e}")  # 調試用

            if success_count > 0:
                messagebox.showinfo(
                    "完成", f"成功為 {success_count} 個檔案加上浮水印！\n"
                    f"檔案已儲存到：{output_dir}")
                self.destroy()
            else:
                messagebox.showerror("錯誤", "沒有檔案成功加上浮水印")

        except Exception as e:
            messagebox.showerror("錯誤", f"加浮水印失敗：{str(e)}")

    def apply_watermark(self, input_path, output_path):
        """應用浮水印到 PDF"""
        doc = fitz.open(input_path)

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]

                if self.watermark_type.get() == "text":
                    self.add_text_watermark(page)
                else:
                    self.add_image_watermark(page)

            doc.save(output_path)

        finally:
            doc.close()

    def add_text_watermark(self, page):
        """添加文字浮水印"""
        text = self.watermark_text.get().strip()
        font_size = self.font_size.get()
        opacity = self.opacity.get()
        position = self.position.get()

        # 獲取頁面尺寸
        rect = page.rect

        # 計算位置
        if position == "center":
            x = rect.width / 2
            y = rect.height / 2
        elif position == "top-left":
            x = rect.width * 0.15
            y = rect.height * 0.15
        elif position == "top-right":
            x = rect.width * 0.85
            y = rect.height * 0.15
        elif position == "bottom-left":
            x = rect.width * 0.15
            y = rect.height * 0.85
        else:  # bottom-right
            x = rect.width * 0.85
            y = rect.height * 0.85

        # 使用更簡單的顏色設定 - 直接使用數字
        gray_value = 0.5  # 中等灰色
        color = (gray_value, gray_value, gray_value)

        # 嘗試多種 API 方式
        success = False

        # 方法1：基本的insert_text
        try:
            page.insert_text(
                (x, y),  # 使用元組而不是fitz.Point
                text,
                fontsize=font_size,
                color=color)
            success = True
            print("方法1成功：基本insert_text")

        except Exception as e1:
            print(f"方法1失敗：{e1}")

            # 方法2：使用fitz.Point
            try:
                page.insert_text(fitz.Point(x, y),
                                 text,
                                 fontsize=font_size,
                                 color=color)
                success = True
                print("方法2成功：使用fitz.Point")

            except Exception as e2:
                print(f"方法2失敗：{e2}")

                # 方法3：最簡單的版本
                try:
                    page.insert_text(fitz.Point(x, y),
                                     text,
                                     fontsize=font_size)
                    success = True
                    print("方法3成功：最簡單版本")

                except Exception as e3:
                    print(f"方法3失敗：{e3}")

                    # 方法4：使用drawString (如果可用)
                    try:
                        # 創建一個形狀來繪製文字
                        shape = page.new_shape()
                        shape.insert_text(fitz.Point(x, y),
                                          text,
                                          fontsize=font_size,
                                          color=color)
                        shape.commit()
                        success = True
                        print("方法4成功：使用shape")

                    except Exception as e4:
                        print(f"方法4失敗：{e4}")
                        print("所有文字插入方法都失敗")

        if not success:
            raise Exception("無法插入文字浮水印")

    def add_image_watermark(self, page):
        """添加圖片浮水印"""
        if not hasattr(self, 'image_path') or not self.image_path:
            return

        position = self.position.get()
        rect = page.rect

        # 計算圖片位置和大小
        img_size = min(rect.width, rect.height) * 0.3  # 圖片大小為頁面的30%

        if position == "center":
            x = (rect.width - img_size) / 2
            y = (rect.height - img_size) / 2
        elif position == "top-left":
            x = rect.width * 0.05
            y = rect.height * 0.05
        elif position == "top-right":
            x = rect.width * 0.95 - img_size
            y = rect.height * 0.05
        elif position == "bottom-left":
            x = rect.width * 0.05
            y = rect.height * 0.95 - img_size
        else:  # bottom-right
            x = rect.width * 0.95 - img_size
            y = rect.height * 0.95 - img_size

        img_rect = fitz.Rect(x, y, x + img_size, y + img_size)

        # 插入圖片
        page.insert_image(img_rect, filename=self.image_path, overlay=True)


class AboutDialog(tk.Toplevel):
    """關於軟體對話框"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("關於 PDF 工具包")
        self.geometry("800x600")
        self.resizable(True, True)
        self.configure(bg='#F5F5F0')

        # 置中顯示
        self.transient(parent)
        self.grab_set()

        # 色系配置
        self.colors = {
            'bg_main': '#F5F5F0',
            'bg_panel': '#FDFDF2',
            'primary': '#4D6FAC',
            'success': '#4A6741',
            'warning': '#D4A574',
            'danger': '#B22222',
            'fg_primary': '#2C2C2C',
            'border': '#D8D8D8'
        }

        self.setup_ui()

    def setup_ui(self):
        """設置使用者介面"""
        main_frame = tk.Frame(self, bg=self.colors['bg_main'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 標題區域
        title_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        title_frame.pack(fill="x", pady=(0, 20))

        title_label = tk.Label(title_frame,
                               text="PDF 多功能處理工具",
                               bg=self.colors['bg_main'],
                               fg=self.colors['primary'],
                               font=("Microsoft YaHei", 18, "bold"))
        title_label.pack()

        version_label = tk.Label(title_frame,
                                 text=f"版本 {APP_VERSION}",
                                 bg=self.colors['bg_main'],
                                 fg=self.colors['fg_primary'],
                                 font=("Microsoft YaHei", 12))
        version_label.pack(pady=(5, 0))

        # 創建筆記本式標籤
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=(0, 20))

        # 功能說明標籤
        features_frame = tk.Frame(notebook, bg=self.colors['bg_panel'])
        notebook.add(features_frame, text="功能說明")

        features_text = tk.Text(features_frame,
                                wrap=tk.WORD,
                                bg=self.colors['bg_panel'],
                                fg=self.colors['fg_primary'],
                                font=("Microsoft YaHei", 10),
                                height=20,
                                padx=10,
                                pady=10)
        features_text.pack(fill="both", expand=True, padx=10, pady=10)

        features_content = """
📄 PDF 合併功能
✓ 合併多個 PDF 檔案
✓ 拖放介面操作
✓ 頁面重新排序
✓ 即時預覽縮圖

✍️ PDF 電子簽名 (手寫 + 上傳圖片 + 文字輸入)
✓ 手寫簽名支援
✓ 圖片簽名上傳
✓ 自訂文字插入
✓ 拖曳調整位置和大小
✓ 多重簽名支援

✂️ PDF 拆分 (按頁數、範圍、單頁擷取)
✓ 按指定頁數分割
✓ 按頁面範圍分割
✓ 單頁獨立擷取
✓ 自訂輸出設定

🗜️ PDF 壓縮 (多級壓縮選項)
✓ 輕度、中度、重度壓縮
✓ 圖片品質最佳化
✓ 進階壓縮選項
✓ 大幅減少檔案大小

💧 PDF 浮水印 (文字 + 圖片浮水印)
✓ 自訂文字浮水印
✓ 圖片浮水印支援
✓ 多種位置選項
✓ 透明度和大小調整
✓ 批次處理支援

支援格式: PDF (.pdf)
操作系統: Windows, macOS, Linux
"""

        features_text.insert("1.0", features_content)
        features_text.config(state="disabled")

        # 操作說明標籤
        guide_frame = tk.Frame(notebook, bg=self.colors['bg_panel'])
        notebook.add(guide_frame, text="操作指南")

        guide_text = tk.Text(guide_frame,
                             wrap=tk.WORD,
                             bg=self.colors['bg_panel'],
                             fg=self.colors['fg_primary'],
                             font=("Microsoft YaHei", 10),
                             height=20,
                             padx=10,
                             pady=10)
        guide_text.pack(fill="both", expand=True, padx=10, pady=10)

        guide_content = """
📄 PDF 合併操作流程:
1. 載入 PDF 檔案 → 2. 拖曳頁面排序 → 3. 點擊「合併 PDF」→ 4. 選擇儲存位置

✍️ PDF 簽名操作流程:
1. 載入 PDF 檔案 → 2. 點擊「PDF 簽名」→ 3. 手寫或上傳簽名/文字 → 4. 拖曳調整位置大小 → 5. 儲存

✂️ PDF 拆分操作流程:
1. 載入 PDF 檔案 → 2. 點擊「拆分 PDF」→ 3. 選擇拆分方式 → 4. 設定參數 → 5. 選擇儲存目錄

🗜️ PDF 壓縮操作流程:
1. 載入 PDF 檔案 → 2. 點擊「壓縮 PDF」→ 3. 選擇壓縮等級 → 4. 設定選項 → 5. 儲存壓縮檔案

💧 PDF 浮水印操作流程:
1. 載入 PDF 檔案 → 2. 點擊「加浮水印」→ 3. 選擇文字或圖片 → 4. 設定位置透明度 → 5. 開始處理

⌨️ 鍵盤快捷鍵 (簽名模式):
• + 或 = : 放大選中的簽名/文字
• - : 縮小選中的簽名/文字  
• 0 : 重設為原始大小
• Delete : 刪除選中的簽名/文字

📁 檔案處理說明:
• 支援批次處理多個檔案
• 自動產生輸出檔案名稱
• 保持原始檔案完整性
• 提供進度回饋和錯誤處理
"""

        guide_text.insert("1.0", guide_content)
        guide_text.config(state="disabled")

        # 關於標籤
        about_frame = tk.Frame(notebook, bg=self.colors['bg_panel'])
        notebook.add(about_frame, text="關於")

        about_content_frame = tk.Frame(about_frame, bg=self.colors['bg_panel'])
        about_content_frame.pack(expand=True, fill="both", padx=20, pady=20)

        about_text = tk.Label(about_content_frame,
                              text="© 2025 PDF Toolkit | Created by \n\n"
                              "一個完整的 PDF 處理解決方案\n"
                              "整合合併、簽名、拆分、壓縮、浮水印功能\n\n"
                              "使用 Python 和 Tkinter 構建\n"
                              "支援跨平台運行\n\n"
                              "感謝使用 PDF 工具包！",
                              bg=self.colors['bg_panel'],
                              fg=self.colors['fg_primary'],
                              font=("Microsoft YaHei", 12),
                              justify="center")
        about_text.pack(expand=True)

        # 按鈕區域
        btn_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        btn_frame.pack(fill="x")

        tk.Button(btn_frame,
                  text="確定",
                  command=self.destroy,
                  bg=self.colors['primary'],
                  fg="white",
                  font=("Microsoft YaHei", 12, "bold"),
                  width=15).pack(pady=10)


class PDFToolkit:
    """PDF 工具包 - 提供PDF合併、簽名、拆分、壓縮等全方位功能"""

    def __init__(self):
        # 設置錯誤日誌
        self._setup_error_logging()

        # 初始化智能多源更新檢查器
        self.update_checker = UpdateChecker(APP_VERSION, UPDATE_SOURCES)

        # 日系配色方案 (基於 nipponcolors.com 和 irocore.com)
        self.colors = {
            # 主背景：淡雪色 (AWAYUKI) - 柔和的米白色
            'bg_main': '#F5F5F0',
            # 面板背景：白茶色 (SHIRACHA) - 溫暖的白色
            'bg_panel': '#FDFDF2',
            # 強調背景：水淺蔥色 (MIZUASAGI) - 清淡的水藍
            'bg_accent': '#E8F2F5',
            # 主要文字：墨色 (SUMI) - 深灰黑
            'fg_primary': '#2C2C2C',
            # 次要文字：鼠色 (NEZUMI) - 中性灰
            'fg_secondary': '#7A7A7A',
            # 邊框：白鼠色 (SHIRONEZUMI) - 淡灰
            'border': '#D8D8D8',
            # 成功色：常磐色 (TOKIWA) - 深綠
            'success': '#4A6741',
            # 警告色：黃土色 (ŌDOIRO) - 溫和黃
            'warning': '#D4A574',
            # 危險色：臙脂色 (ENJI) - 深紅
            'danger': '#B22222',
            # 信息色：瑠璃色 (RURI) - 深藍
            'info': '#4D6FAC',
            # 步驟背景：象牙色 (ZŌGE) - 溫暖米色
            'step_bg': '#F9F7F1',
            # 步驟邊框：利休茶色 (RIKYUCHA) - 淡茶色
            'step_border': '#C8B99C'
        }

        # 初始化主視窗
        self.root = TkinterDnD.Tk()
        self.root.title("PDF 工具包 - 合併、簽名、拆分、壓縮")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 600)  # 降低最小尺寸要求
        self.root.configure(bg=self.colors['bg_main'])

        # 資料結構
        self.pdf_files = []
        self.pages = []
        self.dragging_index = None

        # 響應式佈局變數
        self.window_width = 1400
        self.window_height = 900

        self._setup_ui()
        self._setup_drag_drop()
        self._setup_responsive()

    def _setup_error_logging(self):
        """設置錯誤日誌系統"""
        try:
            # 創建logs目錄
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # 設置日誌檔案名稱（包含日期）
            today = datetime.now().strftime("%Y%m%d")
            log_file = os.path.join(log_dir, f"pdf_toolkit_error_{today}.log")

            # 創建專用的錯誤日誌handler
            error_handler = logging.FileHandler(log_file, encoding='utf-8')
            error_handler.setLevel(logging.ERROR)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s')
            error_handler.setFormatter(formatter)

            self.error_logger = logging.getLogger('PDFToolkit')
            self.error_logger.addHandler(error_handler)
            self.error_logger.setLevel(logging.ERROR)
            self.log_file_path = log_file

        except Exception as e:
            # 如果日誌設置失敗，使用控制台輸出
            print(f"日誌設置失敗：{e}")
            self.error_logger = None
            self.log_file_path = None

    def _log_error(self, error_message, exception=None, context=""):
        """記錄錯誤到日誌檔案"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 構建錯誤訊息
            log_message = f"[{timestamp}] 錯誤: {error_message}"
            if context:
                log_message += f" | 上下文: {context}"

            # 如果有例外物件，添加詳細信息
            if exception:
                log_message += f" | 例外類型: {type(exception).__name__}"
                log_message += f" | 例外訊息: {str(exception)}"

                # 添加堆疊追蹤
                tb_str = traceback.format_exc()
                log_message += f" | 堆疊追蹤:\n{tb_str}"

            # 直接寫入檔案（更可靠的方法）
            if self.log_file_path:
                try:
                    with open(self.log_file_path, 'a', encoding='utf-8') as f:
                        f.write(log_message + "\n\n")
                        f.flush()
                except Exception as file_error:
                    print(f"無法寫入日誌檔案：{file_error}")

            # 使用logging系統（作為備份）
            if self.error_logger:
                self.error_logger.error(log_message)

            # 同時輸出到應用程式日誌
            self._log_message(f"錯誤已記錄到: {self.log_file_path}", "warning")

        except Exception as log_error:
            print(f"無法寫入錯誤日誌：{log_error}")

    def _setup_responsive(self):
        """設定響應式佈局"""

        def on_window_resize(event):
            if event.widget == self.root:
                self.window_width = event.width
                self.window_height = event.height
                self._adjust_layout()

        self.root.bind('<Configure>', on_window_resize)

    def _adjust_layout(self):
        """調整佈局以適應視窗大小"""
        # 根據視窗寬度調整佈局
        if self.window_width < 1000:
            # 小螢幕：垂直佈局
            self._switch_to_vertical_layout()
        else:
            # 大螢幕：水平佈局
            self._switch_to_horizontal_layout()

    def _switch_to_vertical_layout(self):
        """切換到垂直佈局（小螢幕）"""
        # 這裡可以實現垂直佈局邏輯
        pass

    def _switch_to_horizontal_layout(self):
        """切換到水平佈局（大螢幕）"""
        # 這裡可以實現水平佈局邏輯
        pass

    def _setup_ui(self):
        """建立使用者界面"""
        # 創建主要容器
        self.main_container = tk.Frame(self.root, bg=self.colors['bg_main'])
        self.main_container.pack(fill="both", expand=True)

        # 標題區域（置中）
        self._create_header()

        # 主要內容區域（響應式）
        self._create_main_content()

        # 底部狀態列
        self._create_status_bar()

    def _create_header(self):
        """建立標題區域（置中）"""
        header_frame = tk.Frame(self.main_container,
                                bg=self.colors['bg_panel'],
                                height=100)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)

        # 內容容器（置中）
        content_frame = tk.Frame(header_frame, bg=self.colors['bg_panel'])
        content_frame.pack(expand=True)

        # ASCII 標題（置中）
        if PYFIGLET_AVAILABLE:
            title_text = figlet_format("PDF TOOLKIT", font="slant")
        else:
            title_text = figlet_format("PDF TOOLKIT")
        title_label = tk.Label(content_frame,
                               text=title_text,
                               bg=self.colors['bg_panel'],
                               fg=self.colors['info'],
                               font=("Courier", 8),
                               justify="center")
        title_label.pack(pady=5)

        # 副標題（置中）
        subtitle_label = tk.Label(content_frame,
                                  text="專業 PDF 工具包 - 合併、簽名、拆分、壓縮一站式解決方案",
                                  bg=self.colors['bg_panel'],
                                  fg=self.colors['fg_secondary'],
                                  font=("Microsoft YaHei", 12, "bold"))
        subtitle_label.pack()

    # def _create_steps_guide(self):
    #     """建立步驟說明區域 - 已移除，相關說明移至關於對話框"""
    #     steps_frame = tk.Frame(self.main_container,
    #                            bg=self.colors['step_bg'],
    #                            relief="solid",
    #                            bd=1)
    #     steps_frame.pack(fill="x", padx=10, pady=5)
    #
    #     # 標題
    #     tk.Label(steps_frame,
    #              text="操作步驟說明",
    #              bg=self.colors['step_bg'],
    #              fg=self.colors['fg_primary'],
    #              font=("Microsoft YaHei", 11, "bold")).pack(anchor="w",
    #                                                         padx=15,
    #                                                         pady=(10, 5))
    #
    #     # 步驟內容
    #     steps_content = tk.Frame(steps_frame, bg=self.colors['step_bg'])
    #     steps_content.pack(fill="x", padx=15, pady=(0, 10))
    #
    #     # 合併模式步驟（置中顯示）
    #     merge_frame = tk.Frame(steps_content, bg=self.colors['step_bg'])
    #     merge_frame.pack(expand=True)
    #
    #     tk.Label(merge_frame,
    #              text="PDF 工具操作流程：",
    #              bg=self.colors['step_bg'],
    #              fg=self.colors['info'],
    #              font=("Microsoft YaHei", 12, "bold")).pack(pady=5)
    #
    #     operation_steps = [
    #         "【合併模式】1. 載入多個 PDF → 2. 調整頁面順序 → 3. 點擊「合併 PDF」→ 4. 選擇儲存位置",
    #         "【簽名模式】1. 載入 PDF 檔案 → 2. 點擊「PDF 簽名」→ 3. 手寫或上傳簽名/插入文字 → 4. 拖曳調整位置與大小 → 5. 儲存",
    #         "【拆分模式】1. 載入 PDF 檔案 → 2. 點擊「拆分 PDF」→ 3. 選擇拆分方式 → 4. 設定參數 → 5. 選擇儲存目錄",
    #         "【壓縮模式】1. 載入 PDF 檔案 → 2. 點擊「壓縮 PDF」→ 3. 選擇壓縮級別 → 4. 設定選項 → 5. 儲存壓縮檔案"
    #     ]
    #
    #     for step in operation_steps:
    #         tk.Label(merge_frame,
    #                  text=step,
    #                  bg=self.colors['step_bg'],
    #                  fg=self.colors['fg_primary'],
    #                  font=("Microsoft YaHei", 9)).pack(pady=3)

    def _create_main_content(self):
        """建立主要內容區域"""
        content_frame = tk.Frame(self.main_container,
                                 bg=self.colors['bg_main'])
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 左側：檔案載入和預覽區域
        self._create_left_panel(content_frame)

        # 右側：控制面板
        self._create_right_panel(content_frame)

    def _create_left_panel(self, parent):
        """建立左側面板"""
        left_panel = tk.Frame(parent, bg=self.colors['bg_main'])
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # 檔案載入區域
        self._create_file_load_section(left_panel)

        # PDF 預覽區域
        self._create_preview_section(left_panel)

    def _create_file_load_section(self, parent):
        """建立檔案載入區域"""
        load_frame = tk.LabelFrame(parent,
                                   text="檔案載入區域",
                                   bg=self.colors['bg_panel'],
                                   fg=self.colors['fg_primary'],
                                   font=("Microsoft YaHei", 11, "bold"))
        load_frame.pack(fill="x", pady=(0, 10))

        # 拖放提示區域
        drop_zone_container = tk.Frame(load_frame, bg=self.colors['bg_panel'])
        drop_zone_container.pack(fill="x", padx=10, pady=10)

        # 外框（模擬虛線效果）
        outer_frame = tk.Frame(drop_zone_container,
                               bg=self.colors['border'],
                               height=84)
        outer_frame.pack(fill="x")
        outer_frame.pack_propagate(False)

        # 內框（拖放區域）
        drop_zone = tk.Frame(outer_frame,
                             bg=self.colors['bg_accent'],
                             height=80)
        drop_zone.pack(fill="x", padx=2, pady=2)
        drop_zone.pack_propagate(False)

        # 提示文字
        drop_label = tk.Label(drop_zone,
                              text="將 PDF 檔案拖放到此處，或點擊下方按鈕選擇檔案\n支援多檔案同時載入",
                              bg=self.colors['bg_accent'],
                              fg=self.colors['info'],
                              font=("Microsoft YaHei", 11, "bold"),
                              justify="center")
        drop_label.pack(expand=True)

        # 按鈕區域
        btn_frame = tk.Frame(load_frame, bg=self.colors['bg_panel'])
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        # 選擇檔案按鈕
        select_btn = tk.Button(btn_frame,
                               text="選擇 PDF 檔案",
                               command=self._browse_files,
                               bg=self.colors['info'],
                               fg="white",
                               font=("Microsoft YaHei", 10, "bold"),
                               height=2,
                               width=15)
        select_btn.pack(side="left", padx=(0, 10))

        # 清除檔案按鈕
        clear_btn = tk.Button(btn_frame,
                              text="清除所有",
                              command=self._clear_all,
                              bg=self.colors['danger'],
                              fg="white",
                              font=("Microsoft YaHei", 10, "bold"),
                              height=2,
                              width=12)
        clear_btn.pack(side="left")

        # 檔案狀態顯示
        self.file_status_label = tk.Label(btn_frame,
                                          text="尚未載入檔案",
                                          bg=self.colors['bg_panel'],
                                          fg=self.colors['fg_secondary'],
                                          font=("Microsoft YaHei", 10))
        self.file_status_label.pack(side="right")

    def _create_preview_section(self, parent):
        """建立預覽區域"""
        preview_frame = tk.LabelFrame(parent,
                                      text="PDF 頁面預覽（可拖曳調整順序）",
                                      bg=self.colors['bg_panel'],
                                      fg=self.colors['fg_primary'],
                                      font=("Microsoft YaHei", 11, "bold"))
        preview_frame.pack(fill="both", expand=True)

        # 預覽說明
        info_frame = tk.Frame(preview_frame, bg=self.colors['bg_panel'])
        info_frame.pack(fill="x", padx=5, pady=2)

        tk.Label(info_frame,
                 text="提示：按住滑鼠左鍵拖曳頁面縮圖可以調整合併順序",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['warning'],
                 font=("Microsoft YaHei", 9)).pack(anchor="w")

        # 建立可滾動的預覽區域
        canvas_frame = tk.Frame(preview_frame, bg=self.colors['bg_panel'])
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        # Canvas 和滾動條
        self.preview_canvas = tk.Canvas(
            canvas_frame,
            bg="white",
            highlightthickness=1,
            highlightbackground=self.colors['border'])

        # 垂直滾動條
        v_scrollbar = ttk.Scrollbar(canvas_frame,
                                    orient="vertical",
                                    command=self.preview_canvas.yview)
        self.preview_canvas.configure(yscrollcommand=v_scrollbar.set)

        # 水平滾動條
        h_scrollbar = ttk.Scrollbar(canvas_frame,
                                    orient="horizontal",
                                    command=self.preview_canvas.xview)
        self.preview_canvas.configure(xscrollcommand=h_scrollbar.set)

        # 佈局滾動條和 Canvas
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.preview_canvas.pack(side="left", fill="both", expand=True)

        # 縮圖容器
        self.thumbnail_frame = tk.Frame(self.preview_canvas, bg="white")
        self.canvas_window = self.preview_canvas.create_window(
            (0, 0), window=self.thumbnail_frame, anchor="nw")

        # 綁定 Canvas 大小調整事件
        def on_canvas_configure(event):
            self.preview_canvas.configure(
                scrollregion=self.preview_canvas.bbox("all"))
            # 調整內部框架寬度以符合 Canvas 寬度
            canvas_width = event.width
            self.preview_canvas.itemconfig(self.canvas_window,
                                           width=canvas_width)

        self.preview_canvas.bind('<Configure>', on_canvas_configure)

    def _create_right_panel(self, parent):
        """建立右側控制面板"""
        right_panel = tk.Frame(parent, bg=self.colors['bg_main'], width=350)
        right_panel.pack(side="right", fill="y", padx=(5, 0))
        right_panel.pack_propagate(False)

        # 操作按鈕區域
        self._create_action_section(right_panel)

        # 進度顯示區域
        self._create_progress_section(right_panel)

        # 日誌區域
        self._create_log_section(right_panel)

    # def _create_info_section(self, parent):
    #     """建立資訊顯示區域 - 已移除，相關說明移至關於對話框"""
    #     info_frame = tk.LabelFrame(parent,
    #                                text="功能說明",
    #                                bg=self.colors['bg_panel'],
    #                                fg=self.colors['fg_primary'],
    #                                font=("Microsoft YaHei", 11, "bold"))
    #     info_frame.pack(fill="x", pady=(0, 10))
    #
    #     # 功能說明
    #     desc_frame = tk.Frame(info_frame, bg=self.colors['bg_panel'])
    #     desc_frame.pack(fill="x", padx=10, pady=10)
    #
    #     tk.Label(desc_frame,
    #              text="PDF 多功能處理工具",
    #              bg=self.colors['bg_panel'],
    #              fg=self.colors['info'],
    #              font=("Microsoft YaHei", 12, "bold")).pack(anchor="w")
    #
    #     features = [
    #         "✓ 合併多個 PDF 檔案", "✓ PDF 電子簽名（手寫 + 上傳圖片 + 文字插入）",
    #         "✓ PDF 拆分（按頁數、範圍、單頁提取）", "✓ PDF 壓縮（多級別壓縮選項）",
    #         "✓ PDF 浮水印（文字 + 圖片浮水印）"
    #     ]
    #
    #     for feature in features:
    #         tk.Label(desc_frame,
    #                  text=feature,
    #                  bg=self.colors['bg_panel'],
    #                  fg=self.colors['fg_secondary'],
    #                  font=("Microsoft YaHei", 10)).pack(anchor="w", pady=1)
    #
    #     # 支援格式
    #     format_frame = tk.Frame(info_frame, bg=self.colors['bg_panel'])
    #     format_frame.pack(fill="x", padx=10, pady=(5, 10))
    #
    #     tk.Label(format_frame,
    #              text="支援格式：PDF (.pdf)",
    #              bg=self.colors['bg_panel'],
    #              fg=self.colors['fg_secondary'],
    #              font=("Microsoft YaHei", 9)).pack(anchor="w")

    def _create_action_section(self, parent):
        """建立操作按鈕區域"""
        action_frame = tk.LabelFrame(parent,
                                     text="執行操作",
                                     bg=self.colors['bg_panel'],
                                     fg=self.colors['fg_primary'],
                                     font=("Microsoft YaHei", 11, "bold"))
        action_frame.pack(fill="x", pady=(0, 10))

        # 按鈕容器（2x2網格佈局）
        button_container = tk.Frame(action_frame, bg=self.colors['bg_main'])
        button_container.pack(fill="x", padx=10, pady=(15, 5))

        # 第一行按鈕
        first_row = tk.Frame(button_container, bg=self.colors['bg_main'])
        first_row.pack(fill="x", pady=(0, 5))

        # 合併按鈕
        self.merge_btn = tk.Button(first_row,
                                   text="合併",
                                   command=self._merge_pdfs,
                                   bg=self.colors['success'],
                                   fg="white",
                                   font=("Microsoft YaHei", 11, "bold"),
                                   height=2)
        self.merge_btn.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # 簽名按鈕
        self.sign_btn = tk.Button(first_row,
                                  text="簽名",
                                  command=self._open_signature_editor,
                                  bg=self.colors['info'],
                                  fg="white",
                                  font=("Microsoft YaHei", 11, "bold"),
                                  height=2)
        self.sign_btn.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # 第二行按鈕
        second_row = tk.Frame(button_container, bg=self.colors['bg_main'])
        second_row.pack(fill="x")

        # 拆分按鈕
        self.split_btn = tk.Button(second_row,
                                   text="拆分",
                                   command=self._split_pdf,
                                   bg="#66BAB7",
                                   fg="white",
                                   font=("Microsoft YaHei", 11, "bold"),
                                   height=2)
        self.split_btn.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # 壓縮按鈕
        self.compress_btn = tk.Button(second_row,
                                      text="壓縮",
                                      command=self._compress_pdf,
                                      bg="#6A4C9C",
                                      fg="white",
                                      font=("Microsoft YaHei", 11, "bold"),
                                      height=2)
        self.compress_btn.pack(side="left",
                               fill="both",
                               expand=True,
                               padx=(0, 5))

        # 浮水印按鈕
        self.watermark_btn = tk.Button(
            second_row,
            text="浮水印",
            command=self._add_watermark,
            bg="#E67E22",  # 柿色 (KAKI) - 日系橘色
            fg="white",
            font=("Microsoft YaHei", 11, "bold"),
            height=2)
        self.watermark_btn.pack(side="right",
                                fill="both",
                                expand=True,
                                padx=(5, 0))

        # 版本和更新區域
        version_container = tk.Frame(action_frame, bg=self.colors['bg_panel'])
        version_container.pack(fill="x", padx=10, pady=(10, 5))

        # 版本標籤
        version_label = tk.Label(version_container,
                                 text=f"v{APP_VERSION}",
                                 bg=self.colors['bg_panel'],
                                 fg=self.colors['fg_secondary'],
                                 font=("Microsoft YaHei", 9))
        version_label.pack(side="left")

        # 檢查更新按鈕（小巧版）
        # 按鈕區域
        btn_container = tk.Frame(version_container, bg=self.colors['bg_panel'])
        btn_container.pack(side="right")

        # 關於按鈕
        about_btn = tk.Button(btn_container,
                              text="ℹ️ 關於",
                              command=self._show_about,
                              bg=self.colors['fg_secondary'],
                              fg="white",
                              font=("Microsoft YaHei", 9),
                              relief="flat",
                              cursor="hand2",
                              padx=10,
                              pady=2)
        about_btn.pack(side="right", padx=(0, 5))

        # 檢查更新按鈕
        update_btn = tk.Button(btn_container,
                               text="🔄 檢查更新",
                               command=self._check_for_updates,
                               bg=self.colors['info'],
                               fg="white",
                               font=("Microsoft YaHei", 9),
                               relief="flat",
                               cursor="hand2",
                               padx=10,
                               pady=2)
        update_btn.pack(side="right")

    def _create_progress_section(self, parent):
        """建立進度顯示區域"""
        progress_frame = tk.LabelFrame(parent,
                                       text="處理進度",
                                       bg=self.colors['bg_panel'],
                                       fg=self.colors['fg_primary'],
                                       font=("Microsoft YaHei", 11, "bold"))
        progress_frame.pack(fill="x", pady=(0, 10))

        # 進度條
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(fill="x", padx=10, pady=10)

        # 狀態文字
        self.progress_label = tk.Label(progress_frame,
                                       text="就緒",
                                       bg=self.colors['bg_panel'],
                                       fg=self.colors['success'],
                                       font=("Microsoft YaHei", 10))
        self.progress_label.pack(padx=10, pady=(0, 10))

    def _create_log_section(self, parent):
        """建立日誌區域"""
        log_frame = tk.LabelFrame(parent,
                                  text="操作日誌",
                                  bg=self.colors['bg_panel'],
                                  fg=self.colors['fg_primary'],
                                  font=("Microsoft YaHei", 11, "bold"))
        log_frame.pack(fill="both", expand=True)

        # 日誌文字區域
        log_text_frame = tk.Frame(log_frame, bg=self.colors['bg_panel'])
        log_text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_text = tk.Text(log_text_frame,
                                height=12,
                                font=("Consolas", 9),
                                bg="#2C3E50",
                                fg="#ECF0F1",
                                insertbackground="#ECF0F1",
                                wrap="word")

        log_scrollbar = ttk.Scrollbar(log_text_frame,
                                      orient="vertical",
                                      command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        log_scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        # 初始化日誌
        self._log_message("系統啟動完成", "info")
        self._log_message("請載入 PDF 檔案開始使用", "info")

    def _create_status_bar(self):
        """建立狀態列"""
        status_frame = tk.Frame(self.main_container,
                                bg=self.colors['bg_panel'],
                                height=30)
        status_frame.pack(fill="x", side="bottom", padx=10, pady=(5, 10))
        status_frame.pack_propagate(False)

        # 版權資訊
        tk.Label(status_frame,
                 text="© 2025 PDF 工具包 | 作者：",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['fg_secondary'],
                 font=("Microsoft YaHei", 9)).pack(side="left", padx=10)

        # 版本資訊
        tk.Label(status_frame,
                 text=f"v{APP_VERSION}",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['info'],
                 font=("Microsoft YaHei", 9, "bold")).pack(side="right",
                                                           padx=10)

    def _setup_drag_drop(self):
        """設定拖放功能"""
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self._on_drop_files)

    def _on_drop_files(self, event):
        """處理拖放檔案事件"""
        files = self.root.splitlist(event.data)
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]

        if pdf_files:
            self._load_files(pdf_files)
        else:
            messagebox.showwarning("警告", "請拖放 PDF 檔案")

    def _browse_files(self):
        """瀏覽選擇檔案"""
        files = filedialog.askopenfilenames(title="選擇 PDF 檔案",
                                            filetypes=[("PDF 檔案", "*.pdf"),
                                                       ("所有檔案", "*.*")])

        if files:
            self._load_files(files)

    def _load_files(self, file_paths):
        """載入檔案"""
        self._log_message(f"開始載入 {len(file_paths)} 個檔案", "info")

        success_count = 0
        for file_path in file_paths:
            try:
                if file_path.lower().endswith('.pdf'):
                    self._add_pdf_file(file_path)
                    success_count += 1
                    self._log_message(f"✓ 已載入：{os.path.basename(file_path)}",
                                      "success")
                else:
                    self._log_message(f"✗ 不支援：{os.path.basename(file_path)}",
                                      "warning")
            except Exception as e:
                self._log_message(
                    f"✗ 載入失敗：{os.path.basename(file_path)} - {str(e)}",
                    "error")

        if success_count > 0:
            self._update_preview()
            self._update_file_status()
            self._log_message(f"成功載入 {success_count} 個 PDF 檔案", "success")

    def _add_pdf_file(self, file_path):
        """添加 PDF 檔案"""
        doc = fitz.open(file_path)

        # 添加到檔案列表
        self.pdf_files.append({
            'path': file_path,
            'doc': doc,
            'name': os.path.basename(file_path),
            'pages': len(doc)
        })

        # 添加頁面到預覽
        for page_index in range(len(doc)):
            self.pages.append({
                'doc': doc,
                'page_index': page_index,
                'file_name': os.path.basename(file_path),
                'file_path': file_path
            })

    def _update_preview(self):
        """更新預覽區域"""
        # 清除現有縮圖
        for widget in self.thumbnail_frame.winfo_children():
            widget.destroy()

        if not self.pages:
            # 顯示空狀態
            empty_label = tk.Label(self.thumbnail_frame,
                                   text="尚無 PDF 頁面\n請載入 PDF 檔案",
                                   bg="white",
                                   fg=self.colors['fg_secondary'],
                                   font=("Microsoft YaHei", 14),
                                   justify="center")
            empty_label.pack(expand=True, pady=50)
            return

        # 使用網格佈局顯示縮圖
        cols = 4  # 每行顯示4個縮圖
        for i, page_info in enumerate(self.pages):
            row = i // cols
            col = i % cols
            self._create_thumbnail(row, col, i, page_info)

        # 配置列權重以消除右側空白
        for col in range(cols):
            self.thumbnail_frame.columnconfigure(col, weight=1)

        # 更新 Canvas 滾動區域
        self.thumbnail_frame.update_idletasks()
        self.preview_canvas.configure(
            scrollregion=self.preview_canvas.bbox("all"))

    def _create_thumbnail(self, row, col, index, page_info):
        """建立可拖曳的縮圖"""
        try:
            doc = page_info['doc']
            page_index = page_info['page_index']
            file_name = page_info['file_name']

            # 生成縮圖
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=fitz.Matrix(0.25, 0.25))
            mode = "RGBA" if pix.alpha else "RGB"
            img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)

            # 調整縮圖大小
            max_width = 150
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)

            thumb_image = ImageTk.PhotoImage(img)

            # 建立縮圖容器
            thumb_container = tk.Frame(self.thumbnail_frame,
                                       bg="white",
                                       relief="solid",
                                       bd=1,
                                       cursor="hand2")
            thumb_container.grid(row=row,
                                 column=col,
                                 padx=5,
                                 pady=5,
                                 sticky="nsew")

            # 縮圖標籤
            thumb_label = tk.Label(thumb_container,
                                   image=thumb_image,
                                   bg="white")
            thumb_label.image = thumb_image  # 保持引用
            thumb_label.pack(pady=(10, 5))

            # 頁面資訊
            info_text = f"{file_name}\n第 {page_index + 1} 頁"
            info_label = tk.Label(thumb_container,
                                  text=info_text,
                                  bg="white",
                                  fg=self.colors['fg_primary'],
                                  font=("Microsoft YaHei", 8),
                                  justify="center")
            info_label.pack(pady=(0, 10))

            # 拖曳順序提示
            order_label = tk.Label(thumb_container,
                                   text=f"順序: {index + 1}",
                                   bg=self.colors['info'],
                                   fg="white",
                                   font=("Microsoft YaHei", 8, "bold"))
            order_label.pack(fill="x")

            # 綁定拖曳事件
            self._bind_drag_events(thumb_container, index)
            self._bind_drag_events(thumb_label, index)
            self._bind_drag_events(info_label, index)

        except Exception as e:
            self._log_message(f"建立縮圖失敗：{str(e)}", "error")

    def _bind_drag_events(self, widget, index):
        """綁定拖曳事件"""

        def on_drag_start(event):
            self.dragging_index = index
            widget.configure(relief="raised", bd=3)

        def on_drag_motion(event):
            if self.dragging_index is not None:
                # 獲取滑鼠相對於縮圖框架的位置
                x = self.thumbnail_frame.winfo_pointerx(
                ) - self.thumbnail_frame.winfo_rootx()
                y = self.thumbnail_frame.winfo_pointery(
                ) - self.thumbnail_frame.winfo_rooty()

                # 找到目標位置
                target_index = self._get_drop_target(x, y)
                if target_index != self.dragging_index and target_index is not None:
                    # 高亮目標位置
                    self._highlight_drop_target(target_index)

        def on_drag_end(event):
            if self.dragging_index is not None:
                widget.configure(relief="solid", bd=1)

                # 獲取滑鼠相對於縮圖框架的位置
                x = self.thumbnail_frame.winfo_pointerx(
                ) - self.thumbnail_frame.winfo_rootx()
                y = self.thumbnail_frame.winfo_pointery(
                ) - self.thumbnail_frame.winfo_rooty()

                # 執行拖曳排序
                target_index = self._get_drop_target(x, y)
                if target_index is not None and target_index != self.dragging_index:
                    self._reorder_pages(self.dragging_index, target_index)

                self.dragging_index = None
                self._clear_drop_highlights()

        widget.bind("<ButtonPress-1>", on_drag_start)
        widget.bind("<B1-Motion>", on_drag_motion)
        widget.bind("<ButtonRelease-1>", on_drag_end)

    def _get_drop_target(self, x, y):
        """根據滑鼠位置獲取目標索引"""
        # 簡化的目標檢測邏輯
        cols = 4
        thumbnail_width = 160  # 縮圖容器寬度（包含間距）
        thumbnail_height = 200  # 縮圖容器高度（包含間距）

        col = x // thumbnail_width
        row = y // thumbnail_height

        target_index = row * cols + col

        if 0 <= target_index < len(self.pages):
            return target_index
        return None

    def _highlight_drop_target(self, target_index):
        """高亮目標位置"""
        # 這裡可以添加視覺反饋邏輯
        pass

    def _clear_drop_highlights(self):
        """清除拖曳高亮"""
        # 這裡可以添加清除高亮的邏輯
        pass

    def _reorder_pages(self, from_index, to_index):
        """重新排序頁面"""
        if 0 <= from_index < len(self.pages) and 0 <= to_index < len(
                self.pages):
            # 移動頁面
            page = self.pages.pop(from_index)
            self.pages.insert(to_index, page)

            # 更新預覽
            self._update_preview()
            self._log_message(
                f"頁面順序已調整：從位置 {from_index + 1} 移動到 {to_index + 1}", "info")

    def _update_file_status(self):
        """更新檔案狀態顯示"""
        if self.pdf_files:
            file_count = len(self.pdf_files)
            page_count = len(self.pages)
            status_text = f"已載入 {file_count} 個檔案，共 {page_count} 頁"
            self.file_status_label.config(text=status_text,
                                          fg=self.colors['success'])
        else:
            self.file_status_label.config(text="尚未載入檔案",
                                          fg=self.colors['fg_secondary'])

    def _merge_pdfs(self):
        """合併 PDF"""
        if not self.pages:
            messagebox.showwarning("警告", "請先載入 PDF 檔案")
            return

        save_path = filedialog.asksaveasfilename(title="儲存合併後的 PDF",
                                                 defaultextension=".pdf",
                                                 filetypes=[("PDF 檔案", "*.pdf")
                                                            ])

        if not save_path:
            return

        try:
            self.progress_label.config(text="正在合併 PDF...",
                                       fg=self.colors['warning'])
            self.progress.config(mode='indeterminate')
            self.progress.start()

            # 在新執行緒中執行合併
            thread = threading.Thread(target=self._do_merge,
                                      args=(save_path, ))
            thread.daemon = True
            thread.start()

        except Exception as e:
            self._merge_error(f"合併失敗：{str(e)}")

    def _do_merge(self, save_path):
        """執行 PDF 合併（在背景執行緒中）"""
        try:
            self._log_message("開始合併 PDF 檔案", "info")

            new_doc = fitz.open()

            for i, page_info in enumerate(self.pages):
                doc = page_info['doc']
                page_index = page_info['page_index']
                new_doc.insert_pdf(doc,
                                   from_page=page_index,
                                   to_page=page_index)

                # 更新進度（在主執行緒中）
                progress = (i + 1) / len(self.pages) * 100
                self.root.after(
                    0, lambda p=progress: self._update_merge_progress(p))

            new_doc.save(save_path)
            new_doc.close()

            # 合併完成
            self.root.after(0, lambda: self._merge_complete(save_path))

        except Exception as e:
            self.root.after(0, lambda: self._merge_error(f"合併失敗：{str(e)}"))

    def _update_merge_progress(self, progress):
        """更新合併進度"""
        self.progress.config(mode='determinate')
        self.progress['value'] = progress

    def _merge_complete(self, save_path):
        """合併完成"""
        self.progress.stop()
        self.progress['value'] = 100
        self.progress_label.config(text="合併完成", fg=self.colors['success'])
        self._log_message(f"PDF 合併完成：{save_path}", "success")
        messagebox.showinfo("完成", f"PDF 已成功合併並儲存到：\n{save_path}")

        # 重置進度
        self.root.after(3000, self._reset_progress)

    def _merge_error(self, error_msg):
        """合併錯誤"""
        self.progress.stop()
        self.progress_label.config(text="合併失敗", fg=self.colors['danger'])
        self._log_message(error_msg, "error")
        messagebox.showerror("錯誤", error_msg)

        # 重置進度
        self.root.after(3000, self._reset_progress)

    def _reset_progress(self):
        """重置進度顯示"""
        self.progress['value'] = 0
        self.progress_label.config(text="就緒", fg=self.colors['success'])

    def _clear_all(self):
        """清除所有資料"""
        # 關閉所有 PDF 文件
        for pdf_file in self.pdf_files:
            try:
                pdf_file['doc'].close()
            except:
                pass

        self.pdf_files.clear()
        self.pages.clear()

        # 更新界面
        self._update_preview()
        self._update_file_status()

        self._log_message("已清除所有檔案", "info")

    def _open_signature_editor(self):
        """開啟PDF簽名編輯器"""
        if not self.pdf_files:
            messagebox.showwarning("警告", "請先載入 PDF 檔案")
            return

        # 讓用戶選擇要簽名的PDF檔案
        if len(self.pdf_files) == 1:
            # 只有一個檔案，直接使用
            selected_file = self.pdf_files[0]
        else:
            # 多個檔案，讓用戶選擇
            file_names = [pdf['name'] for pdf in self.pdf_files]
            selection_window = tk.Toplevel(self.root)
            selection_window.title("選擇要簽名的檔案")
            selection_window.geometry("400x300")
            selection_window.resizable(False, False)
            selection_window.configure(bg=self.colors['bg_main'])

            # 置中顯示
            selection_window.transient(self.root)
            selection_window.grab_set()

            # 標題
            tk.Label(selection_window,
                     text="請選擇要進行簽名的 PDF 檔案：",
                     bg=self.colors['bg_main'],
                     fg=self.colors['fg_primary'],
                     font=("Microsoft YaHei", 12, "bold")).pack(pady=20)

            # 檔案列表
            listbox_frame = tk.Frame(selection_window,
                                     bg=self.colors['bg_main'])
            listbox_frame.pack(fill="both", expand=True, padx=20, pady=10)

            listbox = tk.Listbox(listbox_frame,
                                 font=("Microsoft YaHei", 10),
                                 height=8)

            scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical")
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)

            for name in file_names:
                listbox.insert(tk.END, name)

            listbox.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # 預設選擇第一個
            listbox.selection_set(0)

            # 按鈕
            btn_frame = tk.Frame(selection_window, bg=self.colors['bg_main'])
            btn_frame.pack(fill="x", padx=20, pady=20)

            selected_index = [0]  # 使用列表來保存選擇

            def on_select():
                selection = listbox.curselection()
                if selection:
                    selected_index[0] = selection[0]
                    selection_window.destroy()

            def on_cancel():
                selected_index[0] = -1
                selection_window.destroy()

            tk.Button(btn_frame,
                      text="確定",
                      command=on_select,
                      bg=self.colors['success'],
                      fg="white",
                      font=("Microsoft YaHei", 10, "bold"),
                      width=10).pack(side="right", padx=5)

            tk.Button(btn_frame,
                      text="取消",
                      command=on_cancel,
                      bg=self.colors['secondary'],
                      fg="white",
                      font=("Microsoft YaHei", 10),
                      width=10).pack(side="right", padx=5)

            # 等待視窗關閉
            self.root.wait_window(selection_window)

            if selected_index[0] == -1:
                return  # 用戶取消

            selected_file = self.pdf_files[selected_index[0]]

        try:
            # 開啟簽名編輯器
            signature_editor = SignEditor(self.root, selected_file['path'],
                                          self._log_message)
            self._log_message(f"已開啟簽名編輯器：{selected_file['name']}", "info")

        except Exception as e:
            error_msg = f"開啟簽名編輯器失敗：{str(e)}"
            self._log_message(error_msg, "error")
            messagebox.showerror("錯誤", error_msg)

    def _open_signature_editor_with_hint(self, action_type):
        """開啟簽名編輯器並提示用戶操作"""
        if action_type == "upload":
            hint_msg = "即將開啟簽名編輯器。開啟後請點擊工具列中的「上傳簽名」按鈕選擇圖片檔案。"
        elif action_type == "draw":
            hint_msg = "即將開啟簽名編輯器。開啟後請點擊工具列中的「手寫簽名」按鈕進行手寫。"
        else:
            hint_msg = "即將開啟簽名編輯器。"

        result = messagebox.askokcancel("提示",
                                        hint_msg + "\n\n點擊「確定」繼續開啟簽名編輯器。")

        if result:
            self._open_signature_editor()

    def _split_pdf(self):
        """PDF拆分功能"""
        if not self.pdf_files:
            messagebox.showwarning("警告", "請先選擇PDF檔案")
            return

        if len(self.pdf_files) > 1:
            messagebox.showinfo("提示", "拆分功能只能處理單一PDF檔案，將使用第一個檔案")

        pdf_path = self.pdf_files[0]['path']
        try:
            split_dialog = PDFSplitDialog(self.root, pdf_path, self.colors)
            # 檢查對話框是否成功創建
            if split_dialog.winfo_exists():
                self.root.wait_window(split_dialog)
        except Exception as e:
            error_msg = f"開啟PDF拆分功能失敗：{str(e)}"
            self._log_error(error_msg, e, "PDF拆分功能")
            self._log_message(error_msg, "error")
            messagebox.showerror("錯誤", error_msg)

    def _compress_pdf(self):
        """PDF壓縮功能"""
        if not self.pdf_files:
            messagebox.showwarning("警告", "請先選擇PDF檔案")
            return

        if len(self.pdf_files) > 1:
            messagebox.showinfo("提示", "壓縮功能只能處理單一PDF檔案，將使用第一個檔案")

        pdf_path = self.pdf_files[0]['path']
        try:
            compress_dialog = PDFCompressDialog(self.root, pdf_path,
                                                self.colors)
            # 檢查對話框是否成功創建
            if compress_dialog.winfo_exists():
                self.root.wait_window(compress_dialog)
        except Exception as e:
            error_msg = f"開啟PDF壓縮功能失敗：{str(e)}"
            self._log_error(error_msg, e, "PDF壓縮功能")
            self._log_message(error_msg, "error")
            messagebox.showerror("錯誤", error_msg)

    def _show_about(self):
        """顯示關於對話框"""
        try:
            about_dialog = AboutDialog(self.root)
            self.root.wait_window(about_dialog)
        except Exception as e:
            error_msg = f"開啟關於對話框失敗：{str(e)}"
            self._log_error(error_msg, e, "關於對話框")
            messagebox.showerror("錯誤", error_msg)

    def _add_watermark(self):
        """加浮水印"""
        if not self.pdf_files:
            messagebox.showwarning("警告", "請先載入 PDF 檔案")
            return

        try:
            # 開啟浮水印對話框
            watermark_dialog = PDFWatermarkDialog(self.root, self.pdf_files,
                                                  self._log_message)
            self.root.wait_window(watermark_dialog)
        except Exception as e:
            error_msg = f"開啟浮水印功能失敗：{str(e)}"
            self._log_error(error_msg, e, "PDF浮水印功能")
            self._log_message(error_msg, "error")
            messagebox.showerror("錯誤", error_msg)

    def _log_message(self, message, level="info"):
        """記錄日誌訊息"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")

        # 設定日誌前綴和顏色
        prefixes = {
            "info": "[資訊]",
            "success": "[成功]",
            "warning": "[警告]",
            "error": "[錯誤]"
        }

        prefix = prefixes.get(level, "[資訊]")
        log_entry = f"{timestamp} {prefix} {message}\n"

        # 插入日誌
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)

        # 限制日誌長度
        lines = self.log_text.get(1.0, tk.END).count('\n')
        if lines > 500:
            self.log_text.delete(1.0, "50.0")

    def run(self):
        """啟動應用程式"""
        self._log_message("PDF 工具包已啟動", "success")
        if self.log_file_path:
            self._log_message(f"錯誤日誌檔案：{self.log_file_path}", "info")
        else:
            self._log_message("錯誤日誌系統未啟用", "warning")

        # 啟動後自動檢查更新（在背景執行）
        self.root.after(2000, self._auto_check_updates)  # 2秒後檢查

        self.root.mainloop()

    def _check_for_updates(self):
        """手動檢查更新"""
        self._log_message("檢查更新中...", "info")

        def on_update_result(result):
            # 在主執行緒中處理結果
            self.root.after(
                0, lambda: self._handle_update_result(result, manual=True))

        self.update_checker.check_for_updates(on_update_result)

    def _auto_check_updates(self):
        """自動檢查更新（靜默）"""

        def on_update_result(result):
            # 在主執行緒中處理結果
            self.root.after(
                0, lambda: self._handle_update_result(result, manual=False))

        self.update_checker.check_for_updates(on_update_result)

    def _handle_update_result(self, result, manual=False):
        """處理更新檢查結果"""
        try:
            if 'error' in result:
                if manual:  # 只有手動檢查時才顯示錯誤
                    messagebox.showerror("檢查更新失敗", result['message'])
                self._log_message(f"更新檢查失敗：{result['message']}", "error")

            elif result.get('available', False):
                # 有新版本可用
                self._log_message(f"發現新版本 v{result['version']}", "success")
                if manual or self._should_show_update_dialog(
                        result['version']):
                    # 顯示更新對話框
                    UpdateDialog(self.root, result)

            else:
                # 已是最新版本
                if manual:  # 只有手動檢查時才顯示
                    # 顯示當前版本的更新說明
                    self._show_current_version_info()
                self._log_message("已使用最新版本", "info")

        except Exception as e:
            error_msg = f"處理更新結果時發生錯誤：{str(e)}"
            self._log_message(error_msg, "error")
            if manual:
                messagebox.showerror("錯誤", error_msg)

    def _should_show_update_dialog(self, new_version):
        """判斷是否應該顯示更新對話框（自動檢查時）"""
        # 在實際應用中，這裡可以檢查用戶設置或跳過的版本
        # 現在簡單返回True，表示總是顯示
        return True

    def _show_current_version_info(self):
        """顯示當前版本的更新說明"""
        current_version_info = {
            "4.2.0": {
                "title": "PDF 工具包 v4.2.0 - 浮水印功能與日系設計更新",
                "features": [
                    "✨ 新增 PDF 浮水印功能",
                    "  • 支援文字浮水印（可調整大小、透明度、角度）",
                    "  • 支援圖片浮水印（多種位置選項）",
                    "  • 批次處理多個 PDF 檔案",
                    "  • 靈活的位置設定（中央、四角）",
                    "",
                    "🎨 全新日系配色設計",
                    "  • 採用傳統日本色彩 (nipponcolors.com 和 irocore.com)",
                    "  • 淡雪色、白茶色背景，溫暖舒適",
                    "  • 瑠璃色、常磐色等優雅配色",
                    "  • 減少眼睛疲勞，提升使用體驗",
                    "",
                    "🔧 介面優化",
                    "  • 浮水印按鈕採用柿色 (日系橘色) 設計",
                    "  • 新增關於對話框，包含詳細操作指南",
                    "  • 改善檢查更新功能，顯示當前版本資訊",
                    "  • 精簡界面，移除冗餘說明文字",
                    "",
                    "🐛 修復",
                    "  • 優化文字浮水印定位演算法",
                    "  • 改善透明度計算方式",
                    "  • 增強錯誤處理機制"
                ]
            },
            "4.1.0": {
                "title":
                "PDF 工具包 v4.1.0 - 自動更新與增強功能",
                "features":
                ["✨ 自動更新檢查功能", "🔧 修復手寫簽名位置精度", "📱 響應式設計優化", "📝 完整的更新文檔"]
            }
        }

        version_info = current_version_info.get(APP_VERSION, {
            "title": f"PDF 工具包 v{APP_VERSION}",
            "features": ["當前版本的詳細資訊暫未提供"]
        })

        # 創建對話框
        dialog = tk.Toplevel(self.root)
        dialog.title("版本資訊")
        dialog.geometry("600x500")
        dialog.resizable(True, True)
        dialog.configure(bg='#F5F5F0')
        dialog.transient(self.root)
        dialog.grab_set()

        # 主框架
        main_frame = tk.Frame(dialog, bg='#F5F5F0')
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 標題
        title_label = tk.Label(main_frame,
                               text=version_info["title"],
                               bg='#F8F9FA',
                               fg='#007BFF',
                               font=("Microsoft YaHei", 16, "bold"))
        title_label.pack(pady=(0, 15))

        # 狀態
        status_label = tk.Label(main_frame,
                                text="✅ 您正在使用最新版本！",
                                bg='#F8F9FA',
                                fg='#28A745',
                                font=("Microsoft YaHei", 12, "bold"))
        status_label.pack(pady=(0, 20))

        # 功能列表
        features_frame = tk.Frame(main_frame,
                                  bg='#FFFFFF',
                                  relief="solid",
                                  bd=1)
        features_frame.pack(fill="both", expand=True, pady=(0, 20))

        features_text = tk.Text(features_frame,
                                wrap=tk.WORD,
                                bg='#FFFFFF',
                                fg='#212529',
                                font=("Microsoft YaHei", 10),
                                padx=15,
                                pady=15,
                                relief="flat")
        features_text.pack(fill="both", expand=True)

        # 插入功能列表
        features_content = "\n".join(version_info["features"])
        features_text.insert("1.0", features_content)
        features_text.config(state="disabled")

        # 按鈕
        btn_frame = tk.Frame(main_frame, bg='#F8F9FA')
        btn_frame.pack(fill="x")

        tk.Button(btn_frame,
                  text="確定",
                  command=dialog.destroy,
                  bg='#007BFF',
                  fg="white",
                  font=("Microsoft YaHei", 12, "bold"),
                  width=15).pack(pady=10)


class SignEditor(tk.Toplevel):
    """增強的 PDF 簽名編輯器"""

    def __init__(self, master, pdf_path, log_callback=None):
        super().__init__(master)
        self.title("PDF 簽名編輯器")
        self.geometry("1200x800")
        self.resizable(True, True)

        # 設定視窗圖示（如果有的話）
        try:
            self.iconbitmap('icon.ico')
        except:
            pass

        self.pdf_path = pdf_path
        self.pdf = fitz.open(pdf_path)
        self.page_index = 0
        self.signatures = []  # 儲存多個簽名
        self.selected_signature = None  # 當前選中的簽名
        self.scale = 1.0
        self.log_callback = log_callback or (lambda msg, level: None)

        # 色系配置
        self.colors = {
            'bg_main': '#F8F9FA',
            'bg_panel': '#FFFFFF',
            'primary': '#007BFF',
            'success': '#28A745',
            'warning': '#FFC107',
            'danger': '#DC3545',
            'secondary': '#6C757D',
            'info': '#007BFF'
        }

        self._build_ui()
        self._show_page()
        self._bind_keyboard_shortcuts()

        if self.log_callback:
            self.log_callback(f"開啟簽名編輯器：{os.path.basename(pdf_path)}", "info")

    def _bind_keyboard_shortcuts(self):
        """綁定鍵盤快捷鍵"""

        def on_key_press(event):
            if self.selected_signature:
                # 處理放大功能 - 多種可能的按鍵
                if (event.char in ['+', '=']
                        or event.keysym in ['plus', 'equal', 'KP_Add']
                        or (event.keysym == 'equal'
                            and event.state & 0x1)):  # Shift + =
                    self._scale_selected_signature(1.2)
                    return "break"
                # 處理縮小功能
                elif event.char == '-' or event.keysym in [
                        'minus', 'KP_Subtract'
                ]:
                    self._scale_selected_signature(0.8)
                    return "break"
                # 處理重設功能
                elif event.char == '0' or event.keysym in ['0', 'KP_0']:
                    self._reset_selected_signature()
                    return "break"
                # 處理刪除功能
                elif event.keysym in ['Delete', 'KP_Delete', 'BackSpace']:
                    self._delete_selected_signature()
                    return "break"
            else:
                # 沒有選中簽名時的提示
                if (event.char in ['+', '=', '-', '0'] or event.keysym
                        in ['Delete', 'BackSpace', 'plus', 'minus']):
                    self.log_callback("請先點擊選中一個簽名", "warning")

        # 綁定到視窗和 Canvas
        self.bind('<KeyPress>', on_key_press)
        self.canvas.bind('<KeyPress>', on_key_press)

        # 確保視窗可以接收鍵盤事件
        self.focus_set()

        # 簡化Canvas點擊事件處理
        def on_canvas_click(event):
            self.focus_set()
            self.canvas.focus_set()

            # 檢查點擊位置
            clicked_items = self.canvas.find_overlapping(
                event.x, event.y, event.x, event.y)
            self.log_callback(
                f"Canvas點擊 ({event.x}, {event.y})，項目：{clicked_items}", "info")

            # 檢查是否點擊了簽名
            signature_found = False
            for item in clicked_items:
                # 檢查這個item是否屬於某個簽名
                for sig in self.signatures:
                    if sig.get('canvas_id') == item:
                        signature_found = True
                        self.log_callback(f"通過Canvas ID找到簽名：{sig['id']}",
                                          "info")
                        break
                if signature_found:
                    break

            # 只有當沒有簽名正在拖曳時才處理空白區域點擊
            if not signature_found:
                dragging_signature = any(
                    sig.get('dragging', False) for sig in self.signatures)
                if not dragging_signature:
                    self.log_callback("點擊空白區域，取消選中", "info")
                    self.selected_signature = None
                    self._update_selection_visual()
                    self._update_selected_info()

        self.canvas.bind('<Button-1>', on_canvas_click)

    def _delete_selected_signature(self):
        """刪除選中的簽名"""
        if self.selected_signature:
            if messagebox.askyesno("確認", "確定要刪除選中的簽名嗎？"):
                self.signatures.remove(self.selected_signature)
                self.selected_signature = None
                self._redraw_signatures()
                self._update_selected_info()
                self.log_callback("已刪除選中的簽名", "info")

    def _test_signature(self):
        """測試簽名功能"""
        try:
            self.log_callback("開始測試簽名功能", "info")

            # 創建一個簡單的測試圖片
            test_img = Image.new('RGBA', (200, 60), (255, 255, 255, 0))
            draw = ImageDraw.Draw(test_img)

            # 繪製測試簽名
            try:
                # 嘗試使用預設字體
                draw.text((10, 10), "Test Signature", fill="black")
            except:
                # 如果字體失敗，用簡單圖形
                draw.rectangle([10, 10, 180, 30], outline="black", width=2)
                draw.text((15, 15), "TEST", fill="black")

            draw.rectangle([10, 35, 190, 50], outline="red", width=2)
            draw.text((15, 37), f"ID: {len(self.signatures) + 1}", fill="red")

            self._add_signature(test_img, "test")
            self.log_callback("測試簽名已添加", "success")

        except Exception as e:
            self.log_callback(f"測試簽名失敗：{str(e)}", "error")

    def _update_selected_info(self):
        """更新選中簽名的資訊顯示"""
        if self.selected_signature:
            sig = self.selected_signature
            scale = sig.get('scale_factor', 1.0)
            info_text = f"已選中簽名 #{sig['id']} | 縮放: {scale:.1f}x | 類型: {sig['type']}"
            self.signature_info_label.config(text=info_text)
        else:
            total_sigs = len(
                [s for s in self.signatures if s['page'] == self.page_index])
            if total_sigs > 0:
                self.signature_info_label.config(
                    text=f"本頁共 {total_sigs} 個簽名 - 點擊簽名進行選擇")
            else:
                self.signature_info_label.config(text="")

    def _build_ui(self):
        """建立使用者界面"""
        self.configure(bg=self.colors['bg_main'])

        # 標題區域
        self._create_title_section()

        # 工具列
        self._create_toolbar()

        # 主要內容區域
        self._create_main_content()

        # 底部狀態列
        self._create_status_section()

    def _create_title_section(self):
        """建立標題區域"""
        title_frame = tk.Frame(self, bg=self.colors['bg_panel'], height=60)
        title_frame.pack(fill="x", padx=10, pady=(10, 5))
        title_frame.pack_propagate(False)

        tk.Label(title_frame,
                 text="PDF 簽名編輯器",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['primary'],
                 font=("Microsoft YaHei", 16, "bold")).pack(side="left",
                                                            padx=15,
                                                            pady=15)

        tk.Label(title_frame,
                 text=f"檔案：{os.path.basename(self.pdf_path)}",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['secondary'],
                 font=("Microsoft YaHei", 10)).pack(side="right",
                                                    padx=15,
                                                    pady=15)

    def _create_toolbar(self):
        """建立工具列"""
        toolbar = tk.Frame(self, bg=self.colors['bg_panel'], height=140)
        toolbar.pack(fill="x", padx=10, pady=5)
        toolbar.pack_propagate(False)

        # 左側：頁面控制
        page_frame = tk.Frame(toolbar, bg=self.colors['bg_panel'])
        page_frame.pack(side="left", padx=15, pady=10)

        tk.Label(page_frame,
                 text="頁面導航：",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['secondary'],
                 font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")

        nav_frame = tk.Frame(page_frame, bg=self.colors['bg_panel'])
        nav_frame.pack(fill="x", pady=5)

        tk.Button(nav_frame,
                  text="上一頁",
                  command=lambda: self._turn_page(-1),
                  bg=self.colors['secondary'],
                  fg="white",
                  font=("Microsoft YaHei", 9),
                  width=8).pack(side="left", padx=2)

        self.page_label = tk.Label(nav_frame,
                                   text=f"第 1 頁 / 共 {len(self.pdf)} 頁",
                                   bg=self.colors['bg_panel'],
                                   fg=self.colors['primary'],
                                   font=("Microsoft YaHei", 10, "bold"))
        self.page_label.pack(side="left", padx=10)

        tk.Button(nav_frame,
                  text="下一頁",
                  command=lambda: self._turn_page(1),
                  bg=self.colors['secondary'],
                  fg="white",
                  font=("Microsoft YaHei", 9),
                  width=8).pack(side="left", padx=2)

        # 中間：簽名控制
        sign_frame = tk.Frame(toolbar, bg=self.colors['bg_panel'])
        sign_frame.pack(side="left", padx=30, pady=10)

        tk.Label(sign_frame,
                 text="簽名工具：",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['secondary'],
                 font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")

        sign_btn_frame = tk.Frame(sign_frame, bg=self.colors['bg_panel'])
        sign_btn_frame.pack(fill="x", pady=5)

        tk.Button(sign_btn_frame,
                  text="📁 上傳簽名",
                  command=self._upload_signature,
                  bg=self.colors['primary'],
                  fg="white",
                  font=("Microsoft YaHei", 9),
                  width=10).pack(side="left", padx=2)

        tk.Button(sign_btn_frame,
                  text="手寫簽名",
                  command=self._draw_signature,
                  bg=self.colors['success'],
                  fg="white",
                  font=("Microsoft YaHei", 9),
                  width=10).pack(side="left", padx=2)

        tk.Button(sign_btn_frame,
                  text="插入文字",
                  command=self._insert_text,
                  bg=self.colors['info'],
                  fg="white",
                  font=("Microsoft YaHei", 9),
                  width=10).pack(side="left", padx=2)

        tk.Button(sign_btn_frame,
                  text="清除簽名",
                  command=self._clear_signatures,
                  bg=self.colors['warning'],
                  fg="white",
                  font=("Microsoft YaHei", 9),
                  width=10).pack(side="left", padx=2)

        # 第二行：簽名控制按鈕
        control_label_frame = tk.Frame(sign_frame, bg=self.colors['bg_panel'])
        control_label_frame.pack(fill="x", pady=(10, 0))

        tk.Label(control_label_frame,
                 text="簽名控制：",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['secondary'],
                 font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")

        control_btn_frame = tk.Frame(sign_frame, bg=self.colors['bg_panel'])
        control_btn_frame.pack(fill="x", pady=2)

        tk.Button(control_btn_frame,
                  text="🔍+ 放大",
                  command=lambda: self._scale_selected_signature(1.2),
                  bg="#28a745",
                  fg="white",
                  font=("Microsoft YaHei", 8),
                  width=9).pack(side="left", padx=1)

        tk.Button(control_btn_frame,
                  text="🔍- 縮小",
                  command=lambda: self._scale_selected_signature(0.8),
                  bg="#17a2b8",
                  fg="white",
                  font=("Microsoft YaHei", 8),
                  width=9).pack(side="left", padx=1)

        tk.Button(control_btn_frame,
                  text="↺ 重設",
                  command=self._reset_selected_signature,
                  bg="#6c757d",
                  fg="white",
                  font=("Microsoft YaHei", 8),
                  width=8).pack(side="left", padx=1)

        tk.Button(control_btn_frame,
                  text="🗑 刪除",
                  command=self._delete_selected_signature,
                  bg="#dc3545",
                  fg="white",
                  font=("Microsoft YaHei", 8),
                  width=8).pack(side="left", padx=1)

        # 添加測試按鈕
        tk.Button(control_btn_frame,
                  text="🧪 測試",
                  command=self._test_signature,
                  bg="#6f42c1",
                  fg="white",
                  font=("Microsoft YaHei", 8),
                  width=8).pack(side="left", padx=1)

        # 右側：儲存控制
        save_frame = tk.Frame(toolbar, bg=self.colors['bg_panel'])
        save_frame.pack(side="right", padx=15, pady=10)

        tk.Label(save_frame,
                 text="儲存選項：",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['secondary'],
                 font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")

        save_btn_frame = tk.Frame(save_frame, bg=self.colors['bg_panel'])
        save_btn_frame.pack(fill="x", pady=5)

        tk.Button(save_btn_frame,
                  text="儲存 PDF",
                  command=self._save_pdf,
                  bg=self.colors['danger'],
                  fg="white",
                  font=("Microsoft YaHei", 10, "bold"),
                  width=12).pack(side="right")

    def _create_main_content(self):
        """建立主要內容區域"""
        content_frame = tk.Frame(self, bg=self.colors['bg_main'])
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 說明區域
        info_frame = tk.Frame(content_frame,
                              bg=self.colors['bg_panel'],
                              height=120)
        info_frame.pack(fill="x", pady=(0, 5))
        info_frame.pack_propagate(False)

        instruction_text = """操作說明：
1. 📝 點擊「上傳簽名」、「手寫簽名」或「插入文字」添加內容  2. 👆 點擊簽名/文字選中（會顯示紅色虛線框）
3. 🖱️ 按住並拖曳移動位置  4. 🔍 使用工具列按鈕或鍵盤快捷鍵縮放  5. 💾 點擊「儲存PDF」完成

💡 快捷鍵：+ 或 = 放大 | - 縮小 | 0 重設大小 | Delete 刪除選中項目
📌 提示：添加的內容會自動出現在頁面下方，立即被選中可直接操作"""

        tk.Label(info_frame,
                 text=instruction_text,
                 bg=self.colors['bg_panel'],
                 fg=self.colors['secondary'],
                 font=("Microsoft YaHei", 9),
                 justify="left").pack(expand=True, pady=10)

        # PDF 顯示區域
        pdf_frame = tk.Frame(content_frame, bg=self.colors['bg_panel'])
        pdf_frame.pack(fill="both", expand=True)

        # Canvas 和滾動條
        canvas_frame = tk.Frame(pdf_frame, bg=self.colors['bg_panel'])
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(canvas_frame,
                                bg="#FFFFFF",
                                highlightthickness=1,
                                highlightbackground=self.colors['secondary'],
                                takefocus=True)

        # 滾動條
        v_scrollbar = ttk.Scrollbar(canvas_frame,
                                    orient="vertical",
                                    command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame,
                                    orient="horizontal",
                                    command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=v_scrollbar.set,
                              xscrollcommand=h_scrollbar.set)

        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

    def _create_status_section(self):
        """建立狀態區域"""
        status_frame = tk.Frame(self, bg=self.colors['bg_panel'], height=40)
        status_frame.pack(fill="x", side="bottom", padx=10, pady=(5, 10))
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(status_frame,
                                     text="就緒 - 請添加簽名",
                                     bg=self.colors['bg_panel'],
                                     fg=self.colors['success'],
                                     font=("Microsoft YaHei", 10))
        self.status_label.pack(side="left", padx=15, pady=10)

        # 簽名資訊顯示
        self.signature_info_label = tk.Label(status_frame,
                                             text="",
                                             bg=self.colors['bg_panel'],
                                             fg=self.colors['primary'],
                                             font=("Microsoft YaHei", 9))
        self.signature_info_label.pack(side="left", padx=15, pady=10)

        tk.Label(status_frame,
                 text=f"總頁數：{len(self.pdf)}",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['secondary'],
                 font=("Microsoft YaHei", 9)).pack(side="right",
                                                   padx=15,
                                                   pady=10)

    def _show_page(self):
        """顯示 PDF 頁面"""
        self.canvas.delete("all")

        try:
            page = self.pdf.load_page(self.page_index)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

            # 等待 Canvas 初始化完成
            self.canvas.update_idletasks()

            # 調整頁面大小以適應 Canvas - 使用更激進的全頁顯示
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # 確保 Canvas 已經有實際尺寸
            if canvas_width > 100 and canvas_height > 100:
                img_width, img_height = img.size

                # 計算縮放比例 - 讓PDF幾乎填滿整個區域，增加縮放係數
                width_ratio = (canvas_width - 20) / img_width  # 留20像素邊距
                height_ratio = (canvas_height - 20) / img_height  # 留20像素邊距
                self.scale = min(width_ratio, height_ratio, 5.0)  # 允許放大到5倍

                # 如果縮放比例太小，至少保持一個合理的最小縮放
                self.scale = max(self.scale, 1.0)

                if self.scale != 1.0:
                    new_width = int(img_width * self.scale)
                    new_height = int(img_height * self.scale)
                    img = img.resize((new_width, new_height), Image.LANCZOS)
            else:
                # Canvas 還沒準備好，使用較大的預設縮放
                self.scale = 2.0
                img_width, img_height = img.size
                new_width = int(img_width * self.scale)
                new_height = int(img_height * self.scale)
                img = img.resize((new_width, new_height), Image.LANCZOS)

            self.page_tk = ImageTk.PhotoImage(img)

            # 居中顯示 PDF 頁面
            canvas_width = max(self.canvas.winfo_width(), 100)
            canvas_height = max(self.canvas.winfo_height(), 100)
            canvas_center_x = canvas_width // 2
            canvas_center_y = canvas_height // 2

            self.canvas.create_image(canvas_center_x,
                                     canvas_center_y,
                                     image=self.page_tk,
                                     anchor="center",
                                     tags="page")

            # 更新滾動區域
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

            # 重新放置簽名
            self._redraw_signatures()

            # 更新頁面標籤
            self.page_label.config(
                text=f"第 {self.page_index + 1} 頁 / 共 {len(self.pdf)} 頁")

            self.log_callback(f"顯示第 {self.page_index + 1} 頁", "info")

        except Exception as e:
            self.log_callback(f"顯示頁面失敗：{str(e)}", "error")

    def _turn_page(self, delta):
        """翻頁"""
        new_index = self.page_index + delta
        if 0 <= new_index < len(self.pdf):
            self.page_index = new_index
            self.selected_signature = None  # 切換頁面時取消選中
            self._show_page()
            self._update_selected_info()
        else:
            if delta > 0:
                messagebox.showinfo("提示", "已經是最後一頁")
            else:
                messagebox.showinfo("提示", "已經是第一頁")

    def _upload_signature(self):
        """上傳簽名圖片"""
        try:
            self.log_callback("開始上傳簽名圖片", "info")

            filetypes = [("圖片檔案", "*.png *.jpg *.jpeg *.gif *.bmp"),
                         ("PNG 檔案", "*.png"), ("JPEG 檔案", "*.jpg *.jpeg"),
                         ("所有檔案", "*.*")]

            file_path = filedialog.askopenfilename(title="選擇簽名圖片",
                                                   filetypes=filetypes)

            if file_path:
                self.log_callback(f"選擇了檔案：{file_path}", "info")
                try:
                    signature_img = Image.open(file_path)
                    # 確保圖片有效
                    signature_img.load()
                    self.log_callback("圖片載入成功，正在添加簽名", "info")
                    self._add_signature(signature_img, "uploaded")
                    self.log_callback(f"已上傳簽名：{os.path.basename(file_path)}",
                                      "success")
                    self.status_label.config(text="簽名已上傳 - 已自動選中可操作",
                                             fg=self.colors['success'])
                except Exception as e:
                    self.log_callback(f"上傳簽名失敗：{str(e)}", "error")
                    messagebox.showerror("錯誤", f"無法載入圖片：{str(e)}")
            else:
                self.log_callback("用戶取消了檔案選擇", "info")
        except Exception as e:
            self.log_callback(f"上傳簽名過程出錯：{str(e)}", "error")
            messagebox.showerror("錯誤", f"上傳過程出錯：{str(e)}")

    def _insert_text(self):
        """插入文字"""
        text_dialog = TextInsertDialog(self, self.colors)
        self.wait_window(text_dialog)

        # 檢查是否有輸入內容
        if hasattr(text_dialog, 'result') and text_dialog.result:
            text_content = text_dialog.result['text']
            font_name = text_dialog.result['font_name']
            font_size = text_dialog.result['font_size']
            text_color = text_dialog.result['color']

            if text_content.strip():
                self.log_callback(f"準備插入文字：{text_content}", "info")
                self._create_text_image(text_content, font_name, font_size,
                                        text_color)
            else:
                messagebox.showwarning("警告", "請輸入要插入的文字")

    def _create_text_image(self, text_content, font_name, font_size,
                           text_color):
        """創建文字圖片並添加為簽名"""
        try:
            from PIL import ImageFont

            # 嘗試載入字體
            try:
                if font_name == "Microsoft YaHei":
                    font = ImageFont.truetype("msyh.ttc", font_size)
                elif font_name == "SimSun":
                    font = ImageFont.truetype("simsun.ttc", font_size)
                elif font_name == "Arial":
                    font = ImageFont.truetype("arial.ttf", font_size)
                else:
                    font = ImageFont.load_default()
            except:
                # 如果無法載入指定字體，使用預設字體
                font = ImageFont.load_default()
                self.log_callback("使用預設字體", "warning")

            # 計算文字尺寸
            # 創建臨時圖片來測量文字大小
            temp_img = Image.new('RGBA', (1, 1), (255, 255, 255, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            bbox = temp_draw.textbbox((0, 0), text_content, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 添加邊距
            padding = 10
            img_width = text_width + padding * 2
            img_height = text_height + padding * 2

            # 創建文字圖片（透明背景）
            text_img = Image.new('RGBA', (img_width, img_height),
                                 (255, 255, 255, 0))
            draw = ImageDraw.Draw(text_img)

            # 繪製文字
            draw.text((padding, padding),
                      text_content,
                      font=font,
                      fill=text_color)

            # 將文字圖片添加為簽名
            self._add_signature(text_img, "text")
            self.log_callback(f"文字插入成功：{text_content}", "success")

        except Exception as e:
            error_msg = f"創建文字圖片失敗：{str(e)}"
            self.log_callback(error_msg, "error")
            messagebox.showerror("錯誤", error_msg)

    def _draw_signature(self):
        """手寫簽名"""
        # 獲取父視窗大小來調整子視窗
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()

        # 計算合適的視窗大小（響應式）
        window_width = min(700, parent_width - 100)
        window_height = min(500, parent_height - 100)
        canvas_width = window_width - 80
        canvas_height = window_height - 200

        draw_window = tk.Toplevel(self)
        draw_window.title("手寫簽名")
        draw_window.geometry(f"{window_width}x{window_height}")
        draw_window.resizable(True, True)
        draw_window.configure(bg=self.colors['bg_main'])

        # 置中顯示
        draw_window.transient(self)

        # 計算置中位置
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        draw_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # 確保視窗可以關閉
        draw_window.protocol("WM_DELETE_WINDOW", draw_window.destroy)

        # 標題
        title_frame = tk.Frame(draw_window, bg=self.colors['bg_panel'])
        title_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(title_frame,
                 text="手寫簽名",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['primary'],
                 font=("Microsoft YaHei", 14, "bold")).pack(pady=5)

        # 按鈕區域 - 移到上方
        btn_frame = tk.Frame(draw_window, bg=self.colors['bg_main'])
        btn_frame.pack(fill="x", padx=20, pady=10)

        # 創建按鈕容器
        btn_container = tk.Frame(btn_frame, bg=self.colors['bg_main'])
        btn_container.pack()

        # 定義按鈕功能（提前定義，稍後會定義畫布相關變數）
        def clear_signature_func():
            pass  # 稍後會重新定義

        def finish_signature_func():
            pass  # 稍後會重新定義

        # 按鈕
        clear_btn = tk.Button(btn_container,
                              text="清除",
                              command=clear_signature_func,
                              bg=self.colors['warning'],
                              fg="white",
                              font=("Microsoft YaHei", 11),
                              width=10,
                              height=2)
        clear_btn.pack(side="left", padx=10)

        finish_btn = tk.Button(btn_container,
                               text="完成",
                               command=finish_signature_func,
                               bg=self.colors['success'],
                               fg="white",
                               font=("Microsoft YaHei", 11, "bold"),
                               width=10,
                               height=2)
        finish_btn.pack(side="left", padx=10)

        cancel_btn = tk.Button(btn_container,
                               text="取消",
                               command=draw_window.destroy,
                               bg=self.colors['secondary'],
                               fg="white",
                               font=("Microsoft YaHei", 11),
                               width=10,
                               height=2)
        cancel_btn.pack(side="left", padx=10)

        # 說明
        instruction_frame = tk.Frame(draw_window, bg=self.colors['bg_main'])
        instruction_frame.pack(pady=5)

        tk.Label(instruction_frame,
                 text="請在下方白色區域手寫您的簽名（按住滑鼠左鍵繪製）",
                 bg=self.colors['bg_main'],
                 fg=self.colors['secondary'],
                 font=("Microsoft YaHei", 10)).pack()

        tk.Label(instruction_frame,
                 text="完成繪製後點擊上方「完成」按鈕即可添加簽名到PDF",
                 bg=self.colors['bg_main'],
                 fg=self.colors['info'],
                 font=("Microsoft YaHei", 9)).pack()

        # 畫布容器
        canvas_container = tk.Frame(draw_window, bg=self.colors['bg_main'])
        canvas_container.pack(expand=True, fill="both", padx=20, pady=10)

        # 確保畫布尺寸合理
        canvas_width = max(canvas_width, 400)
        canvas_height = max(canvas_height, 250)

        # 畫布區域
        draw_canvas = tk.Canvas(canvas_container,
                                width=canvas_width,
                                height=canvas_height,
                                bg="white",
                                relief="solid",
                                bd=2,
                                cursor="pencil",
                                highlightthickness=1,
                                highlightbackground="#cccccc")
        draw_canvas.pack(expand=False, pady=10)  # 不要讓畫布自動擴展

        # 建立簽名圖片
        signature_image = Image.new("RGBA", (canvas_width, canvas_height),
                                    (255, 255, 255, 0))
        draw_obj = ImageDraw.Draw(signature_image)

        # 繪圖變數
        drawing = False
        last_x, last_y = 0, 0

        def start_draw(event):
            nonlocal drawing, last_x, last_y
            drawing = True
            last_x, last_y = event.x, event.y

        def draw_line(event):
            nonlocal last_x, last_y
            if drawing:
                x, y = event.x, event.y
                # 在 Canvas 上繪製
                draw_canvas.create_line(last_x,
                                        last_y,
                                        x,
                                        y,
                                        fill="black",
                                        width=4,
                                        capstyle=tk.ROUND,
                                        smooth=tk.TRUE,
                                        joinstyle=tk.ROUND)
                # 在圖片上繪製（使用圓形筆刷效果）
                draw_obj.line((last_x, last_y, x, y), fill="black", width=4)
                # 在線條端點繪製圓點，使線條更平滑
                draw_obj.ellipse((x - 2, y - 2, x + 2, y + 2), fill="black")
                last_x, last_y = x, y

        def stop_draw(event):
            nonlocal drawing
            drawing = False

        # 重新定義按鈕功能，現在畫布變數已經可用
        def clear_signature():
            draw_canvas.delete("all")
            nonlocal signature_image, draw_obj
            signature_image = Image.new("RGBA", (canvas_width, canvas_height),
                                        (255, 255, 255, 0))
            draw_obj = ImageDraw.Draw(signature_image)

        def finish_signature():
            # 檢查是否有繪製內容
            try:
                bbox = signature_image.getbbox()
                if bbox:
                    # 裁剪簽名圖片，去除空白區域
                    cropped_signature = signature_image.crop(bbox)
                    self._add_signature(cropped_signature, "handwritten")
                    draw_window.destroy()
                    self.log_callback("手寫簽名已完成", "success")
                    self.status_label.config(text="手寫簽名完成 - 已自動選中可操作",
                                             fg=self.colors['success'])
                else:
                    messagebox.showwarning("警告", "請先繪製簽名")
            except Exception as e:
                self.log_callback(f"完成簽名失敗：{str(e)}", "error")
                messagebox.showerror("錯誤", f"處理簽名失敗：{str(e)}")

        # 更新按鈕的command
        clear_btn.config(command=clear_signature)
        finish_btn.config(command=finish_signature)

        # 綁定繪圖事件
        draw_canvas.bind('<Button-1>', start_draw)
        draw_canvas.bind('<B1-Motion>', draw_line)
        draw_canvas.bind('<ButtonRelease-1>', stop_draw)

        # 響應式調整函數
        def on_window_resize(event):
            if event.widget == draw_window:
                try:
                    new_width = event.width
                    new_height = event.height
                    new_canvas_width = new_width - 80
                    new_canvas_height = new_height - 200

                    if new_canvas_width > 200 and new_canvas_height > 100:
                        draw_canvas.config(width=new_canvas_width,
                                           height=new_canvas_height)
                except Exception as e:
                    pass  # 忽略調整錯誤

        draw_window.bind('<Configure>', on_window_resize)

    def _add_signature(self, signature_img, signature_type):
        """添加簽名到當前頁面"""
        # 調整簽名大小
        signature_copy = signature_img.copy()

        # 根據類型調整大小
        if signature_type == "handwritten":
            # 手寫簽名可能需要裁剪空白區域
            bbox = signature_copy.getbbox()
            if bbox:
                signature_copy = signature_copy.crop(bbox)

        # 設定合適的簽名尺寸
        if signature_type == "handwritten":
            # 手寫簽名保持原始比例，但限制最大尺寸
            max_width, max_height = 250, 120
        else:
            # 上傳的圖片簽名可以稍大一些
            max_width, max_height = 300, 150

        # 只有當圖片超過最大尺寸時才進行縮放
        if signature_copy.width > max_width or signature_copy.height > max_height:
            signature_copy.thumbnail((max_width, max_height), Image.LANCZOS)

        # 建立簽名物件 - 使用PDF座標系統
        # 獲取PDF頁面尺寸
        page = self.pdf.load_page(self.page_index)
        page_rect = page.rect
        pdf_width = page_rect.width
        pdf_height = page_rect.height

        # 計算簽名的預設位置（PDF中央偏下，以PDF坐標為準）
        # 使用縮放後的圖片尺寸來計算位置
        default_x = (pdf_width - signature_copy.width) / 2
        default_y = pdf_height * 0.7  # PDF頁面70%高度的位置

        # 確保位置在合理範圍內
        safe_x = max(50, min(default_x, pdf_width - signature_copy.width - 50))
        safe_y = max(50, min(default_y,
                             pdf_height - signature_copy.height - 50))

        signature_obj = {
            'image': signature_copy,
            'original_image': signature_copy.copy(),  # 保存原始圖片用於縮放
            'page': self.page_index,
            'x': safe_x,  # 使用安全的PDF坐標
            'y': safe_y,  # 使用安全的PDF坐標
            'type': signature_type,
            'id': len(self.signatures) + 1,
            'scale_factor': 1.0  # 縮放係數
        }

        self.signatures.append(signature_obj)

        # 記錄簽名添加的詳細信息
        self.log_callback(
            f"添加{signature_type}簽名: PDF坐標=({safe_x:.1f}, {safe_y:.1f}), "
            f"圖片尺寸=({signature_copy.width}, {signature_copy.height})", "info")

        self._redraw_signatures()

        # 自動選中新添加的簽名
        self.selected_signature = signature_obj
        self._update_selected_info()

        # 更新狀態提示
        self.status_label.config(text=f"簽名已添加並選中 - 可使用鍵盤 +/- 縮放或拖曳移動",
                                 fg=self.colors['success'])

    def _redraw_signatures(self):
        """重新繪製所有簽名"""
        # 清除舊的簽名顯示 - 使用新的標籤系統
        for sig in self.signatures:
            if 'canvas_id' in sig:
                self.canvas.delete(sig['canvas_id'])
            if 'frame_id' in sig:
                self.canvas.delete(sig['frame_id'])

        # 繪製當前頁面的簽名
        for signature in self.signatures:
            if signature['page'] == self.page_index:
                self._draw_signature_on_canvas(signature)

    def _draw_signature_on_canvas(self, signature):
        """在 Canvas 上繪製簽名"""
        try:
            # 根據縮放係數調整簽名圖片
            scale_factor = signature.get('scale_factor', 1.0)
            original_img = signature['original_image']

            # 應用縮放
            if scale_factor != 1.0:
                new_width = int(original_img.width * scale_factor)
                new_height = int(original_img.height * scale_factor)
                scaled_img = original_img.resize((new_width, new_height),
                                                 Image.LANCZOS)
            else:
                scaled_img = original_img

            # 更新簽名圖片
            signature['image'] = scaled_img
            signature_tk = ImageTk.PhotoImage(scaled_img)

            # 將PDF坐標轉換為Canvas坐標
            page_bbox = self.canvas.bbox("page")
            if page_bbox:
                page_left, page_top = page_bbox[0], page_bbox[1]
                # PDF坐標轉Canvas坐標
                display_x = page_left + (signature['x'] * self.scale)
                display_y = page_top + (signature['y'] * self.scale)

                # 調試記錄座標轉換
                self.log_callback(
                    f"簽名 {signature['id']} 座標轉換: PDF坐標=({signature['x']:.1f}, {signature['y']:.1f}) "
                    f"-> Canvas坐標=({display_x:.1f}, {display_y:.1f}), scale={self.scale:.2f}",
                    "debug")
            else:
                # 後備方案：直接使用PDF坐標
                display_x = signature['x']
                display_y = signature['y']
                self.log_callback("無法獲取頁面邊界，使用PDF坐標作為Canvas坐標", "warning")

            # 創建簽名圖片 - 使用簡單的標籤系統
            signature_tag = f"sig_{signature['id']}"
            signature_id = self.canvas.create_image(display_x,
                                                    display_y,
                                                    image=signature_tk,
                                                    anchor="nw",
                                                    tags=signature_tag)

            self.log_callback(
                f"創建簽名 {signature['id']} 在位置 ({display_x}, {display_y}), Canvas ID: {signature_id}",
                "info")

            # 如果是選中的簽名，添加選中框
            if signature == self.selected_signature:
                x1, y1 = display_x - 3, display_y - 3
                x2, y2 = display_x + scaled_img.width + 3, display_y + scaled_img.height + 3
                frame_id = self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    outline="red",
                    width=2,
                    dash=(5, 5),
                    tags=f"{signature_tag}_frame")
                signature['frame_id'] = frame_id

            # 保持圖片引用
            signature['tk_image'] = signature_tk
            signature['canvas_id'] = signature_id

            # 直接綁定到Canvas項目ID
            self._bind_signature_events_simple(signature, signature_id)

        except Exception as e:
            self.log_callback(f"繪製簽名失敗：{str(e)}", "error")

    def _bind_signature_events_simple(self, signature, canvas_id):
        """簡化的簽名事件綁定"""

        def on_click(event):
            old_selected = self.selected_signature
            self.selected_signature = signature

            # 只有當選中的簽名改變時才重繪，避免破壞拖曳狀態
            if old_selected != signature:
                self._update_selection_visual()
                self._update_selected_info()

            self.canvas.focus_set()
            self.focus_force()
            signature['dragging'] = True
            signature['drag_start_x'] = event.x
            signature['drag_start_y'] = event.y
            self.log_callback(f"選中簽名 {signature['id']}", "success")

        def on_drag(event):
            if signature.get('dragging', False):
                dx = event.x - signature['drag_start_x']
                dy = event.y - signature['drag_start_y']
                self.canvas.move(canvas_id, dx, dy)
                if 'frame_id' in signature:
                    self.canvas.move(signature['frame_id'], dx, dy)
                signature['drag_start_x'] = event.x
                signature['drag_start_y'] = event.y

        def on_release(event):
            if signature.get('dragging', False):
                signature['dragging'] = False
                coords = self.canvas.coords(canvas_id)
                if coords:
                    # 轉換Canvas坐標到PDF坐標
                    try:
                        page_bbox = self.canvas.bbox("page")
                        if page_bbox:
                            page_left, page_top = page_bbox[0], page_bbox[1]
                            # 更新相對於PDF的位置（考慮縮放）
                            # 確保座標轉換的精確性
                            pdf_x = (coords[0] - page_left) / self.scale
                            pdf_y = (coords[1] - page_top) / self.scale

                            # 驗證PDF坐標的合理性
                            page = self.pdf.load_page(signature['page'])
                            page_rect = page.rect
                            pdf_width, pdf_height = page_rect.width, page_rect.height

                            # 確保坐標在PDF範圍內
                            signature['x'] = max(
                                0,
                                min(pdf_x,
                                    pdf_width - signature['image'].width))
                            signature['y'] = max(
                                0,
                                min(pdf_y,
                                    pdf_height - signature['image'].height))

                            self.log_callback(
                                f"簽名移動到 PDF坐標 ({signature['x']:.1f}, {signature['y']:.1f})",
                                "info")
                        else:
                            # 如果無法獲取PDF邊界，使用Canvas坐標作為後備
                            signature['x'] = coords[0]
                            signature['y'] = coords[1]
                            self.log_callback(
                                f"簽名移動到 Canvas坐標 ({signature['x']:.1f}, {signature['y']:.1f})",
                                "warning")
                    except Exception as e:
                        # 發生錯誤時使用Canvas坐標作為後備
                        signature['x'] = coords[0]
                        signature['y'] = coords[1]
                        self.log_callback(f"坐標轉換失敗，使用Canvas坐標：{str(e)}",
                                          "warning")

        # 綁定事件到Canvas項目
        self.canvas.tag_bind(canvas_id, "<Button-1>", on_click)
        self.canvas.tag_bind(canvas_id, "<B1-Motion>", on_drag)
        self.canvas.tag_bind(canvas_id, "<ButtonRelease-1>", on_release)

        # 游標效果
        self.canvas.tag_bind(canvas_id, "<Enter>",
                             lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(canvas_id, "<Leave>",
                             lambda e: self.canvas.config(cursor="arrow"))

        self.log_callback(f"已綁定簽名 {signature['id']} 事件到 Canvas ID {canvas_id}",
                          "info")

    def _update_selection_visual(self):
        """更新選中框視覺效果，不重繪簽名"""
        # 清除所有舊的選中框
        for sig in self.signatures:
            if 'frame_id' in sig:
                self.canvas.delete(sig['frame_id'])
                del sig['frame_id']

        # 為選中的簽名添加選中框
        if self.selected_signature and 'canvas_id' in self.selected_signature:
            try:
                canvas_id = self.selected_signature['canvas_id']
                coords = self.canvas.coords(canvas_id)
                if coords and len(coords) >= 2:
                    x, y = coords[0], coords[1]
                    scaled_img = self.selected_signature['image']

                    # 創建選中框
                    x1, y1 = x - 3, y - 3
                    x2, y2 = x + scaled_img.width + 3, y + scaled_img.height + 3
                    frame_id = self.canvas.create_rectangle(
                        x1,
                        y1,
                        x2,
                        y2,
                        outline="red",
                        width=2,
                        dash=(5, 5),
                        tags=f"sig_{self.selected_signature['id']}_frame")
                    self.selected_signature['frame_id'] = frame_id

                    self.log_callback(
                        f"更新簽名 {self.selected_signature['id']} 的選中框", "info")
            except Exception as e:
                self.log_callback(f"更新選中框失敗：{str(e)}", "error")

    def _update_signature_scale_only(self, signature):
        """只更新簽名的縮放，保持事件綁定和位置"""
        try:
            if 'canvas_id' not in signature:
                return

            # 獲取當前位置
            canvas_id = signature['canvas_id']
            coords = self.canvas.coords(canvas_id)
            if not coords:
                return

            current_x, current_y = coords[0], coords[1]

            # 重新縮放圖片
            scale_factor = signature.get('scale_factor', 1.0)
            original_img = signature['original_image']

            if scale_factor != 1.0:
                new_width = int(original_img.width * scale_factor)
                new_height = int(original_img.height * scale_factor)
                scaled_img = original_img.resize((new_width, new_height),
                                                 Image.LANCZOS)
            else:
                scaled_img = original_img

            signature['image'] = scaled_img
            signature_tk = ImageTk.PhotoImage(scaled_img)
            signature['tk_image'] = signature_tk

            # 更新Canvas圖片，保持位置
            self.canvas.itemconfig(canvas_id, image=signature_tk)

            # 更新選中框
            if signature == self.selected_signature:
                self._update_selection_visual()

            self.log_callback(f"簽名 {signature['id']} 縮放更新完成", "info")

        except Exception as e:
            self.log_callback(f"更新簽名縮放失敗：{str(e)}", "error")

    def _bind_signature_drag(self, signature):
        """綁定簽名拖曳事件"""
        signature_tag = f"signature_{signature['id']}"

        def on_click(event):
            # 選中這個簽名
            self.selected_signature = signature
            self._redraw_signatures()  # 重繪以顯示選中框
            self._update_selected_info()
            self.log_callback(
                f"已選中簽名 {signature['id']} 在坐標 ({event.x}, {event.y})", "info")

            # 確保Canvas獲得焦點以接收鍵盤事件
            self.canvas.focus_set()

            # 強制設定焦點到視窗
            self.focus_force()

            # 設定拖曳起始點
            signature['drag_start_x'] = event.x
            signature['drag_start_y'] = event.y
            signature['dragging'] = True

        def on_drag(event):
            if signature.get('dragging', False):
                # 計算移動距離
                dx = event.x - signature['drag_start_x']
                dy = event.y - signature['drag_start_y']

                # 移動簽名圖片
                self.canvas.move(signature_tag, dx, dy)

                # 如果有選中框，也移動選中框的所有元素
                if 'frame_id' in signature:
                    # 找到所有與此簽名相關的選中框元素並移動
                    frame_items = self.canvas.find_withtag(
                        f"{signature_tag}_frame")
                    for item in frame_items:
                        self.canvas.move(item, dx, dy)

                # 更新拖曳起始點
                signature['drag_start_x'] = event.x
                signature['drag_start_y'] = event.y

        def on_release(event):
            if signature.get('dragging', False):
                signature['dragging'] = False

                # 更新簽名的實際位置
                try:
                    coords = self.canvas.coords(signature['canvas_id'])
                    if coords and len(coords) >= 2:
                        # 獲取 PDF 頁面位置
                        page_bbox = self.canvas.bbox("page")
                        if page_bbox:
                            page_left, page_top = page_bbox[0], page_bbox[1]
                            # 更新相對於PDF的位置（確保精確性）
                            pdf_x = (coords[0] - page_left) / self.scale
                            pdf_y = (coords[1] - page_top) / self.scale

                            # 驗證PDF坐標的合理性
                            page = self.pdf.load_page(signature['page'])
                            page_rect = page.rect
                            pdf_width, pdf_height = page_rect.width, page_rect.height

                            # 確保坐標在PDF範圍內
                            signature['x'] = max(
                                0,
                                min(pdf_x,
                                    pdf_width - signature['image'].width))
                            signature['y'] = max(
                                0,
                                min(pdf_y,
                                    pdf_height - signature['image'].height))

                            self.log_callback(
                                f"簽名移動到 PDF坐標 ({signature['x']:.1f}, {signature['y']:.1f})",
                                "info")
                except Exception as e:
                    self.log_callback(f"更新位置失敗：{str(e)}", "error")

        # 綁定滑鼠事件到簽名圖片
        self.canvas.tag_bind(signature_tag, "<Button-1>", on_click)
        self.canvas.tag_bind(signature_tag, "<B1-Motion>", on_drag)
        self.canvas.tag_bind(signature_tag, "<ButtonRelease-1>", on_release)

        # 同時綁定到簽名對應的canvas_id
        self.canvas.tag_bind(signature_id, "<Button-1>", on_click)
        self.canvas.tag_bind(signature_id, "<B1-Motion>", on_drag)
        self.canvas.tag_bind(signature_id, "<ButtonRelease-1>", on_release)

        # 調試：輸出綁定信息
        self.log_callback(
            f"已綁定簽名 {signature['id']} 的事件，標籤：{signature_tag}, ID：{signature_id}",
            "info")

        # 設定游標
        def on_enter(event):
            self.canvas.config(cursor="hand2")

        def on_leave(event):
            self.canvas.config(cursor="arrow")

        self.canvas.tag_bind(signature_tag, "<Enter>", on_enter)
        self.canvas.tag_bind(signature_tag, "<Leave>", on_leave)
        self.canvas.tag_bind(signature_id, "<Enter>", on_enter)
        self.canvas.tag_bind(signature_id, "<Leave>", on_leave)

    def _scale_selected_signature(self, scale_factor):
        """縮放選中的簽名"""
        if not self.selected_signature:
            messagebox.showinfo("提示", "請先選擇一個簽名")
            return

        signature = self.selected_signature
        current_scale = signature.get('scale_factor', 1.0)
        new_scale = current_scale * scale_factor

        # 限制縮放範圍
        if 0.1 <= new_scale <= 5.0:
            signature['scale_factor'] = new_scale
            self._update_signature_scale_only(signature)
            self._update_selected_info()
            self.log_callback(f"簽名已縮放到 {new_scale:.1f}x", "info")
        else:
            messagebox.showwarning("警告", "縮放範圍限制在 0.1x 到 5.0x 之間")

    def _reset_selected_signature(self):
        """重設選中簽名的大小"""
        if not self.selected_signature:
            messagebox.showinfo("提示", "請先選擇一個簽名")
            return

        self.selected_signature['scale_factor'] = 1.0
        self._update_signature_scale_only(self.selected_signature)
        self._update_selected_info()
        self.log_callback("簽名大小已重設", "info")

    def _clear_signatures(self):
        """清除所有簽名"""
        if self.signatures:
            if messagebox.askyesno("確認", "確定要清除所有簽名嗎？"):
                self.log_callback(f"開始清除 {len(self.signatures)} 個簽名", "info")

                # 清除Canvas上的所有簽名相關項目
                for sig in self.signatures:
                    if 'canvas_id' in sig:
                        self.canvas.delete(sig['canvas_id'])
                    if 'frame_id' in sig:
                        self.canvas.delete(sig['frame_id'])

                # 清除所有以sig_開頭的標籤
                self.canvas.delete("sig_*")

                self.signatures.clear()
                self.selected_signature = None
                self._update_selected_info()
                self.log_callback("已清除所有簽名", "success")
                self.status_label.config(text="簽名已清除 - 請重新添加簽名",
                                         fg=self.colors['warning'])
        else:
            messagebox.showinfo("提示", "目前沒有簽名可以清除")

    def _save_pdf(self):
        """儲存帶簽名的 PDF"""
        if not self.signatures:
            messagebox.showwarning("警告", "請先添加簽名")
            return

        save_path = filedialog.asksaveasfilename(title="儲存簽名後的 PDF",
                                                 defaultextension=".pdf",
                                                 filetypes=[("PDF 檔案", "*.pdf")
                                                            ])

        if not save_path:
            return

        try:
            self.status_label.config(text="正在儲存 PDF...",
                                     fg=self.colors['warning'])

            # 建立暫存目錄
            temp_dir = "temp_signatures"
            os.makedirs(temp_dir, exist_ok=True)

            # 為每個簽名建立暫存圖片
            for i, signature in enumerate(self.signatures):
                temp_path = os.path.join(temp_dir, f"signature_{i}.png")
                # 使用當前顯示的圖片（已縮放的）
                signature['image'].save(temp_path)
                signature['temp_path'] = temp_path

            # 將簽名插入到 PDF
            for signature in self.signatures:
                page = self.pdf.load_page(signature['page'])

                # 使用實際的縮放後圖片大小
                actual_img = signature['image']  # 這已經是縮放後的圖片
                img_width, img_height = actual_img.size

                # 記錄詳細信息用於調試
                self.log_callback(
                    f"保存簽名 {signature['id']}: 位置=({signature['x']:.1f}, {signature['y']:.1f}), "
                    f"尺寸=({img_width}, {img_height}), 類型={signature['type']}",
                    "info")

                # 簽名矩形 - 使用實際圖片尺寸和PDF坐標
                rect = fitz.Rect(signature['x'], signature['y'],
                                 signature['x'] + img_width,
                                 signature['y'] + img_height)

                # 驗證矩形位置是否在頁面範圍內
                page_rect = page.rect
                if (rect.x0 < 0 or rect.y0 < 0 or rect.x1 > page_rect.width
                        or rect.y1 > page_rect.height):
                    self.log_callback(f"警告：簽名 {signature['id']} 超出頁面範圍，將調整位置",
                                      "warning")
                    # 調整矩形位置確保在頁面內
                    rect.x0 = max(0, min(rect.x0, page_rect.width - img_width))
                    rect.y0 = max(0, min(rect.y0,
                                         page_rect.height - img_height))
                    rect.x1 = rect.x0 + img_width
                    rect.y1 = rect.y0 + img_height

                # 插入簽名圖片
                page.insert_image(rect,
                                  filename=signature['temp_path'],
                                  keep_proportion=True,
                                  overlay=True)

            # 儲存 PDF
            self.pdf.save(save_path)

            # 清理暫存檔案
            for signature in self.signatures:
                if 'temp_path' in signature and os.path.exists(
                        signature['temp_path']):
                    os.remove(signature['temp_path'])

            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)

            self.status_label.config(text="PDF 儲存成功",
                                     fg=self.colors['success'])
            self.log_callback(f"PDF 簽名完成：{save_path}", "success")

            messagebox.showinfo("完成", f"PDF 已成功儲存到：\n{save_path}")

            # 詢問是否關閉編輯器
            if messagebox.askyesno("完成", "簽名完成！是否關閉編輯器？"):
                self.destroy()

        except Exception as e:
            error_msg = f"儲存 PDF 失敗：{str(e)}"
            self.status_label.config(text="儲存失敗", fg=self.colors['danger'])
            self.log_callback(error_msg, "error")
            messagebox.showerror("錯誤", error_msg)

    def destroy(self):
        """關閉編輯器時清理資源"""
        try:
            self.pdf.close()
        except:
            pass
        super().destroy()


if __name__ == "__main__":
    app = PDFToolkit()
    app.run()
