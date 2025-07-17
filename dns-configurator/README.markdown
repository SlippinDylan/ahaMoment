# DNS Configurator / DNS 配置器

A macOS Python script to automatically configure DNS settings based on the connected network.  
这是一个用于 macOS 的 Python 脚本，根据连接的网络自动配置 DNS 设置。

## Background / 背景
**English**: This script was developed to address issues with automatic DNS configuration in specific network environments (e.g., enterprise or institutional WiFi). In some networks, the Mac fails to acquire the correct internal DNS server, leading to connectivity issues. This script detects such networks and sets the appropriate DNS server automatically.  
**中文**: 该脚本旨在解决特定网络环境（如企业或机构 WiFi）下自动 DNS 配置的问题。在某些网络中，Mac 无法获取正确的内部 DNS 服务器，导致连接问题。该脚本检测此类网络并自动设置合适的 DNS 服务器。

## Functionality / 功能
- **Detects Specific Network / 检测特定网络**: Checks if the ARP table contains specified IP addresses (`SPECIFIC_NETWORK_IPS`) associated with the target network.  
  检查 ARP 表是否包含与目标网络关联的指定 IP 地址（`SPECIFIC_NETWORK_IPS`）。
- **DNS Configuration / DNS 配置**:
  - If connected to the specific network, sets the DNS server to a predefined address (`SPECIFIC_DNS`).  
    如果连接到特定网络，将 DNS 服务器设置为预定义地址（`SPECIFIC_DNS`）。
  - If connected to another network, clears the DNS configuration.  
    如果连接到其他网络，清除 DNS 配置。
- **DNS Flush / DNS 刷新**: Refreshes the DNS cache after configuration changes.  
  在配置更改后刷新 DNS 缓存。
- **Debug Mode / 调试模式**: Provides network information for troubleshooting.  
  提供网络信息以便排错。

## Prerequisites / 前置条件
- **Python 3**: Ensure Python 3 is installed (`python3 --version`).  
  确保已安装 Python 3（运行 `python3 --version` 检查）。
- **macOS Tools / macOS 工具**: Uses built-in tools (`arp`, `networksetup`, `dscacheutil`, `mDNSResponder`).  
  使用内置工具（`arp`、`networksetup`、`dscacheutil`、`mDNSResponder`）。

## Installation / 安装
1. **Place Files / 放置文件**:
   - Save `dns_monitor.py` and `com.user.dnsmonitor.plist` to `~/Library/LaunchAgents/`.  
     将 `dns_monitor.py` 和 `com.user.dnsmonitor.plist` 保存到 `~/Library/LaunchAgents/`。
   ```bash
   mkdir -p ~/Library/LaunchAgents
   cp dns_monitor.py ~/Library/LaunchAgents/
   cp com.user.dnsmonitor.plist ~/Library/LaunchAgents/
   ```

2. **Set Permissions / 设置权限**:
   ```bash
   chmod +x ~/Library/LaunchAgents/dns_monitor.py
   ```

3. **Configure Parameters / 配置参数**:
   - Edit `dns_monitor.py` to set:  
     编辑 `dns_monitor.py`，设置：
     - `SPECIFIC_NETWORK_IPS`: List of IP addresses identifying the specific network (e.g., `["192.168.10.1", "192.168.10.2"]`).  
       标识特定网络的 IP 地址列表（例如 `["192.168.10.1", "192.168.10.2"]`）。
     - `SPECIFIC_DNS`: The DNS server for the specific network (e.g., `192.168.10.253`).  
       特定网络的 DNS 服务器（例如 `192.168.10.253`）。

4. **Load LaunchAgent / 加载 LaunchAgent**:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.user.dnsmonitor.plist
   ```

5. **View Logs / 查看日志**:
   ```bash
   tail -f ~/Library/LaunchAgents/dns_monitor.log
   ```

## Debugging / 调试
Run in debug mode to inspect network information:  
以调试模式运行以检查网络信息：
```bash
python3 ~/Library/LaunchAgents/dns_monitor.py debug
```

## Notes / 注意事项
- **sudo Permissions / sudo 权限**: The script requires `sudo` for DNS configuration and flush commands (`networksetup`, `dscacheutil`, `mDNSResponder`). Configure `sudoers` for passwordless execution if needed:  
  脚本需要 `sudo` 权限执行 DNS 配置和刷新命令（`networksetup`、`dscacheutil`、`mDNSResponder`）。如需免密码执行，可配置 `sudoers`：
  ```bash
  sudo visudo
  # Add / 添加: <username> ALL=(ALL) NOPASSWD: /usr/sbin/dscacheutil -flushcache, /usr/bin/killall -HUP mDNSResponder, /usr/sbin/networksetup -setdnsservers Wi-Fi *
  ```
- **Customization / 自定义**: Adjust `CHECK_INTERVAL` and `MAX_RETRY_TIME` for different polling frequencies or timeout durations.  
  调整 `CHECK_INTERVAL` 和 `MAX_RETRY_TIME` 以设置不同的轮询频率或超时时间。
- **Network Specificity / 网络特定性**: Ensure `SPECIFIC_NETWORK_IPS` and `SPECIFIC_DNS` match your target network's configuration.  
  确保 `SPECIFIC_NETWORK_IPS` 和 `SPECIFIC_DNS` 与目标网络的配置匹配。

## License / 许可证
 [MIT License](https://github.com/SlippinDylan/ahaMoment/tree/master/LICENSE.md) 