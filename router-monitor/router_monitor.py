#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 设置命令:
# launchctl unload ~/Library/LaunchAgents/com.user.routermonitor.plist
# chmod +x ~/Library/LaunchAgents/router_monitor.py
# launchctl load ~/Library/LaunchAgents/com.user.routermonitor.plist
# tail -f ~/Library/LaunchAgents/router_monitor.log
import os
import sys
import time
import re
import subprocess
import logging
from logging.handlers import RotatingFileHandler
import netifaces

# 配置
HOME_GATEWAY_IP = "<HOME_GATEWAY_IP>"       # 家庭网关IP地址（替换为实际IP）
HOME_GATEWAY_MAC = "<HOME_GATEWAY_MAC>"     # 家庭网关MAC地址（替换为实际MAC）
MIHOMO_APP = "Sparkle"                      # 主控应用程序名称（替换为实际应用名）
TAILSCALE_APP = "Tailscale"                 # Tailscale应用程序名称（替换为实际应用名）
LOG_DIR = "~/Library/LaunchAgents"          # 日志目录
LOG_FILE = os.path.join(os.path.expanduser(LOG_DIR), "router_monitor.log")  # 日志文件路径
CHECK_INTERVAL = 5                          # 检查间隔（秒）
MAX_RETRY_TIME = 750                        # 最大重试时间（12.5分钟）

# 日志设置
os.makedirs(os.path.expanduser(LOG_DIR), exist_ok=True)

class CustomFormatter(logging.Formatter):
    def format(self, record):
        return f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n[{self.formatTime(record)}] {record.levelname}\n{record.getMessage()}"

def initialize_logger():
    """初始化日志系统"""
    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1024*300,  # 300KB 约300条日志
        backupCount=1,
        encoding='utf-8'
    )
    handler.setFormatter(CustomFormatter())
    
    logger = logging.getLogger("RouterMonitor")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    logger.info("▶▶▶ 路由器监控启动")
    return logger

# 工具函数
def standardize_mac(raw_mac):
    """将MAC地址标准化为XX:XX:XX:XX:XX:XX格式"""
    try:
        parts = re.findall(r"[0-9a-fA-F]{1,2}", raw_mac)
        if len(parts) == 6:
            return ":".join(f"{int(p,16):02x}" for p in parts)
        return None
    except Exception as e:
        logger.error(f"MAC地址标准化失败: {str(e)}")
        return None

