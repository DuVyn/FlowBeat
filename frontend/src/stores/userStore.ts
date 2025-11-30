import {defineStore} from 'pinia';
import {ref, computed} from 'vue';
import type {User} from '@/types/entity';
import type {LoginRequest, RegisterRequest, TokenResponse} from '@/types/api';
// 暂时直接引入 axios 实例用于 API 调用，后续会将 API 调用逻辑抽离到 src/api/auth.ts
// 但为了保持 Store 的自包含性，此处设计为 Store 调用 API 层（下一步实现 API 层）
import apiService from '@/api/axios';
import {usePlayerStore} from '@/stores/playerStore';

// 定义 LocalStorage Key 常量，避免硬编码
const TOKEN_KEY = 'flowbeat_token';

export const useUserStore = defineStore('user', () => {
    // --- State ---

    // 从 LocalStorage 初始化 Token，实现页面刷新后的登录态保持
    const token = ref<string | null>(localStorage.getItem(TOKEN_KEY));
    const userInfo = ref<User | null>(null);
    const isLoading = ref<boolean>(false);

    // --- Getters ---

    // 判断用户是否已登录
    const isAuthenticated = computed(() => !!token.value);

    // 判断是否为管理员
    const isAdmin = computed(() => userInfo.value?.role === 'ADMIN');

    // --- Actions ---

    /**
     * 登录动作
     * @description 调用登录接口，保存 Token，并拉取用户信息
     */
    async function login(loginForm: LoginRequest) {
        isLoading.value = true;
        try {
            // 1. 调用登录接口获取 Token
            // URL 对应后端 backend/app/api/v1/endpoints/auth.py 中的 /login/access-token
            // 注意：OAuth2PasswordRequestForm 需要 content-type: application/x-www-form-urlencoded
            // 这里我们需要特殊处理一下参数，或者确认后端是否支持 JSON
            // 假设后端标准 OAuth2 实现，通常需要 Form Data。
            // 为了简化，这里演示使用 URLSearchParams 转换
            const params = new URLSearchParams();
            params.append('username', loginForm.username); // 后端字段是 username (对应邮箱)
            params.append('password', loginForm.password);

            const data = await apiService.post<any, TokenResponse>('/auth/login/access-token', params, {
                headers: {'Content-Type': 'application/x-www-form-urlencoded'}
            });

            // 2. 保存 Token 到状态和 LocalStorage
            setToken(data.access_token);

            // 3. 并行获取用户信息
            await fetchUserInfo();

            return true;
        } catch (error) {
            // 错误已由 Axios 拦截器处理，此处只需中断流程
            throw error;
        } finally {
            isLoading.value = false;
        }
    }

    /**
     * 获取当前用户信息
     * @description 使用当前 Token 换取 User Profile
     */
    async function fetchUserInfo() {
        try {
            // URL 对应后端 backend/app/api/v1/endpoints/users.py 中的 /users/me
            const user = await apiService.get<any, User>('/users/me');
            userInfo.value = user;
        } catch (error) {
            // 如果获取用户信息失败（如 Token 失效），执行登出清理
            logout();
            throw error;
        }
    }

    /**
     * 注册动作
     */
    async function register(registerForm: RegisterRequest) {
        isLoading.value = true;
        try {
            // URL 对应后端 backend/app/api/v1/endpoints/users.py 中的 /users/
            await apiService.post<any, User>('/users/', registerForm);
            // 注册成功后通常不需要自动登录，或者由前端引导去登录页
        } finally {
            isLoading.value = false;
        }
    }

    /**
     * 登出动作
     * @description 清除状态和本地存储，重置路由状态，清空播放器
     */
    function logout() {
        token.value = null;
        userInfo.value = null;
        localStorage.removeItem(TOKEN_KEY);
        // 清空播放器状态，防止切换账号后自动播放
        const playerStore = usePlayerStore();
        playerStore.clearPlaylist();
        // 这里通常会结合 Router 跳转到 /login，将在组件层或 Router Guard 中处理
    }

    /**
     * 内部方法：设置 Token
     */
    function setToken(newToken: string) {
        token.value = newToken;
        localStorage.setItem(TOKEN_KEY, newToken);
    }

    return {
        token,
        userInfo,
        isLoading,
        isAuthenticated,
        isAdmin,
        login,
        register,
        fetchUserInfo,
        logout
    };
});