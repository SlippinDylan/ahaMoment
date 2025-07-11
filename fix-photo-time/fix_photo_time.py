#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import datetime
import subprocess
import shutil
from pathlib import Path
import piexif
from PIL import Image
import pillow_heif
import tqdm

def parse_filename_datetime(filename, file_path):
    """
    从文件名中解析时间信息
    支持格式: 
    1. YYYY-MM-DD HHMMSS (如: 2015-03-25 115355.jpg)
    2. YYYYMMDD_HHMMSS... (如: 20200214_150140525_iOS.jpg)
    3. IMG_YYYYMMDD_HHMMSS (如: IMG_20160408_201545.jpg)
    4. Screenshot_YYYY-MM-DD-HH-MM-SS (如: Screenshot_2015-11-21-22-50-58.png)
    5. Screenshot_YYYYMMDD-HHMMSS (如: Screenshot_20160321-222949.png)
    6. YY-MM-DD (如: 19-05-16-8e40504419249f1087c216e30242a984__c0_30_960_960__w960_h1280.jpg)
    7. QQ图片YYYYMMDDHHMMSS (如: QQ图片20150815155353.jpg)
    8. IMGYYYYMMDDHHMMSS (如: IMG20150812205222.jpg)
    """
    file_ext = os.path.splitext(filename)[1].lower()

    # 模式1: YYYY-MM-DD HHMMSS
    pattern1 = r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2})(\d{2})(\d{2})'
    match1 = re.search(pattern1, filename)
    
    if match1:
        year, month, day, hour, minute, second = match1.groups()
        try:
            dt = datetime.datetime(
                int(year), int(month), int(day),
                int(hour), int(minute), int(second)
            )
            return dt
        except ValueError as e:
            print(f"时间格式错误: {filename} - {e}")
            return None
    
    # 模式2: YYYYMMDD_HHMMSS... (如: 20200214_150140525_iOS.jpg)
    pattern2 = r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})'
    match2 = re.search(pattern2, filename)
    
    if match2:
        year, month, day, hour, minute, second = match2.groups()
        try:
            dt = datetime.datetime(
                int(year), int(month), int(day),
                int(hour), int(minute), int(second)
            )
            return dt
        except ValueError as e:
            print(f"时间格式错误: {filename} - {e}")
            return None
    
    # 模式3: IMG_YYYYMMDD_HHMMSS (如: IMG_20160408_201545.jpg)
    pattern3 = r'IMG_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})'
    match3 = re.search(pattern3, filename)
    
    if match3:
        year, month, day, hour, minute, second = match3.groups()
        try:
            dt = datetime.datetime(
                int(year), int(month), int(day),
                int(hour), int(minute), int(second)
            )
            return dt
        except ValueError as e:
            print(f"时间格式错误: {filename} - {e}")
            return None
    
    # 模式4: Screenshot_YYYY-MM-DD-HH-MM-SS (如: Screenshot_2015-11-21-22-50-58.png)
    pattern4 = r'Screenshot_(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})'
    match4 = re.search(pattern4, filename)
    
    if match4:
        year, month, day, hour, minute, second = match4.groups()
        try:
            dt = datetime.datetime(
                int(year), int(month), int(day),
                int(hour), int(minute), int(second)
            )
            return dt
        except ValueError as e:
            print(f"时间格式错误: {filename} - {e}")
            return None
    
    # 模式5: Screenshot_YYYYMMDD-HHMMSS (如: Screenshot_20160321-222949.png)
    pattern5 = r'Screenshot_(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})'
    match5 = re.search(pattern5, filename)
    
    if match5:
        year, month, day, hour, minute, second = match5.groups()
        try:
            dt = datetime.datetime(
                int(year), int(month), int(day),
                int(hour), int(minute), int(second)
            )
            return dt
        except ValueError as e:
            print(f"时间格式错误: {filename} - {e}")
            return None
    
    # 模式6: YY-MM-DD (如: 19-05-16-8e40504419249f1087c216e30242a984__c0_30_960_960__w960_h1280.jpg)
    pattern6 = r'^(\d{2})-(\d{2})-(\d{2})[-_]'
    match6 = re.search(pattern6, filename)
    
    if match6:
        year, month, day = match6.groups()
        try:
            # 假设 00-99 表示 2000-2099
            year = int(year) + 2000
            dt = datetime.datetime(year, int(month), int(day))
            return dt
        except ValueError as e:
            print(f"时间格式错误: {filename} - {e}")
            return None
    
    # 模式7: QQ图片YYYYMMDDHHMMSS (如: QQ图片20150815155353.jpg)
    pattern7 = r'QQ图片(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})'
    match7 = re.search(pattern7, filename)
    
    if match7:
        year, month, day, hour, minute, second = match7.groups()
        try:
            dt = datetime.datetime(
                int(year), int(month), int(day),
                int(hour), int(minute), int(second)
            )
            return dt
        except ValueError as e:
            print(f"时间格式错误: {filename} - {e}")
            return None

    # 模式8: IMGYYYYMMDDHHMMSS (如: IMG20150812205222.jpg)
    pattern8 = r'IMG(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})'
    match8 = re.search(pattern8, filename)
    
    if match8:
        year, month, day, hour, minute, second = match8.groups()
        try:
            dt = datetime.datetime(
                int(year), int(month), int(day),
                int(hour), int(minute), int(second)
            )
            return dt
        except ValueError as e:
            print(f"时间格式错误: {filename} - {e}")
            return None

    return None

