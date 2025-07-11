# Photo and Video Time Fixer

A Python script to update EXIF/QuickTime metadata and file modification times for photos and videos based on their filenames, organizing files into categorized folders.

## Features

- **Parses Time from Filenames**: Extracts timestamps from various filename formats (e.g., `IMG_20160408_201545.jpg`, `20200214_150140525_iOS.heic`, `IMG20150812205222.jpg`).
- **Updates Metadata**:
  - Updates EXIF for `.jpg`, `.jpeg` files using `piexif`.
  - Updates QuickTime metadata for `.mov`, `.mp4`, and `.heic` files using `exiftool`.
  - Updates file modification times for all supported formats.
- **Skips Unchanged Files**:
  - Skips files where filename time matches EXIF/QuickTime and file modification time.
  - Skips files with valid EXIF/QuickTime time even if the filename lacks a timestamp (e.g., `IMG_3192.JPG`).
- **Organizes Files**:
  - `exif_and_filetime_updated`: Files with updated EXIF/QuickTime and file time.
  - `filetime_only_updated`: Files with only file time updated (e.g., `.png`, `.gif`, or failed metadata updates).
  - `unprocessed_files`: Files with no parsable filename time, EXIF, or file time.
- **Progress Bar**: Displays real-time progress with total files, processed files, remaining files, and percentage (e.g., `Processing: 500/1244 photos (744 remaining, 40.19%)`).
- **Dry Run Mode**: Preview changes without modifying or moving files.

## Supported Filename Formats

1. `YYYY-MM-DD HHMMSS` (e.g., `2015-03-25 115355.jpg`)
2. `YYYYMMDD_HHMMSS...` (e.g., `20200214_150140525_iOS.jpg`)
3. `IMG_YYYYMMDD_HHMMSS` (e.g., `IMG_20160408_201545.jpg`)
4. `Screenshot_YYYY-MM-DD-HH-MM-SS` (e.g., `Screenshot_2015-11-21-22-50-58.png`)
5. `Screenshot_YYYYMMDD-HHMMSS` (e.g., `Screenshot_20160321-222949.png`)
6. `YY-MM-DD` (e.g., `19-05-16-xxx.jpg`, assumes 2000-2099)
7. `QQ图片YYYYMMDDHHMMSS` (e.g., `QQ图片20150815155353.jpg`)
8. `IMGYYYYMMDDHHMMSS` (e.g., `IMG20150812205222.jpg`)

## Supported File Formats

- Photos: `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`, `.heic`, `.gif`
- Videos: `.mov`, `.mp4`

## Requirements

- Python 3.6+
- Dependencies:
  - `pillow`: For handling image files.
  - `piexif`: For updating EXIF data in `.jpg`/`.jpeg`.
  - `pillow-heif`: For supporting `.heic` files.
  - `tqdm`: For progress bar display.
  - `exiftool`: For updating `.heic`, `.mov`, `.mp4` metadata.

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install pillow piexif pillow-heif tqdm
   ```

2. **Install `exiftool`**:
   - On macOS:
     ```bash
     brew install exiftool
     ```
   - On Linux:
     ```bash
     sudo apt-get install libimage-exiftool-perl
     ```
   - On Windows: Download and install from [ExifTool website](https://exiftool.org/).

3. **Clone the repository**:
   ```bash
   git clone https://github.com/<your-username>/<your-repo-name>.git
   cd <your-repo-name>
   ```

## Usage

1. **Edit the script**:
   - Open `fix_photo_time.py`.
   - Update the `photo_directory` variable in the `main()` function to your photos/videos directory:
     ```python
     photo_directory = "/path/to/your/photos"
     ```

2. **Run in dry-run mode** (preview changes without modifying/moving files):
   ```bash
   python3 fix_photo_time.py
   ```

3. **Run in actual mode** (apply changes and move files):
   - Uncomment the actual mode section in the `main()` function:
     ```python
     print("\n=== 实际修改模式 ===")
     process_photos(photo_directory, dry_run=False)
     ```
   - Run the script:
     ```bash
     python3 fix_photo_time.py
     ```

4. **Backup your files** before running in actual mode to prevent data loss.

## Output Folders

Files are moved to subfolders in the input directory:
- `exif_and_filetime_updated`: Files with updated EXIF/QuickTime and file modification time.
- `filetime_only_updated`: Files with only file modification time updated (e.g., `.png`, `.gif`, or failed metadata updates).
- `unprocessed_files`: Files with no parsable time from filename, EXIF, or file system.

## Example Output

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

## Notes

- **File Conflicts**: If a file with the same name exists in the target folder, moving may fail. Ensure target folders (`exif_and_filetime_updated`, etc.) are empty or modify the script to handle conflicts (e.g., rename files).
- **Permissions**: Ensure write permissions for the input directory:
  ```bash
  ls -l /path/to/your/photos
  ```
- **HEIC Issues**: If `.heic` metadata updates fail, verify with:
  ```bash
  exiftool -DateTimeOriginal="2019:01:26 15:01:22" /path/to/file.heic
  ```
- **Performance**: Processing large directories may be slow due to EXIF/QuickTime checks. The progress bar provides real-time feedback.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for suggestions/bug reports.

## Contact

For questions, contact [<your-username>] on GitHub.