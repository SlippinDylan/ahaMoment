# Router Monitor / 路由器监控

A macOS Python script to automatically manage applications based on the connected network's gateway IP and MAC address.  
这是一个用于 macOS 的 Python 脚本，根据连接的网络网关 IP 和 MAC 地址自动管理应用程序。

## Background / 背景
**English**: This script was created to optimize application behavior in a home network environment. My home router runs a proxy service (e.g., OpenWrt with a proxy application). When my Mac connects to the home network, there's no need to run the same proxy application locally, and other related applications (e.g., VPN clients) can also be safely closed to save resources.  
**中文**: 该脚本旨在优化家庭网络环境下的应用程序行为。我的家用路由器运行了代理服务（例如 OpenWrt 上的代理应用）。当我的 Mac 连接到家庭网络时，无需本地运行相同的代理应用，其他相关应用（如 VPN 客户端）也可以安全关闭以节省资源。

## Functionality / 功能
- **Detects Home Network / 检测家庭网络**: Checks if the current network's gateway matches the specified IP (`<HOME_GATEWAY_IP>`) and MAC address (`<HOME_GATEWAY_MAC>`).  
  检查当前网络的网关是否匹配指定的 IP（`<HOME_GATEWAY_IP>`）和 MAC 地址（`<HOME_GATEWAY_MAC>`）。
- **Application Management / 应用管理**:
  - If connected to the home network, gracefully quits specified applications (e.g., `Sparkle` and `Tailscale`).  
    如果连接到家庭网络，优雅退出指定应用（如 `Sparkle` 和 `Tailscale`）。
  - If connected to another network, launches the proxy application (`Sparkle`).  
    如果连接到其他网络，启动代理应用（`Sparkle`）。
- **DNS Flush / DNS 刷新**: Refreshes the DNS cache after application operations to ensure network configuration consistency.  
  在应用操作完成后刷新 DNS 缓存，确保网络配置一致性。
- **Debug Mode / 调试模式**: Provides detailed network information for troubleshooting.  
  提供详细的网络信息以便排错。

## Prerequisites / 前置条件
- **Python 3**: Ensure Python 3 is installed (`python3 --version`).  
  确保已安装 Python 3（运行 `python3 --version` 检查）。
- **netifaces**: Install via `pip3 install netifaces`.  
  通过 `pip3 install netifaces` 安装。
- **macOS Tools / macOS 工具**: Uses built-in tools (`arp`, `ping`, `netstat`, `osascript`, `pgrep`).  
  使用内置工具（`arp`、`ping`、`netstat`、`osascript`、`pgrep`）。
- **Applications / 应用**: Ensure the applications specified in `MIHOMO_APP` and `TAILSCALE_APP` (e.g., `Sparkle`, `Tailscale`) are installed in `/Applications`.  
  确保 `MIHOMO_APP` 和 `TAILSCALE_APP` 指定的应用（如 `Sparkle`、`Tailscale`）已安装在 `/Applications`。

## Installation / 安装
1. **Place Files / 放置文件**:
   - Save `router_monitor.py` and `com.user.routermonitor.plist` to `~/Library/LaunchAgents/`.  
     将 `router_monitor.py` 和 `com.user.routermonitor.plist` 保存到 `~/Library/LaunchAgents/`。
   ```bash
   mkdir -p ~/Library/LaunchAgents
   cp router_monitor.py ~/Library/LaunchAgents/
   cp com.user.routermonitor.plist ~/Library/LaunchAgents/
   ```

2. **Set Permissions / 设置权限**:
   ```bash
   chmod +x ~/Library/LaunchAgents/router_monitor.py
   ```

3. **Configure Parameters / 配置参数**:
   - Edit `router_monitor.py` to set:  
     编辑 `router_monitor.py`，设置：
     - `HOME_GATEWAY_IP`: Your home router's gateway IP (e.g., `192.168.1.1`).  
       家庭路由器的网关 IP（例如 `192.168.1.1`）。
     - `HOME_GATEWAY_MAC`: Your home router's MAC address (e.g., `00:14:22:01:23:45`).  
       家庭路由器的 MAC 地址（例如 `00:14:22:01:23:45`）。
     - `MIHOMO_APP`: Your proxy application name (e.g., `Sparkle`).  
       代理应用名称（例如 `Sparkle`）。
     - `TAILSCALE_APP`: Your VPN application name (e.g., `Tailscale`).  
       VPN 应用名称（例如 `Tailscale`）。

4. **Load LaunchAgent / 加载 LaunchAgent**:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.user.routermonitor.plist
   ```

5. **View Logs / 查看日志**:
   ```bash
   tail -f ~/Library/LaunchAgents/router_monitor.log
   ```

## Debugging / 调试
Run in debug mode to inspect network information:  
以调试模式运行以检查网络信息：
```bash
python3 ~/Library/LaunchAgents/router_monitor.py debug
```

## Notes / 注意事项
- **sudo Permissions / sudo 权限**: The script requires `sudo` for DNS flush commands (`dscacheutil`, `mDNSResponder`). Configure `sudoers` for passwordless execution if needed:  
  脚本需要 `sudo` 权限执行 DNS 刷新命令（`dscacheutil`、`mDNSResponder`）。如需免密码执行，可配置 `sudoers`：
  ```bash
  sudo visudo
  # Add / 添加: <username> ALL=(ALL) NOPASSWD: /usr/sbin/dscacheutil -flushcache, /usr/bin/killall -HUP mDNSResponder
  ```
- **Customization / 自定义**: Adjust `CHECK_INTERVAL` and `MAX_RETRY_TIME` for different polling frequencies or timeout durations.  
  调整 `CHECK_INTERVAL` 和 `MAX_RETRY_TIME` 以设置不同的轮询频率或超时时间。
- **Application Names / 应用名称**: Update `MIHOMO_APP` and `TAILSCALE_APP` to match your installed applications.  
  更新 `MIHOMO_APP` 和 `TAILSCALE_APP` 以匹配你安装的应用。

## License / 许可证
MIT License