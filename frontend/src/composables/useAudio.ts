/**
 * 音频控制组合式函数
 *
 * 封装 HTML5 Audio API 的响应式控制逻辑，提供:
 * - 播放/暂停/跳转控制
 * - 音量调节
 * - 播放进度追踪
 * - 缓冲状态监控
 *
 * 设计原则:
 * 1. 响应式封装: 所有状态均为 Vue ref，可直接在模板中使用
 * 2. 事件解耦: 通过回调函数暴露关键事件，便于上层组件处理业务逻辑
 * 3. 资源管理: 提供清理函数，防止内存泄漏
 */

import {ref, onUnmounted, watch} from 'vue';

/**
 * 音频事件回调配置
 */
export interface AudioCallbacks {
    onEnded?: () => void;        // 播放结束回调
    onError?: (error: Error) => void;  // 错误回调
    onTimeUpdate?: (currentTime: number) => void;  // 时间更新回调
}

/**
 * useAudio 返回类型
 */
export interface UseAudioReturn {
    // 状态
    isPlaying: ReturnType<typeof ref<boolean>>;
    currentTime: ReturnType<typeof ref<number>>;
    duration: ReturnType<typeof ref<number>>;
    volume: ReturnType<typeof ref<number>>;
    buffered: ReturnType<typeof ref<number>>;
    isLoading: ReturnType<typeof ref<boolean>>;

    // 方法
    play: () => Promise<void>;
    pause: () => void;
    togglePlay: () => Promise<void>;
    seek: (time: number) => void;
    setVolume: (vol: number) => void;
    loadTrack: (url: string) => void;
    cleanup: () => void;
}

/**
 * 音频控制 Hook
 *
 * 为什么独立封装:
 * 播放器逻辑复杂且与 UI 无关，抽取为 Hook 可以:
 * 1. 保持 UI 组件轻量化
 * 2. 便于单元测试
 * 3. 支持多组件复用
 *
 * @param callbacks 事件回调配置
 * @returns 响应式状态和控制方法
 */
