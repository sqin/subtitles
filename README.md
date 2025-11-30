# Young Sheldon 字幕搜索系统

一个基于 Vue 3 + FastAPI + SQLite 的现代化字幕搜索系统，可以快速搜索 Young Sheldon 剧集中的中英文字幕。

## 功能特点

- 🔍 **智能搜索**：支持中英文关键词模糊搜索
- 📊 **SQLite 索引**：使用 SQLite + FTS5 全文搜索，查询速度快
- 🎬 **详细信息**：显示匹配对白的季数、集数、时间段
- 📝 **上下文显示**：显示前后各一条对白，方便理解语境
- 🎨 **现代化 UI**：Vue 3 + TypeScript 构建的响应式界面
- 🎵 **音频片段**：支持生成音频片段
- 🎥 **视频片段**：支持生成和合并视频片段
- 🚀 **后台运行**：提供便捷的启动/停止脚本，支持后台运行

## 项目结构

```
sheldon/
├── data/                    # 字幕文件目录
├── audio/                   # 音频文件目录
├── video/                   # 视频文件目录
├── backend/                 # 后端服务
│   ├── parser.py           # 字幕解析器
│   ├── indexer.py          # SQLite 索引构建器
│   ├── main.py             # FastAPI 后端
│   ├── audio_processor.py  # 音频处理模块
│   ├── video_processor.py  # 视频处理模块
│   └── pyproject.toml      # 项目配置（uv）
├── frontend/                # 前端应用
│   ├── src/
│   │   ├── App.vue         # 主应用组件
│   │   ├── components/
│   │   │   └── ResultItem.vue  # 结果展示组件
│   │   ├── main.ts
│   │   └── style.css
│   ├── package.json
│   └── vite.config.ts
├── logs/                    # 日志文件目录（自动创建）
├── start.sh                 # 启动脚本（后台运行）
├── stop.sh                  # 停止脚本
└── README.md
```

## 快速开始

### 1. 构建索引

首先需要构建数据库索引（只需执行一次）：

```bash
cd backend
uv run python indexer.py
```

这会：
- 解析所有字幕文件
- 提取季集信息和对话内容
- 构建 SQLite 数据库索引

### 2. 后台启动所有服务

项目提供了便捷的启动脚本，可以在后台同时启动前后端服务：

```bash
# 在项目根目录执行
./start.sh
```

这会在后台启动：
- 后端服务：`http://localhost:6000`
- 前端服务：`http://localhost:5173`

日志文件保存在 `logs/` 目录：
- `logs/backend.log` - 后端日志
- `logs/frontend.log` - 前端日志

**查看实时日志：**
```bash
tail -f logs/backend.log    # 后端日志
tail -f logs/frontend.log   # 前端日志
```

**停止所有服务：**
```bash
./stop.sh
```

### 3. 手动启动（可选）

如果需要单独启动或前台运行：

**启动后端：**
```bash
cd backend
uv run python main.py
```

**启动前端：**
```bash
cd frontend
npm install
npm run dev
```

### 4. 使用系统

在浏览器中打开 `http://localhost:5173`，输入关键词（支持中英文）进行搜索。

## API 接口

### GET /search

搜索字幕

**参数**：
- `q` (string): 搜索关键词
- `limit` (int, 可选): 最大返回结果数，默认 50

**返回**：
```json
{
  "query": "谢尔顿",
  "total": 10,
  "results": [
    {
      "season": 5,
      "episode": 1,
      "filename": "Young Sheldon S05E01...",
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

**返回**：
```json
{
  "total_files": 141,
  "total_dialogues": 12345,
  "seasons": {
    "1": {"episode_count": 22, "episodes": [1,2,3,...]},
    "2": {"episode_count": 22, "episodes": [1,2,3,...]},
    ...
  }
}
```

## 技术栈

### 后端
- Python 3.8+
- FastAPI: 现代化的 Web 框架
- SQLite: 轻量级数据库
- FTS5: 全文搜索功能

### 前端
- Vue 3: 渐进式 JavaScript 框架
- TypeScript: 类型安全的 JavaScript
- Vite: 快速的构建工具
- Axios: HTTP 客户端

## 开发说明

### 数据库结构

**files 表**：存储文件信息
- id, filename, file_path, season, episode

**dialogues 表**：存储对话内容
- id, file_id, dialogue_index, start_time, end_time
- chinese_text, english_text, raw_text

**dialogues_fts 表**：FTS5 全文搜索索引
- chinese_text, english_text

## 许可证

MIT License

