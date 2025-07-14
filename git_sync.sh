#!/bin/bash

# 主要的 GitLab 和 GitHub 倉庫檢查與同步腳本
# 作者：AI Assistant
# 版本：2.2（新增分支檢查功能）

# 腳本目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 顏色代碼
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 調試模式（設為 true 來啟用調試訊息）
DEBUG=false

# 調試函數
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $1${NC}" >&2
    fi
}

# 檢查並修正分支配置
check_branch_configuration() {
    debug_log "檢查分支配置"

    local current_branch=$(git branch --show-current)
    local default_branch=$(git config --get init.defaultBranch 2>/dev/null)

    echo -e "${BLUE}檢查分支配置...${NC}"

    # 檢查並設定全域預設分支為 main
    if [ "$default_branch" != "main" ]; then
        echo -e "${YELLOW}設定 main 為全域預設分支...${NC}"
        git config --global init.defaultBranch main
        echo -e "${GREEN}✓ 已設定 main 為全域預設分支${NC}"
    else
        echo -e "${GREEN}✓ main 已是全域預設分支${NC}"
    fi

    # 檢查當前分支名稱
    if [ "$current_branch" = "master" ]; then
        echo -e "${YELLOW}⚠ 檢測到使用舊式 'master' 分支${NC}"
        echo -e "${YELLOW}建議使用現代標準的 'main' 分支${NC}"
        echo ""
        echo "選項："
        echo "1) 將 master 重新命名為 main（推薦）"
        echo "2) 保持使用 master 分支"
        echo "3) 取消操作"

        read -p "請選擇 (1-3): " branch_choice

        case $branch_choice in
        1)
            rename_master_to_main
            return $?
            ;;
        2)
            echo -e "${YELLOW}保持使用 master 分支${NC}"
            ;;
        3)
            echo -e "${YELLOW}操作已取消${NC}"
            return 1
            ;;
        *)
            echo -e "${RED}無效選項，保持現狀${NC}"
            ;;
        esac
    elif [ "$current_branch" = "main" ]; then
        echo -e "${GREEN}✓ 當前使用 main 分支（符合現代標準）${NC}"
    else
        echo -e "${BLUE}ℹ 當前分支：$current_branch${NC}"
    fi

    echo ""
    return 0
}

# 重新命名 master 為 main
rename_master_to_main() {
    echo -e "${BLUE}開始將 master 重新命名為 main...${NC}"

    # 重新命名本地分支
    git branch -m master main

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 本地分支重新命名成功${NC}"

        # 檢查是否有遠端配置
        local remotes=$(git remote)
        if [ ! -z "$remotes" ]; then
            echo -e "${YELLOW}檢測到遠端倉庫，建議稍後更新遠端分支${NC}"
            echo -e "${BLUE}ℹ 執行同步時會自動推送 main 分支到遠端${NC}"
        fi

        return 0
    else
        echo -e "${RED}✗ 本地分支重新命名失敗${NC}"
        return 1
    fi
}

# 檢查分支是否有提交記錄
check_branch_has_commits() {
    local branch_name="$1"

    # 檢查分支是否存在且有提交
    if git rev-parse --verify "$branch_name" >/dev/null 2>&1; then
        # 檢查是否有提交記錄
        local commit_count=$(git rev-list --count "$branch_name" 2>/dev/null || echo "0")
        if [ "$commit_count" -gt 0 ]; then
            debug_log "分支 $branch_name 有 $commit_count 個提交"
            return 0
        else
            debug_log "分支 $branch_name 存在但沒有提交記錄"
            return 1
        fi
    else
        debug_log "分支 $branch_name 不存在"
        return 1
    fi
}

