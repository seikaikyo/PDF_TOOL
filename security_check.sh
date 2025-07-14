#!/bin/bash

# 安全檢查模組
# 負責檢測機密資訊並提供相應的處理措施
# 版本：2.1

# 全域變數
declare -A FOUND_SECURITY_ISSUES
declare -A SECURITY_PATTERNS
SECURITY_CHECK_PASSED=true

# 初始化安全檢查模式
init_security_patterns() {
    # 定義機密資訊的正則表達式模式（使用英文鍵值避免語法錯誤）

    # 基本認證資訊
    SECURITY_PATTERNS["password"]="(password|passwd|pwd)\s*[=:]\s*[\"']?[^\s\"']{3,}[\"']?"
    SECURITY_PATTERNS["api_key"]="(api[_-]?key|apikey|access[_-]?key|secret[_-]?key)\s*[=:]\s*[\"']?[a-zA-Z0-9_-]{10,}[\"']?"
    SECURITY_PATTERNS["jwt_token"]="(jwt|token|bearer)\s*[=:]\s*[\"']?[a-zA-Z0-9_.-]{20,}[\"']?"
    SECURITY_PATTERNS["database_url"]="(database[_-]?url|db[_-]?url|connection[_-]?string)\s*[=:]\s*[\"']?[^\s\"']{10,}[\"']?"

    # 個人資訊
    SECURITY_PATTERNS["email"]="[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    SECURITY_PATTERNS["phone"]="(\+?886|0)[0-9]{8,9}"
    SECURITY_PATTERNS["credit_card"]="[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}"

    # 金鑰與憑證
    SECURITY_PATTERNS["private_key"]="-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----"
    SECURITY_PATTERNS["ssh_key"]="ssh-(rsa|dss|ed25519) [A-Za-z0-9+/]+"

    # 平台特定權杖
    SECURITY_PATTERNS["aws_key"]="AKIA[0-9A-Z]{16}"
    SECURITY_PATTERNS["aws_secret"]="[A-Za-z0-9/+=]{40}"
    SECURITY_PATTERNS["github_token"]="ghp_[a-zA-Z0-9]{36}"
    SECURITY_PATTERNS["github_classic"]="gh[pousr]_[A-Za-z0-9_]{36,255}"
    SECURITY_PATTERNS["slack_token"]="xox[bpsr]-[a-zA-Z0-9-]+"
    SECURITY_PATTERNS["google_api"]="AIza[0-9A-Za-z_-]{35}"
    SECURITY_PATTERNS["facebook_token"]="EAA[0-9A-Za-z]+"
    SECURITY_PATTERNS["twitter_token"]="[1-9][0-9]+-[0-9a-zA-Z]{40}"
    SECURITY_PATTERNS["twitter_secret"]="[A-Za-z0-9]{45,50}"
    SECURITY_PATTERNS["docker_token"]="dckr_pat_[a-zA-Z0-9_-]+"
    SECURITY_PATTERNS["stripe_key"]="sk_live_[a-zA-Z0-9]{24,99}"
    SECURITY_PATTERNS["paypal_key"]="access_token\$production\$[a-z0-9]{16}\$[a-z0-9]{32}"
}

# 獲取模式的顯示名稱（中文）
get_pattern_display_name() {
    local pattern_key="$1"

    case "$pattern_key" in
    "password") echo "密碼" ;;
    "api_key") echo "API金鑰" ;;
    "jwt_token") echo "JWT權杖" ;;
    "database_url") echo "資料庫連線" ;;
    "email") echo "電子郵件" ;;
    "phone") echo "手機號碼" ;;
    "credit_card") echo "信用卡號" ;;
    "private_key") echo "私鑰" ;;
    "ssh_key") echo "SSH金鑰" ;;
    "aws_key") echo "AWS存取金鑰" ;;
    "aws_secret") echo "AWS秘密金鑰" ;;
    "github_token") echo "GitHub權杖" ;;
    "github_classic") echo "GitHub經典權杖" ;;
    "slack_token") echo "Slack權杖" ;;
    "google_api") echo "Google API金鑰" ;;
    "facebook_token") echo "Facebook權杖" ;;
    "twitter_token") echo "Twitter權杖" ;;
    "twitter_secret") echo "Twitter秘密" ;;
    "docker_token") echo "Docker權杖" ;;
    "stripe_key") echo "Stripe金鑰" ;;
    "paypal_key") echo "PayPal金鑰" ;;
    *) echo "$pattern_key" ;;
    esac
}

