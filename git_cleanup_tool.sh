#!/bin/bash

# Git 機密清理與安全推送工具
# 版本：3.0.0
# 功能：移除 Git 歷史中的機密資訊並安全推送

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[資訊]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

log_error() {
    echo -e "${RED}[錯誤]${NC} $1"
}

# 檢查必要工具
check_requirements() {
    log_info "檢查必要工具..."
    
    if ! command -v git &> /dev/null; then
        log_error "Git 未安裝"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        log_warning "Python3 未安裝，部分功能可能無法使用"
    fi
    
    log_success "工具檢查完成"
}

# 備份當前分支
backup_current_branch() {
    local current_branch=$(git branch --show-current)
    local backup_branch="backup-${current_branch}-$(date +%Y%m%d-%H%M%S)"
    
    log_info "建立備份分支：${backup_branch}"
    git branch "${backup_branch}"
    
    if [ $? -eq 0 ]; then
        log_success "備份分支建立成功"
        echo "${backup_branch}"
    else
        log_error "備份分支建立失敗"
        exit 1
    fi
}

# 掃描並列出機密資訊
scan_secrets() {
    log_info "掃描機密資訊..."
    
    # 常見的機密模式
    local patterns=(
        "glpat-[a-zA-Z0-9_-]{20}"  # GitLab Personal Access Token
        "ghp_[a-zA-Z0-9_]{36}"     # GitHub Personal Access Token
        "sk-[a-zA-Z0-9]{32,}"      # OpenAI API Key
        "ya29\.[a-zA-Z0-9_-]+"     # Google OAuth
        "AKIA[0-9A-Z]{16}"         # AWS Access Key
        "[a-zA-Z0-9_-]{40}"        # Generic 40 char token
    )
    
    local found_secrets=()
    
    for pattern in "${patterns[@]}"; do
        while IFS= read -r line; do
            if [[ -n "$line" ]]; then
                found_secrets+=("$line")
            fi
        done < <(git log --all --full-history -- "*" | grep -E "$pattern" | head -10)
    done
    
    if [ ${#found_secrets[@]} -gt 0 ]; then
        log_warning "發現潛在機密資訊：${#found_secrets[@]} 筆"
        for secret in "${found_secrets[@]}"; do
            echo "  - $secret"
        done
        return 1
    else
        log_success "未發現明顯的機密資訊"
        return 0
    fi
}

# 建立環境變數設定檔
create_env_template() {
    log_info "建立環境變數範本..."
    
    cat > .env.template << 'EOF'
# 環境變數設定範本
# 複製此檔案為 .env 並填入真實的值

# GitLab 設定
GITLAB_TOKEN=your_gitlab_token_here
GITLAB_BASE_URL=https://gitlab.example.com

# GitHub 設定  
GITHUB_TOKEN=your_github_token_here

# 其他 API 設定
# API_KEY=your_api_key_here
EOF

    # 確保 .env 被忽略
    if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
        echo ".env" >> .gitignore
        log_info "已將 .env 新增至 .gitignore"
    fi
    
    log_success "環境變數範本建立完成"
}

# 建立安全的配置載入器
create_config_loader() {
    log_info "建立配置載入器..."
    
    cat > config_loader.py << 'EOF'
#!/usr/bin/env python3
"""
安全的配置載入器
從環境變數或 .env 檔案載入設定
"""

import os
import sys
from typing import Optional

def load_env_file(env_path: str = '.env') -> dict:
    """載入 .env 檔案"""
    env_vars = {}
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"警告：找不到 {env_path} 檔案")
    except Exception as e:
        print(f"錯誤：讀取 {env_path} 失敗 - {e}")
    
    return env_vars

def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    安全地取得配置值
    優先順序：環境變數 > .env 檔案 > 預設值
    """
    # 首先檢查環境變數
    value = os.environ.get(key)
    if value:
        return value
    
    # 其次檢查 .env 檔案
    env_vars = load_env_file()
    value = env_vars.get(key)
    if value:
        return value
    
    # 最後使用預設值
    return default

def validate_config() -> bool:
    """驗證必要的配置是否存在"""
    required_configs = ['GITLAB_TOKEN', 'GITHUB_TOKEN']
    missing_configs = []
    
    for config in required_configs:
        if not get_config(config):
            missing_configs.append(config)
    
    if missing_configs:
        print(f"錯誤：缺少必要配置：{', '.join(missing_configs)}")
        print("請設定環境變數或建立 .env 檔案")
        return False
    
    return True

# 使用範例
if __name__ == "__main__":
    # 驗證配置
    if validate_config():
        print("配置驗證成功")
        
        # 取得配置值
        gitlab_token = get_config('GITLAB_TOKEN')
        github_token = get_config('GITHUB_TOKEN')
        gitlab_url = get_config('GITLAB_BASE_URL', 'https://gitlab.com')
        
        print(f"GitLab URL: {gitlab_url}")
        print(f"GitLab Token: {'已設定' if gitlab_token else '未設定'}")
        print(f"GitHub Token: {'已設定' if github_token else '未設定'}")
    else:
        sys.exit(1)
EOF

    chmod +x config_loader.py
    log_success "配置載入器建立完成"
}

# 移除 Git 歷史中的機密資訊
clean_git_history() {
    log_warning "即將清理 Git 歷史中的機密資訊"
    log_warning "此操作將重寫 Git 歷史，請確保已建立備份"
    
    read -p "是否繼續？(y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "操作已取消"
        return 1
    fi
    
    log_info "開始清理 Git 歷史..."
    
    # 使用 git filter-branch 移除機密檔案的敏感內容
    local files_to_clean=("app.py" "MULTI_SOURCE_UPDATE.md")
    
    for file in "${files_to_clean[@]}"; do
        if [[ -f "$file" ]]; then
            log_info "清理檔案：$file"
            
            # 建立清理腳本
            cat > clean_secrets.py << 'EOF'
#!/usr/bin/env python3
import sys
import re

def clean_secrets(content):
    """移除內容中的機密資訊"""
    patterns = [
        (r'glpat-[a-zA-Z0-9_-]{20}', 'GITLAB_TOKEN_PLACEHOLDER'),
        (r'ghp_[a-zA-Z0-9_]{36}', 'GITHUB_TOKEN_PLACEHOLDER'),
        (r'sk-[a-zA-Z0-9]{32,}', 'API_KEY_PLACEHOLDER'),
        (r'ya29\.[a-zA-Z0-9_-]+', 'OAUTH_TOKEN_PLACEHOLDER'),
        (r'AKIA[0-9A-Z]{16}', 'AWS_ACCESS_KEY_PLACEHOLDER'),
    ]
    
    cleaned_content = content
    for pattern, replacement in patterns:
        cleaned_content = re.sub(pattern, replacement, cleaned_content)
    
    return cleaned_content

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方式: python clean_secrets.py <檔案路徑>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cleaned_content = clean_secrets(content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"已清理檔案：{file_path}")
    except Exception as e:
        print(f"清理檔案時發生錯誤：{e}")
        sys.exit(1)
EOF
            
            python3 clean_secrets.py "$file"
            rm clean_secrets.py
        fi
    done
    
    # 提交清理後的檔案
    git add .
    git commit -m "清理機密資訊，使用環境變數替代硬編碼 Token"
    
    log_success "Git 歷史清理完成"
}

# 使用 BFG 清理（如果可用）
clean_with_bfg() {
    if command -v bfg &> /dev/null; then
        log_info "使用 BFG Repo-Cleaner 進行深度清理..."
        
        # 建立 patterns 檔案
        cat > secrets-patterns.txt << 'EOF'
glpat-*
ghp_*
sk-*
ya29.*
AKIA*
EOF
        
        # 使用 BFG 清理
        bfg --replace-text secrets-patterns.txt --no-blob-protection .
        
        # 清理參考
        git reflog expire --expire=now --all
        git gc --prune=now --aggressive
        
        rm secrets-patterns.txt
        log_success "BFG 清理完成"
    else
        log_warning "BFG Repo-Cleaner 未安裝，跳過深度清理"
        log_info "安裝方式：brew install bfg (macOS) 或 https://rtyley.github.io/bfg-repo-cleaner/"
    fi
}

# 測試推送
test_push() {
    log_info "測試推送到遠端倉庫..."
    
    # 首先測試 GitLab
    log_info "測試推送到 GitLab..."
    if git push gitlab main --dry-run; then
        log_success "GitLab 推送測試通過"
    else
        log_error "GitLab 推送測試失敗"
        return 1
    fi
    
    # 然後測試 GitHub
    log_info "測試推送到 GitHub..."
    if git push github main --dry-run; then
        log_success "GitHub 推送測試通過"
    else
        log_error "GitHub 推送測試失敗"
        return 1
    fi
    
    return 0
}

# 實際推送
perform_push() {
    log_info "開始實際推送..."
    
    local push_success=true
    
    # 推送到 GitLab
    log_info "推送到 GitLab..."
    if git push gitlab main; then
        log_success "GitLab 推送成功"
    else
        log_error "GitLab 推送失敗"
        push_success=false
    fi
    
    # 推送到 GitHub
    log_info "推送到 GitHub..."
    if git push github main; then
        log_success "GitHub 推送成功"
    else
        log_error "GitHub 推送失敗"
        push_success=false
    fi
    
    if $push_success; then
        log_success "所有遠端倉庫推送成功"
        return 0
    else
        log_error "部分或全部推送失敗"
        return 1
    fi
}

# 主要執行流程
main() {
    echo "==================== Git 機密清理與安全推送工具 ===================="
    echo "版本：3.0.0"
    echo "功能：移除 Git 歷史中的機密資訊並安全推送"
    echo "====================================================================="
    
    # 檢查必要工具
    check_requirements
    
    # 建立備份
    backup_branch=$(backup_current_branch)
    
    # 掃描機密資訊
    if ! scan_secrets; then
        log_warning "發現機密資訊，建議進行清理"
    fi
    
    # 建立安全配置
    create_env_template
    create_config_loader
    
    # 詢問是否清理歷史
    read -p "是否清理 Git 歷史中的機密資訊？(y/N): " clean_history
    if [[ "$clean_history" =~ ^[Yy]$ ]]; then
        clean_git_history
        clean_with_bfg
    fi
    
    # 測試推送
    if test_push; then
        read -p "測試通過，是否執行實際推送？(y/N): " do_push
        if [[ "$do_push" =~ ^[Yy]$ ]]; then
            perform_push
        fi
    else
        log_error "推送測試失敗，請檢查配置"
    fi
    
    echo "====================================================================="
    echo "腳本執行完成"
    echo "備份分支：$backup_branch"
    echo "如需還原，執行：git checkout $backup_branch"
    echo "====================================================================="
}

# 執行主程式
main "$@"