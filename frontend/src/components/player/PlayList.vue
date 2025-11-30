<script setup lang="ts">
/**
 * 播放列表抽屉组件
 *
 * 功能:
 * - 显示当前播放队列
 * - 点击切换播放曲目
 * - 从队列中移除曲目
 * - 清空队列
 *
 * 设计原则:
 * 1. 响应式: 队列变化自动更新
 * 2. 交互友好: 当前播放曲目高亮
 * 3. 可访问性: 支持键盘操作
 */

import {NDrawer, NDrawerContent, NList, NListItem, NIcon, NButton, NEmpty, NSpace, NText} from 'naive-ui';
import {Trash, Close, Play} from '@vicons/ionicons5';

import {usePlayerStore} from '@/stores/playerStore';
import type {Music} from '@/types/entity';

// ==========================================================================
// Store
// ==========================================================================

const playerStore = usePlayerStore();

// ==========================================================================
// 计算属性
// ==========================================================================

/**
 * 格式化时长
 */
const formatDuration = (seconds: number): string => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

// ==========================================================================
// 事件处理
// ==========================================================================

/**
 * 关闭抽屉
 */
const handleClose = () => {
    playerStore.togglePlaylistVisible();
};

/**
 * 播放指定曲目
 */
const handlePlayTrack = (index: number) => {
    playerStore.jumpTo(index);
};

/**
 * 移除曲目
 */
const handleRemoveTrack = (trackId: number, event: Event) => {
    event.stopPropagation();
    playerStore.removeFromPlaylist(trackId);
};

/**
 * 清空队列
 */
const handleClearPlaylist = () => {
    playerStore.clearPlaylist();
};

/**
 * 获取艺术家名称
 */
const getArtistName = (track: Music): string => {
    return track.album?.artist?.name || '未知艺术家';
};
</script>

<template>
    <n-drawer
        :show="playerStore.isPlaylistVisible"
        :width="360"
        placement="right"
        @update:show="handleClose"
    >
        <n-drawer-content title="播放列表" closable>
            <template #header>
                <n-space justify="space-between" align="center" style="width: 100%">
                    <span>播放列表 ({{ playerStore.queueLength }})</span>
                    <n-button
                        v-if="!playerStore.isEmpty"
                        size="small"
                        quaternary
                        @click="handleClearPlaylist"
                    >
                        <template #icon>
                            <n-icon><Trash /></n-icon>
                        </template>
                        清空
                    </n-button>
                </n-space>
            </template>

            <n-empty
                v-if="playerStore.isEmpty"
                description="播放列表为空"
                style="margin-top: 100px"
            />

            <n-list v-else hoverable clickable>
                <n-list-item
                    v-for="(track, index) in playerStore.playlist"
                    :key="track.id"
                    :class="{'is-current': index === playerStore.currentIndex}"
                    @click="handlePlayTrack(index)"
                >
                    <template #prefix>
                        <div class="track-index">
                            <n-icon
                                v-if="index === playerStore.currentIndex && playerStore.isPlaying"
                                :size="16"
                                color="var(--n-primary-color)"
                            >
                                <Play />
                            </n-icon>
                            <span v-else class="index-number">{{ index + 1 }}</span>
                        </div>
                    </template>

                    <div class="track-item">
                        <div class="track-title">{{ track.title }}</div>
                        <div class="track-meta">
                            <n-text depth="3">{{ getArtistName(track) }}</n-text>
                            <n-text depth="3" style="margin-left: 8px">
                                {{ formatDuration(track.duration) }}
                            </n-text>
                        </div>
                    </div>

                    <template #suffix>
                        <n-button
                            quaternary
                            circle
                            size="small"
                            @click="(e: Event) => handleRemoveTrack(track.id, e)"
                        >
                            <template #icon>
                                <n-icon><Close /></n-icon>
                            </template>
                        </n-button>
                    </template>
                </n-list-item>
            </n-list>
        </n-drawer-content>
    </n-drawer>
</template>

<style scoped>
.track-index {
    width: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.index-number {
    font-size: 12px;
    color: var(--n-text-color-3);
}

.track-item {
    flex: 1;
    min-width: 0;
}

.track-title {
    font-size: 14px;
    color: var(--n-text-color);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.track-meta {
    font-size: 12px;
    margin-top: 4px;
}

.is-current {
    background: var(--n-color-hover);
}

.is-current .track-title {
    color: var(--n-primary-color);
    font-weight: 500;
}
</style>