#!/bin/bash

# 提示运行的脚本路径
echo "运行脚本：$0"

# 检查调试选项
DEBUG=true
if [ "$1" = "--no-debug" ]; then
    DEBUG=false
fi

# 函数：输出调试信息
debug() {
    if [ "$DEBUG" = true ]; then
        echo "调试：$1"
    fi
}

# 设置工作目录为当前目录
DOCKER_DIR="."
cd "$DOCKER_DIR" || { echo "错误：无法切换到当前目录 $DOCKER_DIR"; exit 1; }

# 初始化计数器和数组
TOTAL_DIRS=$(find . -maxdepth 1 -type d -not -path . -exec test -f {}/docker-compose.yml \; -print | wc -l)
CURRENT_DIR=0
declare -A IMAGE_MAP  # 存储镜像及其使用的容器
declare -A SERVICE_IMAGE_MAP  # 存储服务到镜像的映射
declare -a INVALID_COMPOSE_FILES  # 存储无效的 compose 文件
declare -a UPDATED_IMAGES  # 存储需要更新的镜像

# 函数：重试命令
retry() {
    local attempts=3
    local delay=5
    local cmd="$@"
    for ((i=1; i<=attempts; i++)); do
        if $cmd; then
            return 0
        fi
        echo "错误：命令失败，第 $i 次重试..."
        sleep $delay
    done
    echo "错误：命令 $cmd 失败 $attempts 次，退出"
    exit 1
}

# 函数：检查 docker-compose 文件有效性
check_compose_file() {
    local dir="$1"
    local file="$dir/docker-compose.yml"
    debug "检查文件 $file 是否存在"
    if [ ! -f "$file" ]; then
        echo "错误：目录 $dir 中未找到 docker-compose.yml"
        INVALID_COMPOSE_FILES+=("$file")
        return 1
    fi
    if ! docker-compose -f "$file" config >/dev/null 2>&1; then
        echo "错误：$file 文件格式无效"
        INVALID_COMPOSE_FILES+=("$file")
        return 1
    fi
    debug "文件 $file 有效"
    return 0
}

# 函数：检查容器是否运行（优化版）
is_container_running() {
    local container_name="$1"
    local container_id=""
    
    debug "检查容器 $container_name 是否运行"
    
    # 方法1：直接通过容器名称检查
    if docker ps --filter "name=^${container_name}$" --format "{{.Names}}" | grep -q "^${container_name}$"; then
        debug "容器 $container_name 正在运行（通过名称检查）"
        return 0
    fi
    
    # 方法2：如果传入的是容器ID，直接检查ID
    if [[ "$container_name" =~ ^[0-9a-f]{12,64}$ ]]; then
        if docker ps --filter "id=$container_name" --format "{{.ID}}" | grep -q "$container_name"; then
            debug "容器 $container_name 正在运行（通过ID检查）"
            return 0
        fi
    fi
    
    # 方法3：通过 docker inspect 检查容器状态
    local container_status=$(docker inspect --format '{{.State.Status}}' "$container_name" 2>/dev/null)
    if [[ "$container_status" == "running" ]]; then
        debug "容器 $container_name 正在运行（通过inspect检查，状态：$container_status）"
        return 0
    elif [[ -n "$container_status" ]]; then
        debug "容器 $container_name 存在但未运行（状态：$container_status）"
        return 1
    fi
    
    # 方法4：检查是否是部分匹配问题
    local exact_match=$(docker ps --format "{{.Names}}" | grep -E "^${container_name}$")
    if [[ -n "$exact_match" ]]; then
        debug "容器 $container_name 正在运行（精确匹配）"
        return 0
    fi
    
    # 方法5：模糊匹配，可能存在命名差异
    local fuzzy_match=$(docker ps --format "{{.Names}}" | grep "$container_name")
    if [[ -n "$fuzzy_match" ]]; then
        debug "发现类似的运行容器：$fuzzy_match"
        debug "容器 $container_name 可能在运行，但名称不完全匹配"
    fi
    
    debug "容器 $container_name 未运行或不存在"
    
    # 额外调试信息
    if [ "$DEBUG" = true ]; then
        echo "调试：当前所有运行的容器："
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
        echo "调试：所有容器（包括停止的）："
        docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | head -10
    fi
    
    return 1
}