def get_metadata_datetime(file_path):
    """
    获取文件的 EXIF 或 QuickTime 元数据时间
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext in ['.jpg', '.jpeg', '.heic']:
        try:
            img = Image.open(file_path)
            exif_dict = piexif.load(img.info.get('exif', b''))
            time_str = exif_dict.get('Exif', {}).get(piexif.ExifIFD.DateTimeOriginal)
            if time_str:
                return datetime.datetime.strptime(time_str.decode('utf-8'), "%Y:%m:%d %H:%M:%S")
        except Exception:
            return None
    elif file_ext in ['.mov', '.mp4']:
        try:
            result = subprocess.run([
                "exiftool", "-CreationDate", "-d", "%Y:%m:%d %H:%M:%S", file_path
            ], capture_output=True, text=True, check=True)
            time_str = result.stdout.split(": ", 1)[1].strip()
            return datetime.datetime.strptime(time_str, "%Y:%m:%d %H:%M:%S")
        except Exception:
            return None
    return None

def update_mov_metadata(file_path, target_datetime):
    """
    使用 exiftool 更新 MOV、MP4 或 HEIC 文件的元数据
    """
    time_str = target_datetime.strftime("%Y:%m:%d %H:%M:%S")
    try:
        # 对于 HEIC，使用 DateTimeOriginal；对于 MOV/MP4，使用 CreationDate
        tag = "DateTimeOriginal" if os.path.splitext(file_path)[1].lower() == '.heic' else "CreationDate"
        subprocess.run([
            "exiftool",
            "-overwrite_original",
            f"-{tag}={time_str}",
            file_path
        ], check=True)
        print(f"✓ 已更新: {os.path.basename(file_path)} -> {time_str} ({tag}元数据)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠ 元数据更新失败: {os.path.basename(file_path)} - {e}")
        return False

def update_photo_times(file_path, target_datetime):
    """
    更新照片的EXIF时间信息、视频的QuickTime元数据和文件修改时间
    返回元数据更新状态以决定移动目标文件夹
    """
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        metadata_updated = False
        
        # 对于支持EXIF的格式，尝试更新EXIF数据
        if file_ext in ['.jpg', '.jpeg']:
            try:
                # 打开图片
                img = Image.open(file_path)
                
                # 获取现有的EXIF数据
                exif_dict = piexif.load(img.info.get('exif', b''))
                
                # 格式化时间字符串 (EXIF格式: "YYYY:MM:DD HH:MM:SS")
                time_str = target_datetime.strftime("%Y:%m:%d %H:%M:%S")
                
                # 确保EXIF字典有必要的键
                if '0th' not in exif_dict:
                    exif_dict['0th'] = {}
                if 'Exif' not in exif_dict:
                    exif_dict['Exif'] = {}
                
                # 更新EXIF中的时间字段
                exif_dict['0th'][piexif.ImageIFD.DateTime] = time_str
                exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = time_str
                exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = time_str
                
                # 转换为字节数据
                exif_bytes = piexif.dump(exif_dict)
                
                # 保存图片（会覆盖原文件）
                img.save(file_path, exif=exif_bytes)
                
                print(f"✓ 已更新: {os.path.basename(file_path)} -> {time_str} (EXIF + 文件时间)")
                metadata_updated = True
                
            except Exception as exif_error:
                print(f"⚠ EXIF更新失败: {os.path.basename(file_path)} - {exif_error}")
                print(f"  仅更新文件时间...")
        
        # 对于HEIC、MOV或MP4，使用 exiftool 更新元数据
        elif file_ext in ['.heic', '.mov', '.mp4']:
            if update_mov_metadata(file_path, target_datetime):
                metadata_updated = True
            else:
                print(f"  仅更新文件时间...")
        
        elif file_ext in ['.png', '.gif']:
            print(f"⚠ {file_ext.upper()}文件跳过EXIF更新: {os.path.basename(file_path)} (仅更新文件时间)")
        
        # 更新文件的修改时间和访问时间
        timestamp = target_datetime.timestamp()
        os.utime(file_path, (timestamp, timestamp))
        
        if file_ext in ['.png', '.gif', '.heic', '.mov', '.mp4']:
            print(f"✓ 已更新: {os.path.basename(file_path)} -> {target_datetime.strftime('%Y:%m:%d %H:%M:%S')} (仅文件时间)")
        
        return metadata_updated
    
    except Exception as e:
        print(f"✗ 更新失败: {os.path.basename(file_path)} - {e}")
        return False

def move_file(file_path, target_dir, dry_run):
    """
    移动文件到指定目录
    """
    if dry_run:
        print(f"[试运行] 将移动到 {target_dir.name}: {os.path.basename(file_path)}")
        return True
    try:
        dest_path = target_dir / os.path.basename(file_path)
        shutil.move(str(file_path), str(dest_path))
        print(f"已移动到 {target_dir.name}: {os.path.basename(file_path)}")
        return True
    except Exception as e:
        print(f"移动文件失败: {os.path.basename(file_path)} - {e}")
        return False

def process_photos(directory_path, dry_run=True):
    """
    处理指定目录下的所有照片和视频
    按处理结果分类移动文件到子文件夹：
    - exif_and_filetime_updated: EXIF/QuickTime元数据和文件时间更新成功
    - filetime_only_updated: 仅文件时间更新
    - unprocessed_files: 文件名、EXIF和文件时间均无法解析
    - 跳过文件名无法解析但有有效EXIF/QuickTime时间的文件
    显示动态进度条，包含总照片数、已处理数、剩余数和百分比
    
    Args:
        directory_path: 照片和视频目录路径
        dry_run: 是否为试运行模式（不实际修改文件或移动文件）
    """
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f"错误: 目录不存在 - {directory_path}")
        return
    
    # 创建分类文件夹
    exif_dir = directory / "exif_and_filetime_updated"
    filetime_dir = directory / "filetime_only_updated"
    unprocessed_dir = directory / "unprocessed_files"
    
    if not dry_run:
        for d in [exif_dir, filetime_dir, unprocessed_dir]:
            if not d.exists():
                d.mkdir()
                print(f"已创建文件夹: {d}")
    
    # 支持的图片和视频格式
    media_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.mov', '.mp4', '.heic', '.gif'}
    
    # 统计信息
    total_files = 0
    exif_updated_files = 0
    filetime_updated_files = 0
    unprocessed_files = 0
    skipped_unchanged = 0
    
    # 收集所有媒体文件
    media_files = [f for f in directory.rglob("*") if f.is_file() and f.suffix.lower() in media_extensions]
    total_files = len(media_files)
    
    print(f"开始处理目录: {directory_path}")
    print(f"模式: {'试运行' if dry_run else '实际修改'}")
    print("-" * 50)
    
    # 使用 tqdm 显示进度条
    pbar = tqdm.tqdm(total=total_files, desc="Processing", unit="photo")
    for file_path in media_files:
        # 从文件名解析时间
        target_datetime = parse_filename_datetime(file_path.name, str(file_path))
        
        if target_datetime:
            # 获取 EXIF/QuickTime 元数据时间和文件修改时间
            metadata_datetime = get_metadata_datetime(str(file_path))
            file_mtime = datetime.datetime.fromtimestamp(os.stat(file_path).st_mtime)
            
            # 检查时间是否一致（忽略秒以下精度）
            metadata_match = (
                metadata_datetime and
                metadata_datetime.replace(microsecond=0) == target_datetime.replace(microsecond=0)
            ) or (not metadata_datetime and file_path.suffix.lower() in ['.png', '.gif'])
            filetime_match = file_mtime.replace(microsecond=0) == target_datetime.replace(microsecond=0)
            
            if metadata_match and filetime_match:
                print(f"时间一致，跳过: {file_path.name} -> {target_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                skipped_unchanged += 1
            else:
                if dry_run:
                    print(f"[试运行] {file_path.name} -> {target_datetime.strftime('%Y-%m-%d %H:%M:%S')} (元数据 + 文件时间)")
                    # 假设元数据更新成功，移动到 exif_and_filetime_updated
                    move_file(file_path, exif_dir, dry_run)
                    exif_updated_files += 1
                else:
                    metadata_updated = update_photo_times(str(file_path), target_datetime)
                    if metadata_updated:
                        if move_file(file_path, exif_dir, dry_run):
                            exif_updated_files += 1
                    else:
                        if move_file(file_path, filetime_dir, dry_run):
                            filetime_updated_files += 1
        else:
            # 文件名无法解析，检查 EXIF/QuickTime 时间
            metadata_datetime = get_metadata_datetime(str(file_path))
            if metadata_datetime:
                print(f"文件名无法解析但有元数据时间，跳过: {file_path.name} -> {metadata_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                skipped_unchanged += 1
            else:
                # 回退：检查文件系统时间
                try:
                    file_mtime = datetime.datetime.fromtimestamp(os.stat(file_path).st_mtime)
                    print(f"文件名无法解析但有文件时间，跳过: {file_path.name} -> {file_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                    skipped_unchanged += 1
                except Exception as e:
                    print(f"文件名和元数据均无法解析: {file_path.name} - {e}")
                    if move_file(file_path, unprocessed_dir, dry_run):
                        unprocessed_files += 1
        
        # 更新进度条描述
        processed_count = exif_updated_files + filetime_updated_files + unprocessed_files + skipped_unchanged
        remaining = total_files - processed_count
        percentage = processed_count / total_files * 100 if total_files > 0 else 0
        pbar.set_description(f"Processing: {processed_count}/{total_files} photos ({remaining} remaining, {percentage:.2f}%)")
        pbar.update(1)
    
    pbar.close()
    
    # 输出统计信息
    print("-" * 50)
    print(f"处理完成!")
    print(f"总文件数: {total_files}")
    print(f"未处理（时间一致或有元数据/文件时间）: {skipped_unchanged}")
    print(f"{'预计' if dry_run else '成功'}更新 EXIF 和文件时间: {exif_updated_files}")
    print(f"{'预计' if dry_run else '成功'}仅更新文件时间: {filetime_updated_files}")
    print(f"{'预计' if dry_run else '已'}移动到 unprocessed_files: {unprocessed_files}")
    
    if dry_run:
        print("\n这是试运行模式，没有实际修改或移动文件。")
        print("如果结果看起来正确，请将 dry_run=False 来实际执行修改和移动。")

def main():
    """
    主函数 - 使用示例
    """
    # 修改这里的路径为你的照片和视频目录
    photo_directory = "/path/to/your/photos"
    
    # 首先试运行，检查结果
    print("=== 试运行模式 ===")
    process_photos(photo_directory, dry_run=True)
    
    # 确认无误后，取消下面的注释来实际执行
    print("\n=== 实际修改模式 ===")
    process_photos(photo_directory, dry_run=False)

if __name__ == "__main__":
    # 检查依赖库
    try:
        import piexif
        from PIL import Image
        import subprocess
        import pillow_heif
        import shutil
        import tqdm
    except ImportError as e:
        print("错误: 缺少必要的库")
        print("请先安装依赖:")
        print("pip install pillow piexif pillow-heif tqdm")
        print("并确保已安装 exiftool (例如: brew install exiftool)")
        exit(1)
    
    # 检查 exiftool 是否可用
    try:
        subprocess.run(["exiftool", "-ver"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: 未找到 exiftool")
        print("请安装 exiftool (例如: brew install exiftool)")
        exit(1)
    
    main()