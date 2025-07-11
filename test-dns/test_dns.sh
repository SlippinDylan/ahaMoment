#!/bin/bash

# 定义DNS服务器和测试网站
DNS=$1
SITES=("www.baidu.com" "www.taobao.com" "www.qq.com" "www.bilibili.com" "www.163.com" "www.douyin.com" "home.mi.com")
ROUNDS=10

# 检查是否提供了DNS参数
if [ -z "$DNS" ]; then
    echo "请提供DNS服务器地址，例如: ./dns_test.sh 223.5.5.5"
    exit 1
fi

echo "测试DNS服务器: $DNS"
echo "=================================================="

# 对每个网站进行多轮测试
for site in "${SITES[@]}"
do
    total_time=0
    max_time=0
    min_time=9999
    
    # 运行ROUNDS轮测试
    for ((i=1; i<=ROUNDS; i++))
    do
        # 使用dig命令并提取Query time，兼容macOS
        result=$(dig @$DNS $site | grep "Query time")
        query_time=$(echo $result | sed -E 's/.*Query time: ([0-9]+) msec.*/\1/')
        
        # 更新统计数据
        total_time=$((total_time + query_time))
        
        # 更新最大值
        if [ "$query_time" -gt "$max_time" ]; then
            max_time=$query_time
        fi
        
        # 更新最小值
        if [ "$query_time" -lt "$min_time" ]; then
            min_time=$query_time
        fi
        
        # 短暂停顿，避免过快请求
        sleep 0.5
    done
    
    # 计算平均时间
    avg_time=$(echo "scale=2; $total_time / $ROUNDS" | bc)
    
    # 输出简洁结果 - 确保包含网站名
    printf "%s：平均[%s] msec，最高[%s] msec，最低[%s] msec\n" "$site" "$avg_time" "$max_time" "$min_time"
done

echo "=================================================="
echo "测试完成"