import request from './axios';
import type {Artist, Album, Music} from '@/types/entity';

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
        request.get<any, Music[]>('/music/', {params: {skip, limit}}),
};