# 函数：获取容器的详细状态信息
get_container_detailed_status() {
    local container_name="$1"
    local status_info=""
    
    debug "获取容器 $container_name 的详细状态"
    
    status_info=$(docker inspect --format 'Status: {{.State.Status}} | Health: {{.State.Health.Status}} | Running: {{.State.Running}}' "$container_name" 2>/dev/null)
    
    if [[ -n "$status_info" ]]; then
        debug "容器 $container_name 详细状态：$status_info"
        echo "$status_info"
        return 0
    fi
    
    debug "无法获取容器 $container_name 的详细状态"
    return 1
}

# 函数：从docker-compose.yml提取镜像（优化版）
extract_image_from_compose() {
    local compose_file="$1"
    local service="$2"
    local image=""
    
    debug "提取服务 $service 的镜像信息"
    
    # 方法1：使用 docker-compose config 输出的 JSON 格式
    if command -v jq >/dev/null 2>&1; then
        debug "使用 jq 提取镜像信息"
        image=$(docker-compose -f "$compose_file" config --format json 2>/dev/null | jq -r ".services.\"$service\".image" 2>/dev/null)
        if [[ "$image" != "null" && -n "$image" ]]; then
            debug "jq 成功提取镜像：$image"
            echo "$image"
            return 0
        fi
    fi
    
    # 方法2：使用 docker-compose config 的 YAML 输出 + grep/awk
    debug "使用 grep/awk 提取镜像信息"
    image=$(docker-compose -f "$compose_file" config 2>/dev/null | awk -v service="$service" '
        BEGIN { 
            in_services = 0
            in_target_service = 0
            service_indent = 0
        }
        /^services:/ { 
            in_services = 1
            next 
        }
        in_services && /^[[:space:]]*[a-zA-Z0-9_-]+:/ {
            match($0, /^[[:space:]]*/);
            current_indent = RLENGTH;
            
            current_service = $0;
            gsub(/^[[:space:]]*/, "", current_service);
            gsub(/:.*$/, "", current_service);
            
            if (current_service == service) {
                in_target_service = 1;
                service_indent = current_indent;
                debug_print("找到目标服务: " service " 缩进级别: " service_indent);
            } else if (current_indent <= service_indent && in_target_service) {
                in_target_service = 0;
            }
        }
        in_target_service && /^[[:space:]]*image:/ {
            image_line = $0;
            gsub(/^[[:space:]]*image:[[:space:]]*/, "", image_line);
            gsub(/^["\047]/, "", image_line);
            gsub(/["\047][[:space:]]*$/, "", image_line);
            print image_line;
            exit;
        }
        function debug_print(msg) {
            if (ENVIRON["DEBUG"] == "true") {
                print "AWK调试：" msg > "/dev/stderr";
            }
        }
    ')
    
    if [[ -n "$image" ]]; then
        debug "grep/awk 成功提取镜像：$image"
        echo "$image"
        return 0
    fi
    
    # 方法3：直接解析 docker-compose.yml 文件
    debug "直接解析 docker-compose.yml 文件"
    image=$(awk -v service="$service" '
        BEGIN { 
            in_services = 0
            in_target_service = 0
            service_indent = 0
        }
        /^services:/ { 
            in_services = 1
            next 
        }
        in_services && /^[[:space:]]*[a-zA-Z0-9_-]+:/ {
            match($0, /^[[:space:]]*/);
            current_indent = RLENGTH;
            
            current_service = $0;
            gsub(/^[[:space:]]*/, "", current_service);
            gsub(/:.*$/, "", current_service);
            
            if (current_service == service) {
                in_target_service = 1;
                service_indent = current_indent;
            } else if (current_indent <= service_indent && in_target_service) {
                in_target_service = 0;
            }
        }
        in_target_service && /^[[:space:]]*image:/ {
            image_line = $0;
            gsub(/^[[:space:]]*image:[[:space:]]*/, "", image_line);
            gsub(/^["\047]/, "", image_line);
            gsub(/["\047][[:space:]]*$/, "", image_line);
            print image_line;
            exit;
        }
    ' "$compose_file")
    
    if [[ -n "$image" ]]; then
        debug "直接解析成功提取镜像：$image"
        echo "$image"
        return 0
    fi
    
    debug "所有方法均未能提取镜像信息"
    return 1
}

# 函数：获取容器名称（优化版）
get_container_name() {
    local compose_file="$1"
    local service="$2"
    local project_name="$3"
    local container_name=""
    local container_id=""
    
    debug "获取服务 $service 的容器名称"
    
    # 方法1：使用项目名称查找容器ID
    container_id=$(docker-compose -f "$compose_file" -p "$project_name" ps -q "$service" 2>/dev/null | head -1)
    if [[ -n "$container_id" ]]; then
        container_name=$(docker inspect --format '{{.Name}}' "$container_id" 2>/dev/null | sed 's|^/||')
        if [[ -n "$container_name" ]]; then
            debug "通过项目名称找到容器：$container_name (ID: $container_id)"
            echo "$container_name"
            return 0
        fi
    fi
    
    # 方法2：不使用项目名称查找容器ID
    container_id=$(docker-compose -f "$compose_file" ps -q "$service" 2>/dev/null | head -1)
    if [[ -n "$container_id" ]]; then
        container_name=$(docker inspect --format '{{.Name}}' "$container_id" 2>/dev/null | sed 's|^/||')
        if [[ -n "$container_name" ]]; then
            debug "不使用项目名称找到容器：$container_name (ID: $container_id)"
            echo "$container_name"
            return 0
        fi
    fi
    
    # 方法3：使用新的 docker compose ps 格式（包含停止的容器）
    container_name=$(docker-compose -f "$compose_file" -p "$project_name" ps -a --format '{{.Name}}' --filter "service=$service" 2>/dev/null | head -1)
    if [[ -n "$container_name" ]]; then
        debug "通过新格式找到容器：$container_name"
        echo "$container_name"
        return 0
    fi
    
    # 方法4：通过标签查找（包含停止的容器）
    container_name=$(docker ps -a --filter "label=com.docker.compose.service=$service" --filter "label=com.docker.compose.project=$project_name" --format '{{.Names}}' | head -1)
    if [[ -n "$container_name" ]]; then
        debug "通过标签找到容器：$container_name"
        echo "$container_name"
        return 0
    fi
    
    # 方法5：通过项目目录名称模糊匹配（多种命名模式）
    container_name=$(docker ps -a --format '{{.Names}}' | grep -E "^${project_name}[-_]${service}[-_][0-9]+$" | head -1)
    if [[ -n "$container_name" ]]; then
        debug "通过模糊匹配找到容器：$container_name"
        echo "$container_name"
        return 0
    fi
    
    # 方法6：尝试 project-service 格式
    container_name=$(docker ps -a --format '{{.Names}}' | grep -E "^${project_name}[-_]${service}$" | head -1)
    if [[ -n "$container_name" ]]; then
        debug "通过简单模糊匹配找到容器：$container_name"
        echo "$container_name"
        return 0
    fi
    
    # 方法7：直接使用服务名查找
    if docker ps -a --format '{{.Names}}' | grep -q "^${service}$"; then
        debug "直接使用服务名找到容器：$service"
        echo "$service"
        return 0
    fi
    
    debug "未找到服务 $service 的容器，尝试列出所有容器进行调试"
    if [ "$DEBUG" = true ]; then
        docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}' | head -10
    fi
    
    return 1
}

# 函数：检查镜像是否有更新（优化版，避免重复拉取）
check_image_update() {
    local image="$1"
    local output
    debug "检查镜像 $image 是否需要更新"
    
    # 检查是否已经检查过该镜像
    if [[ " ${UPDATED_IMAGES[*]} " =~ " $image " ]]; then
        debug "镜像 $image 已经检查过，需要更新"
        return 0
    fi
    
    # 先获取当前镜像的 digest
    local current_digest=$(docker inspect --format='{{index .RepoDigests 0}}' "$image" 2>/dev/null)
    debug "当前镜像 digest: $current_digest"
    
    # 获取远程镜像的 digest（不拉取）
    local remote_digest=""
    if command -v skopeo >/dev/null 2>&1; then
        remote_digest=$(skopeo inspect "docker://$image" 2>/dev/null | jq -r '.Digest' 2>/dev/null)
        debug "远程镜像 digest: $remote_digest"
        
        if [[ -n "$remote_digest" && "$current_digest" != *"$remote_digest"* ]]; then
            debug "镜像 $image 需要更新（digest不匹配）"
            UPDATED_IMAGES+=("$image")
            return 0
        elif [[ -n "$remote_digest" ]]; then
            echo "提示：镜像 $image 已是最新版本，无需更新"
            return 1
        fi
    fi
    
    # 如果 skopeo 不可用，回退到 docker pull 方法
    echo "正在检查镜像 $image 的更新..."
    output=$(docker pull "$image" 2>&1)
    if echo "$output" | grep -q "Status: Image is up to date"; then
        echo "提示：镜像 $image 已是最新版本，无需更新"
        return 1
    elif echo "$output" | grep -q "Error response from daemon"; then
        echo "错误：无法拉取镜像 $image，可能存在网络问题"
        return 1
    fi
    
    debug "镜像 $image 需要更新"
    UPDATED_IMAGES+=("$image")
    return 0
}

# 函数：显示更新摘要
show_update_summary() {
    echo -e "\n===== 更新摘要 ====="
    echo "总镜像数：$(( $(printf '%s\n' "${!IMAGE_MAP[@]}" | grep -v -E '-(running|not-running)$' | wc -l) ))"
    echo "需要更新的镜像数：${#UPDATED_IMAGES[@]}"
    echo "需要更新的目录数：${#DIRS_TO_UPDATE[@]}"
    
    if [ ${#UPDATED_IMAGES[@]} -gt 0 ]; then
        echo -e "\n更新的镜像："
        for image in "${UPDATED_IMAGES[@]}"; do
            echo "- $image"
        done
    fi
    
    echo "==================="
}

# 函数：计算镜像占用空间（MB）
get_disk_usage() {
    local size=$(docker system df --format '{{.Size}}' 2>/dev/null | grep Images | awk '{print $2}' | head -n 1)
    if [[ "$size" =~ MB$ ]]; then
        size=${size%MB}
    elif [[ "$size" =~ GB$ ]]; then
        if command -v bc >/dev/null 2>&1; then
            size=$(bc <<< "${size%GB} * 1024" | awk '{printf "%.2f", $0}')
        else
            size=$(awk "BEGIN {printf \"%.2f\", ${size%GB} * 1024}")
        fi
    else
        size=0
    fi
    echo "${size:-0}"
}

# 函数：收集镜像和容器信息
collect_images() {
    echo "正在扫描当前目录：$PWD"
    echo "预计处理 $TOTAL_DIRS 个子目录"

    for container_dir in $(find . -maxdepth 1 -type d -not -path . -exec test -f {}/docker-compose.yml \; -print | sort); do
        ((CURRENT_DIR++))
        container_dir=${container_dir#./}
        echo -e "\n处理目录 $container_dir ($CURRENT_DIR/$TOTAL_DIRS)"

        if ! check_compose_file "$container_dir"; then
            continue
        fi

        local compose_file="$container_dir/docker-compose.yml"
        local project_name=$(basename "$container_dir")
        services=$(docker-compose -f "$compose_file" config --services 2>/dev/null)
        if [[ -z "$services" ]]; then
            echo "警告：无法获取 $container_dir 的服务列表"
            continue
        fi
        
        debug "发现服务：$services"
        
        while IFS= read -r service; do
            [[ -z "$service" ]] && continue
            
            debug "处理服务：$service"
            
            image=$(extract_image_from_compose "$compose_file" "$service")
            
            if [[ -n "$image" ]]; then
                if [[ ! "$image" =~ : ]]; then
                    image="$image:latest"
                fi
                
                IMAGE_MAP["$image"]+="$container_dir,"
                SERVICE_IMAGE_MAP["$container_dir:$service"]="$image"
                debug "服务 $service 使用镜像 $image"

                container=$(get_container_name "$compose_file" "$service" "$project_name")
                if [[ -n "$container" ]]; then
                    debug "找到容器名称：$container"
                    
                    if [ "$DEBUG" = true ]; then
                        get_container_detailed_status "$container"
                    fi
                    
                    if is_container_running "$container"; then
                        IMAGE_MAP["$image-running"]+="$container,"
                        echo "容器 $container 正在运行"
                    else
                        IMAGE_MAP["$image-not-running"]+="$container,"
                        echo "容器 $container 未运行"
                    fi
                else
                    echo "警告：服务 $service 未找到对应容器"
                fi
            else
                echo "警告：服务 $service 未找到镜像信息"
            fi
        done <<< "$services"
    done

    if [ ${#INVALID_COMPOSE_FILES[@]} -gt 0 ]; then
        echo -e "\n以下 docker-compose 文件无效："
        for file in "${INVALID_COMPOSE_FILES[@]}"; do
            echo "- $file"
        done
    else
        echo -e "\n所有 docker-compose 文件均有效"
    fi

    echo -e "\n发现以下镜像："
    total_images=0
    running_images=0
    not_running_images=0
    for image in "${!IMAGE_MAP[@]}"; do
        if [[ ! "$image" =~ -running$ && ! "$image" =~ -not-running$ ]]; then
            echo "- $image (使用目录：${IMAGE_MAP[$image]})"
            ((total_images++))
            if [ -n "${IMAGE_MAP[$image-running]}" ]; then
                ((running_images++))
            fi
            if [ -n "${IMAGE_MAP[$image-not-running]}" ]; then
                ((not_running_images++))
            fi
        fi
    done
    echo "总计镜像数：$total_images"
    echo "运行中的镜像数：$running_images"
    echo "未运行的镜像数：$not_running_images"
}

# 函数：更新镜像和容器
update_images_and_containers() {
    echo -e "\n检查镜像更新..."
    total_images_to_update=0
    for image in "${!IMAGE_MAP[@]}"; do
        if [[ ! "$image" =~ -running$ && ! "$image" =~ -not-running$ ]]; then
            ((total_images_to_update++))
        fi
    done
    current_image=0
    declare -A DIRS_TO_UPDATE
    declare -A SERVICES_TO_UPDATE

    for image in "${!IMAGE_MAP[@]}"; do
        if [[ ! "$image" =~ -running$ && ! "$image" =~ -not-running$ ]]; then
            ((current_image++))
            echo -e "\n检查镜像 $image ($current_image/$total_images_to_update)"
            
            if [ -n "${IMAGE_MAP[$image-running]}" ]; then
                if check_image_update "$image"; then
                    echo "需要更新镜像：$image"
                    for key in "${!SERVICE_IMAGE_MAP[@]}"; do
                        if [[ "${SERVICE_IMAGE_MAP[$key]}" == "$image" ]]; then
                            local dir_service="$key"
                            local dir="${dir_service%:*}"
                            local service="${dir_service#*:}"
                            DIRS_TO_UPDATE["$dir"]=1
                            SERVICES_TO_UPDATE["$dir_service"]="$image"
                            debug "标记目录 $dir 的服务 $service 需要更新"
                        fi
                    done
                else
                    echo "镜像 $image 无需更新，跳过"
                fi
            else
                echo "提示：镜像 $image 无运行容器，跳过更新"
            fi
        fi
    done

    echo -e "\n需要更新的镜像数：${#UPDATED_IMAGES[@]}"
    if [ ${#UPDATED_IMAGES[@]} -eq 0 ]; then
        echo "所有镜像已是最新版本，无需更新"
        return
    fi

    echo -e "\n需要更新的目录："
    for dir in "${!DIRS_TO_UPDATE[@]}"; do
        echo "- $dir"
        for key in "${!SERVICES_TO_UPDATE[@]}"; do
            if [[ "$key" =~ ^$dir: ]]; then
                local service="${key#*:}"
                local image="${SERVICES_TO_UPDATE[$key]}"
                echo "  └── 服务 $service (镜像: $image)"
            fi
        done
    done

    echo -e "\n开始更新容器..."
    total_dirs_to_update=${#DIRS_TO_UPDATE[@]}
    current_dir=0
    
    for container_dir in "${!DIRS_TO_UPDATE[@]}"; do
        ((current_dir++))
        local compose_file="$container_dir/docker-compose.yml"
        if [ ! -f "$compose_file" ]; then
            echo "错误：目录 $container_dir 中未找到 docker-compose.yml"
            continue
        fi
        if ! check_compose_file "$container_dir"; then
            continue
        fi

        local project_name=$(basename "$container_dir")
        echo -e "\n更新目录 $container_dir ($current_dir/$total_dirs_to_update)"
        
        local services_to_pull=""
        for key in "${!SERVICES_TO_UPDATE[@]}"; do
            if [[ "$key" =~ ^$container_dir: ]]; then
                local service="${key#*:}"
                services_to_pull="$services_to_pull $service"
            fi
        done
        
        if [[ -n "$services_to_pull" ]]; then
            echo "需要更新的服务：$services_to_pull"
            
            for service in $services_to_pull; do
                local image="${SERVICE_IMAGE_MAP[$container_dir:$service]}"
                if [[ " ${UPDATED_IMAGES[*]} " =~ " $image " ]]; then
                    echo "正在拉取服务 $service 的镜像 ($image)..."
                    if ! retry docker-compose -f "$compose_file" -p "$project_name" pull "$service"; then
                        echo "错误：服务 $service 的镜像拉取失败"
                        continue
                    fi
                else
                    echo "服务 $service 的镜像 ($image) 无需更新，跳过拉取"
                fi
            done
            
            echo "正在重启容器..."
            if retry docker-compose -f "$compose_file" -p "$project_name" up -d; then
                echo "成功：目录 $container_dir 的容器已更新"
            else
                echo "错误：目录 $container_dir 的容器重启失败"
            fi
        else
            echo "警告：目录 $container_dir 未找到需要更新的服务"
        fi
    done
    
    echo -e "\n跳过的目录（无需更新）："
    for container_dir in $(find . -maxdepth 1 -type d -not -path . -exec test -f {}/docker-compose.yml \; -print | sort); do
        container_dir=${container_dir#./}
        if [[ -z "${DIRS_TO_UPDATE[$container_dir]}" ]]; then
            echo "- $container_dir（所有镜像已是最新版本）"
        fi
    done
}

# 函数：清理旧镜像
cleanup_old_images() {
    echo -e "\n开始清理旧的 Docker 镜像..."
    before_usage=$(get_disk_usage)

    total_deletable=0
    total_non_deletable=0

    if [ ${#UPDATED_IMAGES[@]} -eq 0 ]; then
        echo "没有镜像更新，跳过历史镜像清理"
        echo "可删除的镜像数：0"
        echo "不可删除的镜像数：0"
        echo "正在清理悬空镜像..."
        docker image prune -f
        after_usage=$(get_disk_usage)
        if command -v bc >/dev/null 2>&1; then
            saved_space=$(bc <<< "$before_usage - $after_usage" 2>/dev/null || echo 0)
        else
            saved_space=$(awk "BEGIN {printf \"%.2f\", $before_usage - $after_usage}")
        fi
        echo "镜像清理完成，节省空间：${saved_space:-0} MB"
        return
    fi

    for image in "${UPDATED_IMAGES[@]}"; do
        repo=$(echo "$image" | sed 's/:.*$//')
        debug "检查镜像 $image 的历史版本（存储库：$repo）"

        old_images=$(docker images --format "{{.Repository}}:{{.Tag}} {{.ID}}" --filter reference="$repo" | grep -v "$image")
        if [ -z "$old_images" ]; then
            debug "镜像 $image 无历史版本"
            continue
        fi

        while read -r old_image_info; do
            [[ -z "$old_image_info" ]] && continue
            old_image=$(echo "$old_image_info" | awk '{print $1}')
            old_image_id=$(echo "$old_image_info" | awk '{print $2}')

            if [ -n "$(docker ps -a --filter ancestor="$old_image" -q)" ]; then
                ((total_non_deletable++))
                echo "提示：历史镜像 $old_image (ID: $old_image_id) 正在使用，跳过删除"
                debug "使用的容器：$(docker ps -a --filter ancestor="$old_image" --format '{{.Names}}')"
            else
                ((total_deletable++))
                echo "正在删除未使用的历史镜像：$old_image (ID: $old_image_id)"
                if docker rmi -f "$old_image_id" >/dev/null 2>&1; then
                    debug "成功删除历史镜像 $old_image"
                else
                    echo "警告：删除历史镜像 $old_image 失败，可能被其他容器使用"
                    debug "删除失败，可能被其他容器使用"
                fi
            fi
        done <<< "$old_images"
    done

    echo -e "\n可删除的镜像数：$total_deletable"
    echo "不可删除的镜像数：$total_non_deletable"

    echo "正在清理悬空镜像..."
    docker image prune -f

    after_usage=$(get_disk_usage)
    if command -v bc >/dev/null 2>&1; then
        saved_space=$(bc <<< "$before_usage - $after_usage" 2>/dev/null || echo 0)
    else
        saved_space=$(awk "BEGIN {printf \"%.2f\", $before_usage - $after_usage}")
    fi
    echo "镜像清理完成，节省空间：${saved_space:-0} MB"
}

# 主程序
echo "===== Docker 容器更新脚本 ====="
echo "工作目录：当前目录 ($PWD)"
echo "=============================="

if ! command -v docker >/dev/null 2>&1; then
    echo "错误：未找到 docker 命令"
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1; then
    echo "错误：未找到 docker-compose 命令"
    exit 1
fi

if ! command -v bc >/dev/null 2>&1; then
    echo "警告：未找到 bc 命令，空间计算可能不准确。请安装 bc（例如：sudo apt install bc）"
fi

if command -v jq >/dev/null 2>&1; then
    echo "信息：发现 jq 命令，将优先使用 JSON 解析"
    debug "jq 版本：$(jq --version 2>&1)"
else
    echo "警告：未找到 jq 命令，建议安装以提高 JSON 解析可靠性（例如：sudo apt install jq）"
fi

collect_images
update_images_and_containers
show_update_summary
cleanup_old_images

echo -e "\n===== 更新和清理完成 ====="