# 執行安全檢查的主函數
perform_security_check() {
    echo -e "${BLUE}正在檢查機密資訊...${NC}"

    # 初始化檢查模式
    init_security_patterns

    # 重置全域變數
    unset FOUND_SECURITY_ISSUES
    declare -A FOUND_SECURITY_ISSUES
    SECURITY_CHECK_PASSED=true

    # 獲取要檢查的檔案
    local files_to_check=$(get_files_to_check)

    if [ -z "$files_to_check" ]; then
        echo -e "${YELLOW}沒有檔案需要檢查${NC}"
        return 0
    fi

    # 執行檢查
    scan_files_for_secrets "$files_to_check"

    # 回報結果
    if [ "$SECURITY_CHECK_PASSED" = true ]; then
        echo -e "${GREEN}✓ 未發現機密資訊${NC}"
        return 0
    else
        display_security_issues
        return 1
    fi
}

# 獲取需要檢查的檔案清單
get_files_to_check() {
    local staged_files=$(git diff --cached --name-only 2>/dev/null)
    local modified_files=$(git diff --name-only 2>/dev/null)
    local all_files="$staged_files $modified_files"

    # 如果沒有檔案變更，檢查所有追蹤的檔案的前 10 個
    if [ -z "$all_files" ]; then
        all_files=$(git ls-files | head -10)
    fi

    # 過濾掉不需要檢查的檔案
    local filtered_files=""
    for file in $all_files; do
        if should_check_file "$file"; then
            filtered_files="$filtered_files $file"
        fi
    done

    echo "$filtered_files"
}

# 判斷是否應該檢查該檔案
should_check_file() {
    local file="$1"

    # 檢查檔案是否存在
    if [ ! -f "$file" ]; then
        return 1
    fi

    # 排除常見的二進位檔案和不需要檢查的檔案
    local excluded_patterns="\.(jpg|jpeg|png|gif|bmp|ico|svg|pdf|doc|docx|xls|xlsx|ppt|pptx|zip|tar|gz|7z|rar|exe|dll|so|dylib|bin|class|jar|war|ear|woff|woff2|ttf|eot)$"

    if echo "$file" | grep -E "$excluded_patterns" >/dev/null; then
        return 1
    fi

    # 排除特定目錄
    if echo "$file" | grep -E "^(node_modules|\.git|build|dist|\.vscode|\.idea)/" >/dev/null; then
        return 1
    fi

    return 0
}

# 掃描檔案中的機密資訊
scan_files_for_secrets() {
    local files="$1"

    for file in $files; do
        echo -e "${YELLOW}檢查檔案：$file${NC}"

        # 檢查每個模式
        for pattern_name in "${!SECURITY_PATTERNS[@]}"; do
            local pattern="${SECURITY_PATTERNS[$pattern_name]}"
            local matches=$(grep -iEn "$pattern" "$file" 2>/dev/null)

            if [ ! -z "$matches" ]; then
                SECURITY_CHECK_PASSED=false

                # 獲取顯示名稱
                local display_name=$(get_pattern_display_name "$pattern_name")

                # 記錄發現的問題（正確處理關聯陣列鍵值）
                if [ -z "${FOUND_SECURITY_ISSUES["$file"]:-}" ]; then
                    FOUND_SECURITY_ISSUES["$file"]="$display_name"
                else
                    FOUND_SECURITY_ISSUES["$file"]="${FOUND_SECURITY_ISSUES["$file"]}, $display_name"
                fi

                echo -e "${RED}  ✗ 發現 $display_name${NC}"
            fi
        done

        if [ -z "${FOUND_SECURITY_ISSUES["$file"]:-}" ]; then
            echo -e "${GREEN}  ✓ 安全${NC}"
        fi
    done
}

# 顯示安全問題
display_security_issues() {
    echo -e "${RED}警告：發現可能的機密資訊！${NC}"
    echo ""

    for file in "${!FOUND_SECURITY_ISSUES[@]}"; do
        echo -e "${YELLOW}檔案：${NC}$file"
        echo -e "${RED}發現的敏感資訊類型：${NC}${FOUND_SECURITY_ISSUES["$file"]}"
        echo ""
    done
}

