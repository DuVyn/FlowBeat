<script setup lang="ts">
/**
 * 底部固定播放控制条组件
 *
 * 功能:
 * - 显示当前播放音乐信息
 * - 播放/暂停控制
 * - 上一曲/下一曲切换
 * - 进度条拖动
 * - 音量调节
 * - 播放模式切换
 * - 打开播放列表
 *
 * 交互事件上报:
 * - 播放完成时上报 PLAY 事件
 * - 跳过音乐时上报 SKIP 事件
 */

import {watch, computed} from 'vue';
import {
    NSlider,
    NIcon,
    NTooltip,
    NSpin,
} from 'naive-ui';
import {
    Play,
    Pause,
    PlaySkipBack,
    PlaySkipForward,
    VolumeHigh,
    VolumeMute,
    List,
    Repeat,
    Shuffle,
    MusicalNotes,
} from '@vicons/ionicons5';

import {useAudio} from '@/composables/useAudio';
import {usePlayerStore, PlayMode} from '@/stores/playerStore';
import {musicApi} from '@/api/music';
import {InteractionType} from '@/types/entity';
import LikeButton from '@/components/common/LikeButton.vue';

// ==========================================================================
// Store 和 Composables
// ==========================================================================

const playerStore = usePlayerStore();

// 音频控制 Hook
const {
    isPlaying,
    currentTime,
    duration,
    volume,
    isLoading,
    play,
    pause,
    seek,
    setVolume,
    loadTrack,
} = useAudio({
    onEnded: handleTrackEnded,
    onError: handleError,
});

// ==========================================================================
// 计算属性
// ==========================================================================

/**
 * 格式化时间为 mm:ss 格式
 */
const formatTime = (seconds: number): string => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

/**
 * 当前播放时间格式化
 */
const currentTimeFormatted = computed(() => formatTime(currentTime.value));

/**
 * 总时长格式化
 */
const durationFormatted = computed(() => formatTime(duration.value));

/**
 * 进度百分比
 */
const progressPercent = computed(() => {
    if (duration.value === 0) return 0;
    return (currentTime.value / duration.value) * 100;
});

/**
 * 播放模式图标
 */
const playModeIcon = computed(() => {
    switch (playerStore.playMode) {
        case PlayMode.REPEAT_ONE:
            return Repeat; // 使用同一个图标，通过样式区分
        case PlayMode.SHUFFLE:
            return Shuffle;
        default:
            return Repeat;
    }
});

/**
 * 播放模式提示文字
 */
const playModeTooltip = computed(() => {
    switch (playerStore.playMode) {
        case PlayMode.REPEAT_ONE:
            return '单曲循环';
        case PlayMode.SHUFFLE:
            return '随机播放';
        default:
            return '顺序播放';
    }
});

/**
 * 是否静音
 */
const isMuted = computed(() => volume.value === 0);

/**
 * 当前音乐的艺术家名称
 */
const artistName = computed(() => {
    return playerStore.currentTrack?.album?.artist?.name || '未知艺术家';
});

/**
 * 当前音乐的封面
 */
const coverUrl = computed(() => {
    return playerStore.currentTrack?.album?.cover_url || '/default-cover.png';
});

// ==========================================================================
// 事件处理
// ==========================================================================

/**
 * 播放完成事件处理
 * 上报 PLAY 交互并自动播放下一曲
 */
async function handleTrackEnded() {
    // 上报播放完成事件
    if (playerStore.currentTrack) {
        try {
            await musicApi.recordInteraction({
                music_id: playerStore.currentTrack.id,
                interaction_type: InteractionType.PLAY,
            });
        } catch (error) {
            console.error('上报播放事件失败:', error);
        }
    }

    // 自动播放下一曲
    const nextTrack = playerStore.playNext();
    if (nextTrack) {
        loadTrack(nextTrack.file_url);
        await play();
    } else {
        playerStore.setPlaying(false);
    }
}

/**
 * 错误处理
 */
function handleError(error: Error) {
    console.error('音频播放错误:', error);
}

/**
 * 上一曲
 */
async function handlePrevious() {
    const prevTrack = playerStore.playPrevious();
    if (prevTrack) {
        loadTrack(prevTrack.file_url);
        await play();
    }
}

/**
 * 下一曲
 * 如果是用户主动跳过，上报 SKIP 事件
 */
async function handleNext() {
    // 上报跳过事件 (仅当当前有播放曲目且正在播放时)
    if (playerStore.currentTrack && isPlaying.value) {
        try {
            await musicApi.recordInteraction({
                music_id: playerStore.currentTrack.id,
                interaction_type: InteractionType.SKIP,
            });
        } catch (error) {
            console.error('上报跳过事件失败:', error);
        }
    }

    const nextTrack = playerStore.playNext();
    if (nextTrack) {
        loadTrack(nextTrack.file_url);
        await play();
    }
}

/**
 * 进度条拖动
 */
function handleProgressChange(value: number) {
    const targetTime = (value / 100) * duration.value;
    seek(targetTime);
}

/**
 * 音量调节
 */
function handleVolumeChange(value: number) {
    setVolume(value / 100);
}

/**
 * 切换静音
 */
let previousVolume = 1;
function toggleMute() {
    if (isMuted.value) {
        setVolume(previousVolume);
    } else {
        previousVolume = volume.value;
        setVolume(0);
    }
}

/**
 * 切换播放/暂停
 */
async function handleTogglePlay() {
    if (!playerStore.currentTrack) return;

    if (isPlaying.value) {
        pause();
    } else {
        await play();
    }
}

// ==========================================================================
// 监听器
// ==========================================================================

// 同步播放状态到 Store
watch(isPlaying, (playing) => {
    playerStore.setPlaying(playing);
});

