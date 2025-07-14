#!/bin/bash

# 遠端配置模組
# 負責 GitLab 和 GitHub 遠端的檢測、配置和管理
# 版本：2.1

# 全域變數
DETECTED_GITLAB_REMOTE=""
DETECTED_GITHUB_REMOTE=""

# 配置所有遠端倉庫的主函數
configure_remotes() {
    echo -e "${YELLOW}檢查 Git 遠端...${NC}"
    git remote -v
    echo ""

    # 配置 GitLab 遠端
    configure_gitlab_remote

    # 配置 GitHub 遠端
    configure_github_remote

    echo ""
}

# 配置 GitLab 遠端
configure_gitlab_remote() {
    echo -e "${BLUE}檢查 GitLab 遠端配置...${NC}"

    # 首先查找明確命名為 gitlab 的遠端
    if git remote -v | grep -q "gitlab"; then
        DETECTED_GITLAB_REMOTE=$(git remote -v | grep "gitlab" | grep "(push)" | head -n1 | awk '{print $1}')
        echo -e "${GREEN}✓ 找到 GitLab 遠端：${DETECTED_GITLAB_REMOTE}${NC}"
    else
        # 查找指向 GitLab 的 URL
        find_gitlab_by_url
    fi
}

# 根據 URL 查找 GitLab 遠端
find_gitlab_by_url() {
    local gitlab_remote=""

    while read -r remote_name remote_url _; do
        if echo "$remote_url" | grep -q "gitlab"; then
            gitlab_remote="$remote_name"
            break
        fi
    done < <(git remote -v | grep "(push)")

    if [ ! -z "$gitlab_remote" ]; then
        DETECTED_GITLAB_REMOTE="$gitlab_remote"
        echo -e "${GREEN}✓ 找到指向 GitLab 的遠端：${DETECTED_GITLAB_REMOTE}${NC}"
    else
        echo -e "${RED}✗ 未找到 GitLab 遠端${NC}"
        prompt_add_gitlab_remote
    fi
}

# 提示新增 GitLab 遠端
prompt_add_gitlab_remote() {
    echo -e "${YELLOW}是否要添加 GitLab 遠端？(y/n)${NC}"
    read add_gitlab

    if [ "$add_gitlab" = "y" ] || [ "$add_gitlab" = "Y" ]; then
        echo -e "${YELLOW}請輸入您的 GitLab 倉庫 URL：${NC}"
        read gitlab_url

        # 驗證並添加 URL
        add_gitlab_remote "$gitlab_url"
    fi
}

# 添加 GitLab 遠端
add_gitlab_remote() {
    local gitlab_url="$1"

    # 驗證 URL 格式
    if validate_git_url "$gitlab_url"; then
        # 確保 URL 以 .git 結尾
        gitlab_url=$(normalize_git_url "$gitlab_url")

        git remote add gitlab "$gitlab_url"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ GitLab 遠端添加成功${NC}"
            DETECTED_GITLAB_REMOTE="gitlab"
        else
            echo -e "${RED}✗ 添加 GitLab 遠端失敗${NC}"
        fi
    else
        echo -e "${RED}✗ 無效的 Git URL 格式${NC}"
    fi
}

# 配置 GitHub 遠端
configure_github_remote() {
    echo -e "${BLUE}檢查 GitHub 遠端配置...${NC}"

    # 優先級順序：origin > github > 其他指向 github.com 的遠端
    # 但排除 'all' 遠端，因為它是合併遠端

    # 1. 首先檢查 origin 是否指向 GitHub
    if check_origin_github; then
        return
    fi

    # 2. 然後檢查明確命名為 github 的遠端
    if check_explicit_github_remote; then
        return
    fi

    # 3. 最後查找其他指向 GitHub 的遠端（排除 all）
    find_github_by_url
}

# 檢查 origin 是否指向 GitHub
check_origin_github() {
    if git remote -v | grep -q "origin" && ! git remote -v | grep "origin" | grep -q "all"; then
        local origin_url=$(git remote get-url origin 2>/dev/null)
        if echo "$origin_url" | grep -q "github.com"; then
            DETECTED_GITHUB_REMOTE="origin"
            echo -e "${GREEN}✓ 找到 GitHub 遠端：${DETECTED_GITHUB_REMOTE}${NC}"
            return 0
        fi
    fi
    return 1
}

# 檢查明確命名的 GitHub 遠端
check_explicit_github_remote() {
    if git remote -v | grep -q "^github\s"; then
        local github_remote_name="github"
        local github_remote_url=$(git remote get-url github 2>/dev/null)

        # 確認 URL 確實指向 GitHub
        if echo "$github_remote_url" | grep -q "github.com"; then
            DETECTED_GITHUB_REMOTE="$github_remote_name"
            echo -e "${GREEN}✓ 找到 GitHub 遠端：${DETECTED_GITHUB_REMOTE}${NC}"
            return 0
        fi
    fi
    return 1
}

