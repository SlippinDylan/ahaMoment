# 照片和视频时间修正工具

一个 Python 脚本，用于根据文件名中的时间信息更新照片的 EXIF 元数据或视频的 QuickTime 元数据，并将文件按处理结果分类到子文件夹。

## 功能

- **解析文件名时间**：支持多种文件名格式提取时间（如 `IMG_20160408_201545.jpg`、`20200214_150140525_iOS.heic`、`IMG20150812205222.jpg`）。
- **更新元数据**：
  - 使用 `piexif` 更新 `.jpg`、`.jpeg` 文件的 EXIF 数据。
  - 使用 `exiftool` 更新 `.mov`、`.mp4` 和 `.heic` 文件的 QuickTime 元数据。
  - 更新所有支持格式的文件修改时间。
- **跳过无需处理的文件**：
  - 跳过文件名时间与 EXIF/QuickTime 和文件修改时间一致的文件。
  - 跳过文件名无法解析但有有效 EXIF/QuickTime 时间的文件（如 `IMG_3192.JPG`）。
- **文件分类**：
  - `exif_and_filetime_updated`：成功更新 EXIF/QuickTime 和文件时间。
  - `filetime_only_updated`：仅更新文件时间（例如 `.png`、`.gif` 或元数据更新失败）。
  - `unprocessed_files`：文件名、EXIF 和文件时间均无法解析。
- **进度条**：实时显示处理进度，包括总文件数、已处理数、剩余数和百分比（例如 `Processing: 500/1244 photos (744 remaining, 40.19%)`）。
- **试运行模式**：预览更改而不实际修改或移动文件。

## 支持的文件名格式

1. `YYYY-MM-DD HHMMSS`（如 `2015-03-25 115355.jpg`）
2. `YYYYMMDD_HHMMSS...`（如 `20200214_150140525_iOS.jpg`）
3. `IMG_YYYYMMDD_HHMMSS`（如 `IMG_20160408_201545.jpg`）
4. `Screenshot_YYYY-MM-DD-HH-MM-SS`（如 `Screenshot_2015-11-21-22-50-58.png`）
5. `Screenshot_YYYYMMDD-HHMMSS`（如 `Screenshot_20160321-222949.png`）
6. `YY-MM-DD`（如 `19-05-16-xxx.jpg`，假设 2000-2099 年）
7. `QQ图片YYYYMMDDHHMMSS`（如 `QQ图片20150815155353.jpg`）
8. `IMGYYYYMMDDHHMMSS`（如 `IMG20150812205222.jpg`）

## 支持的文件格式

- 照片：`.jpg`、`.jpeg`、`.png`、`.tiff`、`.tif`、`.heic`、`.gif`
- 视频：`.mov`、`.mp4`

## 依赖要求

- Python 3.6+
- 依赖库：
  - `pillow`：处理图像文件。
  - `piexif`：更新 `.jpg`/`.jpeg` 的 EXIF 数据。
  - `pillow-heif`：支持 `.heic` 文件。
  - `tqdm`：显示进度条。
  - `exiftool`：更新 `.heic`、`.mov`、`.mp4` 的元数据。

## 安装步骤

1. **安装 Python 依赖**：
   ```bash
   pip install pillow piexif pillow-heif tqdm
   ```

2. **安装 `exiftool`**：
   - 在 macOS 上：
     ```bash
     brew install exiftool
     ```
   - 在 Linux 上：
     ```bash
     sudo apt-get install libimage-exiftool-perl
     ```
   - 在 Windows 上：从 [ExifTool 官网](https://exiftool.org/) 下载并安装。

3. **克隆仓库**：
   ```bash
   git clone https://github.com/<你的用户名>/<你的仓库名>.git
   cd <你的仓库名>
   ```

## 使用方法

1. **编辑脚本**：
   - 打开 `fix_photo_time.py`。
   - 在 `main()` 函数中修改 `photo_directory` 为你的照片/视频目录：
     ```python
     photo_directory = "/你的照片目录路径"
     ```

2. **运行试运行模式**（预览更改，不修改或移动文件）：
   ```bash
   python3 fix_photo_time.py
   ```

3. **运行实际模式**（应用更改并移动文件）：
   - 在 `main()` 函数中取消以下注释：
     ```python
     print("\n=== 实际修改模式 ===")
     process_photos(photo_directory, dry_run=False)
     ```
   - 运行脚本：
     ```bash
     python3 fix_photo_time.py
     ```

4. **备份文件**：在运行实际模式前，备份你的照片/视频目录以防数据丢失。

## 输出文件夹

文件将被移动到输入目录下的子文件夹：
- `exif_and_filetime_updated`：成功更新 EXIF/QuickTime 和文件时间的文件。
- `filetime_only_updated`：仅更新文件时间的文件（例如 `.png`、`.gif` 或元数据更新失败）。
- `unprocessed_files`：文件名、EXIF 和文件时间均无法解析的文件。

## 示例输出

```bash
=== 试运行模式 ===
开始处理目录: /Volumes/Samsung PM971 BGA NVMe SSD/全量照片
模式: 试运行
--------------------------------------------------
文件名无法解析但有元数据时间，跳过: IMG_3192.JPG -> 2020-05-10 14:30:00
时间一致，跳过: 20190126_150122574_iOS.heic -> 2019-01-26 15:01:22
[试运行] IMG20150812205222.jpg -> 2015-08-12 20:52:22 (元数据 + 文件时间)
[试运行] 将移动到 exif_and_filetime_updated: IMG20150812205222.jpg
⚠ PNG文件跳过EXIF更新: Screenshot_20160321-222949.png (仅更新文件时间)
[试运行] 将移动到 filetime_only_updated: Screenshot_20160321-222949.png
文件名和元数据均无法解析: IMB_bOor_6875.JPG
[试运行] 将移动到 unprocessed_files: IMB_bOor_6875.JPG
Processing: 500/1244 photos (744 remaining, 40.19%): [██████████▌     ]
--------------------------------------------------
处理完成!
总文件数: 1244
未处理（时间一致或有元数据/文件时间）: 600
预计更新 EXIF 和文件时间: 400
预计仅更新文件时间: 200
预计移动到 unprocessed_files: 44
```

## 注意事项

- **文件冲突**：如果目标文件夹（`exif_and_filetime_updated` 等）已有同名文件，移动可能失败。建议清空目标文件夹，或修改脚本以处理冲突（例如重命名）。
- **权限**：确保对输入目录有写权限：
  ```bash
  ls -l /你的照片目录路径
  ```
- **HEIC 问题**：如果 `.heic` 元数据更新失败，可手动验证：
  ```bash
  exiftool -DateTimeOriginal="2019:01:26 15:01:22" /路径/文件.heic
  ```
- **性能**：处理大量文件可能较慢，因需检查 EXIF/QuickTime 元数据。进度条提供实时反馈。

## 许可证

MIT 许可证。详情见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎贡献！请提交 Pull Request 或在 GitHub 上提出 Issue 报告问题或建议。

## 联系方式

如有问题，请在 GitHub 上联系 [<你的用户名>]。