// 监听当前曲目变化，自动加载新音频
watch(() => playerStore.currentTrack, async (newTrack, oldTrack) => {
    if (newTrack && newTrack.id !== oldTrack?.id) {
        loadTrack(newTrack.file_url);
        await play();
    }
}, {immediate: true});
</script>

<template>
    <div class="audio-player">
        <!-- 有歌曲时显示完整播放器 -->
        <template v-if="playerStore.currentTrack">
            <!-- 左侧: 音乐信息 -->
            <div class="player-info">
                <img
                    :src="coverUrl"
                    alt="封面"
                    class="cover-image"
                />
                <div class="track-info">
                    <div class="track-title">{{ playerStore.currentTrack.title }}</div>
                    <div class="track-artist">{{ artistName }}</div>
                </div>
                <LikeButton
                    v-if="playerStore.currentTrack"
                    :music-id="playerStore.currentTrack.id"
                />
            </div>

            <!-- 中间: 播放控制 -->
            <div class="player-controls">
                <div class="control-buttons">
                    <n-tooltip trigger="hover">
                        <template #trigger>
                            <button
                                class="control-btn"
                                :disabled="!playerStore.hasPrevious"
                                @click="handlePrevious"
                            >
                                <n-icon :size="20"><PlaySkipBack /></n-icon>
                            </button>
                        </template>
                        上一曲
                    </n-tooltip>

                    <button
                        class="control-btn play-btn"
                        @click="handleTogglePlay"
                    >
                        <n-spin v-if="isLoading" :size="20" />
                        <n-icon v-else :size="28">
                            <Pause v-if="isPlaying" />
                            <Play v-else />
                        </n-icon>
                    </button>

                    <n-tooltip trigger="hover">
                        <template #trigger>
                            <button
                                class="control-btn"
                                :disabled="!playerStore.hasNext"
                                @click="handleNext"
                            >
                                <n-icon :size="20"><PlaySkipForward /></n-icon>
                            </button>
                        </template>
                        下一曲
                    </n-tooltip>
                </div>

                <!-- 进度条 -->
                <div class="progress-bar">
                    <span class="time-label">{{ currentTimeFormatted }}</span>
                    <n-slider
                        :value="progressPercent"
                        :step="0.1"
                        :tooltip="false"
                        @update:value="handleProgressChange"
                    />
                    <span class="time-label">{{ durationFormatted }}</span>
                </div>
            </div>

            <!-- 右侧: 附加控制 -->
            <div class="player-extra">
                <n-tooltip trigger="hover">
                    <template #trigger>
                        <button
                            class="control-btn"
                            :class="{ 'mode-active': playerStore.playMode !== PlayMode.SEQUENTIAL }"
                            @click="playerStore.togglePlayMode"
                        >
                            <n-icon :size="18">
                                <component :is="playModeIcon" />
                            </n-icon>
                        </button>
                    </template>
                    {{ playModeTooltip }}
                </n-tooltip>

                <div class="volume-control">
                    <button class="control-btn" @click="toggleMute">
                        <n-icon :size="18">
                            <VolumeMute v-if="isMuted" />
                            <VolumeHigh v-else />
                        </n-icon>
                    </button>
                    <n-slider
                        :value="volume * 100"
                        :step="1"
                        :tooltip="false"
                        style="width: 80px"
                        @update:value="handleVolumeChange"
                    />
                </div>

                <n-tooltip trigger="hover">
                    <template #trigger>
                        <button class="control-btn" @click="playerStore.togglePlaylistVisible">
                            <n-icon :size="18"><List /></n-icon>
                        </button>
                    </template>
                    播放列表
                </n-tooltip>
            </div>
        </template>

        <!-- 无歌曲时显示占位状态 -->
        <template v-else>
            <div class="player-placeholder">
                <n-icon :size="24" class="placeholder-icon"><MusicalNotes /></n-icon>
                <span class="placeholder-text">选择一首歌曲开始播放</span>
            </div>
        </template>
    </div>
</template>

<style scoped>
.audio-player {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 80px;
    background: var(--n-color);
    border-top: 1px solid var(--n-border-color);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    z-index: 1000;
}

/* 左侧音乐信息 */
.player-info {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 200px;
}

.cover-image {
    width: 56px;
    height: 56px;
    border-radius: 4px;
    object-fit: cover;
}

.track-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.track-title {
    font-size: 14px;
    font-weight: 500;
    color: var(--n-text-color);
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.track-artist {
    font-size: 12px;
    color: var(--n-text-color-3);
}

/* 中间播放控制 */
.player-controls {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    flex: 2;
    max-width: 600px;
}

.control-buttons {
    display: flex;
    align-items: center;
    gap: 16px;
}

.control-btn {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--n-text-color);
    padding: 8px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.control-btn:hover {
    background: var(--n-color-hover);
}

.control-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.control-btn.mode-active {
    color: var(--n-primary-color);
}

.play-btn {
    width: 40px;
    height: 40px;
    background: var(--n-primary-color);
    color: white;
}

.play-btn:hover {
    background: var(--n-primary-color-hover);
}

.progress-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
}

.time-label {
    font-size: 12px;
    color: var(--n-text-color-3);
    min-width: 40px;
    text-align: center;
}

/* 右侧附加控制 */
.player-extra {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    justify-content: flex-end;
    min-width: 200px;
}

.volume-control {
    display: flex;
    align-items: center;
    gap: 4px;
}

/* 占位状态 */
.player-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    width: 100%;
    color: var(--n-text-color-3);
}

.placeholder-icon {
    opacity: 0.6;
}

.placeholder-text {
    font-size: 14px;
}
</style>