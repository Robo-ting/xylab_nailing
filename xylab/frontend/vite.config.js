import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// XYLab 智能钉合控制系统 - Vite 构建配置
export default defineConfig({
    plugins: [react()],
    server: {
        host: '0.0.0.0',
        port: 5173,
        strictPort: true,
        open: true,
        proxy: {
            // 预留后端 API 代理：以后接入真实 YOLO / RAG / LLM / ROS 服务
            '/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
            },
        },
    },
    build: {
        outDir: 'dist',
        sourcemap: false,
    },
});
