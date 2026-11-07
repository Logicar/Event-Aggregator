import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// base 用相对路径，兼容 GitHub Pages 的 /<仓库名>/ 子路径
export default defineConfig({
  base: './',
  plugins: [vue()]
})