# 處理安全問題的主函數
handle_security_issues() {
    echo -e "${YELLOW}請選擇處理方式：${NC}"
    echo "1) 查看詳細內容並手動處理"
    echo "2) 將包含機密資訊的檔案加入 .gitignore"
    echo "3) 創建環境變數範本檔案"
    echo "4) 掃描整個專案（進階檢查）"
    echo "5) 繼續推送（不建議）"
    echo "6) 取消推送"

    read -p "請輸入選項 (1-6): " choice

    case $choice in
    1)
        show_detailed_security_issues
        return 1
        ;;
    2)
        add_to_gitignore
        return 1
        ;;
    3)
        create_env_template
        return 1
        ;;
    4)
        scan_entire_project
        return 1
        ;;
    5)
        confirm_risky_push
        return $?
        ;;
    6)
        echo -e "${YELLOW}推送已取消。${NC}"
        return 1
        ;;
    *)
        echo -e "${RED}無效的選項，推送已取消。${NC}"
        return 1
        ;;
    esac
}

# 顯示詳細的安全問題
show_detailed_security_issues() {
    echo -e "${BLUE}顯示包含機密資訊的詳細內容：${NC}"
    echo ""

    for file in "${!FOUND_SECURITY_ISSUES[@]}"; do
        echo -e "${YELLOW}檔案：${NC}$file"
        echo -e "${PURPLE}===========================================${NC}"

        for pattern_name in "${!SECURITY_PATTERNS[@]}"; do
            local pattern="${SECURITY_PATTERNS[$pattern_name]}"
            local matches=$(grep -iEn --color=always "$pattern" "$file" 2>/dev/null)

            if [ ! -z "$matches" ]; then
                local display_name=$(get_pattern_display_name "$pattern_name")
                echo -e "${RED}$display_name 模式匹配：${NC}"
                echo "$matches"
                echo ""
            fi
        done

        echo -e "${PURPLE}===========================================${NC}"
        echo ""
    done

    echo -e "${YELLOW}請手動處理後重新執行腳本。${NC}"
}

# 將檔案加入 .gitignore
add_to_gitignore() {
    echo -e "${BLUE}將檔案加入 .gitignore...${NC}"

    local added_files=0
    for file in "${!FOUND_SECURITY_ISSUES[@]}"; do
        if ! grep -Fxq "$file" .gitignore 2>/dev/null; then
            echo "$file" >>.gitignore
            echo -e "${GREEN}已將 $file 加入 .gitignore${NC}"
            ((added_files++))
        else
            echo -e "${YELLOW}$file 已在 .gitignore 中${NC}"
        fi
    done

    if [ $added_files -gt 0 ]; then
        # 移除已加入 .gitignore 的檔案
        for file in "${!FOUND_SECURITY_ISSUES[@]}"; do
            git rm --cached "$file" 2>/dev/null && echo -e "${YELLOW}已從暫存區移除 $file${NC}"
        done

        echo -e "${GREEN}處理完成，請提交 .gitignore 的變更。${NC}"
        echo -e "${YELLOW}建議執行：git add .gitignore && git commit -m \"更新 .gitignore\"${NC}"
    fi
}

