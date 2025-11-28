import {defineConfig} from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            // 配置路径别名，使用 @ 指代 src 目录
            '@': path.resolve(__dirname, 'src'),
        },
    },
    server: {
        port: 3000, // 前端开发端口
        proxy: {
            // 配置反向代理，解决开发环境 CORS 问题
            '/api': {
                target: 'http://localhost:8000', // 指向本地后端服务
                changeOrigin: true,
            },
        },
    },
});