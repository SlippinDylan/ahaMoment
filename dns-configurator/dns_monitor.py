#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 设置命令:
# launchctl unload ~/Library/LaunchAgents/com.user.dnsmonitor.plist
# chmod +x ~/Library/LaunchAgents/dns_monitor.py
# launchctl load ~/Library/LaunchAgents/com.user.dnsmonitor.plist
# tail -f ~/Library/LaunchAgents/dns_monitor.log
import os
import sys
import time
import re
import subprocess
import logging
from logging.handlers import RotatingFileHandler

# 配置
SPECIFIC_NETWORK_IPS = ["<SPECIFIC_NETWORK_IP1>", "<SPECIFIC_NETWORK_IP2>", "<SPECIFIC_NETWORK_IP3>"]  # 特定网络的ARP IP地址（替换为实际IP）
SPECIFIC_DNS = "<SPECIFIC_DNS>"             # 特定网络的DNS地址（替换为实际DNS）
LOG_DIR = "~/Library/LaunchAgents"          # 日志目录
LOG_FILE = os.path.join(os.path.expanduser(LOG_DIR), "dns_monitor.log")  # 日志文件路径
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
    
    logger = logging.getLogger("DNSMonitor")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    logger.info("▶▶▶ DNS监控启动")
    return logger

# 工具函数
def flush_dns():
    """刷新DNS缓存"""
    try:
        logger.info("开始刷新DNS缓存...")
        subprocess.run(["sudo", "dscacheutil", "-flushcache"], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], check=True, stdout=subprocess.DEVNULL)
        logger.info("DNS缓存刷新成功")
    except subprocess.CalledProcessError as e:
        logger.error(f"DNS刷新失败: {str(e)}")

def check_specific_network():
    """检查是否为特定网络IP"""
    try:
        arp_output = subprocess.check_output(["arp", "-a"], text=True, stderr=subprocess.DEVNULL)
        for ip in SPECIFIC_NETWORK_IPS:
            if re.search(rf'\({re.escape(ip)}\)', arp_output):
                logger.info(f"检测到特定网络: {ip}")
                return True
        logger.info("未检测到特定网络")
        return False
    except Exception as e:
        logger.error(f"特定网络检查失败: {str(e)}")
        return False

def configure_specific_dns(should_set):
    """配置或清除特定网络DNS"""
    try:
        if should_set:
            logger.info(f"设置特定网络DNS: {SPECIFIC_DNS}")
            subprocess.run([
                "networksetup", "-setdnsservers", "Wi-Fi", SPECIFIC_DNS
            ], check=True)
        else:
            logger.info("清除DNS配置")
            subprocess.run([
                "networksetup", "-setdnsservers", "Wi-Fi", "Empty"
            ], check=False)
            subprocess.run([
                "networksetup", "-setdnsservers", "Wi-Fi", ""
            ], check=False)
        flush_dns()
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"特定网络DNS配置失败: {str(e)}")
        return False

def handle_specific_network_found():
    """处理检测到特定网络的情况"""
    logger.info("检测到特定网络，配置DNS")
    configure_specific_dns(True)
    return True

def handle_normal_network():
    """处理普通网络的情况"""
    logger.info("检测到普通网络，清除DNS")
    configure_specific_dns(False)
    return True

def dns_monitor():
    """主DNS监控函数"""
    global logger
    logger = initialize_logger()
    start_time = time.time()
    
    try:
        while (time.time() - start_time) < MAX_RETRY_TIME:
            if check_specific_network():
                handle_specific_network_found()
                break
            else:
                handle_normal_network()
                break
        else:
            logger.warning("超时：未检测到有效网络信息")
    except Exception as e:
        logger.error(f"监控异常: {str(e)}")
    finally:
        logger.info("◀◀◀ DNS监控结束")

def debug_dns():
    """调试模式：显示DNS信息"""
    print("=== DNS调试信息 ===")
    try:
        arp_output = subprocess.check_output(["arp", "-a"], text=True, stderr=subprocess.DEVNULL)
        print("ARP表内容：")
        print(arp_output)
    except Exception as e:
        print(f"获取ARP表失败: {str(e)}")
    
    is_specific = check_specific_network()
    print(f"是否为特定网络: {is_specific}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        debug_dns()
    else:
        dns_monitor()
    sys.exit(0)