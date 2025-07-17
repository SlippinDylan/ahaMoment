#!/bin/bash

# ChromeDriver 自动更新脚本
log_file="/var/log/chromedriver-update.log"

echo "$(date): 开始检查 ChromeDriver 更新..." >> $log_file

# 检查 Chrome 是否安装
if ! command -v google-chrome &> /dev/null; then
    echo "$(date): Chrome 未安装，跳过 ChromeDriver 更新" >> $log_file
    exit 0
fi

# 获取当前 Chrome 版本
CHROME_VERSION=$(google-chrome --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+\.\d+')
if [ -z "$CHROME_VERSION" ]; then
    echo "$(date): 无法获取 Chrome 版本" >> $log_file
    exit 1
fi

# 获取当前 ChromeDriver 版本（如果存在）
CURRENT_DRIVER_VERSION=""
if command -v chromedriver &> /dev/null; then
    CURRENT_DRIVER_VERSION=$(chromedriver --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+\.\d+')
fi

echo "$(date): Chrome 版本: $CHROME_VERSION" >> $log_file
echo "$(date): ChromeDriver 版本: $CURRENT_DRIVER_VERSION" >> $log_file

# 检查是否需要更新
if [ "$CHROME_VERSION" != "$CURRENT_DRIVER_VERSION" ]; then
    echo "$(date): 需要更新 ChromeDriver 到版本 $CHROME_VERSION" >> $log_file
    
    # 创建临时目录
    temp_dir=$(mktemp -d)
    cd $temp_dir
    
    # 下载新版本
    download_url="https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip"
    
    if wget -q "$download_url" -O chromedriver.zip; then
        if unzip -q chromedriver.zip; then
            # 安装新版本
            mv chromedriver-linux64/chromedriver /usr/local/bin/
            chmod +x /usr/local/bin/chromedriver
            echo "$(date): ChromeDriver 更新成功到版本 $CHROME_VERSION" >> $log_file
        else
            echo "$(date): 解压失败" >> $log_file
        fi
    else
        echo "$(date): 下载失败: $download_url" >> $log_file
    fi
    
    # 清理临时文件
    rm -rf $temp_dir
else
    echo "$(date): ChromeDriver 已是最新版本" >> $log_file
fi

echo "$(date): ChromeDriver 检查完成" >> $log_file