# 創建環境變數範本檔案
create_env_template() {
    echo -e "${BLUE}創建環境變數範本檔案...${NC}"

    local env_example_file=".env.example"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # 檢查是否已存在範本檔案
    if [ -f "$env_example_file" ]; then
        echo -e "${YELLOW}$env_example_file 已存在，將追加新內容${NC}"
        echo "" >>"$env_example_file"
        echo "# 新增於 $timestamp" >>"$env_example_file"
    else
        echo -e "${GREEN}創建新的 $env_example_file 檔案${NC}"
        cat >"$env_example_file" <<EOF
# 環境變數範本檔案
# 複製此檔案為 .env 並填入實際值
# 注意：.env 檔案不應加入版本控制
# 創建於 $timestamp

EOF
    fi

    # 分析發現的機密資訊類型並生成對應的環境變數
    for file in "${!FOUND_SECURITY_ISSUES[@]}"; do
        echo "# 來自檔案：$file" >>"$env_example_file"

        # 掃描檔案中的具體機密資訊並生成範本
        local added_vars=()
        for pattern_name in "${!SECURITY_PATTERNS[@]}"; do
            local pattern="${SECURITY_PATTERNS[$pattern_name]}"
            local matches=$(grep -iE "$pattern" "$file" 2>/dev/null)

            if [ ! -z "$matches" ]; then
                case "$pattern_name" in
                "password")
                    if [[ ! " ${added_vars[@]} " =~ " PASSWORD " ]]; then
                        echo "PASSWORD=your_password_here" >>"$env_example_file"
                        added_vars+=("PASSWORD")
                    fi
                    ;;
                "api_key")
                    if [[ ! " ${added_vars[@]} " =~ " API_KEY " ]]; then
                        echo "API_KEY=your_api_key_here" >>"$env_example_file"
                        echo "SECRET_KEY=your_secret_key_here" >>"$env_example_file"
                        added_vars+=("API_KEY" "SECRET_KEY")
                    fi
                    ;;
                "jwt_token")
                    if [[ ! " ${added_vars[@]} " =~ " JWT_SECRET " ]]; then
                        echo "JWT_SECRET=your_jwt_secret_here" >>"$env_example_file"
                        added_vars+=("JWT_SECRET")
                    fi
                    ;;
                "database_url")
                    if [[ ! " ${added_vars[@]} " =~ " DATABASE_URL " ]]; then
                        echo "DATABASE_URL=your_database_url_here" >>"$env_example_file"
                        added_vars+=("DATABASE_URL")
                    fi
                    ;;
                "google_api")
                    if [[ ! " ${added_vars[@]} " =~ " GOOGLE_API_KEY " ]]; then
                        echo "GOOGLE_API_KEY=your_google_api_key_here" >>"$env_example_file"
                        added_vars+=("GOOGLE_API_KEY")
                    fi
                    ;;
                "aws_key" | "aws_secret")
                    if [[ ! " ${added_vars[@]} " =~ " AWS_ACCESS_KEY_ID " ]]; then
                        echo "AWS_ACCESS_KEY_ID=your_aws_access_key_here" >>"$env_example_file"
                        echo "AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here" >>"$env_example_file"
                        added_vars+=("AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY")
                    fi
                    ;;
                "stripe_key")
                    if [[ ! " ${added_vars[@]} " =~ " STRIPE_SECRET_KEY " ]]; then
                        echo "STRIPE_SECRET_KEY=your_stripe_secret_key_here" >>"$env_example_file"
                        echo "STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key_here" >>"$env_example_file"
                        added_vars+=("STRIPE_SECRET_KEY" "STRIPE_PUBLISHABLE_KEY")
                    fi
                    ;;
                esac
            fi
        done

        echo "" >>"$env_example_file"
    done

    # 確保 .env 和相關檔案在 .gitignore 中
    update_gitignore_for_env

    echo -e "${GREEN}✓ 環境變數範本檔案已創建：$env_example_file${NC}"
    display_env_usage_instructions
}

# 更新 .gitignore 以處理環境變數檔案
update_gitignore_for_env() {
    local env_patterns=(".env" ".env.local" ".env.production" ".env.staging" ".env.development")

    for pattern in "${env_patterns[@]}"; do
        if ! grep -q "^$pattern$" .gitignore 2>/dev/null; then
            echo "$pattern" >>.gitignore
            echo -e "${GREEN}已將 $pattern 加入 .gitignore${NC}"
        fi
    done

    # 確保 .env.example 可以被版本控制
    if ! grep -q "^!\.env\.example$" .gitignore 2>/dev/null; then
        echo "!.env.example" >>.gitignore
        echo -e "${GREEN}已將 !.env.example 加入 .gitignore（允許版本控制）${NC}"
    fi
}

# 顯示環境變數使用說明
display_env_usage_instructions() {
    echo -e "${YELLOW}請執行以下步驟：${NC}"
    echo -e "  1. 複製範本：${CYAN}cp .env.example .env${NC}"
    echo -e "  2. 編輯 .env 填入實際值：${CYAN}nano .env${NC}"
    echo -e "  3. 修改程式碼使用環境變數："
    echo -e "     ${CYAN}# Node.js${NC}"
    echo -e "     ${CYAN}const apiKey = process.env.API_KEY;${NC}"
    echo -e "     ${CYAN}# Python${NC}"
    echo -e "     ${CYAN}import os${NC}"
    echo -e "     ${CYAN}api_key = os.getenv('API_KEY')${NC}"
    echo -e "  4. 提交變更：${CYAN}git add .gitignore .env.example${NC}"
}

