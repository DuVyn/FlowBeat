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