export function useAudio(callbacks: AudioCallbacks = {}): UseAudioReturn {
    // ==========================================================================
    // 响应式状态
    // ==========================================================================

    // 播放状态: 是否正在播放
    const isPlaying = ref(false);

    // 当前播放时间 (秒)
    const currentTime = ref(0);

    // 音频总时长 (秒)
    const duration = ref(0);

    // 音量: 0-1 范围
    const volume = ref(1);

    // 缓冲进度: 0-100 百分比
    const buffered = ref(0);

    // 加载状态: 是否正在加载音频
    const isLoading = ref(false);

    // ==========================================================================
    // 内部状态
    // ==========================================================================

    // 音频实例
    // 为什么使用 let 而非 ref: Audio 对象不需要响应式，避免额外开销
    let audio: HTMLAudioElement | null = null;

    // ==========================================================================
    // 事件处理器
    // ==========================================================================

    /**
     * 时间更新事件处理
     * 频率: 约每秒触发 4-60 次 (取决于浏览器实现)
     */
    const handleTimeUpdate = () => {
        if (audio) {
            currentTime.value = audio.currentTime;
            callbacks.onTimeUpdate?.(audio.currentTime);
        }
    };

    /**
     * 元数据加载完成事件处理
     * 此时可获取音频时长
     */
    const handleLoadedMetadata = () => {
        if (audio) {
            duration.value = audio.duration;
            isLoading.value = false;
        }
    };

    /**
     * 播放结束事件处理
     */
    const handleEnded = () => {
        isPlaying.value = false;
        currentTime.value = 0;
        callbacks.onEnded?.();
    };

    /**
     * 播放事件处理
     */
    const handlePlay = () => {
        isPlaying.value = true;
    };

    /**
     * 暂停事件处理
     */
    const handlePause = () => {
        isPlaying.value = false;
    };

    /**
     * 缓冲进度更新事件处理
     */
    const handleProgress = () => {
        if (audio && audio.buffered.length > 0) {
            // 获取最后一个缓冲区间的结束位置
            const bufferedEnd = audio.buffered.end(audio.buffered.length - 1);
            buffered.value = duration.value > 0
                ? (bufferedEnd / duration.value) * 100
                : 0;
        }
    };

    /**
     * 等待数据事件处理 (缓冲中)
     */
    const handleWaiting = () => {
        isLoading.value = true;
    };

    /**
     * 可播放事件处理 (缓冲完成)
     */
    const handleCanPlay = () => {
        isLoading.value = false;
    };

    /**
     * 错误事件处理
     */
    const handleError = () => {
        isLoading.value = false;
        isPlaying.value = false;
        const error = new Error('音频加载失败');
        callbacks.onError?.(error);
    };

    // ==========================================================================
    // 控制方法
    // ==========================================================================

    /**
     * 加载音轨
     * @param url 音频文件 URL
     */
    const loadTrack = (url: string) => {
        // 清理旧实例
        cleanup();

        // 创建新的 Audio 实例
        audio = new Audio(url);
        isLoading.value = true;
        currentTime.value = 0;
        duration.value = 0;
        buffered.value = 0;

        // 设置初始音量
        audio.volume = volume.value;

        // 绑定事件监听器
        audio.addEventListener('timeupdate', handleTimeUpdate);
        audio.addEventListener('loadedmetadata', handleLoadedMetadata);
        audio.addEventListener('ended', handleEnded);
        audio.addEventListener('play', handlePlay);
        audio.addEventListener('pause', handlePause);
        audio.addEventListener('progress', handleProgress);
        audio.addEventListener('waiting', handleWaiting);
        audio.addEventListener('canplay', handleCanPlay);
        audio.addEventListener('error', handleError);
    };

    /**
     * 播放
     */
    const play = async (): Promise<void> => {
        if (audio) {
            try {
                await audio.play();
            } catch (error) {
                // 处理自动播放策略限制
                // 现代浏览器要求用户交互后才能播放音频
                console.error('播放失败:', error);
                callbacks.onError?.(error as Error);
            }
        }
    };

    /**
     * 暂停
     */
    const pause = () => {
        if (audio) {
            audio.pause();
        }
    };

    /**
     * 切换播放/暂停状态
     */
    const togglePlay = async (): Promise<void> => {
        if (isPlaying.value) {
            pause();
        } else {
            await play();
        }
    };

    /**
     * 跳转到指定时间
     * @param time 目标时间 (秒)
     */
    const seek = (time: number) => {
        if (audio) {
            // 边界检查
            const clampedTime = Math.max(0, Math.min(time, audio.duration || 0));
            audio.currentTime = clampedTime;
            currentTime.value = clampedTime;
        }
    };

    /**
     * 设置音量
     * @param vol 音量值 (0-1)
     */
    const setVolume = (vol: number) => {
        const clampedVol = Math.max(0, Math.min(1, vol));
        volume.value = clampedVol;
        if (audio) {
            audio.volume = clampedVol;
        }
    };

    /**
     * 清理资源
     * 移除事件监听器并释放 Audio 实例
     */
    const cleanup = () => {
        if (audio) {
            // 暂停播放
            audio.pause();

            // 移除所有事件监听器
            audio.removeEventListener('timeupdate', handleTimeUpdate);
            audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
            audio.removeEventListener('ended', handleEnded);
            audio.removeEventListener('play', handlePlay);
            audio.removeEventListener('pause', handlePause);
            audio.removeEventListener('progress', handleProgress);
            audio.removeEventListener('waiting', handleWaiting);
            audio.removeEventListener('canplay', handleCanPlay);
            audio.removeEventListener('error', handleError);

            // 释放资源
            audio.src = '';
            audio = null;
        }

        // 重置状态
        isPlaying.value = false;
        currentTime.value = 0;
        duration.value = 0;
        buffered.value = 0;
        isLoading.value = false;
    };

    // ==========================================================================
    // 生命周期管理
    // ==========================================================================

    // 组件卸载时自动清理
    onUnmounted(() => {
        cleanup();
    });

    // 监听音量变化并同步到 Audio 实例
    watch(volume, (newVol) => {
        if (audio) {
            audio.volume = newVol;
        }
    });

    return {
        // 状态
        isPlaying,
        currentTime,
        duration,
        volume,
        buffered,
        isLoading,

        // 方法
        play,
        pause,
        togglePlay,
        seek,
        setVolume,
        loadTrack,
        cleanup,
    };
}