"""
FastAPI 后端主程序 - 提供字幕搜索 API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os


app = FastAPI(title="字幕搜索系统", version="1.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite 默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
temp_audio_dir = os.path.join(os.path.dirname(__file__), 'temp_audio')
os.makedirs(temp_audio_dir, exist_ok=True)
app.mount("/temp_audio", StaticFiles(directory=temp_audio_dir), name="temp_audio")

temp_video_dir = os.path.join(os.path.dirname(__file__), 'temp_video')
os.makedirs(temp_video_dir, exist_ok=True)
app.mount("/temp_video", StaticFiles(directory=temp_video_dir), name="temp_video")


class SearchResult(BaseModel):
    """搜索结果数据模型"""
    season: int
    episode: int
    filename: str
    dialogue_index: int
    start_time: str
    end_time: str
    chinese_text: str
    english_text: str
    context_before: Optional[str] = None
    context_after: Optional[str] = None


class SearchResponse(BaseModel):
    """搜索响应数据模型"""
    query: str
    results: List[SearchResult]
    total: int


class AudioClipRequest(BaseModel):
    """音频截取请求数据模型"""
    season: int
    episode: int
    start_time: str
    end_time: str


class AudioClipResponse(BaseModel):
    """音频截取响应数据模型"""
    success: bool
    audio_url: Optional[str] = None
    message: Optional[str] = None


class VideoClipRequest(BaseModel):
    """视频截取请求数据模型"""
    season: int
    episode: int
    start_time: str
    end_time: str


class VideoClipResponse(BaseModel):
    """视频截取响应数据模型"""
    success: bool
    video_url: Optional[str] = None
    message: Optional[str] = None


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "字幕搜索系统 API",
        "version": "1.0.0",
        "endpoints": ["/search", "/stats"]
    }


@app.get("/search")
async def search(q: str, limit: int = 5000) -> SearchResponse:
    """
    搜索字幕
    
    Args:
        q: 搜索关键词（支持中英文）
        limit: 最大返回结果数（默认5000）
        
    Returns:
        搜索结果
    """
    from indexer import search_dialogues
    
    if not q or not q.strip():
        return SearchResponse(query=q, results=[], total=0)
    
    results = search_dialogues(q, limit=limit)
    
    return SearchResponse(
        query=q,
        results=results,
        total=len(results)
    )


@app.get("/stats")
async def stats():
    """获取统计信息"""
    from indexer import get_statistics
    
    try:
        stats_data = get_statistics()
        return stats_data
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"无法获取统计信息: {str(e)}")


@app.post("/generate_audio", response_model=AudioClipResponse)
async def generate_audio(request: AudioClipRequest):
    """
    生成音频片段
    
    Args:
        request: 音频截取请求
        
    Returns:
        音频片段 URL
    """
    from audio_processor import extract_audio_clip, cleanup_old_files
    
    try:
        # 清理旧文件
        cleanup_old_files()
        
        # 截取音频
        audio_path = extract_audio_clip(
            season=request.season,
            episode=request.episode,
            start_time=request.start_time,
            end_time=request.end_time
        )
        
        if audio_path:
            # 返回相对路径，前端会自动使用当前域名
            return AudioClipResponse(
                success=True,
                audio_url=f"/{audio_path}"
            )
        else:
            return AudioClipResponse(
                success=False,
                message="无法找到音频文件或截取失败"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成音频失败: {str(e)}")


@app.post("/generate_video", response_model=VideoClipResponse)
async def generate_video(request: VideoClipRequest):
    """
    生成视频片段
    
    Args:
        request: 视频截取请求
        
    Returns:
        视频片段 URL
    """
    from video_processor import extract_video_clip, cleanup_old_files
    
    try:
        # 清理旧文件
        cleanup_old_files()
        
        # 截取视频
        video_path = extract_video_clip(
            season=request.season,
            episode=request.episode,
            start_time=request.start_time,
            end_time=request.end_time
        )
        
        if video_path:
            # 返回相对路径，前端会自动使用当前域名
            return VideoClipResponse(
                success=True,
                video_url=f"/{video_path}"
            )
        else:
            return VideoClipResponse(
                success=False,
                message="无法找到视频文件或截取失败"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成视频失败: {str(e)}")


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)

