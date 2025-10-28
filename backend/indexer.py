"""
索引构建器 - 使用 SQLite 构建搜索索引
"""
import sqlite3
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from parser import parse_ass_file, parse_season_episode


def init_database(db_file: str = 'subtitle_index.db'):
    """初始化数据库"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 创建文件表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            season INTEGER NOT NULL,
            episode INTEGER NOT NULL,
            UNIQUE(filename)
        )
    ''')
    
    # 创建对话表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dialogues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            dialogue_index INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            chinese_text TEXT NOT NULL,
            english_text TEXT NOT NULL,
            raw_text TEXT,
            FOREIGN KEY (file_id) REFERENCES files(id)
        )
    ''')
    
    # 创建全文搜索索引（FTS5）
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS dialogues_fts USING fts5(
            file_id UNINDEXED,
            dialogue_index UNINDEXED,
            chinese_text,
            english_text,
            content='dialogues',
            content_rowid='id'
        )
    ''')
    
    # 创建普通索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_id ON dialogues(file_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_season_episode ON files(season, episode)')
    
    conn.commit()
    return conn


def build_index(data_dir: str = 'data', db_file: str = 'subtitle_index.db'):
    """
    构建所有字幕文件的索引并存储到 SQLite
    
    Args:
        data_dir: 字幕文件所在目录
        db_file: SQLite 数据库文件路径
    """
    data_path = Path(data_dir)
    
    # 初始化数据库
    conn = init_database(db_file)
    cursor = conn.cursor()
    
    # 清空现有数据（如果需要重新构建）
    cursor.execute('DELETE FROM dialogues')
    cursor.execute('DELETE FROM files')
    cursor.execute('DELETE FROM dialogues_fts')
    conn.commit()
    
    # 获取所有 .ass 文件
    ass_files = sorted(data_path.glob('*.ass'))
    
    print(f"找到 {len(ass_files)} 个字幕文件")
    
    for i, file_path in enumerate(ass_files, 1):
        print(f"处理文件 {i}/{len(ass_files)}: {file_path.name}")
        
        try:
            # 解析文件名获取季集信息
            season, episode = parse_season_episode(file_path.name)
            
            if season is None or episode is None:
                print(f"  警告: 无法从文件名提取季集信息: {file_path.name}")
                continue
            
            # 解析 ASS 文件
            dialogues = parse_ass_file(file_path)
            
            # 插入文件记录
            cursor.execute('''
                INSERT INTO files (filename, file_path, season, episode)
                VALUES (?, ?, ?, ?)
            ''', (file_path.name, str(file_path), season, episode))
            
            file_id = cursor.lastrowid
            
            # 插入对话记录
            for idx, dialogue in enumerate(dialogues):
                cursor.execute('''
                    INSERT INTO dialogues (
                        file_id, dialogue_index, start_time, end_time,
                        chinese_text, english_text, raw_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_id, idx, dialogue.start_time, dialogue.end_time,
                    dialogue.chinese_text, dialogue.english_text, dialogue.raw_text
                ))
            
            conn.commit()
            
        except Exception as e:
            print(f"  错误处理文件 {file_path.name}: {e}")
            continue
    
    # 重建 FTS 索引
    print("\n重建全文搜索索引...")
    cursor.execute('INSERT INTO dialogues_fts(dialogues_fts) VALUES(\'rebuild\')')
    conn.commit()
    
    print(f"\n索引构建完成！")
    conn.close()


def get_statistics(db_file: str = 'subtitle_index.db') -> Dict[str, Any]:
    """获取索引统计信息"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 总文件数
    cursor.execute('SELECT COUNT(*) FROM files')
    total_files = cursor.fetchone()[0]
    
    # 总对话数
    cursor.execute('SELECT COUNT(*) FROM dialogues')
    total_dialogues = cursor.fetchone()[0]
    
    # 统计每季的集数
    cursor.execute('''
        SELECT season, COUNT(DISTINCT episode) as episode_count,
               GROUP_CONCAT(DISTINCT episode)
        FROM files
        GROUP BY season
        ORDER BY season
    ''')
    
    seasons = {}
    for row in cursor.fetchall():
        season, episode_count, episodes_str = row
        episodes = [int(e) for e in episodes_str.split(',')]
        seasons[season] = {
            'episode_count': episode_count,
            'episodes': episodes
        }
    
    conn.close()
    
    return {
        'total_files': total_files,
        'total_dialogues': total_dialogues,
        'seasons': seasons
    }


