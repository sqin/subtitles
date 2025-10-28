import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0', // 监听所有网络接口，允许局域网访问
    port: 5173,
    allowedHosts: [
      '1153xm656fy44.vicp.fun',
      'localhost',
      '.local',
      '.vicp.fun' // 允许所有 vicp.fun 子域名
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/temp_audio': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/temp_video': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})

