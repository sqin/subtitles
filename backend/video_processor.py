"""
视频处理模块 - 截取和生成视频片段
"""
import os
import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple, Dict, List
from datetime import datetime, timedelta
from collections import defaultdict


TEMP_VIDEO_DIR = Path(__file__).parent / 'temp_video'
# 移动硬盘路径
VIDEO_BASE_DIR = Path("/Volumes/EAGET忆捷/YoungSheldon")
CLEANUP_AFTER_HOURS = 24  # 24小时后清理临时文件


def ensure_temp_dir():
    """确保临时目录存在"""
    TEMP_VIDEO_DIR.mkdir(exist_ok=True)
    return TEMP_VIDEO_DIR


def parse_season_episode_from_filename(filename: str) -> Optional[Tuple[int, int]]:
    """
    从文件名提取季和集数
    
    支持多种格式：
    - S01.01.mkv (第1-5季格式)
    - S06E01.1080p.mp4 (第6季格式)
    - S07E01.mp4 (第7季格式)
    
    Args:
        filename: 文件名
        
    Returns:
        (season, episode) 元组，如 (1, 1)
    """
    # 匹配 S01.01 格式（第1-5季）
    pattern1 = r'S(\d+)\.(\d+)'
    match = re.search(pattern1, filename)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        return (season, episode)
    
    # 匹配 S06E01 格式（第6-7季）
    pattern2 = r'S(\d+)E(\d+)'
    match = re.search(pattern2, filename)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        return (season, episode)
    
    return None


