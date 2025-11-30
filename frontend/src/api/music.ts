import request from './axios';
import type {Artist, Album, Music, MusicListResponse, InteractionCreate, InteractionResponse, LikeStatusResponse, Playlist, PlaylistDetail, PlaylistListResponse, PlaylistCreateRequest, PlaylistUpdateRequest} from '@/types/entity';

export const musicApi = {
    // 获取艺术家列表
    getArtists: () => request.get<any, Artist[]>('/music/artists'),

    // 创建艺术家
    createArtist: (data: { name: string; bio?: string }) =>
        request.post<any, Artist>('/music/artists', data),

    // 获取专辑列表
    getAlbumsByArtist: (artistId: number) =>
        request.get<any, Album[]>(`/music/artists/${artistId}/albums`),

    // 创建专辑
    createAlbum: (data: { title: string; release_date: string; artist_id: number }) =>
        request.post<any, Album>('/music/albums', data),

    // 上传音乐 (Multipart)
    uploadMusic: (file: File, meta: { title: string; duration: number; album_id: number; track_number?: number }) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', meta.title);
        formData.append('duration', meta.duration.toString());
        formData.append('album_id', meta.album_id.toString());
        if (meta.track_number) {
            formData.append('track_number', meta.track_number.toString());
        }

        return request.post<any, Music>('/music/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    // 获取音乐列表
    getMusicList: (skip = 0, limit = 50) =>
        request.get<any, MusicListResponse>('/music/', {params: {skip, limit}}),

    // 删除音乐
    deleteMusic: (id: number) =>
        request.delete<any, void>(`/music/${id}`),

    /**
     * 记录用户交互行为
     * 用于前端播放器事件上报
     *
     * @param data 交互数据，包含音乐ID和交互类型
     * @returns 创建的交互记录
     */
    recordInteraction: (data: InteractionCreate) =>
        request.post<any, InteractionResponse>('/music/interactions', data),

    /**
     * 检查用户是否已收藏某音乐
     * 用于展示收藏状态
     *
     * @param musicId 音乐ID
     * @returns 收藏状态
     */
    checkLikeStatus: (musicId: number) =>
        request.get<any, LikeStatusResponse>(`/music/interactions/like-status/${musicId}`),

    /**
     * 获取用户收藏的音乐列表
     *
     * @param skip 跳过的记录数
     * @param limit 返回数量限制
     * @returns 音乐列表
     */
    getLikedMusic: (skip = 0, limit = 50) =>
        request.get<any, MusicListResponse>('/music/interactions/liked', {params: {skip, limit}}),

    /**
     * 取消用户对某音乐的收藏
     *
     * @param musicId 音乐ID
     */
    removeLike: (musicId: number) =>
        request.delete<any, void>(`/music/interactions/like/${musicId}`),

    /**
     * 搜索音乐
     * 按歌曲名称或歌手名称进行模糊搜索
     *
     * @param q 搜索关键词
     * @param skip 跳过的记录数
     * @param limit 返回数量限制
     * @returns 音乐列表
     */
    searchMusic: (q: string, skip = 0, limit = 20) =>
        request.get<any, MusicListResponse>('/music/search', {params: {q, skip, limit}}),

    // --- Playlist API ---

    /**
     * 创建歌单
     */
    createPlaylist: (data: PlaylistCreateRequest) =>
        request.post<any, Playlist>('/music/playlists', data),

    /**
     * 获取用户歌单列表
     */
    getUserPlaylists: (skip = 0, limit = 50) =>
        request.get<any, PlaylistListResponse>('/music/playlists', {params: {skip, limit}}),

    /**
     * 获取歌单详情
     */
    getPlaylistDetail: (id: number) =>
        request.get<any, PlaylistDetail>(`/music/playlists/${id}`),

    /**
     * 更新歌单
     */
    updatePlaylist: (id: number, data: PlaylistUpdateRequest) =>
        request.put<any, Playlist>(`/music/playlists/${id}`, data),

    /**
     * 删除歌单
     */
    deletePlaylist: (id: number) =>
        request.delete<any, void>(`/music/playlists/${id}`),

    /**
     * 添加歌曲到歌单
     */
    addSongToPlaylist: (playlistId: number, musicId: number) =>
        request.post<any, any>(`/music/playlists/${playlistId}/songs`, {music_id: musicId}),

    /**
     * 从歌单移除歌曲
     */
    removeSongFromPlaylist: (playlistId: number, musicId: number) =>
        request.delete<any, void>(`/music/playlists/${playlistId}/songs/${musicId}`),
};