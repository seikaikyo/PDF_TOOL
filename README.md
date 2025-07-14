# PDF Toolkit - Professional PDF Merger & Signature Tool
# PDF ツールキット - プロフェッショナル PDF マージャー＆署名ツール
# PDF 工具包 - 專業 PDF 合併與簽名工具

[English](#english) | [日本語](#japanese) | [繁體中文](#traditional-chinese)

---

## English

### Overview
A comprehensive PDF toolkit with merging and digital signature capabilities, featuring an intuitive graphical interface built with Python and Tkinter.

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

#### User Experience
- **Responsive Design**: Adaptive layout for different screen sizes
- **Keyboard Shortcuts**: Quick access to scaling and deletion functions
- **Comprehensive Logging**: Detailed operation logs for troubleshooting
- **Coordinate System**: Accurate positioning that preserves location when saving

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
PDF マージとデジタル署名機能を備えた包括的な PDF ツールキットで、Python と Tkinter で構築された直感的なグラフィカルインターフェースを持ちます。

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
一個功能完整的 PDF 工具包，具備合併和數位簽名功能，使用 Python 和 Tkinter 構建，擁有直觀的圖形使用者介面。

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
├── icon.ico             # Application icon / アプリケーションアイコン / 應用程式圖示
├── README.md            # This file / このファイル / 此檔案
└── dist/                # Generated executables / 生成された実行ファイル / 生成的可執行檔案
```

## License / ライセンス / 授權條款

© 2025 PDF Toolkit | Created by 選我正解

## Version History / バージョン履歴 / 版本歷史

### v3.0.0 (Latest / 最新 / 最新版本)
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

Current version / 現在のバージョン / 目前版本: **v3.0.0**