# PDF Toolkit - Complete PDF Solution
# PDF ツールキット - 完全な PDF ソリューション
# PDF 工具包 - 完整 PDF 解決方案

[English](#english) | [日本語](#japanese) | [繁體中文](#traditional-chinese)

---

## English

### Overview
A complete PDF processing solution that combines merging, digital signatures, splitting, and compression capabilities into one powerful application. Built with Python and Tkinter, featuring an intuitive graphical interface for all your PDF needs.

### Features

#### PDF Merging
- **Multi-file PDF Merging**: Combine multiple PDF files into a single document
- **Drag & Drop Interface**: Easily add files by dragging them into the application
- **Page Reordering**: Drag and drop PDF pages to customize merge order
- **Real-time Preview**: View thumbnails of all pages before merging
- **Progress Tracking**: Monitor merge progress with visual feedback

#### Digital Signature & Annotation
- **Handwritten Signatures**: Draw signatures directly with mouse/touchpad
- **Image Signature Upload**: Import signature images (PNG, JPG, etc.)
- **Text Insertion**: Add custom text with various fonts, sizes, and colors
- **Interactive Editing**: Drag, resize, and position signatures/text anywhere on the PDF
- **Multi-signature Support**: Add multiple signatures and text elements per page
- **Real-time Preview**: See changes immediately on the PDF preview

#### PDF Splitting
- **Split by Page Count**: Divide PDF into files with specified number of pages
- **Split by Page Range**: Extract specific page ranges as separate files
- **Single Page Extraction**: Extract individual pages as standalone PDFs
- **Flexible Output**: Choose output directory and custom naming

#### PDF Compression
- **Multiple Compression Levels**: Light, Medium, Heavy compression options
- **Image Optimization**: Compress embedded images with quality control
- **Advanced Options**: Remove unnecessary objects, optimize fonts
- **Size Reduction**: Significant file size reduction while maintaining quality
- **Progress Tracking**: Real-time compression progress display

#### User Experience
- **Unified Interface**: All PDF operations in one application
- **Responsive Design**: Adaptive layout for different screen sizes
- **Keyboard Shortcuts**: Quick access to scaling and deletion functions
- **Error Logging**: Comprehensive error tracking with detailed logs
- **Progress Feedback**: Real-time progress indicators for all operations
- **Intuitive Controls**: User-friendly interface suitable for all skill levels

### Requirements
- Python 3.7 or higher
- Windows, macOS, or Linux
- See `requirements.txt` for Python dependencies

### Installation
1. Clone or download this repository
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage
#### Running the Application
```bash
python app.py
```

#### Basic Workflow

**For PDF Merging:**
1. **Load PDF Files**: Drag and drop PDF files into the application or click "Select PDF Files"
2. **Arrange Pages**: Use the preview area to drag pages and adjust merge order
3. **Merge PDFs**: Click the "Merge PDF" button to combine files
4. **Save Result**: Choose a location and filename for the merged PDF

**For PDF Signing:**
1. **Load PDF**: Open any PDF file using "Select PDF Files"
2. **Open Signature Editor**: Click the "PDF Signature" button
3. **Add Content**: Use "Upload Signature", "Handwritten Signature", or "Insert Text"
4. **Position & Resize**: Drag to move, use +/- keys or toolbar buttons to scale
5. **Save Signed PDF**: Click "Save PDF" to export the final document

**For PDF Splitting:**
1. **Load PDF**: Open a single PDF file using "Select PDF Files"
2. **Open Split Tool**: Click the "Split PDF" button
3. **Choose Method**: Select split by pages, range, or single page extraction
4. **Set Parameters**: Configure page numbers or ranges as needed
5. **Select Output**: Choose destination folder and start splitting

**For PDF Compression:**
1. **Load PDF**: Open a single PDF file using "Select PDF Files"
2. **Open Compress Tool**: Click the "Compress PDF" button
3. **Choose Level**: Select Light, Medium, or Heavy compression
4. **Configure Options**: Enable/disable image compression, object removal, font optimization
5. **Save Compressed**: Choose output location and start compression

#### Keyboard Shortcuts (Signature Mode)
- **+ or =**: Enlarge selected signature/text
- **-**: Shrink selected signature/text
- **0**: Reset to original size
- **Delete**: Remove selected signature/text

#### Building Executable
```bash
python build.py
```

### Dependencies
- **PyInstaller**: For creating standalone executables
- **tkinterdnd2**: Drag and drop functionality
- **PyMuPDF (fitz)**: PDF processing and manipulation
- **Pillow (PIL)**: Image processing for thumbnails and signature handling
- **pyfiglet**: ASCII art for application title
- **tkinter**: GUI framework (included with Python)
- **ImageTk**: Image display in Tkinter
- **ImageDraw**: Drawing capabilities for text rendering
- **ImageFont**: Font handling for text insertion

---

## Japanese

### 概要
PDF の統合、デジタル署名、分割、圧縮機能を一つのアプリケーションに統合した完全な PDF 処理ソリューション。Python と Tkinter で構築され、すべての PDF ニーズに対応する直感的なグラフィカルインターフェースを提供します。

### 機能

#### PDF マージ
- **複数ファイル PDF マージ**: 複数の PDF ファイルを単一のドキュメントに結合
- **ドラッグ＆ドロップインターフェース**: ファイルをアプリケーションにドラッグして簡単に追加
- **ページ順序変更**: PDF ページをドラッグ＆ドロップしてマージ順序をカスタマイズ
- **リアルタイムプレビュー**: マージ前にすべてのページのサムネイルを表示
- **進捗追跡**: 視覚的なフィードバックでマージ進捗を監視

#### デジタル署名＆注釈
- **手書き署名**: マウス/タッチパッドで直接署名を描画
- **署名画像アップロード**: 署名画像（PNG、JPG など）をインポート
- **テキスト挿入**: 様々なフォント、サイズ、色でカスタムテキストを追加
- **インタラクティブ編集**: PDF 上のどこでも署名/テキストをドラッグ、リサイズ、配置
- **複数署名サポート**: ページごとに複数の署名とテキスト要素を追加
- **リアルタイムプレビュー**: PDF プレビューで変更を即座に確認

#### PDF 分割
- **ページ数で分割**: 指定したページ数でファイルを分割
- **ページ範囲で分割**: 特定のページ範囲を個別ファイルとして抽出
- **単ページ抽出**: 個別ページを独立した PDF として抽出
- **柔軟な出力**: 出力ディレクトリとカスタム命名を選択

#### PDF 圧縮
- **複数の圧縮レベル**: 軽度、中度、重度の圧縮オプション
- **画像最適化**: 品質制御付きの埋め込み画像圧縮
- **高度なオプション**: 不要なオブジェクトの削除、フォント最適化
- **サイズ削減**: 品質を維持しながら大幅なファイルサイズ削減
- **進捗追跡**: リアルタイム圧縮進捗表示

#### ユーザーエクスペリエンス
- **レスポンシブデザイン**: 異なる画面サイズに適応するレイアウト
- **キーボードショートカット**: スケーリングと削除機能への迅速なアクセス
- **包括的ログ**: トラブルシューティング用の詳細な操作ログ
- **座標系**: 保存時に位置を保持する正確な配置

### 必要条件
- Python 3.7 以上
- Windows、macOS、または Linux
- Python の依存関係については `requirements.txt` を参照

### インストール
1. このリポジトリをクローンまたはダウンロード
2. 必要な依存関係をインストール:
   ```bash
   pip install -r requirements.txt
   ```

### 使用方法
#### アプリケーションの実行
```bash
python app.py
```

#### 基本的なワークフロー
1. **PDF ファイルの読み込み**: PDF ファイルをアプリケーションにドラッグ＆ドロップするか、「PDF ファイルを選択」をクリック
2. **ページの配置**: プレビューエリアを使用してページをドラッグし、マージ順序を調整
3. **PDF のマージ**: 「PDF をマージ」ボタンをクリックしてファイルを結合
4. **結果の保存**: マージされた PDF の場所とファイル名を選択

#### 実行ファイルの構築
```bash
python build.py
```

### 依存関係
- **PyInstaller**: スタンドアロン実行ファイルの作成
- **tkinterdnd2**: ドラッグ＆ドロップ機能
- **PyMuPDF**: PDF 処理と操作
- **Pillow**: サムネイル用の画像処理
- **pyfiglet**: アプリケーションタイトル用の ASCII アート

---

## Traditional Chinese

### 概述
一個完整的 PDF 處理解決方案，將合併、數位簽名、拆分和壓縮功能整合到一個強大的應用程式中。使用 Python 和 Tkinter 構建，為您的所有 PDF 需求提供直觀的圖形使用者介面。

### 功能特色

#### PDF 合併
- **多檔案 PDF 合併**: 將多個 PDF 檔案合併為單一文件
- **拖放介面**: 通過拖放檔案到應用程式中輕鬆添加檔案
- **頁面重新排序**: 拖放 PDF 頁面以自訂合併順序
- **即時預覽**: 在合併前查看所有頁面的縮圖
- **進度追蹤**: 通過視覺化回饋監控合併進度

#### 數位簽名與註解
- **手寫簽名**: 直接用滑鼠/觸控板繪製簽名
- **簽名圖片上傳**: 匯入簽名圖片（PNG、JPG 等）
- **文字插入**: 添加自訂文字，支援多種字體、大小和顏色
- **互動式編輯**: 在 PDF 上任意位置拖曳、調整大小和定位簽名/文字
- **多重簽名支援**: 每頁可添加多個簽名和文字元素
- **即時預覽**: 在 PDF 預覽中立即查看變更

#### PDF 拆分
- **按頁數拆分**: 將 PDF 分割為指定頁數的檔案
- **按頁面範圍拆分**: 將特定頁面範圍擷取為個別檔案
- **單頁擷取**: 將個別頁面擷取為獨立的 PDF
- **彈性輸出**: 選擇輸出目錄和自訂命名

#### PDF 壓縮
- **多種壓縮級別**: 輕度、中度、重度壓縮選項
- **圖片最佳化**: 具品質控制的嵌入圖片壓縮
- **進階選項**: 移除不必要物件、字體最佳化
- **大小縮減**: 在保持品質的同時大幅減少檔案大小
- **進度追蹤**: 即時壓縮進度顯示

#### 使用者體驗
- **響應式設計**: 適應不同螢幕尺寸的自適應佈局
- **鍵盤快捷鍵**: 快速存取縮放和刪除功能
- **全面日誌記錄**: 詳細的操作日誌用於故障排除
- **座標系統**: 精確定位，儲存時保持位置不變

### 系統需求
- Python 3.7 或更高版本
- Windows、macOS 或 Linux
- Python 依賴項請參考 `requirements.txt`

### 安裝方式
1. 克隆或下載此存儲庫
2. 安裝所需依賴項:
   ```bash
   pip install -r requirements.txt
   ```

### 使用方法
#### 執行應用程式
```bash
python app.py
```

#### 基本工作流程

**PDF 合併模式：**
1. **載入 PDF 檔案**: 將 PDF 檔案拖放到應用程式中或點擊「選擇 PDF 檔案」
2. **排列頁面**: 使用預覽區域拖曳頁面並調整合併順序
3. **合併 PDF**: 點擊「合併 PDF」按鈕來組合檔案
4. **儲存結果**: 為合併後的 PDF 選擇位置和檔案名稱

**PDF 簽名模式：**
1. **載入 PDF**: 使用「選擇 PDF 檔案」開啟任何 PDF 檔案
2. **開啟簽名編輯器**: 點擊「PDF 簽名」按鈕
3. **添加內容**: 使用「上傳簽名」、「手寫簽名」或「插入文字」
4. **調整位置與大小**: 拖曳移動，使用 +/- 鍵或工具列按鈕縮放
5. **儲存簽名 PDF**: 點擊「儲存 PDF」匯出最終文件

#### 鍵盤快捷鍵（簽名模式）
- **+ 或 =**: 放大選中的簽名/文字
- **-**: 縮小選中的簽名/文字
- **0**: 重設為原始大小
- **Delete**: 刪除選中的簽名/文字

#### 構建可執行檔案
```bash
python build.py
```

### 依賴項目
- **PyInstaller**: 用於創建獨立可執行檔案
- **tkinterdnd2**: 拖放功能
- **PyMuPDF**: PDF 處理和操作
- **Pillow**: 縮圖的圖像處理
- **pyfiglet**: 應用程式標題的 ASCII 藝術

---

## Project Structure / プロジェクト構造 / 專案結構

```
dash_pdf/
├── app.py                 # Main application file / メインアプリケーションファイル / 主應用程式檔案
├── build.py              # Build script for executable / 実行ファイル用ビルドスクリプト / 可執行檔案構建腳本
├── requirements.txt      # Python dependencies / Python依存関係 / Python依賴項
├── icon.ico             # Application icon (Windows) / アプリケーションアイコン (Windows) / 應用程式圖示 (Windows)
├── icon.png             # Application icon (macOS/Linux) / アプリケーションアイコン (macOS/Linux) / 應用程式圖示 (macOS/Linux)
├── create_icon.py       # Icon generation script / アイコン生成スクリプト / 圖示生成腳本
├── README.md            # This documentation / このドキュメント / 此說明文件
└── dist/                # Generated executables / 生成された実行ファイル / 生成的可執行檔案
    ├── PDFToolkit.exe   # Windows executable / Windows実行ファイル / Windows可執行檔案
    ├── PDFToolkit       # macOS/Linux executable / macOS/Linux実行ファイル / macOS/Linux可執行檔案
    └── README.md        # Build information / ビルド情報 / 構建資訊
```

## Distribution / 配布 / 發布

### Executable Files / 実行ファイル / 可執行檔案
After building, you will find the following files in the `dist/` folder:

構建後，您可以在 `dist/` 資料夾中找到以下檔案：

- **Windows**: `PDFToolkit.exe` (single executable file)
- **macOS**: `PDFToolkit` or `PDFToolkit.app` (application bundle)  
- **Linux**: `PDFToolkit` (single executable file)

These executables are standalone and do not require Python installation on the target machine.

這些可執行檔案是獨立的，不需要在目標機器上安裝Python。

## License / ライセンス / 授權條款

© 2025 PDF Toolkit | Created by 選我正解

## Version History / バージョン履歴 / 版本歷史

### v4.0.0 (Latest / 最新 / 最新版本) - Complete PDF Solution
- ✨ **NEW**: PDF splitting functionality with multiple split modes
- ✨ **NEW**: PDF compression with three compression levels
- ✨ **NEW**: Comprehensive error logging system
- ✨ **NEW**: Enhanced 2x2 button layout for all four main functions
- ✨ **NEW**: Advanced compression options (image optimization, object removal)
- 🔧 **IMPROVED**: Better coordinate system for accurate signature positioning
- 🔧 **IMPROVED**: Enhanced user interface with progress indicators
- 🔧 **IMPROVED**: Robust error handling and user feedback
- 🔧 **IMPROVED**: Cross-platform compatibility for PyMuPDF versions

### v3.0.0 - Digital Signature & Text Edition
- ✨ **NEW**: Digital signature support with handwritten and uploaded signatures
- ✨ **NEW**: Text insertion with customizable fonts, sizes, and colors
- ✨ **NEW**: Interactive editing - drag, resize, and position elements
- ✨ **NEW**: Multi-signature support per page
- ✨ **NEW**: Keyboard shortcuts for quick editing
- 🔧 **IMPROVED**: Coordinate system for accurate positioning
- 🔧 **IMPROVED**: Enhanced user interface with responsive design
- 🔧 **IMPROVED**: Better error handling and logging

### v2.0.0
- ✨ PDF merging functionality
- ✨ Drag and drop interface
- ✨ Page reordering capabilities
- ✨ Real-time preview

Current version / 現在のバージョン / 目前版本: **v4.0.0**