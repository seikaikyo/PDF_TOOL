# PDF Toolkit GitHub 部署指南

## 🎯 部署目標

將PDF工具包部署到GitHub倉庫：https://github.com/seikaikyo/PDF_TOOL，並設置自動更新功能。

## 📋 部署清單

### 1. 需要上傳的檔案

#### 核心檔案 ✅
- `app.py` - 主應用程式（已包含自動更新功能）
- `requirements.txt` - Python依賴項
- `build.py` - 打包腳本
- `README.md` - 項目說明文檔

#### 圖示檔案 🎨
- `create_icon.py` - 圖示生成腳本
- `icon.ico` - Windows圖示
- `icon.png` - macOS/Linux圖示

#### 更新功能檔案 🔄
- `update_config.json` - 更新配置
- `UPDATE_GUIDE.md` - 更新功能使用指南
- `GITHUB_DEPLOY_GUIDE.md` - 此部署指南

#### 建置檔案（可選）🔧
- `build_exe.bat` - Windows建置腳本
- `fix_and_build.bat` - 修復建置腳本
- 其他建置相關檔案

## 🚀 部署步驟

### 第一步：上傳到GitHub

1. **準備檔案**
   ```bash
   # 確保所有檔案都在 dash_pdf 目錄中
   ls -la /mnt/c/Users/YS00472/Documents/dash_pdf/
   ```

2. **初始化Git倉庫**（如果還沒有）
   ```bash
   cd /mnt/c/Users/YS00472/Documents/dash_pdf/
   git init
   git remote add origin https://github.com/seikaikyo/PDF_TOOL.git
   ```

3. **提交所有檔案**
   ```bash
   git add .
   git commit -m "feat: 完整PDF工具包 v4.1.0 - 包含自動更新功能"
   git push -u origin main
   ```

### 第二步：創建Release版本

1. **前往GitHub倉庫**
   - 開啟 https://github.com/seikaikyo/PDF_TOOL
   - 點擊右側的「Releases」

2. **創建新Release**
   - 點擊「Create a new release」
   - Tag version: `v4.1.0`
   - Release title: `PDF Toolkit v4.1.0 - 自動更新與增強功能`

3. **填寫Release說明**
   ```markdown
   # PDF Toolkit v4.1.0 🎉

   ## ✨ 新增功能
   - 🔄 自動更新檢查功能
   - 📱 美觀的更新提醒對話框
   - 🖱️ 一鍵下載最新版本
   - 🔧 修復手寫簽名位置準確性問題

   ## 📦 完整功能
   - 📄 PDF合併 - 多檔案合併與頁面重排
   - ✍️ 數位簽名 - 手寫簽名、圖片簽名、文字插入
   - ✂️ PDF拆分 - 按頁數、範圍、單頁拆分
   - 🗜️ PDF壓縮 - 三種壓縮等級與優化選項
   - 📊 全面錯誤日誌系統

   ## 🔧 改進優化
   - 提升座標系統精確度
   - 增強錯誤處理機制
   - 優化用戶界面體驗
   - 跨平台兼容性提升

   ## 💾 下載說明
   下載 `PDFToolkit.exe`（Windows）或運行源碼：
   ```bash
   pip install -r requirements.txt
   python app.py
   ```
   ```

4. **上傳可執行檔案**
   - 使用 `build.py` 建置可執行檔案
   - 將 `dist/PDFToolkit.exe` 上傳到Release
   - 添加檔案說明

### 第三步：建置可執行檔案

1. **執行建置腳本**
   ```bash
   cd /mnt/c/Users/YS00472/Documents/dash_pdf/
   python build.py
   ```

2. **檢查建置結果**
   ```bash
   ls -la dist/
   # 應該看到 PDFToolkit.exe (Windows) 或 PDFToolkit (Linux/macOS)
   ```

3. **上傳到Release**
   - 在GitHub Release頁面上傳 `dist/PDFToolkit.exe`
   - 添加檔案描述：「Windows可執行檔案 - 無需安裝Python」

## ⚡ 測試更新功能

### 第四步：測試自動更新

1. **運行應用程式**
   ```bash
   python app.py
   ```

2. **等待自動檢查**
   - 啟動2秒後自動檢查更新
   - 觀察日誌中的更新檢查信息

3. **手動檢查測試**
   - 點擊主界面的「🔄 檢查更新」按鈕
   - 驗證更新對話框是否正常顯示

### 第五步：發布下一個版本（測試）

1. **修改版本號**
   - 在 `app.py` 中修改 `APP_VERSION = "4.2.0"`
   - 在模擬回應中設置 `"tag_name": "v4.3.0"`

2. **創建新Release**
   - Tag: `v4.2.0`
   - 上傳新的可執行檔案

3. **測試更新檢查**
   - 運行v4.1.0版本
   - 驗證是否正確檢測到v4.2.0更新

## 📁 GitHub倉庫結構

建議的倉庫結構：
```
PDF_TOOL/
├── README.md                 # 項目說明（三語言）
├── app.py                   # 主應用程式
├── requirements.txt         # Python依賴
├── build.py                 # 建置腳本
├── update_config.json       # 更新配置
├── UPDATE_GUIDE.md          # 更新使用指南
├── GITHUB_DEPLOY_GUIDE.md   # 部署指南
├── create_icon.py           # 圖示生成
├── icon.ico                 # Windows圖示
├── icon.png                 # macOS/Linux圖示
├── .gitignore              # Git忽略檔案
└── LICENSE                 # 授權條款（建議添加）
```

## 🔧 自動更新工作原理

### API檢查流程
1. 應用程式啟動 → 2秒後背景檢查
2. 請求GitHub API: `https://api.github.com/repos/seikaikyo/PDF_TOOL/releases/latest`
3. 解析返回的JSON，比較版本號
4. 如有新版本 → 顯示更新對話框
5. 用戶點擊下載 → 開啟GitHub Release頁面

### 版本比較邏輯
```python
# 使用packaging庫進行語義化版本比較
from packaging import version
if version.parse("4.2.0") > version.parse("4.1.0"):
    # 顯示更新提醒
```

## ⚠️ 注意事項

### 必須遵循的規則

1. **版本標籤格式**
   - 必須使用 `v4.1.0` 格式
   - 不能使用 `4.1.0` 或其他格式

2. **Release必須是Public**
   - GitHub API只能訪問公開的Release
   - 確保倉庫是Public或Release是Public

3. **網路連接**
   - 用戶需要能訪問GitHub API
   - 中國大陸用戶可能需要考慮網路問題

4. **版本遞增**
   - 新版本號必須大於當前版本
   - 建議使用語義化版本控制

## 🎯 後續維護

### 發布新版本流程

1. **開發新功能** → 測試 → 更新版本號
2. **提交代碼** → 推送到GitHub
3. **建置可執行檔** → 測試功能
4. **創建Release** → 上傳檔案 → 發布
5. **通知用戶** → 等待自動更新檢查

### 版本管理建議

- **主版本號**：重大功能變更（4.x.x → 5.0.0）
- **次版本號**：新功能添加（4.1.x → 4.2.0）
- **修訂版本號**：錯誤修復（4.1.0 → 4.1.1）

---

💡 **提示**：首次部署完成後，您的用戶將能夠自動接收所有後續更新，大大簡化了版本管理工作！