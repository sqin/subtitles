<template>
  <div class="app">
    <h1>🎬 Young Sheldon 字幕搜索</h1>
    
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

const query = ref('')
const results = ref([])
const loading = ref(false)
const stats = ref({ total_files: 0, total_dialogues: 0 })

const API_BASE = `${location.protocol}//${location.hostname}:18000`
const api = axios.create({ baseURL: API_BASE })

const performSearch = async () => {
  if (!query.value.trim()) {
    results.value = []
    return
  }
  
  loading.value = true
  try {
    const response = await api.get(`/search`, {
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
    const response = await api.get('/stats')
    stats.value = response.data
  } catch (error) {
    console.error('加载统计信息失败:', error)
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
</style>