# 根據 URL 查找 GitHub 遠端
find_github_by_url() {
    local github_remote=""

    while read -r remote_name remote_url _; do
        # 排除 'all' 遠端，因為它是合併遠端
        if [ "$remote_name" != "all" ] && echo "$remote_url" | grep -q "github.com"; then
            github_remote="$remote_name"
            break
        fi
    done < <(git remote -v | grep "(push)")

    if [ ! -z "$github_remote" ]; then
        DETECTED_GITHUB_REMOTE="$github_remote"
        echo -e "${GREEN}✓ 找到指向 GitHub 的遠端：${DETECTED_GITHUB_REMOTE}${NC}"
    else
        echo -e "${RED}✗ 未找到 GitHub 遠端${NC}"
        prompt_add_github_remote
    fi
}

# 提示新增 GitHub 遠端
prompt_add_github_remote() {
    echo -e "${YELLOW}是否要添加 GitHub 遠端？(y/n)${NC}"
    read add_github

    if [ "$add_github" = "y" ] || [ "$add_github" = "Y" ]; then
        echo -e "${YELLOW}請輸入您的 GitHub 倉庫 URL：${NC}"
        read github_url

        # 驗證並添加 URL
        add_github_remote "$github_url"
    fi
}

# 添加 GitHub 遠端
add_github_remote() {
    local github_url="$1"

    # 驗證 URL 格式
    if validate_git_url "$github_url"; then
        # 確保 URL 以 .git 結尾
        github_url=$(normalize_git_url "$github_url")

        git remote add github "$github_url"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ GitHub 遠端添加成功${NC}"
            DETECTED_GITHUB_REMOTE="github"
        else
            echo -e "${RED}✗ 添加 GitHub 遠端失敗${NC}"
        fi
    else
        echo -e "${RED}✗ 無效的 Git URL 格式${NC}"
    fi
}

# 設置合併遠端（用於同時推送到兩個倉庫）
setup_all_remote() {
    local gitlab_remote="$1"
    local github_remote="$2"

    if [ -z "$gitlab_remote" ] || [ -z "$github_remote" ]; then
        echo -e "${YELLOW}無法設置合併遠端：缺少必要的遠端配置${NC}"
        return 1
    fi

    # 檢查是否已經設置 'all' 遠端
    if ! git remote -v | grep -q "all"; then
        echo -e "${YELLOW}是否要設置一個 'all' 遠端以同時推送到兩個倉庫？(y/n)${NC}"
        read setup_all

        if [ "$setup_all" = "y" ] || [ "$setup_all" = "Y" ]; then
            create_all_remote "$gitlab_remote" "$github_remote"
        fi
    else
        echo -e "${GREEN}✓ 'all' 遠端已配置${NC}"
        display_all_remote_info
    fi
}

# 創建合併遠端
create_all_remote() {
    local gitlab_remote="$1"
    local github_remote="$2"

    local gitlab_url=$(git remote get-url --push "$gitlab_remote")
    local github_url=$(git remote get-url --push "$github_remote")

    if [ -z "$gitlab_url" ] || [ -z "$github_url" ]; then
        echo -e "${RED}✗ 無法獲取遠端 URL${NC}"
        return 1
    fi

    # 規範化 URL
    gitlab_url=$(normalize_git_url "$gitlab_url")
    github_url=$(normalize_git_url "$github_url")

    # 確保兩個 URL 不同
    if [ "$gitlab_url" = "$github_url" ]; then
        echo -e "${RED}✗ GitLab 和 GitHub 遠端指向相同的 URL，無法創建合併遠端${NC}"
        echo -e "${YELLOW}GitLab URL: $gitlab_url${NC}"
        echo -e "${YELLOW}GitHub URL: $github_url${NC}"
        return 1
    fi

    # 重新配置 'all' 遠端
    recreate_all_remote "$gitlab_url" "$github_url"
}

# 重新創建 'all' 遠端
recreate_all_remote() {
    local gitlab_url="$1"
    local github_url="$2"

    # 刪除現有的 all 遠端（如果存在）
    if git remote | grep -q "^all$"; then
        echo -e "${YELLOW}發現現有的 'all' 遠端，正在重新配置...${NC}"
        git remote remove all
    fi

    # 添加 all 遠端
    git remote add all "$gitlab_url"
    git remote set-url --add --push all "$gitlab_url"
    git remote set-url --add --push all "$github_url"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 成功設置 'all' 遠端${NC}"
        echo -e "${YELLOW}現在您可以使用以下命令推送到兩個倉庫：${GREEN}git push all${NC}"
        display_all_remote_info
    else
        echo -e "${RED}✗ 設置 'all' 遠端失敗${NC}"
        return 1
    fi
}

# 顯示合併遠端資訊
display_all_remote_info() {
    echo -e "${BLUE}'all' 遠端配置：${NC}"
    git remote get-url --all --push all | while read url; do
        if echo "$url" | grep -q "gitlab"; then
            echo -e "${YELLOW}  → GitLab: $url${NC}"
        elif echo "$url" | grep -q "github"; then
            echo -e "${YELLOW}  → GitHub: $url${NC}"
        else
            echo -e "${YELLOW}  → 未知平台: $url${NC}"
        fi
    done
}

