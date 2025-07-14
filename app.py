import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import fitz  # PyMuPDF
from PIL import Image, ImageTk, ImageDraw
from pyfiglet import figlet_format
from datetime import datetime
import threading


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
        main_frame = tk.Frame(self, bg=self.colors['bg_main'], padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # 文字輸入區域
        tk.Label(main_frame, text="輸入文字：", bg=self.colors['bg_main'],
                fg="black", font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")
        
        self.text_entry = tk.Text(main_frame, height=3, font=("Microsoft YaHei", 11))
        self.text_entry.pack(fill="x", pady=(5, 15))
        self.text_entry.focus_set()
        
        # 字體設置區域
        font_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        font_frame.pack(fill="x", pady=(0, 15))
        
        # 字體選擇
        tk.Label(font_frame, text="字體：", bg=self.colors['bg_main'],
                fg="black", font=("Microsoft YaHei", 10)).pack(side="left")
        
        self.font_var = tk.StringVar(value="Microsoft YaHei")
        font_combo = ttk.Combobox(font_frame, textvariable=self.font_var, 
                                 values=["Microsoft YaHei", "SimSun", "Arial"], 
                                 state="readonly", width=15)
        font_combo.pack(side="left", padx=(5, 20))
        
        # 字體大小
        tk.Label(font_frame, text="大小：", bg=self.colors['bg_main'],
                fg="black", font=("Microsoft YaHei", 10)).pack(side="left")
        
        self.size_var = tk.StringVar(value="16")
        size_combo = ttk.Combobox(font_frame, textvariable=self.size_var,
                                 values=["12", "14", "16", "18", "20", "24", "28", "32"],
                                 state="readonly", width=8)
        size_combo.pack(side="left", padx=5)
        
        # 顏色選擇區域
        color_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        color_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(color_frame, text="顏色：", bg=self.colors['bg_main'],
                fg="black", font=("Microsoft YaHei", 10)).pack(side="left")
        
        self.color_var = tk.StringVar(value="black")
        colors_list = [
            ("黑色", "black"),
            ("藍色", "blue"), 
            ("紅色", "red"),
            ("綠色", "green"),
            ("紫色", "purple")
        ]
        
        for i, (color_name, color_value) in enumerate(colors_list):
            tk.Radiobutton(color_frame, text=color_name, variable=self.color_var,
                          value=color_value, bg=self.colors['bg_main'],
                          fg="black",
                          font=("Microsoft YaHei", 9)).pack(side="left", padx=5)
        
        # 按鈕區域
        btn_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        btn_frame.pack(fill="x")
        
        tk.Button(btn_frame, text="確定", command=self._confirm,
                 bg=self.colors['success'], fg="white",
                 font=("Microsoft YaHei", 10, "bold"),
                 width=10).pack(side="right", padx=(5, 0))
        
        tk.Button(btn_frame, text="取消", command=self._cancel,
                 bg=self.colors['danger'], fg="white", 
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


class PDFToolkit:
    """PDF 合併工具 - 專注於 PDF 檔案合併功能"""

    def __init__(self):
        # 色系配置
        self.colors = {
            'bg_main': '#F8F9FA',
            'bg_panel': '#FFFFFF',
            'bg_accent': '#E8F4FD',
            'fg_primary': '#212529',
            'fg_secondary': '#6C757D',
            'border': '#DEE2E6',
            'success': '#28A745',
            'warning': '#FFC107',
            'danger': '#DC3545',
            'info': '#007BFF',
            'step_bg': '#FFF3CD',
            'step_border': '#FFEAA7'
        }

        # 初始化主視窗
        self.root = TkinterDnD.Tk()
        self.root.title("PDF 合併工具")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
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

        # 步驟說明區域
        self._create_steps_guide()

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
        title_text = figlet_format("PDF TOOLKIT", font="slant")
        title_label = tk.Label(content_frame,
                               text=title_text,
                               bg=self.colors['bg_panel'],
                               fg=self.colors['info'],
                               font=("Courier", 8),
                               justify="center")
        title_label.pack(pady=5)

        # 副標題（置中）
        subtitle_label = tk.Label(content_frame,
                                  text="專業 PDF 合併工具 - 快速合併多個 PDF 檔案",
                                  bg=self.colors['bg_panel'],
                                  fg=self.colors['fg_secondary'],
                                  font=("Microsoft YaHei", 12, "bold"))
        subtitle_label.pack()

    def _create_steps_guide(self):
        """建立步驟說明區域"""
        steps_frame = tk.Frame(self.main_container,
                               bg=self.colors['step_bg'],
                               relief="solid",
                               bd=1)
        steps_frame.pack(fill="x", padx=10, pady=5)

        # 標題
        tk.Label(steps_frame,
                 text="操作步驟說明",
                 bg=self.colors['step_bg'],
                 fg=self.colors['fg_primary'],
                 font=("Microsoft YaHei", 11, "bold")).pack(anchor="w",
                                                            padx=15,
                                                            pady=(10, 5))

        # 步驟內容
        steps_content = tk.Frame(steps_frame, bg=self.colors['step_bg'])
        steps_content.pack(fill="x", padx=15, pady=(0, 10))

        # 合併模式步驟（置中顯示）
        merge_frame = tk.Frame(steps_content, bg=self.colors['step_bg'])
        merge_frame.pack(expand=True)

        tk.Label(merge_frame,
                 text="PDF 工具操作流程：",
                 bg=self.colors['step_bg'],
                 fg=self.colors['info'],
                 font=("Microsoft YaHei", 12, "bold")).pack(pady=5)

        operation_steps = [
            "【合併模式】1. 載入多個 PDF → 2. 調整頁面順序 → 3. 點擊「合併 PDF」→ 4. 選擇儲存位置",
            "【簽名模式】1. 載入 PDF 檔案 → 2. 點擊「PDF 簽名」→ 3. 手寫或上傳簽名 → 4. 拖曳調整位置與大小 → 5. 儲存"
        ]

        for step in operation_steps:
            tk.Label(merge_frame,
                     text=step,
                     bg=self.colors['step_bg'],
                     fg=self.colors['fg_primary'],
                     font=("Microsoft YaHei", 9)).pack(pady=3)

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
        info_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(info_frame,
                 text="提示：按住滑鼠左鍵拖曳頁面縮圖可以調整合併順序",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['warning'],
                 font=("Microsoft YaHei", 9)).pack(anchor="w")

        # 建立可滾動的預覽區域
        canvas_frame = tk.Frame(preview_frame, bg=self.colors['bg_panel'])
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

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

        # 功能選擇區域 - 簡化為只顯示當前功能
        self._create_info_section(right_panel)

        # 操作按鈕區域
        self._create_action_section(right_panel)

        # 進度顯示區域
        self._create_progress_section(right_panel)

        # 日誌區域
        self._create_log_section(right_panel)

    def _create_info_section(self, parent):
        """建立資訊顯示區域"""
        info_frame = tk.LabelFrame(parent,
                                   text="功能說明",
                                   bg=self.colors['bg_panel'],
                                   fg=self.colors['fg_primary'],
                                   font=("Microsoft YaHei", 11, "bold"))
        info_frame.pack(fill="x", pady=(0, 10))

        # 功能說明
        desc_frame = tk.Frame(info_frame, bg=self.colors['bg_panel'])
        desc_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(desc_frame,
                 text="PDF 多功能處理工具",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['info'],
                 font=("Microsoft YaHei", 12, "bold")).pack(anchor="w")

        tk.Label(desc_frame,
                 text="✓ 合併多個 PDF 檔案",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['fg_secondary'],
                 font=("Microsoft YaHei", 10)).pack(anchor="w", pady=(5, 1))

        tk.Label(desc_frame,
                 text="✓ PDF 電子簽名（手寫 + 上傳圖片）",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['fg_secondary'],
                 font=("Microsoft YaHei", 10)).pack(anchor="w", pady=1)

        # 支援格式
        format_frame = tk.Frame(info_frame, bg=self.colors['bg_panel'])
        format_frame.pack(fill="x", padx=10, pady=(5, 10))

        tk.Label(format_frame,
                 text="支援格式：PDF (.pdf)",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['fg_secondary'],
                 font=("Microsoft YaHei", 9)).pack(anchor="w")

    def _create_action_section(self, parent):
        """建立操作按鈕區域"""
        action_frame = tk.LabelFrame(parent,
                                     text="執行操作",
                                     bg=self.colors['bg_panel'],
                                     fg=self.colors['fg_primary'],
                                     font=("Microsoft YaHei", 11, "bold"))
        action_frame.pack(fill="x", pady=(0, 10))

        # 按鈕容器（左右並排）
        button_container = tk.Frame(action_frame, bg=self.colors['bg_main'])
        button_container.pack(fill="x", padx=10, pady=(15, 5))
        
        # 合併按鈕（左側）
        self.merge_btn = tk.Button(button_container,
                                   text="合併 PDF",
                                   command=self._merge_pdfs,
                                   bg=self.colors['success'],
                                   fg="white",
                                   font=("Microsoft YaHei", 12, "bold"),
                                   height=2)
        self.merge_btn.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # 簽名按鈕（右側）
        self.sign_btn = tk.Button(button_container,
                                  text="PDF 簽名",
                                  command=self._open_signature_editor,
                                  bg=self.colors['info'],
                                  fg="white",
                                  font=("Microsoft YaHei", 12, "bold"),
                                  height=2)
        self.sign_btn.pack(side="right", fill="both", expand=True, padx=(5, 0))

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
                 text="© 2025 PDF 合併工具 | 作者：",
                 bg=self.colors['bg_panel'],
                 fg=self.colors['fg_secondary'],
                 font=("Microsoft YaHei", 9)).pack(side="left", padx=10)

        # 版本資訊
        tk.Label(status_frame,
                 text="v2.0.0",
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
        self._log_message("PDF 合併工具已啟動", "success")
        self.root.mainloop()


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
                self._create_text_image(text_content, font_name, font_size, text_color)
            else:
                messagebox.showwarning("警告", "請輸入要插入的文字")

    def _create_text_image(self, text_content, font_name, font_size, text_color):
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
            text_img = Image.new('RGBA', (img_width, img_height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(text_img)
            
            # 繪製文字
            draw.text((padding, padding), text_content, font=font, fill=text_color)
            
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
        default_x = (pdf_width - signature_copy.width) / 2
        default_y = pdf_height * 0.7  # PDF頁面70%高度的位置

        signature_obj = {
            'image': signature_copy,
            'original_image': signature_copy.copy(),  # 保存原始圖片用於縮放
            'page': self.page_index,
            'x': max(50, default_x),  # 確保不會太靠左（PDF坐標）
            'y': max(50, default_y),  # 確保不會太靠上（PDF坐標）
            'type': signature_type,
            'id': len(self.signatures) + 1,
            'scale_factor': 1.0  # 縮放係數
        }

        self.signatures.append(signature_obj)
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
            else:
                # 後備方案：直接使用PDF坐標
                display_x = signature['x']
                display_y = signature['y']

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
                            signature['x'] = (coords[0] - page_left) / self.scale
                            signature['y'] = (coords[1] - page_top) / self.scale
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
                        self.log_callback(f"坐標轉換失敗，使用Canvas坐標：{str(e)}", "warning")

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
                            # 更新相對於PDF的位置
                            signature['x'] = (coords[0] -
                                              page_left) / self.scale
                            signature['y'] = (coords[1] -
                                              page_top) / self.scale
                            self.log_callback(
                                f"簽名移動到 ({signature['x']:.1f}, {signature['y']:.1f})",
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

                # 簽名矩形 - 使用實際圖片尺寸
                rect = fitz.Rect(signature['x'], signature['y'],
                                 signature['x'] + img_width,
                                 signature['y'] + img_height)

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
