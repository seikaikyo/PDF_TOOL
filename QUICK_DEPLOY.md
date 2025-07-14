# 快速部署指南

## 🚀 立即部署到GitHub

### 步驟1：上傳核心檔案

請將以下檔案上傳到您的GitHub倉庫 `https://github.com/seikaikyo/PDF_TOOL`：

#### 必須上傳的檔案 ✅
```
app.py                    # 主程式（含自動更新）
requirements.txt          # Python依賴
build.py                 # 建置腳本
README.md                # 項目說明
update_config.json       # 更新配置
UPDATE_GUIDE.md          # 更新指南
GITHUB_DEPLOY_GUIDE.md   # 部署指南
create_icon.py           # 圖示生成
icon.ico                 # Windows圖示
icon.png                 # macOS/Linux圖示
```

#### 可選檔案 📁
```
build_exe.bat           # Windows建置腳本
fix_and_build.bat       # 修復建置腳本
其他.bat檔案            # 建置輔助檔案
```

#### 不要上傳 ❌
```
build/                  # 建置暫存目錄
dist/                   # 輸出目錄
logs/                   # 日誌檔案
__pycache__/           # Python快取
*.log                  # 日誌檔案
temp_signatures/       # 暫存簽名
```

### 步驟2：創建Release

1. **前往GitHub倉庫**
   - 開啟 https://github.com/seikaikyo/PDF_TOOL
   - 點擊「Releases」→「Create a new release」

2. **填寫Release信息**
   - **Tag version**: `v4.1.0`
   - **Release title**: `PDF Toolkit v4.1.0 - 自動更新功能`
   - **Description**: 
   ```
   🎉 新增自動更新檢查功能！

   ✨ 主要更新：
   - 自動檢查更新功能
   - 修復手寫簽名位置問題
   - 美觀的更新提醒對話框
   - 一鍵下載最新版本

   📦 完整功能：
   - PDF合併、簽名、拆分、壓縮
   - 手寫簽名、圖片簽名、文字插入
   - 全面錯誤日誌系統

   💾 使用方法：
   pip install -r requirements.txt
   python app.py
   ```

3. **建置並上傳可執行檔**
   ```bash
   # 在專案目錄執行
   python build.py
   
   # 上傳 dist/PDFToolkit.exe 到Release
   ```

### 步驟3：測試更新功能

1. **運行應用程式**
   ```bash
   python app.py
   ```

2. **觀察自動檢查**
   - 啟動2秒後自動檢查更新
   - 查看日誌中的更新信息

3. **手動測試**
   - 點擊「🔄 檢查更新」按鈕
   - 驗證更新對話框功能

## 🎯 配置已完成

✅ **GitHub URL已配置**：`https://github.com/seikaikyo/PDF_TOOL`

✅ **更新檢查API**：`https://api.github.com/repos/seikaikyo/PDF_TOOL/releases/latest`

✅ **下載頁面**：`https://github.com/seikaikyo/PDF_TOOL/releases/latest`

✅ **當前版本**：`v4.1.0`

## ⚡ 一鍵建置指令

```bash
# Windows
python build.py

# 或使用批次檔案
build_exe.bat
```

## 🔄 未來更新流程

1. **修改程式** → 更新版本號
2. **提交到GitHub** → 推送代碼
3. **創建新Release** → 上傳可執行檔
4. **用戶自動接收更新提醒** ✨

---

💡 **立即開始**：現在就可以將檔案上傳到GitHub，用戶將自動獲得更新通知！