<script setup lang="ts">
/**
 * 红心收藏按钮组件
 *
 * 功能:
 * - 显示当前收藏状态
 * - 点击切换收藏/取消收藏
 * - 上报 LIKE 交互事件
 *
 * 设计原则:
 * 1. 复用性: 可用于播放器和音乐卡片
 * 2. 响应式: 状态变化自动更新 UI
 * 3. 防抖: 避免频繁点击导致的重复请求
 */

import {ref, onMounted, watch} from 'vue';
import {NIcon, NButton} from 'naive-ui';
import {Heart, HeartOutline} from '@vicons/ionicons5';

import {musicApi} from '@/api/music';
import {InteractionType} from '@/types/entity';

// ==========================================================================
// Props
// ==========================================================================

const props = defineProps<{
    musicId: number;
}>();

// ==========================================================================
// 状态
// ==========================================================================

// 是否已收藏
const isLiked = ref(false);

// 是否正在加载
const isLoading = ref(false);

// ==========================================================================
// 方法
// ==========================================================================

/**
 * 检查收藏状态
 */
const checkLikeStatus = async () => {
    if (!props.musicId) return;

    try {
        const response = await musicApi.checkLikeStatus(props.musicId);
        isLiked.value = response.liked;
    } catch (error) {
        // 查询失败时默认为未收藏
        console.error('检查收藏状态失败:', error);
        isLiked.value = false;
    }
};

/**
 * 切换收藏状态
 */
const toggleLike = async () => {
    if (isLoading.value || !props.musicId) return;

    isLoading.value = true;

    try {
        if (isLiked.value) {
            // 取消收藏
            await musicApi.removeLike(props.musicId);
            isLiked.value = false;
        } else {
            // 上报收藏事件
            await musicApi.recordInteraction({
                music_id: props.musicId,
                interaction_type: InteractionType.LIKE,
            });
            isLiked.value = true;
        }
    } catch (error) {
        console.error('收藏操作失败:', error);
    } finally {
        isLoading.value = false;
    }
};

// ==========================================================================
// 生命周期
// ==========================================================================

// 组件挂载时检查收藏状态
onMounted(() => {
    checkLikeStatus();
});

// 监听 musicId 变化
watch(() => props.musicId, () => {
    checkLikeStatus();
});
</script>

<template>
    <n-button
        quaternary
        circle
        size="small"
        :loading="isLoading"
        @click.stop="toggleLike"
    >
        <template #icon>
            <n-icon :size="18" :color="isLiked ? '#e74c3c' : undefined">
                <Heart v-if="isLiked" />
                <HeartOutline v-else />
            </n-icon>
        </template>
    </n-button>
</template>

<style scoped>
/* 红心按钮动画效果 */
:deep(.n-icon) {
    transition: transform 0.2s ease;
}

:deep(.n-button:hover .n-icon) {
    transform: scale(1.1);
}

:deep(.n-button:active .n-icon) {
    transform: scale(0.95);
}
</style>