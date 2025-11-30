/**
 * 全局播放器状态管理
 *
 * 使用 Pinia 管理跨组件的播放器状态，包括:
 * - 当前播放曲目
 * - 播放队列
 * - 播放模式 (顺序/随机/单曲循环)
 *
 * 设计原则:
 * 1. 全局单例: 整个应用共享同一个播放状态
 * 2. 持久化: 可选将播放队列保存到 localStorage
 * 3. 响应式: 状态变化自动触发 UI 更新
 */

import {defineStore} from 'pinia';
import {ref, computed} from 'vue';
import type {Music} from '@/types/entity';

/**
 * 播放模式枚举
 */
export enum PlayMode {
    // 顺序播放
    SEQUENTIAL = 'sequential',
    // 单曲循环
    REPEAT_ONE = 'repeat_one',
    // 随机播放
    SHUFFLE = 'shuffle',
}

/**
 * 播放器状态管理 Store
 *
 * 为什么使用 Setup Store 语法:
 * 1. 与 Composition API 风格一致
 * 2. 更灵活的逻辑组织
 * 3. 更好的 TypeScript 类型推断
 */
export const usePlayerStore = defineStore('player', () => {
    // ==========================================================================
    // 状态定义
    // ==========================================================================

    // 当前播放的音乐
    const currentTrack = ref<Music | null>(null);

    // 播放队列
    const playlist = ref<Music[]>([]);

    // 当前播放曲目在队列中的索引
    const currentIndex = ref(-1);

    // 播放模式
    const playMode = ref<PlayMode>(PlayMode.SEQUENTIAL);

    // 是否正在播放 (由 useAudio 控制，此处仅作为状态同步)
    const isPlaying = ref(false);

    // 播放列表抽屉是否可见
    const isPlaylistVisible = ref(false);

    // ==========================================================================
    // 计算属性
    // ==========================================================================

    /**
     * 队列是否为空
     */
    const isEmpty = computed(() => playlist.value.length === 0);

    /**
     * 队列长度
     */
    const queueLength = computed(() => playlist.value.length);

    /**
     * 是否有下一曲
     */
    const hasNext = computed(() => {
        if (isEmpty.value) return false;
        if (playMode.value === PlayMode.REPEAT_ONE) return true;
        if (playMode.value === PlayMode.SHUFFLE) return true;
        return currentIndex.value < playlist.value.length - 1;
    });

    /**
     * 是否有上一曲
     */
    const hasPrevious = computed(() => {
        if (isEmpty.value) return false;
        if (playMode.value === PlayMode.REPEAT_ONE) return true;
        if (playMode.value === PlayMode.SHUFFLE) return true;
        return currentIndex.value > 0;
    });

    // ==========================================================================
    // 核心方法
    // ==========================================================================

    /**
     * 设置播放队列并开始播放
     *
     * @param tracks 音乐列表
     * @param startIndex 起始播放索引
     */
    const setPlaylist = (tracks: Music[], startIndex = 0) => {
        playlist.value = [...tracks];
        if (tracks.length > 0 && startIndex >= 0 && startIndex < tracks.length) {
            currentIndex.value = startIndex;
            currentTrack.value = tracks[startIndex];
        } else {
            currentIndex.value = -1;
            currentTrack.value = null;
        }
    };

    /**
     * 添加音乐到队列末尾
     *
     * @param track 要添加的音乐
     */
    const addToPlaylist = (track: Music) => {
        // 检查是否已存在
        const exists = playlist.value.some(t => t.id === track.id);
        if (!exists) {
            playlist.value.push(track);
        }

        // 如果队列之前为空，自动播放新添加的音乐
        if (playlist.value.length === 1) {
            currentIndex.value = 0;
            currentTrack.value = track;
        }
    };

    /**
     * 从队列中移除音乐
     *
     * @param trackId 要移除的音乐 ID
     */
    const removeFromPlaylist = (trackId: number) => {
        const index = playlist.value.findIndex(t => t.id === trackId);
        if (index === -1) return;

        // 处理移除当前播放曲目的情况
        if (index === currentIndex.value) {
            // 如果是最后一首，切换到前一首
            if (index === playlist.value.length - 1) {
                currentIndex.value = Math.max(0, index - 1);
            }
            // 否则保持索引不变 (实际上会播放下一首)
        } else if (index < currentIndex.value) {
            // 移除的是当前曲目之前的，需要调整索引
            currentIndex.value--;
        }

        playlist.value.splice(index, 1);

        // 更新当前曲目
        if (playlist.value.length === 0) {
            currentTrack.value = null;
            currentIndex.value = -1;
        } else {
            currentTrack.value = playlist.value[currentIndex.value] || null;
        }
    };

    /**
     * 清空播放队列
     */
    const clearPlaylist = () => {
        playlist.value = [];
        currentTrack.value = null;
        currentIndex.value = -1;
        isPlaying.value = false;
    };

    /**
     * 播放指定音乐
     * 如果不在队列中，会添加到队列
     *
     * @param track 要播放的音乐
     */
    const playTrack = (track: Music) => {
        const index = playlist.value.findIndex(t => t.id === track.id);
        if (index === -1) {
            // 不在队列中，添加并播放
            playlist.value.push(track);
            currentIndex.value = playlist.value.length - 1;
        } else {
            // 在队列中，直接跳转
            currentIndex.value = index;
        }
        currentTrack.value = track;
    };

    /**
     * 播放下一曲
     *
     * @returns 下一首音乐，如果没有则返回 null
     */
    const playNext = (): Music | null => {
        if (isEmpty.value) return null;

        let nextIndex: number;

        switch (playMode.value) {
            case PlayMode.REPEAT_ONE:
                // 单曲循环: 保持当前曲目
                nextIndex = currentIndex.value;
                break;

            case PlayMode.SHUFFLE:
                // 随机播放: 随机选择一首 (避免连续播放同一首)
                if (playlist.value.length === 1) {
                    nextIndex = 0;
                } else {
                    do {
                        nextIndex = Math.floor(Math.random() * playlist.value.length);
                    } while (nextIndex === currentIndex.value);
                }
                break;

            case PlayMode.SEQUENTIAL:
            default:
                // 顺序播放: 下一首，到末尾则停止
                if (currentIndex.value >= playlist.value.length - 1) {
                    // 已经是最后一首，不自动循环
                    return null;
                }
                nextIndex = currentIndex.value + 1;
                break;
        }

        currentIndex.value = nextIndex;
        currentTrack.value = playlist.value[nextIndex];
        return currentTrack.value;
    };

    /**
     * 播放上一曲
     *
     * @returns 上一首音乐，如果没有则返回 null
     */
    const playPrevious = (): Music | null => {
        if (isEmpty.value) return null;

        let prevIndex: number;

        switch (playMode.value) {
            case PlayMode.REPEAT_ONE:
                // 单曲循环: 保持当前曲目
                prevIndex = currentIndex.value;
                break;

            case PlayMode.SHUFFLE:
                // 随机播放: 随机选择一首
                if (playlist.value.length === 1) {
                    prevIndex = 0;
                } else {
                    do {
                        prevIndex = Math.floor(Math.random() * playlist.value.length);
                    } while (prevIndex === currentIndex.value);
                }
                break;

            case PlayMode.SEQUENTIAL:
            default:
                // 顺序播放: 上一首，到开头则停止
                if (currentIndex.value <= 0) {
                    return null;
                }
                prevIndex = currentIndex.value - 1;
                break;
        }

        currentIndex.value = prevIndex;
        currentTrack.value = playlist.value[prevIndex];
        return currentTrack.value;
    };

    /**
     * 切换播放模式
     */
    const togglePlayMode = () => {
        const modes = [PlayMode.SEQUENTIAL, PlayMode.REPEAT_ONE, PlayMode.SHUFFLE];
        const currentModeIndex = modes.indexOf(playMode.value);
        const nextModeIndex = (currentModeIndex + 1) % modes.length;
        playMode.value = modes[nextModeIndex];
    };

    /**
     * 设置播放状态
     * 由 AudioPlayer 组件调用，同步播放状态
     */
    const setPlaying = (playing: boolean) => {
        isPlaying.value = playing;
    };

    /**
     * 切换播放列表可见性
     */
    const togglePlaylistVisible = () => {
        isPlaylistVisible.value = !isPlaylistVisible.value;
    };

    /**
     * 跳转到队列中的指定位置播放
     *
     * @param index 目标索引
     */
    const jumpTo = (index: number) => {
        if (index >= 0 && index < playlist.value.length) {
            currentIndex.value = index;
            currentTrack.value = playlist.value[index];
        }
    };

    return {
        // 状态
        currentTrack,
        playlist,
        currentIndex,
        playMode,
        isPlaying,
        isPlaylistVisible,

        // 计算属性
        isEmpty,
        queueLength,
        hasNext,
        hasPrevious,

        // 方法
        setPlaylist,
        addToPlaylist,
        removeFromPlaylist,
        clearPlaylist,
        playTrack,
        playNext,
        playPrevious,
        togglePlayMode,
        setPlaying,
        togglePlaylistVisible,
        jumpTo,
    };
});