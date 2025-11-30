/* File: frontend/src/router/index.ts */
import {createRouter, createWebHistory, type RouteRecordRaw} from 'vue-router';
import {useUserStore} from '@/stores/userStore';
// 引入 NProgress 进度条，需 npm install nprogress @types/nprogress
import NProgress from 'nprogress';
import 'nprogress/nprogress.css';

import MainLayout from '@/components/layout/MainLayout.vue';
import Login from '@/views/auth/Login.vue';
import Register from '@/views/auth/Register.vue';
import UserProfile from '@/views/profile/UserProfile.vue';

// 配置 NProgress
NProgress.configure({showSpinner: false});

const routes: RouteRecordRaw[] = [
    {
        path: '/login',
        name: 'Login',
        component: Login,
        meta: {public: true}
    },
    {
        path: '/register',
        name: 'Register',
        component: Register,
        meta: {public: true}
    },
    {
        path: '/',
        component: MainLayout,
        redirect: '/discovery', // 默认跳转到发现页
        children: [
            {
                path: 'discovery',
                name: 'discovery',
                // 懒加载组件，优化首屏性能
                component: () => import('@/views/discovery/Discovery.vue'),
            },
            {
                path: 'library',
                name: 'library',
                component: () => import('@/views/library/LibraryIndex.vue'),
            },
            {
                path: 'favorites',
                name: 'favorites',
                component: () => import('@/views/library/FavoritesPage.vue'),
            },
            {
                path: 'playlist/:id',
                name: 'playlist-detail',
                component: () => import('@/views/library/PlaylistDetail.vue'),
            },
            {
                path: 'profile',
                name: 'profile',
                component: UserProfile
            }
        ]
    },
    // 404 捕获
    {
        path: '/:pathMatch(.*)*',
        redirect: '/'
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

/**
 * 全局路由守卫
 * @description 负责鉴权逻辑
 */
router.beforeEach(async (to, _from, next) => {
    NProgress.start();

    const userStore = useUserStore();
    const isAuthenticated = userStore.isAuthenticated;

    // 1. 如果访问的是公开页面 (meta.public)
    if (to.meta.public) {
        if (isAuthenticated) {
            // 已登录用户访问登录页 -> 踢回主页
            next('/');
        } else {
            next();
        }
        return;
    }

    // 2. 访问私有页面
    if (!isAuthenticated) {
        // 未登录 -> 重定向到登录页，并记录来源以便登录后跳回
        next(`/login?redirect=${to.path}`);
    } else {
        // 已登录，检查是否已有用户信息（防止刷新丢失）
        if (!userStore.userInfo) {
            try {
                await userStore.fetchUserInfo();
                next();
            } catch (error) {
                // Token 失效，userStore 内部会处理 logout
                next('/login');
            }
        } else {
            next();
        }
    }
});

router.afterEach(() => {
    NProgress.done();
});

export default router;