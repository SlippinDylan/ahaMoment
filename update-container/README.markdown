# Docker Compose Update Script

## 概述 (Overview)

这是一个用于管理和更新 Docker Compose 环境的 Bash 脚本。它会扫描指定目录下的 `docker-compose.yml` 文件，提取所有服务的镜像，检查是否有更新，自动拉取最新镜像，重启相关容器，并清理未使用的旧镜像。该脚本旨在简化 Docker 容器的批量更新流程，特别适合管理多个 Docker Compose 项目。

This is a Bash script designed to manage and update Docker Compose environments. It scans `docker-compose.yml` files in a specified directory, extracts images for all services, checks for updates, pulls the latest images, restarts containers, and cleans up unused old images. The script simplifies the process of updating multiple Docker Compose projects in bulk.

---

## 功能 (Features)

- **扫描和提取镜像**：自动扫描当前目录下所有子目录中的 `docker-compose.yml` 文件，提取每个服务的镜像名称。如果镜像未指定标签（如 `postgres`），自动视为 `latest`（如 `postgres:latest`）。
- **检查镜像更新**：检查每个镜像是否有更新，仅针对有运行容器的镜像执行更新检查，避免不必要的拉取操作。
- **更新容器**：对需要更新的镜像，执行 `docker-compose pull` 和 `docker-compose up -d`，确保容器使用最新镜像。
- **清理旧镜像**：仅清理已更新的镜像的历史版本，跳过未更新镜像，保留运行中的镜像。
- **调试支持**：支持调试模式（默认开启），提供详细日志，便于排查问题。
- **健壮性**：支持多种容器名称匹配方式，兼容不同 Docker Compose 版本和命名模式。

- **Scan and Extract Images**: Automatically scans `docker-compose.yml` files in subdirectories of the current directory and extracts image names for each service. If an image lacks a tag (e.g., `postgres`), it is treated as `latest` (e.g., `postgres:latest`).
- **Check for Updates**: Checks for updates only for images associated with running containers, avoiding unnecessary pull operations.
- **Update Containers**: For images that need updates, runs `docker-compose pull` and `docker-compose up -d` to ensure containers use the latest images.
- **Clean Up Old Images**: Cleans up only the historical versions of updated images, skips non-updated images, and preserves images used by running containers.
- **Debugging Support**: Includes a debug mode (enabled by default) with detailed logs for troubleshooting.
- **Robustness**: Supports multiple container name matching methods, compatible with different Docker Compose versions and naming conventions.

---

## 前提条件 (Prerequisites)

运行脚本前，请确保以下工具已安装：

Before running the script, ensure the following tools are installed:

- **Docker**: 容器运行时。
  - 安装命令 (Ubuntu/Debian)：
    ```bash
    sudo apt update && sudo apt install -y docker.io
    ```
  - 验证：
    ```bash
    docker --version
    ```

- **Docker Compose**: 用于解析 `docker-compose.yml` 文件。
  - 安装命令 (Ubuntu/Debian)：
    ```bash
    sudo apt update && sudo apt install -y docker-compose
    ```
  - 验证：
    ```bash
    docker-compose --version
    ```

- **jq** (推荐)：用于解析 JSON 格式的 `docker-compose config` 输出，提高镜像提取可靠性。
  - 安装命令 (Ubuntu/Debian)：
    ```bash
    sudo apt update && sudo apt install -y jq
    ```
  - 验证：
    ```bash
    jq --version
    ```

- **bc** (推荐)：用于计算镜像占用空间。
  - 安装命令 (Ubuntu/Debian)：
    ```bash
    sudo apt update && sudo apt install -y bc
    ```
  - 验证：
    ```bash
    bc --version
    ```

**注意**：`jq` 和 `bc` 是可选依赖，但建议安装以提高脚本的可靠性和准确性。如果未安装，脚本会使用 `awk` 回退逻辑，可能降低性能。

**Note**: `jq` and `bc` are optional dependencies but recommended for improved reliability and accuracy. If not installed, the script falls back to `awk` logic, which may be less performant.

---

## 目录结构 (Directory Structure)

脚本假定你的 Docker Compose 项目组织如下：

The script assumes your Docker Compose projects are organized as follows:

```
/path/to/docker/
├── filebrowser/
│   └── docker-compose.yml
├── portainer/
│   └── docker-compose.yml
```

- 每个子目录（如 `authentik`, `ddns-go`）包含一个 `docker-compose.yml` 文件。
- 脚本会扫描当前目录（`.`）下的所有子目录，查找 `docker-compose.yml` 文件。
- 如果 `docker-compose.yml` 中的镜像未指定标签（如 `postgres`），脚本会自动将其视为 `latest`（如 `postgres:latest`）。

- Each subdirectory (e.g., `authentik`, `ddns-go`) contains a `docker-compose.yml` file.
- The script scans all subdirectories in the current directory (`.`) for `docker-compose.yml` files.
- If an image in `docker-compose.yml` lacks a tag (e.g., `postgres`), the script treats it as `latest` (e.g., `postgres:latest`).

