import axios, {type AxiosInstance, type AxiosResponse, AxiosError} from 'axios';
import {useUserStore} from '@/stores/userStore';
import {createDiscreteApi} from 'naive-ui'; // 使用 Naive UI 的脱离上下文 API 进行消息提示

// 创建全局唯一的 Axios 实例
// 这里的 baseURL 读取自环境变量，生产环境和开发环境自动切换
const service: AxiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
    timeout: 10000, // 请求超时时间设置为 10s
    headers: {'Content-Type': 'application/json'},
});

// Naive UI 的消息提示工具（用于在组件外弹出提示）
const {message} = createDiscreteApi(['message']);

/**
 * 请求拦截器 (Request Interceptor)
 * @description 在发送请求前自动注入 Token，实现无感认证
 */
service.interceptors.request.use(
    (config) => {
        // 必须在拦截器内部获取 store，因为此时 Pinia 已经挂载
        const userStore = useUserStore();

        // 如果存在 Token，则注入 Authorization Header
        // 遵循 RFC 6750 标准: Authorization: Bearer <token>
        if (userStore.token && config.headers) {
            config.headers.Authorization = `Bearer ${userStore.token}`;
        }
        return config;
    },
    (error) => {
        // 处理请求发送前的错误（如 DNS 解析失败等本地网络问题）
        console.error('Request Error:', error);
        return Promise.reject(error);
    }
);

/**
 * 响应拦截器 (Response Interceptor)
 * @description 统一处理 HTTP 状态码，剥离 data 层，处理 401 自动登出
 */
service.interceptors.response.use(
    (response: AxiosResponse) => {
        // 2xx 范围内的状态码都会触发该函数
        // 直接返回 response.data，让业务层少写一层 .data
        return response.data;
    },
    async (error: AxiosError) => {
        const userStore = useUserStore();

        // 获取后端返回的错误信息，若无则使用默认文案
        // 后端 FastAPI HTTPExecption 通常返回 { detail: "Error message" }
        const errorMsg = (error.response?.data as any)?.detail || error.message || '网络请求异常';

        // 针对特定状态码进行策略处理
        if (error.response) {
            switch (error.response.status) {
                case 401:
                    // Token 过期或无效
                    // 避免在登录页重复弹出提示
                    if (!window.location.pathname.includes('/login')) {
                        message.error('登录已过期，请重新登录');
                        userStore.logout();
                        // 这里可以引入 router 进行跳转，或者依靠 App.vue 的 watchEffect
                        // window.location.reload(); // 可选：强制刷新清理脏状态
                    }
                    break;
                case 403:
                    message.warning('您没有权限执行此操作');
                    break;
                case 404:
                    message.error('请求的资源不存在');
                    break;
                case 500:
                    message.error('服务器内部错误，请联系管理员');
                    break;
                default:
                    message.error(errorMsg);
            }
        } else {
            // 处理断网或超时情况
            if (error.message.includes('timeout')) {
                message.error('请求超时，请检查网络连接');
            } else {
                message.error('网络连接异常');
            }
        }

        return Promise.reject(error);
    }
);

export default service;