def search_dialogues(
    query: str,
    db_file: str = 'subtitle_index.db',
    limit: int = 5000
) -> List[Dict[str, Any]]:
    """
    搜索对话
    
    Args:
        query: 搜索关键词
        db_file: Lorentz SQLite 数据库文件路径
        limit: 最大返回结果数
        
    Returns:
        搜索结果列表
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    query_lower = query.lower().strip()
    
    # 使用全文搜索
    # FTS5 查询语法: column:term 或 "phrase"
    # 使用两个查询：FTS 搜索和普通 LIKE 搜索
    results_ids = set()
    
    # FTS5 全文搜索
    cursor.execute('''
        SELECT d.id
        FROM dialogues_fts fts
        JOIN dialogues d ON fts.rowid = d.id
        WHERE dialogues_fts MATCH ?
        LIMIT ?
    ''', (f'"{query_lower}"', limit))
    
    for row in cursor.fetchall():
        results_ids.add(row[0])
    
    # LIKE 模糊搜索
    cursor.execute('''
        SELECT id FROM dialogues
        WHERE chinese_text LIKE ? OR english_text LIKE ?
        LIMIT ?
    ''', (f'%{query_lower}%', f'%{query_lower}%', limit))
    
    for row in cursor.fetchall():
        results_ids.add(row[0])
    
    if not results_ids:
        return []
    
    # 获取完整结果
    placeholders = ','.join(['?'] * len(results_ids))
    cursor.execute(f'''
        SELECT d.file_id, d.dialogue_index, d.start_time, d.end_time,
               d.chinese_text, d.english_text, f.filename, f.season, f.episode
        FROM dialogues d
        JOIN files f ON d.file_id = f.id
        WHERE d.id IN ({placeholders})
        ORDER BY f.season, f.episode, d.dialogue_index
        LIMIT ?
    ''', list(results_ids) + [limit])
    
    results = []
    for row in cursor.fetchall():
        file_id, dialogue_index, start_time, end_time, chinese_text, english_text, filename, season, episode = row
        
        # 获取上下文（前后各一条）
        context_before = None
        context_after = None
        
        # 获取前一条
        cursor.execute('''
            SELECT chinese_text, english_text
            FROM dialogues
            WHERE file_id = ? AND dialogue_index < ?
            ORDER BY dialogue_index DESC
            LIMIT 1
        ''', (file_id, dialogue_index))
        
        prev_row = cursor.fetchone()
        if prev_row:
            context_before = f"{prev_row[0]}\n{prev_row[1]}"
        
        # 获取后一条
        cursor.execute('''
            SELECT chinese_text, english_text
            FROM dialogues
            WHERE file_id = ? AND dialogue_index > ?
            ORDER BY dialogue_index ASC
            LIMIT 1
        ''', (file_id, dialogue_index))
        
        next_row = cursor.fetchone()
        if next_row:
            context_after = f"{next_row[0]}\n{next_row[1]}"
        
        result = {
            'season': season,
            'episode': episode,
            'filename': filename,
            'dialogue_index': dialogue_index,
            'start_time': start_time,
            'end_time': end_time,
            'chinese_text': chinese_text,
            'english_text': english_text,
            'context_before': context_before,
            'context_after': context_after
        }
        
        results.append(result)
    
    conn.close()
    return results


if __name__ == '__main__':
    # 构建索引
    print("开始构建索引...")
    build_index(data_dir='../data', db_file='subtitle_index.db')
    
    # 显示统计信息
    stats = get_statistics(db_file='subtitle_index.db')
    print("\n索引统计:")
    print(f"  总文件数: {stats['total_files']}")
    print(f"  总对话数: {stats['total_dialogues']}")
    print(f"  季数: {len(stats['seasons'])}")
    for season, info in sorted(stats['seasons'].items()):
        print(f"  第 {season} 季: {info['episode_count']} 集")
    
    # 测试搜索
    print("\n测试搜索 '谢尔顿'...")
    results = search_dialogues('谢尔顿', limit=3)
    print(f"找到 {len(results)} 条结果")
    for i, result in enumerate(results, 1):
        print(f"\n结果 {i}:")
        print(f"  季: {result['season']}, 集: {result['episode']}")
        print(f"  时间: {result['start_time']} - {result['end_time']}")
        print(f"  中文: {result['chinese_text'][:50]}...")
