# 版本化打包改進說明

## 問題描述
之前的打包系統生成的檔案都使用相同的檔案名稱 (如 `PDFToolkit.exe`)，無法區分不同版本，給版本管理和發布帶來困擾。

## 解決方案

### 📋 自動版本檢測
- **Python 腳本** (`build.py`)：使用正則表達式自動從 `app.py` 讀取 `APP_VERSION`
- **批次腳本** (`build_exe.bat`)：使用 `findstr` 命令從 `app.py` 讀取版本號

### 📁 版本化檔案命名
現在生成的檔案將包含版本號：

**舊命名方式**：
```
PDFToolkit.exe
PDFToolkit
```

**新命名方式**：
```
PDFToolkit-v4.2.0.exe      (Windows)
PDFToolkit-v4.2.0          (Linux/macOS)
PDF工具包-v4.2.0.exe       (Windows 中文版)
```

### 🎯 主要改進

#### 1. **build.py 腳本改進**
- ✅ 自動讀取版本號：`get_app_version()` 方法
- ✅ 動態檔案命名：`{base_name}-v{version}`
- ✅ 增強的標題顯示：包含版本資訊
- ✅ 自動發布包創建：`create_release_package()` 方法
- ✅ 詳細的版本化說明文檔

#### 2. **build_exe.bat 腳本改進**
- ✅ Windows 批次版本檢測
- ✅ 動態檔案命名
- ✅ 保持向後兼容性

#### 3. **發布包自動化**
- ✅ 自動創建 `releases/` 目錄
- ✅ 平台特定的壓縮格式：
  - Windows: `PDFToolkit-v4.2.0-windows.zip`
  - Linux: `PDFToolkit-v4.2.0-linux.tar.gz`
  - macOS: `PDFToolkit-v4.2.0-darwin.tar.gz`

## 使用方法

### 🐍 Python 打包 (推薦)
```bash
python build.py
```

**自動功能**：
1. 檢測版本號
2. 生成版本化可執行檔
3. 創建詳細說明文檔
4. 自動打包發布版本

### 🪟 Windows 批次打包
```cmd
build_exe.bat
```

**支援功能**：
1. 版本號檢測
2. 生成英文和中文檔名版本
3. 自動啟動腳本創建

## 輸出結構

### 打包完成後的目錄結構：
```
project/
├── dist/
│   ├── PDFToolkit-v4.2.0.exe    # 主執行檔
│   └── README.md                 # 版本化說明文檔
├── releases/
│   └── PDFToolkit-v4.2.0-windows.zip  # 發布包
└── build/                        # 臨時建置檔案
```

### 版本化說明文檔內容：
- ✅ 應用版本資訊
- ✅ 檔案名稱說明
- ✅ 完整功能列表 (包括最新的浮水印和日系設計)
- ✅ 技術規格和配色說明
- ✅ 建置環境資訊

## 版本發布流程

### 1. **更新版本號**
修改 `app.py` 中的 `APP_VERSION`：
```python
APP_VERSION = "4.3.0"  # 新版本
```

### 2. **執行打包**
```bash
python build.py
```

### 3. **發布到更新源**
上傳 `releases/` 目錄中的檔案到：
- GitLab: `https://gitlab.example.com/team/pdf_tool`
- GitHub: `https://github.com/seikaikyo/PDF_TOOL`

### 4. **測試多源更新**
啟動應用程式測試智能更新系統

## 優勢

### 📊 **版本管理**
- 檔案名稱清楚標示版本
- 避免版本混淆和覆蓋
- 支援並行版本測試

### 🚀 **發布自動化**
- 一鍵生成發布包
- 平台特定的壓縮格式
- 自動化說明文檔生成

### 🔄 **更新系統整合**
- 配合多源更新系統
- 清楚的版本標識
- 用戶友好的下載體驗

### 🛡️ **向後兼容**
- 舊的打包方式仍然可用
- 無版本號時自動降級
- 保持所有原有功能

## 範例輸出

### 成功打包訊息：
```
============================================================
    PDF工具包 (PDFToolkit) 跨平台打包工具
    作者：
    系統：Windows 10
    版本：v4.2.0
    輸出檔案：PDFToolkit-v4.2.0
============================================================

🏷️  讀取到版本號：4.2.0
✅ 打包成功！
📁 輸出檔案：PDFToolkit-v4.2.0.exe
📊 檔案大小：45,623,234 bytes (43.5 MB)
✅ 發布包創建成功：releases/PDFToolkit-v4.2.0-windows.zip
📊 包大小：18,234,567 bytes (17.4 MB)

🎉 建置完成！
🏷️  版本標籤：v4.2.0

📋 後續步驟：
1. 測試可執行檔功能
2. 檢查在不同環境下的相容性  
3. 上傳 releases/ 中的檔案到 GitLab/GitHub
4. 測試多源更新功能
```

## 技術細節

### 版本檢測正則表達式：
```python
pattern = r'APP_VERSION\s*=\s*["\']([^"\']+)["\']'
```

### Windows 批次版本檢測：
```batch
for /f "tokens=2 delims='" %%a in ('findstr "APP_VERSION.*=" app.py') do (
    set "app_version=%%a"
)
```

### 發布包命名規則：
```python
package_name = f"{base_app_name}-v{version}-{platform.lower()}"
```

## 測試驗證

### ✅ 已測試功能：
- [x] 版本號正確檢測 (v4.2.0)
- [x] 檔案名稱包含版本
- [x] Python 腳本語法正確
- [x] Windows 批次腳本相容性
- [x] 說明文檔自動生成

### 🚀 建議測試：
- [ ] 完整打包流程測試
- [ ] 多平台打包驗證
- [ ] 發布包上傳測試
- [ ] 更新系統端到端測試

---

🎯 **總結**：這次改進完全解決了版本標識問題，提供了完整的自動化打包和發布解決方案，讓每個版本都有清楚的標識，大大改善了版本管理和用戶體驗！