# 驗證 Git URL 格式
validate_git_url() {
    local url="$1"

    # 檢查基本的 Git URL 格式
    if echo "$url" | grep -qE '^(https?://|git@|ssh://git@)'; then
        return 0
    else
        return 1
    fi
}

# 規範化 Git URL（確保以 .git 結尾）
normalize_git_url() {
    local url="$1"

    # 如果 URL 已經以 .git 結尾，直接返回
    if echo "$url" | grep -q '\.git$'; then
        echo "$url"
        return
    fi

    # 如果 URL 以 .git/ 結尾，移除斜線
    if echo "$url" | grep -q '\.git/$'; then
        echo "$url" | sed 's|\.git/$|.git|'
        return
    fi

    # 否則添加 .git
    echo "${url}.git"
}

# 獲取 GitLab 遠端名稱
get_gitlab_remote() {
    echo "$DETECTED_GITLAB_REMOTE"
}

# 獲取 GitHub 遠端名稱
get_github_remote() {
    echo "$DETECTED_GITHUB_REMOTE"
}

# 檢查遠端是否存在
remote_exists() {
    local remote_name="$1"
    git remote | grep -q "^$remote_name$"
}

# 獲取遠端 URL
get_remote_url() {
    local remote_name="$1"
    git remote get-url "$remote_name" 2>/dev/null
}

# 列出所有遠端
list_all_remotes() {
    echo -e "${BLUE}所有已配置的遠端：${NC}"
    git remote -v | while read line; do
        echo -e "${YELLOW}  $line${NC}"
    done
}

# 移除遠端
remove_remote() {
    local remote_name="$1"

    if remote_exists "$remote_name"; then
        echo -e "${YELLOW}確定要移除遠端 '$remote_name' 嗎？(y/n)${NC}"
        read confirm

        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            git remote remove "$remote_name"
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ 成功移除遠端 '$remote_name'${NC}"
            else
                echo -e "${RED}✗ 移除遠端 '$remote_name' 失敗${NC}"
            fi
        fi
    else
        echo -e "${RED}遠端 '$remote_name' 不存在${NC}"
    fi
}

# 重新命名遠端
rename_remote() {
    local old_name="$1"
    local new_name="$2"

    if remote_exists "$old_name"; then
        git remote rename "$old_name" "$new_name"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 成功將遠端 '$old_name' 重新命名為 '$new_name'${NC}"
        else
            echo -e "${RED}✗ 重新命名遠端失敗${NC}"
        fi
    else
        echo -e "${RED}遠端 '$old_name' 不存在${NC}"
    fi
}

# 測試遠端連線
test_remote_connection() {
    local remote_name="$1"

    if remote_exists "$remote_name"; then
        echo -e "${YELLOW}測試遠端 '$remote_name' 的連線...${NC}"
        git ls-remote --heads "$remote_name" >/dev/null 2>&1

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 遠端 '$remote_name' 連線正常${NC}"
            return 0
        else
            echo -e "${RED}✗ 遠端 '$remote_name' 連線失敗${NC}"
            return 1
        fi
    else
        echo -e "${RED}遠端 '$remote_name' 不存在${NC}"
        return 1
    fi
}

# 批量測試所有遠端連線
test_all_remotes() {
    echo -e "${BLUE}測試所有遠端連線...${NC}"

    local remotes=$(git remote)
    local success_count=0
    local total_count=0

    for remote in $remotes; do
        ((total_count++))
        if test_remote_connection "$remote"; then
            ((success_count++))
        fi
    done

    echo ""
    echo -e "${BLUE}連線測試結果：${NC}"
    echo -e "  總遠端數：$total_count"
    echo -e "  連線成功：$success_count"

    if [ $success_count -eq $total_count ]; then
        echo -e "  ${GREEN}所有遠端連線正常${NC}"
    else
        echo -e "  ${RED}有遠端連線失敗${NC}"
    fi
}

# 修復 GitLab URL 重定向問題
fix_gitlab_redirect() {
    local gitlab_remote=$(get_gitlab_remote)

    if [ -z "$gitlab_remote" ]; then
        echo -e "${RED}未找到 GitLab 遠端${NC}"
        return 1
    fi

    local current_url=$(git remote get-url "$gitlab_remote")
    local normalized_url=$(normalize_git_url "$current_url")

    if [ "$current_url" != "$normalized_url" ]; then
        echo -e "${YELLOW}修正 GitLab URL 以避免重定向警告...${NC}"
        git remote set-url "$gitlab_remote" "$normalized_url"

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ GitLab URL 已修正${NC}"

            # 如果有 'all' 遠端，也要更新
            if git remote | grep -q "^all$"; then
                local github_remote=$(get_github_remote)
                if [ ! -z "$github_remote" ]; then
                    recreate_all_remote "$normalized_url" "$(git remote get-url $github_remote)"
                fi
            fi
        else
            echo -e "${RED}✗ 修正失敗${NC}"
        fi
    else
        echo -e "${GREEN}GitLab URL 格式正確${NC}"
    fi
}
