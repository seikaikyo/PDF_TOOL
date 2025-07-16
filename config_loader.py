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
