# 多源更新系統配置說明

## 概述

PDF 工具包 v4.2.0 引入了智能多源更新系統，可以根據網絡環境自動選擇最合適的更新源。

## 支援的更新源

### 1. 內網 GitLab (優先級: 1)
- **適用環境**: 公司內網
- **URL**: `https://gitlab.example.com/team/pdf_tool`
- **認證**: 使用 Personal Access Token
- **SSL**: 自動跳過證書驗證（內部伺服器）

### 2. GitHub Public (優先級: 2) 
- **適用環境**: 外網、公共網路
- **URL**: `https://github.com/seikaikyo/PDF_TOOL`
- **認證**: 無需認證（公開倉庫）
- **SSL**: 標準 HTTPS 驗證

## 工作原理

### 智能源選擇
1. **優先級排序**: 系統按照配置的優先級嘗試各個更新源
2. **成功記憶**: 記住上次成功的更新源，下次優先嘗試
3. **自動容錯**: 如果一個源失敗，自動嘗試下一個源
4. **網絡適應**: 根據網絡環境自動選擇可用的源

### 檢查流程
```
開始檢查更新
    ↓
按優先級排序源
    ↓
優先嘗試上次成功的源
    ↓
逐個嘗試各更新源
    ↓
找到可用源 → 顯示更新信息
    ↓
所有源都失敗 → 顯示網絡錯誤
```

## 配置修改

如需修改更新源配置，編輯 `app.py` 中的 `UPDATE_SOURCES` 字典：

```python
UPDATE_SOURCES = {
    'gitlab': {
        'name': 'Internal GitLab',
        'api_url': "https://gitlab.example.com/api/v4/projects/team%2Fpdf_tool/releases?per_page=1",
        'download_url': "https://gitlab.example.com/team/pdf_tool/-/releases",
        'token': "{{GITLAB_TOKEN}}",
        'priority': 1  # 數字越小優先級越高
    },
    'github': {
        'name': 'GitHub Public',
        'api_url': "https://api.github.com/repos/seikaikyo/PDF_TOOL/releases/latest",
        'download_url': "https://github.com/seikaikyo/PDF_TOOL/releases",
        'token': None,
        'priority': 2
    }
}
```

## 使用場景

### 內網用戶
- 自動優先使用 GitLab 內部源
- 訪問速度快，無網絡限制
- 支援私有版本發布

### 外網用戶  
- 自動使用 GitHub 公開源
- 無需 VPN 或特殊網絡設置
- 全球 CDN 加速下載

### 混合環境用戶
- 系統自動檢測可用源
- 內外網切換無感知
- 最佳的更新體驗

## 錯誤處理

- **單源失敗**: 自動嘗試下一個源
- **所有源失敗**: 顯示詳細的網絡診斷信息
- **版本解析錯誤**: 跳過該源，嘗試其他源
- **SSL 證書問題**: GitLab 源自動跳過驗證

## 調試信息

開發模式下，控制台會顯示詳細的更新檢查日誌：
```
嘗試檢查更新源：Internal GitLab
檢查 Internal GitLab 失敗：連接超時
嘗試檢查更新源：GitHub Public
成功從 GitHub Public 獲取更新信息
```

## 版本兼容性

此多源更新系統與以下版本兼容：
- v4.2.0+: 完全支援
- v4.1.0-: 需要手動更新到 v4.2.0 以享受多源功能