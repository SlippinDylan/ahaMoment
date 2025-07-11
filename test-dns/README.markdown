# DNS Testing Script

## Overview
This Bash script (`test_dns.sh`) is designed to test the performance of a specified DNS server by measuring the query response time for a predefined list of popular websites. It performs multiple rounds of tests, calculates average, maximum, and minimum query times, and outputs the results in a concise format.

## Features
- Tests DNS query performance for a list of popular websites.
- Supports multiple rounds of testing (default: 10 rounds).
- Calculates average, maximum, and minimum query times for each website.
- Compatible with Linux and macOS (uses `dig` command for DNS queries).
- Includes a short delay between requests to avoid overwhelming the DNS server.

## Prerequisites
- Bash shell environment.
- `dig` command (part of the `dnsutils` or `bind-tools` package on most systems).
- `bc` command for floating-point calculations (pre-installed on most systems).

## Usage
1. Save the script as `test_dns.sh`.
2. Make it executable:
   ```bash
   chmod +x test_dns.sh
   ```
3. Run the script, specifying a DNS server IP address as an argument:
   ```bash
   ./test_dns.sh 223.5.5.5
   ```
   Replace `223.5.5.5` with the DNS server you want to test.

## Example Output
```plaintext
测试DNS服务器: 223.5.5.5
==================================================
www.baidu.com：平均[12.34] msec，最高[15] msec，最低[10] msec
www.taobao.com：平均[14.56] msec，最高[18] msec，最低[12] msec
...
==================================================
测试完成
```

## Script Details
- **DNS Server**: The script takes a single argument, the IP address of the DNS server to test.
- **Websites**: Tests a hardcoded list of popular websites (`www.baidu.com`, `www.taobao.com`, etc.).
- **Rounds**: Performs 10 rounds of queries per website by default.
- **Metrics**: For each website, it calculates:
  - Average query time (in milliseconds, with two decimal places).
  - Maximum query time.
  - Minimum query time.
- **Sleep**: Includes a 0.5-second delay between queries to prevent overwhelming the DNS server.

## Notes
- Ensure the DNS server IP is valid; otherwise, the script will fail.
- The script requires the `dig` command, which is part of the BIND utilities. Install it if not already present:
  - On Debian/Ubuntu: `sudo apt-get install dnsutils`
  - On Red Hat/CentOS: `sudo yum install bind-utils`
  - On macOS: `dig` is typically pre-installed.
- The script is compatible with macOS due to the use of `sed -E` for regex compatibility.

## License
This script is open-source and available under the MIT License.

---

# DNS测试脚本

## 概述
此 Bash 脚本（`test_dns.sh`）用于测试指定 DNS 服务器的性能，通过测量对一组预定义热门网站的查询响应时间来实现。它会进行多轮测试，计算平均、最大和最小查询时间，并以简洁的格式输出结果。

## 功能
- 测试一组热门网站的 DNS 查询性能。
- 支持多轮测试（默认：10 轮）。
- 计算每个网站的平均、最大和最小查询时间。
- 兼容 Linux 和 macOS（使用 `dig` 命令进行 DNS 查询）。
- 在请求之间加入短暂延迟，以避免对 DNS 服务器造成过大压力。

## 前提条件
- Bash shell 环境。
- `dig` 命令（通常包含在 `dnsutils` 或 `bind-tools` 软件包中）。
- `bc` 命令用于浮点计算（大多数系统上默认安装）。

## 使用方法
1. 将脚本保存为 `test_dns.sh`。
2. 赋予执行权限：
   ```bash
   chmod +x test_dns.sh
   ```
3. 运行脚本，并指定 DNS 服务器的 IP 地址作为参数：
   ```bash
   ./test_dns.sh 223.5.5.5
   ```
   将 `223.5.5.5` 替换为要测试的 DNS 服务器地址。

## 示例输出
```plaintext
测试DNS服务器: 223.5.5.5
==================================================
www.baidu.com：平均[12.34] msec，最高[15] msec，最低[10] msec
www.taobao.com：平均[14.56] msec，最高[18] msec，最低[12] msec
...
==================================================
测试完成
```

## 脚本详情
- **DNS 服务器**：脚本接受一个参数，即要测试的 DNS 服务器的 IP 地址。
- **网站**：测试一组硬编码的热门网站（`www.baidu.com`, `www.taobao.com` 等）。
- **轮次**：默认对每个网站进行 10 轮查询。
- **指标**：对每个网站计算：
  - 平均查询时间（毫秒，保留两位小数）。
  - 最大查询时间。
  - 最小查询时间。
- **延迟**：在每次查询之间加入 0.5 秒的延迟，以防止对 DNS 服务器造成过大压力。

## 注意事项
- 确保 DNS 服务器 IP 有效，否则脚本将失败。
- 脚本需要 `dig` 命令，属于 BIND 工具的一部分。如果未安装，请先安装：
  - 在 Debian/Ubuntu 上：`sudo apt-get install dnsutils`
  - 在 Red Hat/CentOS 上：`sudo yum install bind-utils`
  - 在 macOS 上：`dig` 通常已预装。
- 脚本通过使用 `sed -E` 确保与 macOS 的正则表达式兼容。

## 许可证
此脚本为开源软件，遵循 MIT 许可证。