def refresh_arp_cache(ip):
    """刷新ARP缓存以确保获取最新数据"""
    try:
        subprocess.run(["arp", "-d", ip], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ping", "-c2", "-W1", ip], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"已刷新ARP缓存: {ip}")
    except Exception as e:
        logger.error(f"刷新ARP缓存失败: {str(e)}")

def get_mac_from_arp(ip):
    """从ARP表获取指定IP的MAC地址"""
    try:
        try:
            arp_output = subprocess.check_output(["arp", "-n", ip], text=True, stderr=subprocess.PIPE)
            logger.info(f"ARP表内容: {arp_output.strip()}")
            mac_match = re.search(r"((?:[0-9a-fA-F]{1,2}[:\-\.]){5}[0-9a-fA-F]{1,2})", arp_output)
            if mac_match:
                std_mac = standardize_mac(mac_match.group(1))
                logger.info(f"原始MAC: {mac_match.group(1)} → 标准化: {std_mac}")
                return std_mac
        except subprocess.CalledProcessError:
            logger.info(f"arp -n {ip} 失败，尝试完整ARP表...")
        
        try:
            arp_all_output = subprocess.check_output(["arp", "-a"], text=True, stderr=subprocess.PIPE)
            logger.info(f"完整ARP表: {arp_all_output}")
            gateway_pattern = rf'\? \({re.escape(ip)}\) at ([a-fA-F0-9:]+)'
            gateway_match = re.search(gateway_pattern, arp_all_output)
            if gateway_match:
                raw_mac = gateway_match.group(1)
                std_mac = standardize_mac(raw_mac)
                logger.info(f"从完整ARP表找到MAC: {raw_mac} → 标准化: {std_mac}")
                return std_mac
        except subprocess.CalledProcessError:
            logger.warning("获取完整ARP表失败")
        
        logger.warning(f"无法从ARP表找到{ip}的MAC地址")
        return None
    except Exception as e:
        logger.error(f"获取MAC地址失败: {str(e)}")
        return None

def get_router_info():
    """使用netifaces获取当前路由器IP和MAC地址"""
    try:
        logger.info("开始获取网关信息...")
        gateways = netifaces.gateways()
        logger.info(f"netifaces.gateways()结果: {gateways}")
        
        default_gateway = None
        if 'default' in gateways and netifaces.AF_INET in gateways['default']:
            default_gateway = gateways['default'][netifaces.AF_INET][0]
            logger.info(f"从default获取到网关IP: {default_gateway}")
        elif netifaces.AF_INET in gateways:
            ipv4_gateways = gateways[netifaces.AF_INET]
            if ipv4_gateways:
                default_gateway = ipv4_gateways[0][0]
                logger.info(f"从IPv4路由获取到网关IP: {default_gateway}")
        
        if default_gateway:
            refresh_arp_cache(default_gateway)
            mac_address = get_mac_from_arp(default_gateway)
            return default_gateway, mac_address
        else:
            logger.warning("netifaces未找到默认网关")
            return None, None
    except Exception as e:
        logger.error(f"获取网关信息失败: {str(e)}")
        return None, None

def get_router_info_netstat():
    """使用netstat命令获取默认网关信息（备用方法）"""
    try:
        logger.info("使用netstat获取网关信息...")
        netstat_output = subprocess.check_output(["netstat", "-rn"], text=True, stderr=subprocess.PIPE)
        logger.info(f"netstat输出内容:\n{netstat_output}")
        
        for line in netstat_output.split('\n'):
            if line.startswith('default') and 'UG' in line:
                parts = line.split()
                if len(parts) >= 2:
                    gateway_ip = parts[1]
                    logger.info(f"从netstat获取到网关: {gateway_ip}")
                    refresh_arp_cache(gateway_ip)
                    mac_address = get_mac_from_arp(gateway_ip)
                    logger.info(f"从ARP获取到MAC: {mac_address}")
                    return gateway_ip, mac_address
        logger.warning("netstat未找到IPv4默认网关")
        return None, None
    except Exception as e:
        logger.error(f"netstat获取网关信息失败: {str(e)}")
        return None, None

def get_router_info_combined():
    """组合netifaces和netstat方法获取路由器信息"""
    logger.info("尝试使用netifaces获取网关信息...")
    ip, mac = get_router_info()
    if ip:
        logger.info(f"netifaces成功: IP={ip}, MAC={mac}")
        return ip, mac
    
    logger.info("netifaces失败，尝试netstat...")
    ip, mac = get_router_info_netstat()
    if ip:
        logger.info(f"netstat成功: IP={ip}, MAC={mac}")
        return ip, mac
    
    logger.error("所有方法均无法获取网关信息")
    return None, None

def check_target_router_match(current_ip, current_mac):
    """检查是否匹配目标MAC和IP地址"""
    if not current_ip or not current_mac:
        return False
    ip_match = current_ip == HOME_GATEWAY_IP
    mac_match = current_mac.lower() == HOME_GATEWAY_MAC.lower()
    logger.info(f"目标路由器检查: IP({current_ip}=={HOME_GATEWAY_IP}): {ip_match}, MAC({current_mac}=={HOME_GATEWAY_MAC}): {mac_match}")
    return ip_match and mac_match

def flush_dns():
    """刷新DNS缓存"""
    try:
        logger.info("开始刷新DNS缓存...")
        subprocess.run(["sudo", "dscacheutil", "-flushcache"], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], check=True, stdout=subprocess.DEVNULL)
        logger.info("DNS缓存刷新成功")
    except subprocess.CalledProcessError as e:
        logger.error(f"DNS刷新失败: {str(e)}")