# 檢查倉庫狀態並建議操作
check_repository_status() {
    local current_branch=$(git branch --show-current)

    echo -e "${BLUE}檢查倉庫狀態...${NC}"

    # 檢查是否有未追蹤的檔案
    local untracked_files=$(git ls-files --others --exclude-standard)
    local modified_files=$(git diff --name-only)
    local staged_files=$(git diff --cached --name-only)

    if [ ! -z "$untracked_files" ]; then
        echo -e "${YELLOW}發現未追蹤的檔案：${NC}"
        echo "$untracked_files" | head -5 | while read file; do
            echo -e "  ${CYAN}+ $file${NC}"
        done
        local total_untracked=$(echo "$untracked_files" | wc -l)
        if [ "$total_untracked" -gt 5 ]; then
            echo -e "  ${BLUE}... 以及其他 $((total_untracked - 5)) 個檔案${NC}"
        fi
        echo ""
    fi

    if [ ! -z "$modified_files" ]; then
        echo -e "${YELLOW}發現已修改的檔案：${NC}"
        echo "$modified_files" | head -5 | while read file; do
            echo -e "  ${YELLOW}M $file${NC}"
        done
        echo ""
    fi

    if [ ! -z "$staged_files" ]; then
        echo -e "${GREEN}發現已暫存的檔案：${NC}"
        echo "$staged_files" | head -5 | while read file; do
            echo -e "  ${GREEN}A $file${NC}"
        done
        echo ""
    fi

    # 檢查是否需要初始提交
    if ! check_branch_has_commits "$current_branch"; then
        echo -e "${YELLOW}⚠ 當前分支沒有任何提交記錄${NC}"

        if [ ! -z "$untracked_files" ] || [ ! -z "$modified_files" ] || [ ! -z "$staged_files" ]; then
            echo -e "${BLUE}建議先提交變更：${NC}"
            echo ""
            echo "1) 添加所有檔案：${CYAN}git add .${NC}"
            echo "2) 創建初始提交：${CYAN}git commit -m \"Initial commit\"${NC}"
            echo "3) 重新執行同步腳本"
            echo ""

            read -p "是否現在要執行初始提交？(y/n): " do_initial_commit

            if [ "$do_initial_commit" = "y" ] || [ "$do_initial_commit" = "Y" ]; then
                perform_initial_commit
                return $?
            else
                echo -e "${YELLOW}請手動提交後重新執行腳本${NC}"
                return 1
            fi
        else
            echo -e "${RED}沒有任何檔案可以提交${NC}"
            echo -e "${YELLOW}請添加一些檔案後重新執行腳本${NC}"
            return 1
        fi
    fi

    echo -e "${GREEN}✓ 倉庫狀態正常${NC}"
    return 0
}

# 執行初始提交
perform_initial_commit() {
    echo -e "${BLUE}執行初始提交...${NC}"

    # 添加所有檔案
    echo -e "${YELLOW}添加所有檔案到暫存區...${NC}"
    git add .

    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ 添加檔案失敗${NC}"
        return 1
    fi

    # 檢查是否有檔案被暫存
    local staged_files=$(git diff --cached --name-only)
    if [ -z "$staged_files" ]; then
        echo -e "${RED}✗ 沒有檔案被暫存，可能所有檔案都被 .gitignore 忽略${NC}"
        return 1
    fi

    echo -e "${GREEN}✓ 已添加 $(echo "$staged_files" | wc -l) 個檔案${NC}"

    # 創建提交
    echo -e "${YELLOW}創建初始提交...${NC}"
    git commit -m "Initial commit: 添加專案檔案"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 初始提交成功${NC}"
        return 0
    else
        echo -e "${RED}✗ 提交失敗${NC}"
        return 1
    fi
}
load_modules() {
    debug_log "開始載入模組..."

    # 檢查模組檔案是否存在
    local required_modules=("remote_config.sh" "security_check.sh")

    for module in "${required_modules[@]}"; do
        if [ ! -f "$SCRIPT_DIR/$module" ]; then
            echo -e "${RED}錯誤：找不到模組檔案 $module${NC}"
            echo -e "${YELLOW}請確保 $module 與主腳本在同一目錄中${NC}"
            return 1
        fi
    done

    # 載入模組
    debug_log "載入 remote_config.sh..."
    if ! source "$SCRIPT_DIR/remote_config.sh"; then
        echo -e "${RED}錯誤：載入 remote_config.sh 失敗${NC}"
        return 1
    fi

    debug_log "載入 security_check.sh..."
    if ! source "$SCRIPT_DIR/security_check.sh"; then
        echo -e "${RED}錯誤：載入 security_check.sh 失敗${NC}"
        return 1
    fi

    debug_log "模組載入完成"
    return 0
}

