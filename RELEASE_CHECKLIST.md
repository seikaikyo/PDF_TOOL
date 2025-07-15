# 📋 v4.2.0 發布檢查清單

## 🚀 發布前準備

### 📦 打包準備
- [ ] 確認 `APP_VERSION = "4.2.0"` 在 app.py 中
- [ ] 執行 `python build.py` 生成發布檔案
- [ ] 確認生成了 `dist/PDFToolkit-v4.2.0.exe`
- [ ] 確認生成了 `releases/PDFToolkit-v4.2.0-windows.zip`
- [ ] 確認生成了 `dist/README.md` 包含版本資訊
- [ ] 測試可執行檔案正常運行

### 🔧 功能驗證
- [ ] 測試 PDF 合併功能
- [ ] 測試 PDF 簽名功能
- [ ] 測試 PDF 拆分功能
- [ ] 測試 PDF 壓縮功能
- [ ] 測試 PDF 浮水印功能 (文字和圖片)
- [ ] 測試日系配色顯示正常
- [ ] 測試關於對話框功能
- [ ] 測試響應式設計 (不同螢幕大小)

## 💾 Git 操作

### 📝 提交代碼
```bash
# 1. 添加所有變更
git add .

# 2. 提交 (使用準備好的 commit message)
git commit -F COMMIT_MESSAGE.txt

# 3. 推送到 GitLab
git push origin main
```

### 🔍 提交檢查
- [ ] 確認所有檔案都已提交
- [ ] 確認 commit message 包含所有重要變更
- [ ] 確認推送到 GitLab 成功

## 🌐 GitLab Release

### 📋 創建 Release
1. **進入 GitLab 項目**
   - [ ] 訪問 https://gitlab.example.com/team/pdf_tool
   - [ ] 點擊 **Deployments** → **Releases**
   - [ ] 點擊 **New release**

2. **填寫 Release 資訊**
   - [ ] Tag name: `v4.2.0`
   - [ ] Release title: `PDF 工具包 v4.2.0 - 浮水印功能與日系設計更新`
   - [ ] 複製 `GITLAB_RELEASE_GUIDE.md` 中的 Release notes
   - [ ] 檢查 Release notes 格式正確

3. **上傳發布檔案**
   - [ ] 上傳 `releases/PDFToolkit-v4.2.0-windows.zip`
   - [ ] 設定檔案描述：`Windows 可執行檔案包 (包含完整功能)`
   - [ ] 檢查檔案大小合理 (約 15-20MB)

4. **發布 Release**
   - [ ] 檢查所有資訊無誤
   - [ ] 點擊 **Create release**
   - [ ] 確認發布成功

## 🔄 更新功能測試

### 🧪 測試多源更新
1. **準備測試環境**
   - [ ] 修改 `APP_VERSION = "4.1.0"` (模擬舊版本)
   - [ ] 重新運行應用程式

2. **測試內網更新 (GitLab)**
   - [ ] 在內網環境運行應用程式
   - [ ] 點擊「🔄 檢查更新」
   - [ ] 確認檢測到 v4.2.0 更新
   - [ ] 確認顯示更新內容
   - [ ] 確認下載連結指向 GitLab
   - [ ] 測試下載連結可用

3. **測試外網更新 (GitHub)**
   - [ ] 在外網環境運行應用程式
   - [ ] 點擊「🔄 檢查更新」
   - [ ] 確認自動切換到 GitHub 源
   - [ ] 確認檢測到相應版本
   - [ ] 測試下載連結可用

4. **測試容錯機制**
   - [ ] 模擬 GitLab 無法訪問的情況
   - [ ] 確認自動切換到 GitHub
   - [ ] 確認錯誤提示友善

## 📝 文檔更新

### 📚 文檔檢查
- [ ] 確認 `README.md` 包含 v4.2.0 功能
- [ ] 確認版本歷史已更新
- [ ] 確認 `MULTI_SOURCE_UPDATE.md` 資訊正確
- [ ] 確認 `VERSION_BUILD_IMPROVEMENTS.md` 完整

### 🌍 GitHub 同步 (可選)
- [ ] 推送代碼到 GitHub: `git push github main`
- [ ] 在 GitHub 創建相同的 Release
- [ ] 上傳相同的發布檔案
- [ ] 確認兩個平台版本同步

## ✅ 發布完成驗證

### 🎯 最終檢查
- [ ] GitLab Release 頁面顯示正常
- [ ] 發布檔案可以正常下載
- [ ] 應用程式可以檢測到新版本
- [ ] 更新提示資訊正確
- [ ] 下載連結工作正常
- [ ] 多源更新系統運作正常

### 📊 發布統計
- [ ] 記錄發布時間
- [ ] 記錄檔案大小
- [ ] 記錄主要功能數量
- [ ] 記錄修復問題數量

## 🎉 發布後工作

### 📢 通知相關人員
- [ ] 通知內網用戶新版本可用
- [ ] 更新內部文檔和說明
- [ ] 回饋收集和問題跟踪準備

### 🔍 監控和支援
- [ ] 監控下載數據
- [ ] 收集用戶反饋
- [ ] 準備技術支援文檔
- [ ] 規劃下一版本功能

---

## 📞 緊急聯絡

如果發布過程中遇到問題：
1. 檢查 GitLab 權限和網路連接
2. 確認檔案沒有被防毒軟體攔截
3. 檢查 GitLab API 是否正常運作
4. 確認 Personal Access Token 仍然有效

---

**🎯 發布成功標誌**: 
- GitLab Release 頁面顯示 v4.2.0
- 應用程式可以檢測並提示更新
- 內外網用戶都可以正常下載更新

**📅 預計發布時間**: 2025-01-15  
**👨‍💻 發布負責人**:   
**🔗 GitLab 項目**: https://gitlab.example.com/team/pdf_tool