#!/bin/bash

# Git 歷史清理工具 v2 - 修正版本
# 版本：4.1.0
# 修正：處理未暫存變更、清理 .env 檔案、智慧排除

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

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

log_step() {
    echo -e "${CYAN}[步驟]${NC} $1"
}

# 清理工作區
clean_working_directory() {
    log_step "清理工作區..."
    
    # 檢查是否有未暫存的變更
    if ! git diff-index --quiet HEAD --; then
        log_warning "發現未暫存的變更"
        
        echo "當前狀態："
        git status --porcelain
        
        echo ""
        echo "選擇處理方式："
        echo "1) 暫存所有變更並提交"
        echo "2) 儲存到 stash"
        echo "3) 放棄所有變更 (危險)"
        echo "4) 取消操作"
        
        read -p "請選擇 (1-4): " choice
        
        case $choice in
            1)
                git add .
                git commit -m "清理前：儲存當前變更"
                log_success "變更已提交"
                ;;
            2)
                git stash push -m "清理前備份: $(date)"
                log_success "變更已儲存到 stash"
                ;;
            3)
                git reset --hard HEAD
                git clean -fd
                log_warning "所有變更已放棄"
                ;;
            4)
                log_info "操作已取消"
                exit 0
                ;;
            *)
                log_error "無效選擇"
                exit 1
                ;;
        esac
    else
        log_success "工作區已乾淨"
    fi
}

# 立即清理當前檔案中的機密
clean_current_files() {
    log_step "清理當前檔案中的機密..."
    
    # 清理 .env 檔案
    if [ -f ".env" ]; then
        log_info "清理 .env 檔案..."
        # 備份原始 .env
        cp .env .env.backup
        
        # 替換真實 token 為佔位符
        sed -i.bak 's/glpat-[a-zA-Z0-9_-]\{20\}/YOUR_GITLAB_TOKEN_HERE/g' .env
        sed -i.bak 's/ghp_[a-zA-Z0-9_]\{36\}/YOUR_GITHUB_TOKEN_HERE/g' .env
        
        rm -f .env.bak
        log_success ".env 檔案已清理"
    fi
    
    # 清理其他檔案中的機密（排除工具腳本）
    find . -type f \( -name "*.py" -o -name "*.md" \) \
        ! -name "*cleanup*" ! -name "*cleaner*" ! -path "./.git/*" \
        -exec grep -l "glpat-[a-zA-Z0-9_-]\{20\}" {} \; 2>/dev/null | \
    while read -r file; do
        log_info "清理檔案: $file"
        # 備份原始檔案
        cp "$file" "$file.backup"
        
        # 替換機密
        sed -i.bak 's/glpat-[a-zA-Z0-9_-]\{20\}/{{GITLAB_TOKEN}}/g' "$file"
        sed -i.bak 's/ghp_[a-zA-Z0-9_]\{36\}/{{GITHUB_TOKEN}}/g' "$file"
        
        rm -f "$file.bak"
    done
    
    # 提交清理後的檔案
    if ! git diff-index --quiet HEAD --; then
        git add .
        git commit -m "緊急清理：移除當前檔案中的機密資訊"
        log_success "當前檔案清理已提交"
    fi
}

