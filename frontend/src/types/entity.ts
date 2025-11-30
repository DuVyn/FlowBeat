/**
 * 用户角色枚举
 * 对应后端 app.models.user.UserRole
 */
export enum UserRole {
    ADMIN = 'ADMIN',
    USER = 'USER',
}

/**
 * 用户实体接口
 * 对应后端 app.schemas.user.UserResponse
 * @description 用于前端展示用户信息，包含ID、用户名、邮箱和角色
 */
export interface User {
    id: number;
    email: string;
    username: string;
    role: UserRole;
    is_active: boolean;
    // 头像字段可能为空，后续阶段对接 MinIO 后使用
    avatar_url?: string | null;
}

export interface Artist {
    id: number;
    name: string;
    bio?: string;
    avatar_url?: string;
}

export interface Album {
    id: number;
    title: string;
    release_date: string;
    artist_id: number;
    cover_url?: string;
    artist?: Artist; // 嵌套对象
}

export interface Music {
    id: number;
    title: string;
    duration: number;
    track_number: number;
    file_url: string;
    album_id: number;
    album?: Album;   // 嵌套对象
    created_at: string; // ISO 日期时间字符串
}

/**
 * 分页音乐列表响应
 * 对应后端 app.schemas.music.MusicListResponse
 */
export interface MusicListResponse {
    items: Music[];
    total: number;
}