# 處理單平台情況
handle_single_platform() {
    local existing_remote="$1"
    local platform_name="$2"
    local current_branch="$3"

    echo ""
    echo -e "${YELLOW}檢測到您只配置了 $platform_name 遠端。${NC}"
    echo -e "${YELLOW}您可以選擇：${NC}"
    echo "1) 直接推送到 $platform_name"
    echo "2) 配置第二個平台以啟用雙平台同步"
    echo "3) 取消操作"

    read -p "請選擇 (1-3): " platform_choice

    case $platform_choice in
    1)
        echo -e "${BLUE}執行單平台推送到 $platform_name...${NC}"

        # 執行安全檢查
        echo -e "${PURPLE}================== 安全檢查 ==================${NC}"
        if ! perform_security_check; then
            if ! handle_security_issues; then
                echo -e "${RED}腳本已終止。${NC}"
                return 1
            fi
        fi
        echo -e "${PURPLE}=============================================${NC}"
        echo ""

        # 檢查分支是否有提交記錄
        if ! check_branch_has_commits "$current_branch"; then
            echo -e "${RED}✗ 分支 '$current_branch' 沒有任何提交記錄${NC}"
            echo -e "${YELLOW}請先提交一些變更後再執行推送${NC}"
            return 1
        fi

        # 推送到單個平台
        push_to_single_platform "$existing_remote" "$platform_name" "$current_branch"
        ;;
    2)
        echo -e "${BLUE}開始配置第二個平台...${NC}"
        configure_second_platform "$platform_name" "$existing_remote" "$current_branch"
        ;;
    3)
        echo -e "${YELLOW}操作已取消。${NC}"
        return 1
        ;;
    *)
        echo -e "${RED}無效的選項，操作已取消。${NC}"
        return 1
        ;;
    esac
}

# 推送到單個平台
push_to_single_platform() {
    local remote="$1"
    local platform="$2"
    local branch="$3"

    echo -e "${YELLOW}推送到 $platform (${remote})...${NC}"

    if [ ! -z "$branch" ]; then
        git push "$remote" "$branch"
    else
        git push "$remote"
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 成功推送到 $platform${NC}"
    else
        echo -e "${RED}✗ 推送到 $platform 失敗${NC}"
    fi
}

# 配置第二個平台
configure_second_platform() {
    local platform_name="$1"
    local existing_remote="$2"
    local current_branch="$3"

    if [ "$platform_name" = "GitLab" ]; then
        prompt_add_github_remote
        local new_github=$(get_github_remote)
        if [ ! -z "$new_github" ]; then
            setup_all_remote "$existing_remote" "$new_github"
            perform_dual_platform_sync "$current_branch"
        fi
    else
        prompt_add_gitlab_remote
        local new_gitlab=$(get_gitlab_remote)
        if [ ! -z "$new_gitlab" ]; then
            setup_all_remote "$new_gitlab" "$existing_remote"
            perform_dual_platform_sync "$current_branch"
        fi
    fi
}

# 執行雙平台同步
perform_dual_platform_sync() {
    local current_branch="$1"

    echo -e "${PURPLE}================== 安全檢查 ==================${NC}"
    if ! perform_security_check; then
        if ! handle_security_issues; then
            echo -e "${RED}腳本已終止。${NC}"
            return 1
        fi
    fi
    echo -e "${PURPLE}=============================================${NC}"
    echo ""

    perform_push "$current_branch"
}

# 執行推送函數
perform_push() {
    local current_branch="$1"

    # 如果沒有提供分支名，使用當前分支
    if [ -z "$current_branch" ]; then
        current_branch=$(git branch --show-current)
    fi

    # 檢查分支是否有提交記錄
    if ! check_branch_has_commits "$current_branch"; then
        echo -e "${RED}✗ 分支 '$current_branch' 沒有任何提交記錄${NC}"
        echo -e "${YELLOW}請先提交一些變更後再執行推送${NC}"
        echo ""
        echo "建議操作："
        echo "1. git add .                    # 添加所有檔案"
        echo "2. git commit -m \"初始提交\"    # 創建首次提交"
        echo "3. 重新執行此腳本"
        return 1
    fi

    echo -e "${YELLOW}是否現在要推送到兩個倉庫？(y/n)${NC}"
    read push_now

    if [ "$push_now" = "y" ] || [ "$push_now" = "Y" ]; then
        if git remote -v | grep -q "all"; then
            push_via_all_remote "$current_branch"
        else
            individual_push "$current_branch"
        fi
    else
        echo -e "${YELLOW}推送已取消。${NC}"
    fi
}

# 通過 'all' 遠端推送
push_via_all_remote() {
    local current_branch="$1"

    echo -e "${YELLOW}通過 'all' 遠端推送到兩個倉庫...${NC}"

    if [ ! -z "$current_branch" ]; then
        git push all "$current_branch"
    else
        git push all
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 成功推送到兩個倉庫${NC}"
    else
        echo -e "${RED}✗ 推送到兩個倉庫失敗${NC}"
        fallback_individual_push "$current_branch"
    fi
}

