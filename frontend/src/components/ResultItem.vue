<template>
  <div class="result-item">
    <div class="result-header">
      <span class="season-badge">第 {{ result.season }} 季</span>
      <span class="episode-badge">第 {{ result.episode }} 集</span>
      <span class="time-badge">{{ formatTime(result.start_time) }} - {{ formatTime(result.end_time) }}</span>
    </div>
    
    <!-- 前一句 - 已隐藏 -->
    <!-- <div v-if="result.context_before" class="context context-before">
      <div class="context-label">↑ 前一句</div>
      <div v-html="formatContext(result.context_before)"></div>
    </div> -->
    
    <!-- 目标句 -->
    <div class="dialogue-content dialogue-target">
      <div class="dialogue-chinese" v-html="highlightText(result.chinese_text, query)"></div>
      <div class="dialogue-english" v-html="highlightText(result.english_text, query)"></div>
    </div>
    
    <!-- 后一句 - 已隐藏 -->
    <!-- <div v-if="result.context_after" class="context context-after">
      <div class="context-label">↓ 后一句</div>
      <div v-html="formatContext(result.context_after)"></div>
    </div> -->
    
    <!-- 音频控制 -->
    <div class="audio-controls">
      <button 
        v-if="!audioUrl && !generating" 
        @click="generateAudio" 
        class="generate-btn"
      >
        🎵 生成音频
      </button>
      <button 
        v-if="generating" 
        class="generate-btn generating"
        disabled
      >
        ⏳ 生成中...
      </button>
      <div v-if="audioUrl" class="audio-player">
        <audio :src="audioUrl" controls class="audio-element"></audio>
      </div>
    </div>
    
    <!-- 视频控制 -->
    <div class="video-controls">
      <button 
        v-if="!videoUrl && !generatingVideo" 
        @click="generateVideo" 
        class="generate-btn video-btn"
      >
        🎬 生成视频
      </button>
      <button 
        v-if="generatingVideo" 
        class="generate-btn generating"
        disabled
      >
        ⏳ 生成中...
      </button>
      <div v-if="videoUrl" class="video-player">
        <video 
          :src="videoUrl" 
          controls 
          playsinline 
          webkit-playsinline
          preload="metadata"
          class="video-element"
        ></video>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, ref } from 'vue'
import axios from 'axios'

const props = defineProps<{
  result: any
  query: string
}>()

const audioUrl = ref<string>('')
const generating = ref<boolean>(false)
const videoUrl = ref<string>('')
const generatingVideo = ref<boolean>(false)

const formatTime = (timeStr: string): string => {
  // 从 0:03:11.39 格式提取 03:11
  const parts = timeStr.split(':')
  if (parts.length >= 2) {
    return `${parts[1]}:${parts[2].split('.')[0]}`
  }
  return timeStr
}

const highlightText = (text: string, query: string): string => {
  if (!text || !query) return text
  
  const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi')
  return text.replace(regex, '<span class="highlight">$1</span>')
}

const formatContext = (text: string): string => {
  if (!text) return ''
  // 将换行符转换为 <br> 标签
  return text.replace(/\n/g, '<br>')
}

const escapeRegExp = (str: string): string => {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

const generateAudio = async () => {
  generating.value = true
  try {
    const response = await axios.post('/api/generate_audio', {
      season: props.result.season,
      episode: props.result.episode,
      start_time: props.result.start_time,
      end_time: props.result.end_time
    })
    
    if (response.data.success) {
      audioUrl.value = response.data.audio_url
    } else {
      alert(response.data.message || '生成音频失败')
    }
  } catch (error) {
    console.error('生成音频失败:', error)
    alert('生成音频失败，请稍后重试')
  } finally {
    generating.value = false
  }
}

const generateVideo = async () => {
  generatingVideo.value = true
  try {
    const response = await axios.post('/api/generate_video', {
      season: props.result.season,
      episode: props.result.episode,
      start_time: props.result.start_time,
      end_time: props.result.end_time
    })
    
    if (response.data.success) {
      videoUrl.value = response.data.video_url
    } else {
      alert(response.data.message || '生成视频失败')
    }
  } catch (error) {
    console.error('生成视频失败:', error)
    alert('生成视频失败，请稍后重试')
  } finally {
    generatingVideo.value = false
  }
}
</script>

<style scoped>
.result-item {
  padding: 20px 0;
  border-bottom: 1px solid #f0f0f0;
}

.result-item:last-child {
  border-bottom: none;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.season-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 5px 12px;
  border-radius: 15px;
  font-size: 13px;
  font-weight: 600;
}

.episode-badge {
  background: #f0f0f0;
  color: #333;
  padding: 5px 12px;
  border-radius: 15px;
  font-size: 13px;
  font-weight: 600;
}

.time-badge {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 5px 12px;
  border-radius: 15px;
  font-size: 12px;
}

.dialogue-content {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin: 10px 0;
}

.dialogue-target {
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  border: 2px solid #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.dialogue-chinese {
  color: #333;
  font-size: 16px;
  line-height: 1.6;
  margin-bottom: 8px;
  font-weight: 500;
}

.dialogue-english {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  font-style: italic;
}

.context {
  padding: 10px;
  background: #f5f5f5;
  border-left: 3px solid #ccc;
  border-radius: 4px;
  font-size: 13px;
  color: #666;
  margin: 5px 0;
  line-height: 1.5;
}

.context-before {
  border-left-color: #ff9800;
  background: #fff3e0;
}

.context-after {
  border-left-color: #2196f3;
  background: #e3f2fd;
}

.context-label {
  font-weight: 600;
  color: #999;
  margin-bottom: 5px;
  font-size: 12px;
}

:deep(.highlight) {
  background: #fff59d;
  padding: 2px 4px;
  border-radius: 3px;
}

.audio-controls {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px dashed #ddd;
}

.generate-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.generate-btn:active:not(:disabled) {
  transform: translateY(0);
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.generating {
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
}

.audio-player {
  margin-top: 10px;
}

.audio-element {
  width: 100%;
  height: 40px;
  border-radius: 8px;
}

.video-controls {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px dashed #ddd;
}

.video-btn {
  background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
}

.video-btn:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(244, 67, 54, 0.4);
}

.video-player {
  margin-top: 10px;
}

.video-element {
  width: 100%;
  max-width: 800px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>