# 建立進階清理腳本
create_advanced_cleaner() {
    log_step "建立進階清理腳本..."
    
    cat > /tmp/git_secret_filter.py << 'FILTER_SCRIPT'
#!/usr/bin/env python3
import sys
import re
import os
import tempfile

# 機密模式定義
SECRET_PATTERNS = [
    # GitLab Token
    (rb'glpat-[a-zA-Z0-9_-]{20}', b'{{GITLAB_TOKEN}}'),
    # GitHub Token
    (rb'ghp_[a-zA-Z0-9_]{36}', b'{{GITHUB_TOKEN}}'),
    (rb'gho_[a-zA-Z0-9_]{36}', b'{{GITHUB_OAUTH_TOKEN}}'),
    (rb'ghu_[a-zA-Z0-9_]{36}', b'{{GITHUB_USER_TOKEN}}'),
    (rb'ghs_[a-zA-Z0-9_]{36}', b'{{GITHUB_SERVER_TOKEN}}'),
    (rb'ghr_[a-zA-Z0-9_]{76}', b'{{GITHUB_REFRESH_TOKEN}}'),
    # OpenAI
    (rb'sk-[a-zA-Z0-9]{32,}', b'{{OPENAI_API_KEY}}'),
    # Google OAuth
    (rb'ya29\.[a-zA-Z0-9_-]+', b'{{GOOGLE_OAUTH_TOKEN}}'),
    # AWS
    (rb'AKIA[0-9A-Z]{16}', b'{{AWS_ACCESS_KEY}}'),
]

def should_process_file(filename):
    """判斷是否應該處理此檔案"""
    # 排除清理工具本身
    if any(keyword in filename.lower() for keyword in ['cleanup', 'cleaner', 'filter']):
        return False
    
    # 只處理特定副檔名
    extensions = ['.py', '.md', '.txt', '.yml', '.yaml', '.json', '.sh']
    return any(filename.endswith(ext) for ext in extensions)

def clean_file_content(content):
    """清理檔案內容"""
    cleaned = content
    changes_made = False
    
    for pattern, replacement in SECRET_PATTERNS:
        if re.search(pattern, cleaned):
            cleaned = re.sub(pattern, replacement, cleaned)
            changes_made = True
    
    return cleaned, changes_made

def main():
    if len(sys.argv) != 2:
        sys.exit(0)
    
    filename = sys.argv[1]
    
    # 檢查是否應該處理此檔案
    if not should_process_file(filename):
        sys.exit(0)
    
    try:
        # 讀取檔案（二進位模式以處理各種編碼）
        with open(filename, 'rb') as f:
            content = f.read()
        
        # 清理內容
        cleaned_content, changes_made = clean_file_content(content)
        
        # 如果有變更，寫回檔案
        if changes_made:
            with open(filename, 'wb') as f:
                f.write(cleaned_content)
            print(f"已清理: {filename}", file=sys.stderr)
    
    except Exception as e:
        print(f"處理檔案 {filename} 時發生錯誤: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
FILTER_SCRIPT

    chmod +x /tmp/git_secret_filter.py
    log_success "進階清理腳本已建立"
}

# 使用 git filter-repo (推薦)
rewrite_with_filter_repo() {
    log_step "檢查 git filter-repo..."
    
    if ! command -v git-filter-repo &> /dev/null; then
        log_warning "git filter-repo 未安裝，正在安裝..."
        
        # 嘗試使用 pip 安裝
        if command -v pip3 &> /dev/null; then
            pip3 install git-filter-repo
        elif command -v pip &> /dev/null; then
            pip install git-filter-repo
        else
            log_error "無法安裝 git filter-repo，請手動安裝："
            echo "pip install git-filter-repo"
            return 1
        fi
    fi
    
    log_info "使用 git filter-repo 重寫歷史..."
    
    # 使用 filter-repo 清理
    git filter-repo --force --blob-callback "
import re

# 定義機密模式
patterns = [
    (rb'glpat-[a-zA-Z0-9_-]{20}', b'{{GITLAB_TOKEN}}'),
    (rb'ghp_[a-zA-Z0-9_]{36}', b'{{GITHUB_TOKEN}}'),
]

# 清理 blob 內容
for pattern, replacement in patterns:
    blob.data = re.sub(pattern, replacement, blob.data)
"
    
    log_success "git filter-repo 完成"
}

# 改進的 filter-branch 方法
rewrite_with_improved_filter_branch() {
    log_step "使用改進的 git filter-branch..."
    
    # 設定環境變數來抑制警告
    export FILTER_BRANCH_SQUELCH_WARNING=1
    
    # 使用 index-filter 而不是 tree-filter (更快)
    git filter-branch --force --index-filter '
        git ls-files -s | sed "s/\t\"*\([^\"]*\)\"*/\t\1/" |
        while read mode sha1 stage file; do
            # 只處理特定檔案類型，排除清理工具
            if echo "$file" | grep -E "\.(py|md|txt|yml|yaml|json)$" | grep -v -E "(cleanup|cleaner|filter)" > /dev/null; then
                # 取得檔案內容並清理
                git cat-file blob $sha1 | python3 /tmp/git_secret_filter.py "$file" > /tmp/cleaned_content 2>/dev/null
                if [ -s /tmp/cleaned_content ]; then
                    new_sha1=$(git hash-object -w /tmp/cleaned_content)
                    printf "%s %s %s\t%s\n" "$mode" "$new_sha1" "$stage" "$file"
                else
                    printf "%s %s %s\t%s\n" "$mode" "$sha1" "$stage" "$file"
                fi
            else
                printf "%s %s %s\t%s\n" "$mode" "$sha1" "$stage" "$file"
            fi
        done |
        git update-index --index-info
        rm -f /tmp/cleaned_content
    ' --prune-empty -- --all
    
    log_success "git filter-branch 完成"
}

# 執行歷史重寫
perform_history_rewrite() {
    log_step "執行歷史重寫..."
    
    # 嘗試使用 git filter-repo (現代推薦方法)
    if rewrite_with_filter_repo; then
        return 0
    fi
    
    log_warning "filter-repo 失敗，回退到 filter-branch"
    
    # 回退到改進的 filter-branch
    rewrite_with_improved_filter_branch
}

# 智慧驗證清理結果
smart_verify_cleanup() {
    log_step "智慧驗證清理結果..."
    
    # 檢查當前檔案（排除工具腳本和備份）
    log_info "檢查當前檔案中的機密..."
    
    secret_files=$(find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.txt" \) \
        ! -name "*cleanup*" ! -name "*cleaner*" ! -name "*filter*" \
        ! -name "*.backup" ! -path "./.git/*" \
        -exec grep -l "glpat-[a-zA-Z0-9_-]\{20\}" {} \; 2>/dev/null)
    
    if [ -n "$secret_files" ]; then
        log_warning "發現包含機密的檔案："
        echo "$secret_files"
        return 1
    else
        log_success "當前檔案已清理完成"
    fi
    
    # 檢查 Git 歷史（更精確的檢查）
    log_info "檢查 Git 歷史中的機密..."
    
    if git log --all --source --pretty=format: --name-only | sort -u | \
       xargs -I {} git log --all -p -- {} | grep -q "glpat-[a-zA-Z0-9_-]\{20\}" 2>/dev/null; then
        log_warning "Git 歷史中仍發現機密資訊"
        return 1
    else
        log_success "Git 歷史已清理完成"
    fi
    
    return 0
}

# 強制推送前的最終確認
final_confirmation() {
    log_step "最終確認..."
    
    echo ""
    echo "========================================"
    echo "         最終推送確認"
    echo "========================================"
    echo ""
    echo "即將執行的操作："
    echo "1. 強制推送重寫的歷史到 GitHub"
    echo "2. 強制推送重寫的歷史到 GitLab"
    echo ""
    echo "⚠️  重要提醒："
    echo "- 這將永久覆蓋遠端倉庫的歷史"
    echo "- 所有協作者都需要重新 clone"
    echo "- 此操作無法撤銷"
    echo ""
    
    read -p "輸入 'CONFIRM' 來執行推送: " confirm
    if [ "$confirm" != "CONFIRM" ]; then
        log_info "推送已取消"
        return 1
    fi
    
    return 0
}

# 執行最終推送
execute_push() {
    log_step "執行最終推送..."
    
    local push_failed=false
    
    # 推送到 GitHub
    log_info "推送到 GitHub..."
    if git push github main --force; then
        log_success "GitHub 推送成功"
    else
        log_error "GitHub 推送失敗"
        push_failed=true
    fi
    
    # 推送到 GitLab
    log_info "推送到 GitLab..."
    if git push gitlab main --force; then
        log_success "GitLab 推送成功"
    else
        log_error "GitLab 推送失敗"
        push_failed=true
    fi
    
    if [ "$push_failed" = true ]; then
        return 1
    fi
    
    return 0
}

# 主執行流程
main() {
    echo "==================== Git 歷史清理工具 v2 - 修正版本 ===================="
    echo "版本：4.1.0"
    echo "修正：處理未暫存變更、清理 .env 檔案、智慧排除"
    echo "========================================================================"
    
    # 檢查是否在 Git 倉庫中
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "當前目錄不是 Git 倉庫"
        exit 1
    fi
    
    # 第一步：清理工作區
    clean_working_directory
    
    # 第二步：立即清理當前檔案
    clean_current_files
    
    # 第三步：建立進階清理腳本
    create_advanced_cleaner
    
    # 第四步：執行歷史重寫
    perform_history_rewrite
    
    # 第五步：清理 Git 參考
    log_step "清理 Git 參考..."
    git for-each-ref --format="delete %(refname)" refs/original 2>/dev/null | git update-ref --stdin || true
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive
    log_success "Git 清理完成"
    
    # 第六步：智慧驗證
    if smart_verify_cleanup; then
        log_success "清理驗證通過"
        
        # 第七步：最終確認和推送
        if final_confirmation; then
            if execute_push; then
                log_success "🎉 所有操作完成！"
                
                echo ""
                echo "📋 後續步驟："
                echo "1. 通知團隊成員重新 clone 專案"
                echo "2. 撤銷舊的 GitLab Token"
                echo "3. 建立新的 Token 並更新 .env"
                
            else
                log_error "推送失敗"
                exit 1
            fi
        fi
    else
        log_error "清理驗證失敗"
        echo ""
        echo "建議手動檢查剩餘問題或聯絡支援"
        exit 1
    fi
    
    # 清理臨時檔案
    rm -f /tmp/git_secret_filter.py
}

# 執行主程式
main "$@"