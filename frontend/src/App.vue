<template>
  <div class="app">
    <h1>🎬 Young Sheldon 字幕搜索222</h1>
    
    <div class="search-container">
      <div class="search-box">
        <input
          v-model="query"
          @keyup.enter="performSearch"
          class="search-input"
          type="text"
          placeholder="输入中英文关键词搜索对白..."
        />
        <button @click="performSearch" class="search-btn">搜索</button>
      </div>
      
      <div v-if="stats.total_files > 0" class="results-info">
        共 {{ stats.total_files }} 个文件，
        {{ stats.total_dialogues }} 条对白
      </div>
      
      <div v-if="loading" class="loading">搜索中...</div>
      <div v-else-if="results.length > 0" class="results-info highlight">
        找到 {{ results.length }} 条结果
      </div>
      
      <!-- 合并视频按钮 -->
      <div v-if="!loading && results.length > 0" class="merge-container">
        <button 
          @click="mergeVideos" 
          :disabled="merging || results.length === 0"
          class="merge-btn"
        >
          <span v-if="!merging">🎬 一键合并所有视频片段</span>
          <span v-else>⏳ 合并中，请稍候...</span>
        </button>
        <div v-if="mergedVideoUrl" class="merged-video-container">
          <div class="merged-video-label">合并完成！</div>
          <video 
            :src="mergedVideoUrl" 
            controls 
            playsinline 
            webkit-playsinline
            preload="metadata"
            class="merged-video"
          ></video>
        </div>
      </div>
    </div>
    
    <div v-if="!loading && results.length > 0" class="results-container">
      <ResultItem
        v-for="(result, index) in results"
        :key="index"
        :result="result"
        :query="query"
      />
    </div>
    
    <div v-else-if="!loading && query && results.length === 0" class="results-container">
      <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <div class="empty-state-text">未找到匹配的结果</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import ResultItem from './components/ResultItem.vue'

interface SearchResult {
  season: number
  episode: number
  filename: string
  dialogue_index: number
  start_time: string
  end_time: string
  chinese_text: string
  english_text: string
  context_before?: string
  context_after?: string
}

const query = ref('')
const results = ref<SearchResult[]>([])
const loading = ref(false)
const stats = ref({ total_files: 0, total_dialogues: 0 })
const merging = ref(false)
const mergedVideoUrl = ref('')

const performSearch = async () => {
  if (!query.value.trim()) {
    results.value = []
    mergedVideoUrl.value = '' // 清除合并的视频
    return
  }
  
  loading.value = true
  mergedVideoUrl.value = '' // 清除之前的合并视频
  try {
    const response = await axios.get(`/api/search`, {
      params: { q: query.value }
    })
    results.value = response.data.results
  } catch (error) {
    console.error('搜索失败:', error)
    results.value = []
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await axios.get('/api/stats')
    stats.value = response.data
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

const mergeVideos = async () => {
  if (results.value.length === 0) {
    return
  }
  
  merging.value = true
  mergedVideoUrl.value = ''
  
  try {
    // 准备合并请求数据
    const clips = results.value.map(result => ({
      season: result.season,
      episode: result.episode,
      start_time: result.start_time,
      end_time: result.end_time
    }))
    
    const response = await axios.post('/api/merge_videos', {
      clips: clips
    })
    
    if (response.data.success) {
      mergedVideoUrl.value = response.data.video_url
      // 滚动到合并视频位置
      setTimeout(() => {
        const element = document.querySelector('.merged-video-container')
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
        }
      }, 100)
    } else {
      alert(response.data.message || '合并视频失败')
    }
  } catch (error) {
    console.error('合并视频失败:', error)
    alert('合并视频失败，请稍后重试')
  } finally {
    merging.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.app {
  padding: 20px;
}

.merge-container {
  margin-top: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  border-radius: 12px;
  border: 2px solid #667eea;
}

.merge-btn {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
  color: white;
  border: none;
  padding: 15px 30px;
  border-radius: 25px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
  width: 100%;
  max-width: 400px;
}

.merge-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(76, 175, 80, 0.5);
}

.merge-btn:active:not(:disabled) {
  transform: translateY(0);
}

.merge-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
}

.merged-video-container {
  margin-top: 20px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.merged-video-label {
  font-size: 18px;
  font-weight: 600;
  color: #4caf50;
  margin-bottom: 15px;
  text-align: center;
}

.merged-video {
  width: 100%;
  max-width: 800px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: block;
  margin: 0 auto;
}
</style>

