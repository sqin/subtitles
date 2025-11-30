# Young Sheldon 字幕搜索系统 - 后端服务

基于 FastAPI 的后端服务，提供字幕搜索、音频/视频片段生成和合并功能。

## 功能特点

- 🔍 **字幕搜索**：支持中英文关键词全文搜索，基于 SQLite FTS5
- 🎵 **音频片段生成**：根据时间戳截取音频片段
- 🎬 **视频片段生成**：根据时间戳截取视频片段，支持多季多集
- 🔗 **视频合并**：一键合并多个视频片段为完整视频
- 📊 **统计信息**：提供数据库统计信息接口

## 环境要求

- Python >= 3.10
- [uv](https://github.com/astral-sh/uv) - Python 包管理器
- ffmpeg - 用于音视频处理

### 安装 ffmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

## 项目结构

```
backend/
├── main.py                 # FastAPI 主程序
├── indexer.py             # 索引构建器
├── parser.py              # 字幕解析器
├── audio_processor.py     # 音频处理模块
├── video_processor.py     # 视频处理模块
├── pyproject.toml         # 项目配置（uv）
├── uv.lock                # 依赖锁定文件
├── subtitle_index.db      # SQLite 数据库
├── temp_audio/            # 临时音频文件目录
└── temp_video/            # 临时视频文件目录
```

## 安装与运行

### 1. 安装依赖

项目使用 [uv](https://github.com/astral-sh/uv) 管理依赖，无需手动安装：

```bash
# uv 会自动读取 pyproject.toml 并安装依赖
uv sync
```

### 2. 构建索引（首次运行）

在构建索引之前，确保 `data/` 目录下存在字幕文件（.ass 格式）。

```bash
uv run python indexer.py
```

这会：
- 解析所有字幕文件（.ass 格式）
- 提取季集信息和对话内容
- 构建 SQLite 数据库索引（`subtitle_index.db`）

### 3. 启动服务

#### 方式一：后台运行（推荐）

在项目根目录使用启动脚本：

```bash
# 从项目根目录执行
./start.sh
```

这会在后台启动前后端服务，日志保存在 `logs/` 目录。

#### 方式二：前台运行

```bash
uv run python main.py
```

服务将在 `http://localhost:6000` 启动。

**停止服务：**

如果使用后台运行，执行：
```bash
./stop.sh
```

如果前台运行，使用 `Ctrl+C` 停止。

## 配置说明

### 视频路径配置

视频文件路径在 `video_processor.py` 中配置：

```python
VIDEO_BASE_DIR = Path("/Volumes/EAGET忆捷/YoungSheldon")
```

支持的文件结构：
- **第1-5季**：`第1-5季/S{season}/S{season}.{episode}.mkv` 或 `S{season}.{episode}.mkv`
- **第6季**：`第6季（22集全）/S06E{episode}.1080p.mp4`
- **第7季**：`第7季/S07E{episode}.mp4`

### 音频路径配置

音频文件路径在 `audio_processor.py` 中配置，默认位于项目根目录的 `audio/` 目录。

### 视频截取参数

在 `video_processor.py` 中配置：
- **开始时间偏移**：自动往前移动 5 秒（例如：11:04 → 10:59）
- **结束时间偏移**：自动往后延长 3 秒（例如：11:06 → 11:09）

## API 接口

### GET /

获取 API 基本信息

**响应示例：**
```json
{
  "message": "字幕搜索系统 API",
  "version": "1.0.0",
  "endpoints": ["/search", "/stats"]
}
```

### GET /search

搜索字幕

**参数：**
- `q` (string, 必需): 搜索关键词（支持中英文）
- `limit` (int, 可选): 最大返回结果数，默认 5000

**响应示例：**
```json
{
  "query": "谢尔顿",
  "total": 10,
  "results": [
    {
      "season": 1,
      "episode": 1,
      "filename": "Young Sheldon S01E01.ass",
      "dialogue_index": 42,
      "start_time": "0:03:11.39",
      "end_time": "0:03:14.36",
      "chinese_text": "谢尔顿说了什么...",
      "english_text": "Sheldon said...",
      "context_before": "...",
      "context_after": "..."
    }
  ]
}
```

### GET /stats

获取统计信息

**响应示例：**
```json
{
  "total_files": 141,
  "total_dialogues": 12345,
  "seasons": {
    "1": {
      "episode_count": 22,
      "episodes": [1, 2, 3, ...]
    }
  }
}
```

### POST /generate_audio

生成音频片段

**请求体：**
```json
{
  "season": 1,
  "episode": 1,
  "start_time": "0:03:11.39",
  "end_time": "0:03:14.36"
}
```

**响应示例：**
```json
{
  "success": true,
  "audio_url": "/temp_audio/s01e01_20251129_120000.mp3"
}
```

### POST /generate_video

生成视频片段

**请求体：**
```json
{
  "season": 1,
  "episode": 1,
  "start_time": "0:03:11.39",
  "end_time": "0:03:14.36"
}
```

**响应示例：**
```json
{
  "success": true,
  "video_url": "/temp_video/s01e01_20251129_120000.mp4"
}
```

### POST /merge_videos

合并多个视频片段

**请求体：**
```json
{
  "clips": [
    {
      "season": 1,
      "episode": 1,
      "start_time": "0:03:11.39",
      "end_time": "0:03:14.36"
    },
    {
      "season": 2,
      "episode": 3,
      "start_time": "0:10:20.00",
      "end_time": "0:10:25.00"
    }
  ]
}
```

**响应示例：**
```json
{
  "success": true,
  "video_url": "/temp_video/merged_20251129_120000.mp4"
}
```

## 依赖说明

项目依赖通过 `pyproject.toml` 管理：

- **fastapi**: Web 框架
- **uvicorn**: ASGI 服务器
- **pydantic**: 数据验证

运行 `uv sync` 会自动安装所有依赖。

## 开发说明

### 数据库结构

**files 表**：存储文件信息
- id, filename, file_path, season, episode

**dialogues 表**：存储对话内容
- id, file_id, dialogue_index, start_time, end_time
- chinese_text, english_text, raw_text

**dialogues_fts 表**：FTS5 全文搜索索引
- chinese_text, english_text

### 临时文件管理

- 临时音频文件存储在 `temp_audio/` 目录
- 临时视频文件存储在 `temp_video/` 目录
- 文件会在 24 小时后自动清理
- 同时最多保留 10 个文件

## 故障排查

### 找不到视频文件

检查 `video_processor.py` 中的 `VIDEO_BASE_DIR` 路径是否正确，确保移动硬盘已挂载。

### ffmpeg 错误

确保已正确安装 ffmpeg，并且可在命令行中运行：
```bash
ffmpeg -version
```

### 数据库不存在

运行 `uv run python indexer.py` 构建索引数据库。

## 许可证

MIT License

