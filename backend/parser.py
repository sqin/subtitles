"""
字幕解析器 - 解析 ASS 文件格式，提取对白、时间戳和中英文内容
"""
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Dialogue:
    """对白数据结构"""
    start_time: str  # 开始时间戳 0:03:11.39
    end_time: str    # 结束时间戳 0:03:14.36
    chinese_text: str  # 中文对白
    english_text: str  # 英文对白
    raw_text: str     # 原始文本


def parse_time_to_seconds(time_str: str) -> float:
    """将时间戳转换为秒数"""
    # 格式: 0:03:11.39 -> 191.39
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds_parts = parts[2].split('.')
    seconds = int(seconds_parts[0])
    milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
    
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 100.0
    return total_seconds


def parse_ass_file(file_path: Path) -> List[Dialogue]:
    """
    解析 ASS 文件，提取所有对话
    
    Args:
        file_path: ASS 文件路径
        
    Returns:
        对话列表
    """
    dialogues = []
    
    # 尝试多种编码
    encodings = ['utf-8-sig', 'utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'gb2312', 'gbk', 'gb18030']
    content = None
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                test_content = f.read()
                # 验证内容是否包含有效的 ASS 文件标记
                if '[Script Info]' in test_content or 'Dialogue:' in test_content:
                    content = test_content
                    break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if content is None:
        raise ValueError(f"无法解码文件: {file_path}")
    
    # 提取所有 Dialogue 行（遵循 Events 的 Format 定义）：
    # Format: Layer, Start, End, Style, Actor, MarginL, MarginR, MarginV, Effect, Text
    # 允许任意 Style/Actor，并严格跳过 4 个 Margin 字段与 Effect 字段
    dialogue_regex = re.compile(
        r'^Dialogue:\s*\d+,'                      # Layer
        r'(\d+:\d+:\d+\.\d+),'                 # Start
        r'(\d+:\d+:\d+\.\d+),'                 # End
        r'[^,]*,'                                   # Style
        r'[^,]*,'                                   # Actor
        r'[^,]*,'                                   # MarginL
        r'[^,]*,'                                   # MarginR
        r'[^,]*,'                                   # MarginV
        r'[^,]*,'                                   # Effect
        r'(.*)$',                                   # Text (rest of line)
        re.MULTILINE
    )
    matches = dialogue_regex.findall(content)
    
    for match in matches:
        start_time, end_time, text = match
        
        # 清理文本中的格式标记
        # 移除 ASS 样式标记（{\fs14}, {\c&HFFFFFF&} 等）
        clean_text = re.sub(r'\{[^}]+\}', '', text)
        
        # 分离中英文（用 \N 分隔）
        parts = clean_text.split('\\N')
        
        chinese_text = ''
        english_text = ''
        
        if len(parts) >= 1:
            chinese_text = parts[0].strip()
        if len(parts) >= 2:
            english_text = parts[1].strip()
        
        # 如果中文文本为空，尝试从英文中提取
        if not chinese_text and english_text:
            chinese_text = english_text
        
        dialogue = Dialogue(
            start_time=start_time,
            end_time=end_time,
            chinese_text=chinese_text,
            english_text=english_text,
            raw_text=text
        )
        
        dialogues.append(dialogue)
    
    return dialogues


def parse_season_episode(filename: str) -> Tuple[Optional[int], Optional[int]]:
    """
    从文件名提取季和集数
    
    Args:
        filename: 文件名，如 "Young Sheldon S05E01 One Bad Night.ass"
        
    Returns:
        (season, episode) 元组，如 (5, 1)
    """
    # 匹配 S01E01 或 S05E01 格式
    pattern = r'S(\d+)E(\d+)'
    match = re.search(pattern, filename)
    
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        return (season, episode)
    
    return (None, None)


def format_time_display(seconds: float) -> str:
    """将秒数格式化为可读的时间格式 HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


if __name__ == '__main__':
    # 测试代码
    test_file = Path('../data/Young Sheldon S05E01 One Bad Night and Chaos of Selfish Desires.简英.ass')
    if test_file.exists():
        dialogues = parse_ass_file(test_file)
        print(f"解析了 {len(dialogues)} 条对白")
        
        # 显示前3条对白
        for i, dialogue in enumerate(dialogues[:3]):
            print(f"\n对白 {i+1}:")
            print(f"时间: {dialogue.start_time} - {dialogue.end_time}")
            print(f"中文: {dialogue.chinese_text}")
            print(f"英文: {dialogue.english_text}")
        
        # 测试文件名解析
        season, episode = parse_season_episode(test_file.name)
        print(f"\n季: {season}, 集: {episode}")
    else:
        print(f"测试文件不存在: {test_file}")

