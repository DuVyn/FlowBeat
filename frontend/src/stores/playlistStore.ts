/**
 * 歌单状态管理
 *
 * 使用 Pinia 管理用户歌单数据，包括:
 * - 用户歌单列表
 * - 歌单 CRUD 操作
 */

import {defineStore} from 'pinia';
import {ref} from 'vue';
import type {Playlist, PlaylistDetail} from '@/types/entity';
import {musicApi} from '@/api/music';

export const usePlaylistStore = defineStore('playlist', () => {
    // 用户歌单列表
    const playlists = ref<Playlist[]>([]);
    
    // 当前查看的歌单详情
    const currentPlaylist = ref<PlaylistDetail | null>(null);
    
    // 加载状态
    const isLoading = ref(false);

    /**
     * 获取用户歌单列表
     */
    const fetchPlaylists = async () => {
        isLoading.value = true;
        try {
            const response = await musicApi.getUserPlaylists();
            playlists.value = response.items;
        } catch (error) {
            console.error('获取歌单列表失败:', error);
        } finally {
            isLoading.value = false;
        }
    };

    /**
     * 获取歌单详情
     */
    const fetchPlaylistDetail = async (id: number) => {
        isLoading.value = true;
        try {
            currentPlaylist.value = await musicApi.getPlaylistDetail(id);
        } catch (error) {
            console.error('获取歌单详情失败:', error);
            currentPlaylist.value = null;
        } finally {
            isLoading.value = false;
        }
    };

    /**
     * 创建歌单
     */
    const createPlaylist = async (name: string, description?: string) => {
        try {
            const newPlaylist = await musicApi.createPlaylist({name, description});
            playlists.value.unshift(newPlaylist);
            return newPlaylist;
        } catch (error) {
            console.error('创建歌单失败:', error);
            throw error;
        }
    };

    /**
     * 更新歌单
     */
    const updatePlaylist = async (id: number, name?: string, description?: string) => {
        try {
            const updated = await musicApi.updatePlaylist(id, {name, description});
            const index = playlists.value.findIndex(p => p.id === id);
            if (index !== -1) {
                playlists.value[index] = updated;
            }
            if (currentPlaylist.value?.id === id) {
                currentPlaylist.value = {...currentPlaylist.value, ...updated};
            }
            return updated;
        } catch (error) {
            console.error('更新歌单失败:', error);
            throw error;
        }
    };

    /**
     * 删除歌单
     */
    const deletePlaylist = async (id: number) => {
        try {
            await musicApi.deletePlaylist(id);
            playlists.value = playlists.value.filter(p => p.id !== id);
            if (currentPlaylist.value?.id === id) {
                currentPlaylist.value = null;
            }
        } catch (error) {
            console.error('删除歌单失败:', error);
            throw error;
        }
    };

    /**
     * 添加歌曲到歌单
     */
    const addSongToPlaylist = async (playlistId: number, musicId: number) => {
        try {
            await musicApi.addSongToPlaylist(playlistId, musicId);
            // 更新歌单歌曲数量
            const playlist = playlists.value.find(p => p.id === playlistId);
            if (playlist) {
                playlist.song_count++;
            }
        } catch (error) {
            console.error('添加歌曲到歌单失败:', error);
            throw error;
        }
    };

    /**
     * 从歌单移除歌曲
     */
    const removeSongFromPlaylist = async (playlistId: number, musicId: number) => {
        try {
            await musicApi.removeSongFromPlaylist(playlistId, musicId);
            // 更新歌单歌曲数量
            const playlist = playlists.value.find(p => p.id === playlistId);
            if (playlist) {
                playlist.song_count = Math.max(0, playlist.song_count - 1);
            }
            // 如果当前在歌单详情页，也更新
            if (currentPlaylist.value?.id === playlistId) {
                currentPlaylist.value.songs = currentPlaylist.value.songs.filter(s => s.id !== musicId);
                currentPlaylist.value.song_count = currentPlaylist.value.songs.length;
            }
        } catch (error) {
            console.error('从歌单移除歌曲失败:', error);
            throw error;
        }
    };

    return {
        playlists,
        currentPlaylist,
        isLoading,
        fetchPlaylists,
        fetchPlaylistDetail,
        createPlaylist,
        updatePlaylist,
        deletePlaylist,
        addSongToPlaylist,
        removeSongFromPlaylist,
    };
});