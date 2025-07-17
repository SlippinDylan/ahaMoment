# ChromeDriver Auto Update Tool

A tool to automatically keep ChromeDriver synchronized with Google Chrome versions on Debian/Ubuntu systems.

## 🎯 Problem Solved

When using Google Chrome and ChromeDriver on Debian/Ubuntu systems, you often encounter:

- **Chrome auto-updates**: Chrome installed via APT package manager updates automatically during system updates
- **ChromeDriver manual updates**: Manually downloaded ChromeDriver requires manual updates
- **Version mismatch**: Causes Selenium test failures and compatibility issues

## ✨ Features

- 🔄 **Automatic synchronization**: Automatically checks and updates ChromeDriver during system updates
- 📝 **Detailed logging**: Records all update operations for easy troubleshooting
- 🛡️ **Safe and reliable**: Update failures won't affect normal APT operations
- 🚀 **Zero maintenance**: Set once, works forever

## 🔧 Installation

### 1. Create the auto-update script

```bash
sudo nano /usr/local/bin/update-chromedriver.sh
```

Copy the following content into the file:

```bash
#!/bin/bash

# ChromeDriver auto-update script
log_file="/var/log/chromedriver-update.log"

echo "$(date): Starting ChromeDriver update check..." >> $log_file

# Check if Chrome is installed
if ! command -v google-chrome &> /dev/null; then
    echo "$(date): Chrome not installed, skipping ChromeDriver update" >> $log_file
    exit 0
fi

# Get current Chrome version
CHROME_VERSION=$(google-chrome --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+\.\d+')
if [ -z "$CHROME_VERSION" ]; then
    echo "$(date): Unable to get Chrome version" >> $log_file
    exit 1
fi

# Get current ChromeDriver version (if exists)
CURRENT_DRIVER_VERSION=""
if command -v chromedriver &> /dev/null; then
    CURRENT_DRIVER_VERSION=$(chromedriver --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+\.\d+')
fi

echo "$(date): Chrome version: $CHROME_VERSION" >> $log_file
echo "$(date): ChromeDriver version: $CURRENT_DRIVER_VERSION" >> $log_file

# Check if update is needed
if [ "$CHROME_VERSION" != "$CURRENT_DRIVER_VERSION" ]; then
    echo "$(date): Need to update ChromeDriver to version $CHROME_VERSION" >> $log_file
    
    # Create temporary directory
    temp_dir=$(mktemp -d)
    cd $temp_dir
    
    # Download new version
    download_url="https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip"
    
    if wget -q "$download_url" -O chromedriver.zip; then
        if unzip -q chromedriver.zip; then
            # Install new version
            mv chromedriver-linux64/chromedriver /usr/local/bin/
            chmod +x /usr/local/bin/chromedriver
            echo "$(date): ChromeDriver updated successfully to version $CHROME_VERSION" >> $log_file
        else
            echo "$(date): Extraction failed" >> $log_file
        fi
    else
        echo "$(date): Download failed: $download_url" >> $log_file
    fi
    
    # Clean up temporary files
    rm -rf $temp_dir
else
    echo "$(date): ChromeDriver is already up to date" >> $log_file
fi

echo "$(date): ChromeDriver check completed" >> $log_file
```

### 2. Add execution permissions

```bash
sudo chmod +x /usr/local/bin/update-chromedriver.sh
```

### 3. Create APT hook

```bash
sudo nano /etc/apt/apt.conf.d/99chromedriver-update
```

Add the following content:

```
DPkg::Post-Invoke {"/usr/local/bin/update-chromedriver.sh || true";};
```

### 4. Test installation

```bash
# Manually run the script to test
sudo /usr/local/bin/update-chromedriver.sh

# Check logs
sudo tail -f /var/log/chromedriver-update.log

# Test APT hook
sudo apt update
```

## 📋 Usage

After installation, the script will automatically run during:

- `sudo apt update`
- `sudo apt upgrade`
- `sudo apt install [package]`
- Any operations involving dpkg

## 📊 Verify Version Synchronization

```bash
# Check if versions match
CHROME_VER=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+')
DRIVER_VER=$(chromedriver --version | grep -oP '\d+\.\d+\.\d+\.\d+')

echo "Chrome: $CHROME_VER"
echo "ChromeDriver: $DRIVER_VER"

if [ "$CHROME_VER" = "$DRIVER_VER" ]; then
    echo "✅ Versions match!"
else
    echo "❌ Versions don't match"
fi
```

## 📁 File Locations

- **Script file**: `/usr/local/bin/update-chromedriver.sh`
- **APT hook**: `/etc/apt/apt.conf.d/99chromedriver-update`
- **Log file**: `/var/log/chromedriver-update.log`
- **ChromeDriver installation**: `/usr/local/bin/chromedriver`

## 🔍 Troubleshooting

