# GitLab 發布指南 - PDF 工具包 v4.2.0

## 🚀 發布步驟

### 1. 準備發布檔案
首先執行打包：
```bash
python build.py
```

這會產生：
- `dist/PDFToolkit-v4.2.0.exe` (Windows 可執行檔)
- `releases/PDFToolkit-v4.2.0-windows.zip` (發布包)
- `dist/README.md` (說明文檔)

### 2. 提交代碼變更
```bash
git add .
git commit -m "feat: Release v4.2.0 with watermark functionality and Japanese design

✨ Features:
- PDF watermark support (text + image)
- Japanese-inspired color scheme
- Multi-source update system (GitLab + GitHub)
- Version-aware build system

🎨 Design:
- Traditional Japanese colors (Nippon colors)
- Improved UI with consolidated help
- Better responsive design

🔧 Technical:
- Enhanced text watermark positioning
- Smart update source selection
- Automatic version detection in builds

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

### 3. 創建 GitLab Release

#### 3.1 進入 GitLab 項目
訪問：https://gitlab.example.com/team/pdf_tool

#### 3.2 創建新的 Release
1. 點擊左側選單 **「Deployments」** → **「Releases」**
2. 點擊 **「New release」**
3. 填寫以下資訊：

**Tag name**: `v4.2.0`
**Release title**: `PDF 工具包 v4.2.0 - 浮水印功能與日系設計更新`

**Release notes** (複製以下內容):

---

## PDF 工具包 v4.2.0 - 浮水印功能與日系設計更新

### ✨ 主要新功能

#### 🖊️ PDF 浮水印功能
- **文字浮水印**: 支援自訂文字、字體大小、透明度和旋轉角度
- **圖片浮水印**: 支援 PNG、JPG 等格式，可調整大小和位置
- **靈活定位**: 提供中央、四角等多種位置選項
- **批次處理**: 同時為多個 PDF 檔案添加浮水印
- **即時預覽**: 所見即所得的浮水印效果

#### 🎨 日系配色設計
- **傳統色彩**: 基於 nipponcolors.com 和 irocore.com 的日本傳統色彩
- **溫暖背景**: 淡雪色 (AWAYUKI) 和白茶色 (SHIRACHA) 打造舒適介面
- **優雅配色**: 瑠璃色 (RURI)、常磐色 (TOKIWA)、柿色 (KAKI) 等和諧色調
- **護眼設計**: 減少長時間使用的眼睛疲勞
- **專業外觀**: 提升軟體的視覺品質和用戶體驗

#### 🔄 智能多源更新系統
- **雙源支援**: 同時支援內網 GitLab 和外網 GitHub
- **自動選擇**: 根據網路環境智能選擇最佳更新源
- **容錯機制**: 單一源失敗時自動切換到備用源
- **記憶功能**: 記住上次成功的更新源，提升更新速度

### 🔧 介面優化

#### 🎯 功能整合
- **關於對話框**: 整合所有操作指南和功能說明
- **精簡介面**: 移除冗餘的說明文字，提供更多操作空間
- **響應式設計**: 改善小螢幕和筆記型電腦的顯示效果
- **按鈕配色**: 浮水印按鈕採用柿色 (KAKI) 橘色設計，易於識別

#### 📖 用戶體驗
- **詳細說明**: 關於對話框包含完整的功能介紹和操作步驟
- **版本資訊**: 檢查更新時顯示詳細的版本更新內容
- **多語言支援**: 介面支援繁體中文、英文和日文說明
- **鍵盤快捷鍵**: 簽名模式支援 +、-、0、Delete 等快捷鍵操作

### 🐛 修復和改進

#### 🖊️ 浮水印功能修復
- **定位演算法**: 優化文字浮水印的位置計算，確保準確顯示
- **API 相容性**: 改善與不同版本 PyMuPDF 的相容性
- **透明度計算**: 修正透明度顏色計算方式，提供更好的視覺效果
- **錯誤處理**: 增強錯誤處理機制，提供更友善的錯誤提示

#### 🔧 系統穩定性
- **多源更新**: 解決網路環境限制問題，內外網用戶都能正常更新
- **版本檢測**: 改善版本號讀取和比較邏輯
- **檔案命名**: 打包系統自動包含版本號，避免版本混淆
- **日誌記錄**: 加強錯誤日誌和調試資訊

### 🛠️ 技術更新

#### 📦 打包系統改進
- **版本化命名**: 自動生成帶版本號的檔案名稱 (如 PDFToolkit-v4.2.0.exe)
- **自動化發布**: 一鍵生成發布包和說明文檔
- **平台支援**: 支援 Windows、macOS、Linux 三平台打包
- **檔案優化**: 改善打包檔案大小和啟動速度

#### 🔍 代碼質量
- **模組化設計**: 改善代碼結構，提升維護性
- **錯誤處理**: 加強異常處理和用戶回饋
- **效能優化**: 優化 PDF 處理和 UI 響應速度
- **相容性**: 提升跨平台和不同 Python 版本的相容性

### 📋 使用指南

#### 🖊️ 浮水印功能使用方法
1. 載入 PDF 檔案到工具中
2. 點擊橘色的「加浮水印」按鈕
3. 選擇文字或圖片浮水印類型
4. 設定浮水印內容、大小、透明度和位置
5. 選擇輸出目錄並開始處理
6. 完成後檔案將以 "_watermarked" 後綴儲存

#### 🎨 介面操作說明
- **關於資訊**: 點擊右下角「ℹ️ 關於」查看完整功能說明
- **檢查更新**: 點擊「🔄 檢查更新」獲取最新版本資訊
- **多功能操作**: 支援合併、簽名、拆分、壓縮、浮水印五大功能
- **拖放操作**: 支援拖放 PDF 檔案到應用程式視窗

### 📊 系統需求

- **作業系統**: Windows 7/10/11, macOS 10.14+, Linux (Ubuntu 18.04+)
- **記憶體**: 建議 4GB 以上
- **磁碟空間**: 200MB 以上可用空間
- **網路**: 更新檢查需要網路連接 (GitLab 內網或 GitHub 外網)

### 🔄 更新方式

#### 內網用戶 (GitLab)
- 應用程式會自動優先使用內網 GitLab 源
- 享受高速下載和即時更新
- 支援私有版本和內部測試版本

#### 外網用戶 (GitHub)
- 自動切換到 GitHub 公開源
- 無需 VPN 或特殊網路設定
- 享受全球 CDN 加速下載

### 📞 技術支援

如遇到問題，請檢查以下項目：
1. **更新失敗**: 確認網路連接，內網用戶檢查 GitLab 訪問權限
2. **浮水印問題**: 確認 PDF 檔案沒有密碼保護或編輯限制
3. **介面問題**: 確認螢幕解析度和縮放設定
4. **相容性問題**: 確認作業系統版本和 .NET Framework (Windows)

### 🚀 下一版本預告

計劃中的 v4.3.0 功能：
- 📑 PDF 書籤和目錄管理
- 🔐 PDF 密碼保護和權限設定
- 📊 批次處理進度優化
- 🌍 更多語言介面支援

---

**完整功能列表**: 合併、簽名、拆分、壓縮、浮水印、日系設計、智能更新  
**開發者**:   
**技術支援**: PDF 工具包團隊  
**發布日期**: 2025-01-15  

🎯 **立即體驗全新的 PDF 工具包 v4.2.0！**

---

#### 3.3 上傳發布檔案
在 Release 頁面的 **「Release assets」** 區域：
1. 點擊 **「Add link」** 或直接上傳檔案
2. 上傳 `releases/PDFToolkit-v4.2.0-windows.zip`
3. 設定檔案描述：`Windows 可執行檔案包 (包含完整功能)`

#### 3.4 發布 Release
1. 檢查所有資訊無誤
2. 點擊 **「Create release」**
3. 確認發布成功

### 4. 測試更新功能

發布完成後，測試多源更新：
1. 將應用程式版本改回 `4.1.0`
2. 運行應用程式
3. 點擊「檢查更新」
4. 確認可以檢測到 v4.2.0 更新
5. 驗證下載連結正常工作

### 5. GitHub 同步 (可選)

如果需要同步到 GitHub：
1. 推送代碼到 GitHub: `git push github main`
2. 在 GitHub 創建相同的 Release
3. 上傳相同的發布檔案

## 🎯 檢查清單

- [ ] 執行 `python build.py` 生成發布檔案
- [ ] 提交並推送代碼變更到 GitLab
- [ ] 在 GitLab 創建 v4.2.0 Release
- [ ] 複製提供的 Release Notes
- [ ] 上傳 `PDFToolkit-v4.2.0-windows.zip` 檔案
- [ ] 發布 Release
- [ ] 測試應用程式可以檢測到新版本
- [ ] 驗證下載連結正常工作
- [ ] (可選) 同步到 GitHub

完成這些步驟後，你的智能多源更新系統就可以正常工作了！