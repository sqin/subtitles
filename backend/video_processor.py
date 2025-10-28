"""
视频处理模块 - 截取和生成视频片段
"""
import os
import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta


TEMP_VIDEO_DIR = Path(__file__).parent / 'temp_video'
VIDEO_BASE_DIR = Path(__file__).parent.parent / 'video'
CLEANUP_AFTER_HOURS = 24  # 24小时后清理临时文件


def ensure_temp_dir():
    """确保临时目录存在"""
    TEMP_VIDEO_DIR.mkdir(exist_ok=True)
    return TEMP_VIDEO_DIR


def parse_season_episode_from_filename(filename: str) -> Optional[Tuple[int, int]]:
    """
    从文件名提取季和集数
    
    Args:
        filename: 文件名，如 "S01.01.mkv"
        
    Returns:
        (season, episode) 元组，如 (1, 1)
    """
    pattern = r'S(\d+)\.(\d+)'
    match = re.search(pattern, filename)
    
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        return (season, episode)
    
    return None


def find_video_file(season: int, episode: int) -> Optional[Path]:
    """
    根据季和集数查找视频文件
    
    Args:
        season: 季数
        episode: 集数
        
    Returns:
        视频文件路径，如果不存在则返回 None
    """
    # 文件名格式: S{season}.{episode}.mkv
    video_path = VIDEO_BASE_DIR / f'S{season:02d}.{episode:02d}.mkv'
    
    if video_path.exists():
        return video_path
    
    return None


def time_to_seconds(time_str: str) -> float:
    """
    将时间戳转换为秒数
    
    Args:
        time_str: 时间戳，如 "0:18:38.72"
        
    Returns:
        秒数，如 1118.72
    """
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds_parts = parts[2].split('.')
    seconds = int(seconds_parts[0])
    milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
    
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 100.0
    return total_seconds


def limit_file_count(max_files: int = 10):
    """限制临时文件数量，保留最新的文件"""
    temp_dir = ensure_temp_dir()
    if not temp_dir.exists():
        return
    
    # 获取所有文件及其修改时间
    files = [(f, f.stat().st_mtime) for f in temp_dir.glob('*.mp4')]
    
    # 按修改时间排序（最新的在前）
    files.sort(key=lambda x: x[1], reverse=True)
    
    # 如果文件数量超过限制，删除最早的
    if len(files) > max_files:
        files_to_delete = files[max_files:]
        for file_path, _ in files_to_delete:
            try:
                file_path.unlink()
                print(f"删除旧视频文件: {file_path.name}")
            except Exception as e:
                print(f"删除文件失败 {file_path}: {e}")


def extract_video_clip(
    season: int,
    episode: int,
    start_time: str,
    end_time: str,
    padding: float = 2.0
) -> Optional[str]:
    """
    从视频文件中截取片段
    
    Args:
        season: 季数
        episode: 集数
        start_time: 开始时间戳，如 "0:18:38.72"
        end_time: 结束时间戳，如 "0:18:40.48"
        padding: 前后额外添加的秒数，默认2秒
        
    Returns:
        生成的视频文件路径（相对于静态目录），失败返回 None
    """
    # 查找视频文件
    video_file = find_video_file(season, episode)
    if not video_file:
        return None
    
    # 转换时间戳
    start_seconds = time_to_seconds(start_time)
    end_seconds = time_to_seconds(end_time)
    
    # 添加前后缓冲时间
    start_seconds = max(0, start_seconds - padding)
    end_seconds = end_seconds + padding
    
    # 计算持续时间
    duration = end_seconds - start_seconds
    
    # 确保临时目录存在
    temp_dir = ensure_temp_dir()
    
    # 生成临时文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f's{season:02d}e{episode:02d}_{timestamp}.mp4'
    output_path = temp_dir / output_filename
    
    # 使用 ffmpeg 截取视频
    try:
        cmd = [
            'ffmpeg',
            '-i', str(video_file),
            '-ss', str(start_seconds),
            '-t', str(duration),
            '-c:v', 'libx264',           # 视频编码
            '-profile:v', 'baseline',    # H.264 baseline profile，iOS 兼容
            '-level', '3.0',             # H.264 level，iOS 兼容
            '-preset', 'fast',           # 快速编码
            '-c:a', 'aac',               # 强制转码为 AAC
            '-ar', '48000',              # 音频采样率 48kHz
            '-b:a', '192k',              # 音频比特率
            '-ac', '2',                  # 降混为立体声（iOS 不支持 5.1）
            '-movflags', '+faststart',   # 快速启动，边下载边播放
            '-y',                        # 覆盖已存在的文件
            str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0 and output_path.exists():
            # 限制文件数量
            limit_file_count(max_files=10)
            # 返回相对于静态目录的路径
            return f'temp_video/{output_filename}'
        else:
            print(f"ffmpeg 错误: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("ffmpeg 超时")
        return None
    except Exception as e:
        print(f"截取视频时出错: {e}")
        return None


def cleanup_old_files():
    """清理旧的临时文件"""
    temp_dir = ensure_temp_dir()
    if not temp_dir.exists():
        return
    
    cutoff_time = datetime.now() - timedelta(hours=CLEANUP_AFTER_HOURS)
    deleted_count = 0
    
    for file_path in temp_dir.glob('*.mp4'):
        # 获取文件修改时间
        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        if file_time < cutoff_time:
            try:
                file_path.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"删除文件失败 {file_path}: {e}")
    
    if deleted_count > 0:
        print(f"清理了 {deleted_count} 个旧视频文件")


if __name__ == '__main__':
    # 测试代码
    print("测试视频截取功能...")
    
    # 测试截取 S01E01 的视频
    result = extract_video_clip(
        season=1,
        episode=1,
        start_time='0:01:30.00',
        end_time='0:01:35.00'
    )
    
    if result:
        print(f"成功生成视频: {result}")
    else:
        print("生成视频失败")
    
    # 清理旧文件
    cleanup_old_files()