### Check logs
```bash
sudo tail -20 /var/log/chromedriver-update.log
```

### Manually run script
```bash
sudo /usr/local/bin/update-chromedriver.sh
```

### Check APT hook configuration
```bash
apt-config dump | grep -i invoke
```

### Common Issues

1. **Download failure**
   - Check network connection
   - Verify Chrome version number is correct

2. **Permission issues**
   - Ensure script has execution permissions: `sudo chmod +x /usr/local/bin/update-chromedriver.sh`

3. **Version mismatch**
   - Manually run script to sync
   - Check log file for error messages

## 🗑️ Uninstall

```bash
# Remove script
sudo rm /usr/local/bin/update-chromedriver.sh

# Remove APT hook
sudo rm /etc/apt/apt.conf.d/99chromedriver-update

# Remove log file (optional)
sudo rm /var/log/chromedriver-update.log
```

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

MIT License

## 🌟 Support

If this tool helps you, please give it a Star ⭐


# ChromeDriver 自动更新工具

一个用于在 Debian/Ubuntu 系统上自动保持 ChromeDriver 与 Google Chrome 版本同步的工具。

## 🎯 解决的问题

当你在 Debian/Ubuntu 系统上使用 Google Chrome 和 ChromeDriver 时，经常会遇到以下问题：

- **Chrome 自动更新**：通过 APT 包管理器安装的 Chrome 会在系统更新时自动升级
- **ChromeDriver 手动更新**：手动下载的 ChromeDriver 不会自动更新
- **版本不匹配**：导致 Selenium 测试失败，出现兼容性问题

## ✨ 功能特性

- 🔄 **自动同步**：每次系统更新时自动检查并更新 ChromeDriver
- 📝 **详细日志**：记录所有更新操作，方便问题排查
- 🛡️ **安全可靠**：更新失败不会影响系统的正常 APT 操作
- 🚀 **零维护**：一次设置，永久生效

## 🔧 安装步骤

### 1. 创建自动更新脚本

```bash
sudo nano /usr/local/bin/update-chromedriver.sh
```

复制以下内容到文件中：

```bash
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
```

### 2. 添加执行权限

```bash
sudo chmod +x /usr/local/bin/update-chromedriver.sh
```

### 3. 创建 APT 钩子

```bash
sudo nano /etc/apt/apt.conf.d/99chromedriver-update
```

添加以下内容：

```
DPkg::Post-Invoke {"/usr/local/bin/update-chromedriver.sh || true";};
```

### 4. 测试安装

```bash
# 手动运行脚本测试
sudo /usr/local/bin/update-chromedriver.sh

# 查看日志
sudo tail -f /var/log/chromedriver-update.log

# 测试 APT 钩子
sudo apt update
```

## 📋 使用方法

安装完成后，脚本会在以下情况自动运行：

- `sudo apt update`
- `sudo apt upgrade`
- `sudo apt install [package]`
- 任何涉及 dpkg 的操作

## 📊 验证版本同步

```bash
# 检查版本是否匹配
CHROME_VER=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+')
DRIVER_VER=$(chromedriver --version | grep -oP '\d+\.\d+\.\d+\.\d+')

echo "Chrome: $CHROME_VER"
echo "ChromeDriver: $DRIVER_VER"

if [ "$CHROME_VER" = "$DRIVER_VER" ]; then
    echo "✅ 版本匹配！"
else
    echo "❌ 版本不匹配"
fi
```

## 📁 文件位置

- **脚本文件**：`/usr/local/bin/update-chromedriver.sh`
- **APT 钩子**：`/etc/apt/apt.conf.d/99chromedriver-update`
- **日志文件**：`/var/log/chromedriver-update.log`
- **ChromeDriver 安装位置**：`/usr/local/bin/chromedriver`

## 🔍 故障排除

### 查看日志
```bash
sudo tail -20 /var/log/chromedriver-update.log
```

### 手动运行脚本
```bash
sudo /usr/local/bin/update-chromedriver.sh
```

### 检查 APT 钩子配置
```bash
apt-config dump | grep -i invoke
```

### 常见问题

1. **下载失败**
   - 检查网络连接
   - 确认 Chrome 版本号是否正确

2. **权限问题**
   - 确保脚本有执行权限：`sudo chmod +x /usr/local/bin/update-chromedriver.sh`

3. **版本不匹配**
   - 手动运行脚本进行同步
   - 检查日志文件中的错误信息

## 🗑️ 卸载

```bash
# 删除脚本
sudo rm /usr/local/bin/update-chromedriver.sh

# 删除 APT 钩子
sudo rm /etc/apt/apt.conf.d/99chromedriver-update

# 删除日志文件（可选）
sudo rm /var/log/chromedriver-update.log
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🌟 支持

如果这个工具对你有帮助，请给个 Star ⭐