# 確認風險推送
confirm_risky_push() {
    echo -e "${RED}⚠️  警告：您選擇繼續推送，這可能會洩露機密資訊！${NC}"
    echo -e "${RED}強烈建議您先處理安全問題後再推送。${NC}"
    echo ""
    echo -e "${YELLOW}風險包括：${NC}"
    echo "  • 機密資訊可能被公開存取"
    echo "  • 違反資料保護法規"
    echo "  • 安全漏洞風險"
    echo "  • 可能的財務損失"
    echo ""
    read -p "您確定要繼續嗎？請輸入 'yes' 確認，或任何其他鍵取消: " confirm

    if [ "$confirm" = "yes" ]; then
        echo -e "${YELLOW}已確認繼續推送，請自行承擔風險。${NC}"
        return 0
    else
        echo -e "${GREEN}明智的選擇！請先處理安全問題。${NC}"
        return 1
    fi
}

# 掃描整個專案（進階功能）
scan_entire_project() {
    echo -e "${BLUE}正在掃描整個專案...${NC}"

    init_security_patterns

    local project_files=$(git ls-files)
    local total_files=0
    local scanned_files=0
    local security_issues=0
    local issue_files=()

    for file in $project_files; do
        ((total_files++))

        if should_check_file "$file"; then
            ((scanned_files++))

            local file_has_issues=false
            for pattern_name in "${!SECURITY_PATTERNS[@]}"; do
                local pattern="${SECURITY_PATTERNS[$pattern_name]}"
                if grep -qiE "$pattern" "$file" 2>/dev/null; then
                    if [ "$file_has_issues" = false ]; then
                        ((security_issues++))
                        issue_files+=("$file")
                        file_has_issues=true
                    fi
                    local display_name=$(get_pattern_display_name "$pattern_name")
                    echo -e "${RED}發現 $display_name 於：$file${NC}"
                fi
            done
        fi
    done

    echo ""
    echo -e "${BLUE}掃描結果統計：${NC}"
    echo -e "  總檔案數：$total_files"
    echo -e "  已掃描：$scanned_files"
    echo -e "  有問題的檔案：$security_issues"

    if [ $security_issues -eq 0 ]; then
        echo -e "${GREEN}✓ 整個專案未發現安全問題${NC}"
    else
        echo -e "${RED}⚠ 發現 $security_issues 個檔案包含安全問題${NC}"
        echo ""
        echo -e "${YELLOW}建議處理這些檔案：${NC}"
        for issue_file in "${issue_files[@]}"; do
            echo -e "  • $issue_file"
        done
    fi
}

# 檢查特定檔案
check_file_security() {
    local file="$1"

    if [ ! -f "$file" ]; then
        echo -e "${RED}檔案不存在：$file${NC}"
        return 1
    fi

    echo -e "${BLUE}檢查檔案：$file${NC}"

    init_security_patterns

    local found_issues=false
    for pattern_name in "${!SECURITY_PATTERNS[@]}"; do
        local pattern="${SECURITY_PATTERNS[$pattern_name]}"
        local matches=$(grep -iEn "$pattern" "$file" 2>/dev/null)

        if [ ! -z "$matches" ]; then
            found_issues=true
            local display_name=$(get_pattern_display_name "$pattern_name")
            echo -e "${RED}發現 $display_name：${NC}"
            echo "$matches"
            echo ""
        fi
    done

    if [ "$found_issues" = false ]; then
        echo -e "${GREEN}✓ 檔案安全${NC}"
    fi
}

# 生成安全檢查報告
generate_security_report() {
    local output_file="security_report_$(date +%Y%m%d_%H%M%S).txt"

    echo "Git 同步工具 - 安全檢查報告" >"$output_file"
    echo "生成時間: $(date)" >>"$output_file"
    echo "======================================" >>"$output_file"
    echo "" >>"$output_file"

    scan_entire_project >>"$output_file" 2>&1

    echo -e "${GREEN}✓ 安全檢查報告已生成：$output_file${NC}"
}