def control_mihomo(should_run):
    """控制Mihomo应用（启动/退出）"""
    try:
        action = "启动" if should_run else "退出"
        logger.info(f"正在{action}{MIHOMO_APP}...")
        if should_run:
            result = subprocess.run(["pgrep", "-x", MIHOMO_APP], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                subprocess.run(["open", "-a", MIHOMO_APP], check=False)
                logger.info(f"{MIHOMO_APP}已启动")
            else:
                logger.info(f"{MIHOMO_APP}已在运行")
        else:
            graceful_quit_app(MIHOMO_APP)
        return True
    except Exception as e:
        logger.error(f"{MIHOMO_APP}{action}失败: {str(e)}")
        return False

def graceful_quit_app(app_name):
    """优雅退出指定应用"""
    try:
        result = subprocess.run(["pgrep", "-x", app_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            logger.info(f"检测到{app_name}正在运行，尝试优雅退出...")
            applescript_cmd = f'tell application "{app_name}" to quit'
            subprocess.run(
                ["osascript", "-e", applescript_cmd],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10
            )
            time.sleep(3)
            check_result = subprocess.run(["pgrep", "-x", app_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if check_result.returncode != 0:
                logger.info(f"{app_name}通过AppleScript成功退出")
                return True
            logger.info("AppleScript退出失败，尝试发送Command+Q...")
            activate_cmd = f'tell application "{app_name}" to activate'
            subprocess.run(
                ["osascript", "-e", activate_cmd],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5
            )
            time.sleep(1)
            cmd_q_script = '''
            tell application "System Events"
                key code 12 using {command down}
            end tell
            '''
            subprocess.run(
                ["osascript", "-e", cmd_q_script],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10
            )
            logger.info(f"向{app_name}发送Command+Q")
            time.sleep(5)
            check_result = subprocess.run(["pgrep", "-x", app_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if check_result.returncode != 0:
                logger.info(f"{app_name}通过Command+Q成功退出")
                return True
            logger.warning(f"{app_name}未响应Command+Q，可能需要手动处理")
            return False
        else:
            logger.info(f"{app_name}未运行")
            return True
    except Exception as e:
        logger.error(f"优雅退出{app_name}失败: {str(e)}")
        return False

def check_and_quit_tailscale():
    """退出Tailscale应用"""
    try:
        result = subprocess.run(["pgrep", "-x", TAILSCALE_APP], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            logger.info(f"检测到{TAILSCALE_APP}正在运行，尝试退出...")
            return graceful_quit_app(TAILSCALE_APP)
        else:
            logger.info(f"{TAILSCALE_APP}未运行")
            return True
    except Exception as e:
        logger.error(f"退出{TAILSCALE_APP}失败: {str(e)}")
        return False

def handle_target_router_found():
    """处理检测到目标路由器的情况"""
    logger.info("检测到目标路由器，执行退出操作")
    control_mihomo(False)
    check_and_quit_tailscale()
    flush_dns()  # 在所有应用操作完成后刷新DNS
    return True

def handle_normal_network():
    """处理普通网络的情况"""
    logger.info("检测到普通网络，启动Mihomo")
    control_mihomo(True)
    flush_dns()  # 在所有应用操作完成后刷新DNS
    return True

def router_monitor():
    """主路由器监控函数"""
    global logger
    logger = initialize_logger()
    start_time = time.time()
    
    try:
        while (time.time() - start_time) < MAX_RETRY_TIME:
            current_ip, current_mac = get_router_info_combined()
            if current_ip is None:
                logger.warning("未获取到路由器信息，重试...")
                time.sleep(CHECK_INTERVAL)
                continue
            logger.info(f"当前网关IP: {current_ip}, MAC: {current_mac}")
            if check_target_router_match(current_ip, current_mac):
                handle_target_router_found()
                break
            else:
                handle_normal_network()
                break
        else:
            logger.warning("超时：未检测到有效路由器信息")
            flush_dns()  # 超时情况下也刷新DNS
    except Exception as e:
        logger.error(f"监控异常: {str(e)}")
        flush_dns()  # 异常情况下也刷新DNS
    finally:
        logger.info("◀◀◀ 路由器监控结束")

def debug_router():
    """调试模式：显示路由器信息"""
    print("=== 路由器调试信息 ===")
    try:
        arp_output = subprocess.check_output(["arp", "-a"], text=True, stderr=subprocess.DEVNULL)
        print("ARP表内容：")
        print(arp_output)
    except Exception as e:
        print(f"获取ARP表失败: {str(e)}")
    
    print("\n=== 测试netifaces方法 ===")
    ip, mac = get_router_info()
    print(f"netifaces结果: IP={ip}, MAC={mac}")
    
    print("\n=== 测试netstat方法 ===")
    ip2, mac2 = get_router_info_netstat()
    print(f"netstat结果: IP={ip2}, MAC={mac2}")
    
    print("\n=== 测试组合方法 ===")
    ip3, mac3 = get_router_info_combined()
    print(f"组合方法结果: IP={ip3}, MAC={mac3}")
    
    match = check_target_router_match(ip3, mac3)
    print(f"是否匹配目标路由器: {match}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        debug_router()
    else:
        router_monitor()
    sys.exit(0)