def find_video_file(season: int, episode: int) -> Optional[Path]:
    """
    根据季和集数查找视频文件
    
    支持不同的目录结构和文件命名格式：
    - 第1-5季: 第1-5季/S{season}/S{season}.{episode}.mkv
    - 第6季: 第6季（22集全）/S06E{episode}.1080p.mp4
    - 第7季: 第7季/S07E{episode}.mp4
    
    Args:
        season: 季数
        episode: 集数
        
    Returns:
        视频文件路径，如果不存在则返回 None
    """
    # 第1-5季：在 第1-5季/S{season}/ 目录下，格式为 S{season}.{episode}.mkv
    # 注意：文件命名格式不一致：
    # - 第1-2季：S01.XX.mkv, S02.XX.mkv（带前导零）
    # - 第3-5季：S3.XX.mkv, S4.XX.mkv, S5.XX.mkv（不带前导零）
    if 1 <= season <= 5:
        season_dir = VIDEO_BASE_DIR / f'第1-5季' / f'S{season:02d}'
        
        # 先尝试带前导零的格式（第1-2季）
        video_path = season_dir / f'S{season:02d}.{episode:02d}.mkv'
        if video_path.exists():
            return video_path
        
        # 再尝试不带前导零的格式（第3-5季）
        video_path = season_dir / f'S{season}.{episode:02d}.mkv'
        if video_path.exists():
            return video_path
    
    # 第6季：在 第6季（22集全）/ 目录下，格式为 S06E{episode}.1080p.mp4
    if season == 6:
        video_path = VIDEO_BASE_DIR / f'第6季（22集全）' / f'S06E{episode:02d}.1080p.mp4'
        if video_path.exists():
            return video_path
    
    # 第7季：在 第7季/ 目录下，格式为 S07E{episode}.mp4
    if season == 7:
        video_path = VIDEO_BASE_DIR / f'第7季' / f'S07E{episode:02d}.mp4'
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
        print(f"错误: 找不到视频文件 S{season:02d}E{episode:02d}")
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
    # 根据片段长度动态调整超时时间（每10秒内容给30秒处理时间，最少120秒）
    estimated_timeout = max(120, int(duration * 3) + 60)
    
    try:
        cmd = [
            'ffmpeg',
            '-ss', str(start_seconds),  # 先定位再输入，更快
            '-i', str(video_file),
            '-t', str(duration),
            # 视频编码设置
            '-c:v', 'libx264',           # 视频编码
            '-profile:v', 'baseline',    # H.264 baseline profile，iOS 兼容
            '-level', '3.0',             # H.264 level，iOS 兼容
            '-preset', 'ultrafast',      # 使用最快编码预设，提高速度
            '-crf', '23',                # 使用 CRF 控制质量，比固定比特率更快
            '-pix_fmt', 'yuv420p',       # 确保像素格式一致，便于后续合并
            '-vsync', 'cfr',             # 恒定帧率
            # 音频编码设置
            '-c:a', 'aac',               # 强制转码为 AAC
            '-ar', '48000',              # 音频采样率 48kHz
            '-b:a', '192k',              # 音频比特率
            '-ac', '2',                  # 降混为立体声（iOS 不支持 5.1）
            # 其他设置
            '-avoid_negative_ts', 'make_zero',  # 处理负时间戳
            '-fflags', '+genpts',        # 生成PTS，确保时间戳正确
            '-movflags', '+faststart',   # 快速启动，边下载边播放
            '-y',                        # 覆盖已存在的文件
            str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=estimated_timeout
        )
        
        if result.returncode == 0 and output_path.exists():
            # 限制文件数量
            limit_file_count(max_files=10)
            # 返回相对于静态目录的路径
            return f'temp_video/{output_filename}'
        else:
            error_msg = result.stderr.split('\n')[-10:]  # 只取最后10行错误信息
            print(f"ffmpeg 错误 (S{season:02d}E{episode:02d}): {''.join(error_msg)}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"ffmpeg 超时 (S{season:02d}E{episode:02d}): 片段时长 {duration:.1f}秒，超时时间 {estimated_timeout}秒")
        return None
    except Exception as e:
        print(f"截取视频时出错 (S{season:02d}E{episode:02d}): {e}")
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


def merge_video_clips(clips: List[Dict[str, any]], padding: float = 2.0) -> Optional[str]:
    """
    合并多个视频片段成一个视频文件
    
    Args:
        clips: 视频片段列表，每个元素包含：
            - season: 季数
            - episode: 集数
            - start_time: 开始时间戳，如 "0:18:38.72"
            - end_time: 结束时间戳，如 "0:18:40.48"
        padding: 前后额外添加的秒数，默认2秒
        
    Returns:
        合并后的视频文件路径（相对于静态目录），失败返回 None
    """
    if not clips:
        return None
    
    temp_dir = ensure_temp_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 第一步：为每个片段生成临时视频文件
    clip_files = []
    failed_clips = []
    total_clips = len(clips)
    
    print(f"开始生成 {total_clips} 个视频片段...")
    
    for i, clip in enumerate(clips, 1):
        print(f"正在生成片段 {i}/{total_clips}: S{clip['season']:02d}E{clip['episode']:02d} "
              f"({clip['start_time']} - {clip['end_time']})")
        
        clip_path = extract_video_clip(
            season=clip['season'],
            episode=clip['episode'],
            start_time=clip['start_time'],
            end_time=clip['end_time'],
            padding=padding
        )
        
        if not clip_path:
            failed_info = f"S{clip['season']:02d}E{clip['episode']:02d} ({clip['start_time']} - {clip['end_time']})"
            failed_clips.append(failed_info)
            print(f"警告: 无法生成片段 {i}/{total_clips}: {failed_info}")
            continue
        
        # clip_path 是相对路径，需要转换为绝对路径
        full_clip_path = Path(__file__).parent / clip_path
        if full_clip_path.exists():
            clip_files.append(full_clip_path)
            print(f"✓ 片段 {i}/{total_clips} 生成成功")
        else:
            failed_info = f"S{clip['season']:02d}E{clip['episode']:02d} ({clip['start_time']} - {clip['end_time']})"
            failed_clips.append(failed_info)
            print(f"警告: 片段文件不存在: {full_clip_path}")
    
    if not clip_files:
        print("错误: 没有成功生成任何视频片段")
        return None
    
    success_count = len(clip_files)
    print(f"\n片段生成完成: {success_count}/{total_clips} 成功")
    if failed_clips:
        print(f"失败的片段 ({len(failed_clips)} 个):")
        for failed in failed_clips:
            print(f"  - {failed}")
    
    # 第二步：使用 filter_complex 方法合并视频（更可靠）
    output_filename = f'merged_{timestamp}.mp4'
    output_path = temp_dir / output_filename
    
    print(f"\n开始合并 {len(clip_files)} 个视频片段...")
    
    # 根据片段数量动态调整超时时间
    # 每个片段大约需要5-10秒处理时间
    merge_timeout = max(600, len(clip_files) * 10 + 120)  # 最少10分钟
    
    try:
        # 构建输入参数
        input_args = []
        for clip_file in clip_files:
            input_args.extend(['-i', str(clip_file)])
        
        # 构建 filter_complex：将所有输入的视频和音频流分别连接
        # [0:v][1:v][2:v]...concat=n=N:v=1:a=0[v]  # 连接视频流
        # [0:a][1:a][2:a]...concat=n=N:v=0:a=1[a]  # 连接音频流
        video_inputs = ''.join([f'[{i}:v]' for i in range(len(clip_files))])
        audio_inputs = ''.join([f'[{i}:a]' for i in range(len(clip_files))])
        
        filter_complex = (
            f'{video_inputs}concat=n={len(clip_files)}:v=1:a=0[v];'
            f'{audio_inputs}concat=n={len(clip_files)}:v=0:a=1[a]'
        )
        
        cmd = [
            'ffmpeg',
            *input_args,
            '-filter_complex', filter_complex,
            '-map', '[v]',  # 映射视频流
            '-map', '[a]',  # 映射音频流
            # 视频编码设置
            '-c:v', 'libx264',
            '-profile:v', 'baseline',
            '-level', '3.0',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            # 音频编码设置
            '-c:a', 'aac',
            '-ar', '48000',
            '-b:a', '192k',
            '-ac', '2',
            # 其他设置
            '-movflags', '+faststart',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=merge_timeout
        )
        
        if result.returncode == 0 and output_path.exists():
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"✓ 视频合并成功！文件大小: {file_size_mb:.2f} MB")
            # 限制文件数量
            limit_file_count(max_files=10)
            # 返回相对于静态目录的路径
            return f'temp_video/{output_filename}'
        else:
            error_msg = result.stderr.split('\n')[-20:]  # 取最后20行错误信息
            print(f"✗ ffmpeg 合并错误: {''.join(error_msg)}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"✗ ffmpeg 合并超时 (超时时间: {merge_timeout}秒)")
        return None
    except Exception as e:
        print(f"✗ 合并视频时出错: {e}")
        return None


def analyze_video_directory() -> Dict[int, Dict[str, any]]:
    """
    分析移动硬盘上的视频目录结构，用于后续合并逻辑
    
    Returns:
        字典结构：
        {
            season: {
                'episodes': [episode列表],
                'files': {
                    episode: {
                        'path': 文件路径,
                        'size': 文件大小(字节),
                        'format': 文件格式
                    }
                },
                'total_size': 总大小(字节),
                'directory': 所在目录
            }
        }
    """
    result = defaultdict(lambda: {
        'episodes': [],
        'files': {},
        'total_size': 0,
        'directory': ''
    })
    
    if not VIDEO_BASE_DIR.exists():
        print(f"警告: 视频目录不存在: {VIDEO_BASE_DIR}")
        return dict(result)
    
    # 扫描第1-5季
    season_1_5_dir = VIDEO_BASE_DIR / '第1-5季'
    if season_1_5_dir.exists():
        for season in range(1, 6):
            season_dir = season_1_5_dir / f'S{season:02d}'
            if season_dir.exists():
                result[season]['directory'] = str(season_dir)
                for video_file in season_dir.glob('*.mkv'):
                    parsed = parse_season_episode_from_filename(video_file.name)
                    if parsed and parsed[0] == season:
                        episode = parsed[1]
                        file_size = video_file.stat().st_size
                        result[season]['episodes'].append(episode)
                        result[season]['files'][episode] = {
                            'path': str(video_file),
                            'size': file_size,
                            'format': 'mkv'
                        }
                        result[season]['total_size'] += file_size
                result[season]['episodes'].sort()
    
    # 扫描第6季
    season_6_dir = VIDEO_BASE_DIR / '第6季（22集全）'
    if season_6_dir.exists():
        result[6]['directory'] = str(season_6_dir)
        for video_file in season_6_dir.glob('*.mp4'):
            parsed = parse_season_episode_from_filename(video_file.name)
            if parsed and parsed[0] == 6:
                episode = parsed[1]
                file_size = video_file.stat().st_size
                result[6]['episodes'].append(episode)
                result[6]['files'][episode] = {
                    'path': str(video_file),
                    'size': file_size,
                    'format': 'mp4'
                }
                result[6]['total_size'] += file_size
        result[6]['episodes'].sort()
    
    # 扫描第7季
    season_7_dir = VIDEO_BASE_DIR / '第7季'
    if season_7_dir.exists():
        result[7]['directory'] = str(season_7_dir)
        for video_file in season_7_dir.glob('*.mp4'):
            parsed = parse_season_episode_from_filename(video_file.name)
            if parsed and parsed[0] == 7:
                episode = parsed[1]
                file_size = video_file.stat().st_size
                result[7]['episodes'].append(episode)
                result[7]['files'][episode] = {
                    'path': str(video_file),
                    'size': file_size,
                    'format': 'mp4'
                }
                result[7]['total_size'] += file_size
        result[7]['episodes'].sort()
    
    return dict(result)


def print_directory_analysis():
    """打印目录分析结果"""
    analysis = analyze_video_directory()
    
    print("=" * 60)
    print("视频目录结构分析")
    print("=" * 60)
    
    total_files = 0
    total_size = 0
    
    for season in sorted(analysis.keys()):
        info = analysis[season]
        episode_count = len(info['episodes'])
        size_gb = info['total_size'] / (1024 ** 3)
        total_files += episode_count
        total_size += info['total_size']
        
        print(f"\n第 {season} 季:")
        print(f"  目录: {info['directory']}")
        print(f"  集数: {episode_count} 集")
        print(f"  总大小: {size_gb:.2f} GB")
        print(f"  集列表: {info['episodes']}")
        
        # 显示缺失的集（如果有）
        if season <= 5:
            expected_episodes = set(range(1, 23))  # 假设最多22集
        elif season == 6:
            expected_episodes = set(range(1, 23))  # 第6季22集
        else:
            expected_episodes = set(range(1, 15))  # 第7季可能更少
        
        missing = expected_episodes - set(info['episodes'])
        if missing:
            print(f"  缺失集: {sorted(missing)}")
    
    print("\n" + "=" * 60)
    print(f"总计: {total_files} 个文件, {total_size / (1024 ** 3):.2f} GB")
    print("=" * 60)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'analyze':
        # 分析目录结构
        print_directory_analysis()
    else:
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