# 個別推送函數
individual_push() {
    local current_branch="$1"
    local gitlab_remote=$(get_gitlab_remote)
    local github_remote=$(get_github_remote)

    if [ ! -z "$gitlab_remote" ]; then
        echo -e "${YELLOW}推送到 GitLab (${gitlab_remote})...${NC}"
        if [ ! -z "$current_branch" ]; then
            git push "$gitlab_remote" "$current_branch"
        else
            git push "$gitlab_remote"
        fi

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 成功推送到 GitLab${NC}"
        else
            echo -e "${RED}✗ 推送到 GitLab 失敗${NC}"
        fi
    fi

    if [ ! -z "$github_remote" ]; then
        echo -e "${YELLOW}推送到 GitHub (${github_remote})...${NC}"
        if [ ! -z "$current_branch" ]; then
            git push "$github_remote" "$current_branch"
        else
            git push "$github_remote"
        fi

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 成功推送到 GitHub${NC}"
        else
            echo -e "${RED}✗ 推送到 GitHub 失敗${NC}"
        fi
    fi
}

# 備用個別推送函數
fallback_individual_push() {
    local current_branch="$1"

    echo -e "${YELLOW}嘗試單獨推送...${NC}"
    individual_push "$current_branch"
}

# 主函數
main() {
    debug_log "主函數開始執行"

    echo -e "${CYAN}==================== Git 同步工具 ====================${NC}"
    echo -e "${YELLOW}版本：2.2.1（修正推送錯誤問題）${NC}"
    echo ""

    # 載入模組
    if ! load_modules; then
        echo -e "${RED}模組載入失敗，腳本終止${NC}"
        exit 1
    fi

    # 檢查當前目錄是否為 git 倉庫
    debug_log "檢查 Git 倉庫"
    if [ ! -d ".git" ]; then
        echo -e "${RED}錯誤：當前目錄不是 Git 倉庫。${NC}"
        exit 1
    fi

    # 檢查並修正分支配置
    echo -e "${PURPLE}================== 分支配置檢查 ==================${NC}"
    if ! check_branch_configuration; then
        echo -e "${RED}分支配置檢查失敗或用戶取消操作${NC}"
        exit 1
    fi
    echo -e "${PURPLE}===============================================${NC}"
    echo ""

    # 配置遠端倉庫
    echo -e "${PURPLE}================== 遠端配置檢查 ==================${NC}"
    if ! configure_remotes; then
        echo -e "${RED}遠端配置失敗${NC}"
        exit 1
    fi

    # 檢查倉庫狀態
    echo -e "${PURPLE}================== 倉庫狀態檢查 ==================${NC}"
    if ! check_repository_status; then
        echo -e "${YELLOW}請處理倉庫狀態後重新執行腳本${NC}"
        exit 1
    fi
    echo -e "${PURPLE}===============================================${NC}"
    echo ""

    # 獲取配置結果
    local gitlab_remote=$(get_gitlab_remote)
    local github_remote=$(get_github_remote)

    debug_log "GitLab 遠端: $gitlab_remote"
    debug_log "GitHub 遠端: $github_remote"

    # 重新獲取當前分支（可能已經改名）
    local current_branch=$(git branch --show-current)
    echo -e "${YELLOW}當前分支: ${current_branch}${NC}"
    echo ""

    # 檢查遠端配置狀況並執行相應操作
    process_remote_configuration "$gitlab_remote" "$github_remote" "$current_branch"

    echo -e "${GREEN}腳本執行完成。${NC}"
}