**示例 docker-compose.yml** (Example):

```yaml
version: '3'
services:
  postgresql:
    image: postgres  # 自动视为 postgres:latest
    container_name: authentik_postgresql
  redis:
    image: redis:alpine
  server:
    image: ghcr.io/goauthentik/server:latest
```

---

## 使用方法 (Usage)

1. **克隆仓库** (Clone the Repository):
   ```bash
   git clone https://github.com/your-repo/docker-compose-update.git
   cd docker-compose-update
   ```

2. **保存脚本** (Save the Script):
   将脚本保存为 `update_container.sh`，并确保其具有执行权限：
   Save the script as `update_container.sh` and ensure it is executable:
   ```bash
   chmod +x update_container.sh
   ```

3. **运行脚本** (Run the Script):
   - 默认运行（启用调试模式，输出详细日志）：
     Run with debug mode enabled (default, outputs detailed logs):
     ```bash
     ./update_container.sh
     ```
   - 禁用调试模式（减少日志输出）：
     Run with debug mode disabled (less verbose output):
     ```bash
     ./update_container.sh --no-debug
     ```

4. **查看输出** (View Output):
   - 脚本会输出以下信息：
     - 扫描的目录和发现的镜像。
     - 每个镜像的更新状态（是否需要更新）。
     - 需要更新的目录和服务。
     - 容器重启结果。
     - 清理的旧镜像和节省的磁盘空间。
   - 建议将输出保存到日志文件以便排查问题：
     Save output to a log file for troubleshooting:
     ```bash
     ./update_container.sh > update.log 2>&1
     ```

---

## 脚本流程 (Script Workflow)

1. **扫描目录**：扫描当前目录下的所有子目录，查找 `docker-compose.yml` 文件。
2. **提取镜像**：使用 `jq`（优先）或 `awk` 解析 `docker-compose.yml`，提取每个服务的镜像名称。如果镜像未指定标签，自动添加 `:latest`。
3. **检查容器状态**：检查每个服务对应的容器是否运行，支持多种容器名称匹配方式。
4. **检查镜像更新**：仅对有运行容器的镜像执行更新检查，优先使用 `skopeo`（如果安装）比较镜像 digest，否则使用 `docker pull`。
5. **更新容器**：对需要更新的镜像，执行 `docker-compose pull` 和 `docker-compose up -d`，仅更新相关服务。
6. **清理旧镜像**：仅清理已更新的镜像的历史版本，跳过未更新镜像和运行中的镜像。
7. **输出摘要**：显示更新的镜像数、目录数、节省的磁盘空间等。

1. **Scan Directories**: Scans all subdirectories in the current directory for `docker-compose.yml` files.
2. **Extract Images**: Uses `jq` (preferred) or `awk` to parse `docker-compose.yml` and extract image names. Adds `:latest` to untagged images.
3. **Check Container Status**: Checks if containers for each service are running, using multiple name-matching methods.
4. **Check Image Updates**: Checks for updates only for images with running containers, using `skopeo` (if available) for digest comparison or `docker pull`.
5. **Update Containers**: For updated images, runs `docker-compose pull` and `docker-compose up -d` for relevant services.
6. **Clean Up Old Images**: Cleans only historical versions of updated images, skipping non-updated and running images.
7. **Output Summary**: Displays the number of updated images, directories, and disk space saved.

---

## 调试和故障排查 (Debugging and Troubleshooting)

- **启用调试模式**：默认开启，输出详细日志（如镜像提取、容器状态）。使用 `--no-debug` 禁用。
- **检查依赖**：确保 `docker`, `docker-compose`, `jq`, 和 `bc` 已安装。
- **验证镜像提取**：
  ```bash
  docker-compose -f authentik/docker-compose.yml config --format json | jq -r '.services.postgresql.image'
  ```
  预期输出：`postgres:latest`（或具体镜像，如 `docker.io/library/postgres:16-alpine`）。
- **检查容器状态**：
  ```bash
  docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
  ```
- **查看日志**：检查 `update.log` 中的错误信息，确认镜像提取或更新失败的原因。

- **Enable Debug Mode**: Enabled by default, outputs detailed logs (e.g., image extraction, container status). Use `--no-debug` to disable.
- **Check Dependencies**: Ensure `docker`, `docker-compose`, `jq`, and `bc` are installed.
- **Verify Image Extraction**:
  ```bash
  docker-compose -f authentik/docker-compose.yml config --format json | jq -r '.services.postgresql.image'
  ```
  Expected output: `postgres:latest` (or specific image, e.g., `docker.io/library/postgres:16-alpine`).
- **Check Container Status**:
  ```bash
  docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
  ```
- **Review Logs**: Check `update.log` for errors related to image extraction or updates.

---

## 许可证 (License)

本项目采用 MIT 许可证。详情见 [MIT License](https://github.com/SlippinDylan/ahaMoment/tree/master/LICENSE.md) 文件。

This project is licensed under the MIT License. See the [MIT License](https://github.com/SlippinDylan/ahaMoment/tree/master/LICENSE.md) file for details.