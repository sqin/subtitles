"""
音频处理模块 - 截取和生成音频片段
"""
import os
import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple
import tempfile
import shutil
from datetime import datetime, timedelta


TEMP_AUDIO_DIR = Path(__file__).parent / 'temp_audio'
AUDIO_BASE_DIR = Path(__file__).parent.parent / 'audio'
CLEANUP_AFTER_HOURS = 24  # 24小时后清理临时文件


def ensure_temp_dir():
    """确保临时目录存在"""
    TEMP_AUDIO_DIR.mkdir(exist_ok=True)
    return TEMP_AUDIO_DIR


def parse_season_episode_from_filename(filename: str) -> Optional[Tuple[int, int]]:
    """
    从文件名提取季和集数
    
    Args:
        filename: 文件名，如 "小谢尔顿-S02E03-音频.mp3" 或 "小谢尔顿-S02E03.mp3"
        
    Returns:
        (season, episode) 元组，如 (2, 3)
    """
    pattern = r'S(\d+)E(\d+)'
    match = re.search(pattern, filename)
    
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        return (season, episode)
    
    return None


def find_audio_file(season: int, episode: int) -> Optional[Path]:
    """
    根据季和集数查找音频文件
    
    Args:
        season: 季数
        episode: 集数
        
    Returns:
        音频文件路径，如果不存在则返回 None
    """
    # 尝试两种可能的路径
    possible_paths = [
        AUDIO_BASE_DIR / f'音频-S{season:02d}' / f'小谢尔顿-S{season:02d}E{episode:02d}-音频.mp3',
        AUDIO_BASE_DIR / f'音频-S{season:02d}' / f'小谢尔顿-S{season:02d}E{episode:02d}.mp3',
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None


def limit_file_count(max_files: int = 10):
    """限制临时文件数量，保留最新的文件"""
    temp_dir = ensure_temp_dir()
    if not temp_dir.exists():
        return
    
    # 获取所有文件及其修改时间
    files = [(f, f.stat().st_mtime) for f in temp_dir.glob('*.mp3')]
    
    # 按修改时间排序（最新的在前）
    files.sort(key=lambda x: x[1], reverse=True)
    
    # 如果文件数量超过限制，删除最早的
    if len(files) > max_files:
        files_to_delete = files[max_files:]
        for file_path, _ in files_to_delete:
            try:
                file_path.unlink()
                print(f"删除旧文件: {file_path.name}")
            except Exception as e:
                print(f"删除文件失败 {file_path}: {e}")


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


def extract_audio_clip(
    season: int,
    episode: int,
    start_time: str,
    end_time: str,
    padding: float = 2.0
) -> Optional[str]:
    """
    从音频文件中截取片段
    
    Args:
        season: 季数
        episode: 集数
        start_time: 开始时间戳，如 "0:18:38.72"
        end_time: 结束时间戳，如 "0:18:40.48"
        padding: 前后额外添加的秒数，默认2秒
        
    Returns:
        生成的音频文件路径（相对于静态目录），失败返回 None
    """
    # 查找音频文件
    audio_file = find_audio_file(season, episode)
    if not audio_file:
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
    output_filename = f's{season:02d}e{episode:02d}_{timestamp}.mp3'
    output_path = temp_dir / output_filename
    
    # 使用 ffmpeg 截取音频
    try:
        cmd = [
            'ffmpeg',
            '-i', str(audio_file),
            '-ss', str(start_seconds),
            '-t', str(duration),
            '-acodec', 'copy',  # 直接复制音频流，不做重新编码
            '-y',  # 覆盖已存在的文件
            str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and output_path.exists():
            # 限制文件数量
            limit_file_count(max_files=10)
            # 返回相对于静态目录的路径
            return f'temp_audio/{output_filename}'
        else:
            print(f"ffmpeg 错误: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("ffmpeg 超时")
        return None
    except Exception as e:
        print(f"截取音频时出错: {e}")
        return None


def cleanup_old_files():
    """清理旧的临时文件"""
    temp_dir = ensure_temp_dir()
    if not temp_dir.exists():
        return
    
    cutoff_time = datetime.now() - timedelta(hours=CLEANUP_AFTER_HOURS)
    deleted_count = 0
    
    for file_path in temp_dir.glob('*.mp3'):
        # 获取文件修改时间
        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        if file_time < cutoff_time:
            try:
                file_path.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"删除文件失败 {file_path}: {e}")
    
    if deleted_count > 0:
        print(f"清理了 {deleted_count} 个旧文件")


if __name__ == '__main__':
    # 测试代码
    print("测试音频截取功能...")
    
    # 测试截取 S02E03 的音频
    result = extract_audio_clip(
        season=2,
        episode=3,
        start_time='0:18:38.72',
        end_time='0:18:40.48'
    )
    
    if result:
        print(f"成功生成音频: {result}")
    else:
        print("生成音频失败")
    
    # 清理旧文件
    cleanup_old_files()