# 處理遠端配置
process_remote_configuration() {
    local gitlab_remote="$1"
    local github_remote="$2"
    local current_branch="$3"

    if [ ! -z "$gitlab_remote" ] && [ ! -z "$github_remote" ]; then
        # 雙平台配置
        echo -e "${GREEN}✓ 檢測到 GitLab 和 GitHub 雙平台配置${NC}"
        setup_all_remote "$gitlab_remote" "$github_remote"

        # 執行安全檢查
        echo -e "${PURPLE}================== 安全檢查 ==================${NC}"
        if ! perform_security_check; then
            if ! handle_security_issues; then
                echo -e "${RED}腳本已終止。${NC}"
                exit 1
            fi
        fi
        echo -e "${PURPLE}=============================================${NC}"
        echo ""

        # 執行推送
        perform_push "$current_branch"

    elif [ ! -z "$gitlab_remote" ] && [ -z "$github_remote" ]; then
        # 僅 GitLab
        echo -e "${YELLOW}僅檢測到 GitLab 遠端，是否需要添加 GitHub 遠端以啟用雙平台同步？${NC}"
        handle_single_platform "$gitlab_remote" "GitLab" "$current_branch"

    elif [ -z "$gitlab_remote" ] && [ ! -z "$github_remote" ]; then
        # 僅 GitHub
        echo -e "${YELLOW}僅檢測到 GitHub 遠端，是否需要添加 GitLab 遠端以啟用雙平台同步？${NC}"
        handle_single_platform "$github_remote" "GitHub" "$current_branch"

    else
        # 無有效配置
        echo -e "${RED}錯誤：未檢測到任何有效的遠端配置${NC}"
        echo -e "${YELLOW}請先配置 GitLab 或 GitHub 遠端，然後重新執行腳本${NC}"
        exit 1
    fi
}

# 顯示使用說明
show_usage() {
    echo -e "${BLUE}Git 同步工具使用說明：${NC}"
    echo ""
    echo -e "${YELLOW}功能：${NC}"
    echo "  - 自動檢測和配置 GitLab 與 GitHub 遠端"
    echo "  - 分支名稱檢查與現代化（master → main）"
    echo "  - 安全檢查，防止機密資訊洩露"
    echo "  - 支援同時推送到多個遠端倉庫"
    echo "  - 環境變數範本自動生成"
    echo ""
    echo -e "${YELLOW}使用方法：${NC}"
    echo "  ./git_sync.sh [選項]"
    echo ""
    echo -e "${YELLOW}選項：${NC}"
    echo "  -h, --help     顯示此說明"
    echo "  -v, --version  顯示版本資訊"
    echo "  -d, --debug    啟用調試模式"
    echo ""
    echo -e "${YELLOW}需要的模組檔案：${NC}"
    echo "  - remote_config.sh    (遠端配置模組)"
    echo "  - security_check.sh   (安全檢查模組)"
    echo ""
    echo -e "${YELLOW}範例：${NC}"
    echo "  ./git_sync.sh          # 互動式同步"
    echo "  ./git_sync.sh --debug  # 調試模式"
    echo "  ./git_sync.sh --help   # 顯示說明"
    echo ""
    echo -e "${YELLOW}新功能（v2.2.1）：${NC}"
    echo "  - 修正分支沒有提交記錄時的推送錯誤"
    echo "  - 新增倉庫狀態檢查功能"
    echo "  - 支援自動執行初始提交"
    echo "  - 自動檢測 master 分支並建議改名為 main"
    echo "  - 設定 main 為全域預設分支"
    echo "  - 符合現代 Git 標準"
}

# 顯示版本資訊
show_version() {
    echo "Git 同步工具 v2.2.1（修正推送錯誤問題）"
    echo "作者：AI Assistant"
    echo "支援平台：GitLab, GitHub"
    echo "新功能：分支名稱現代化、環境變數範本生成、進階安全檢查、倉庫狀態檢查"
    echo ""
    echo "版本歷史："
    echo "  v2.2.1 - 修正 'src refspec main does not match any' 錯誤"
    echo "  v2.2 - 新增分支檢查與 master→main 遷移功能"
    echo "  v2.1 - 格式化優化、環境變數管理"
    echo "  v2.0 - 模組化重構、擴展安全檢查"
    echo "  v1.0 - 基本同步功能"
}

# 處理命令列參數
handle_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
        -h | --help)
            show_usage
            exit 0
            ;;
        -v | --version)
            show_version
            exit 0
            ;;
        -d | --debug)
            DEBUG=true
            debug_log "調試模式已啟用"
            shift
            ;;
        --branch-check)
            echo -e "${BLUE}僅執行分支檢查...${NC}"
            if [ ! -d ".git" ]; then
                echo -e "${RED}錯誤：當前目錄不是 Git 倉庫。${NC}"
                exit 1
            fi
            check_branch_configuration
            exit $?
            ;;
        *)
            echo -e "${RED}未知的選項: $1${NC}"
            echo -e "${YELLOW}使用 --help 查看可用選項${NC}"
            exit 1
            ;;
        esac
    done
}

# 主程式入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # 處理命令列參數
    handle_arguments "$@"

    # 執行主函數
    main
fi
