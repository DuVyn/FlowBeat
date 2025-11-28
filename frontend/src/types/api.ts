/**
 * 通用 API 响应结构
 * @description 用于解包后端标准响应，虽然后端 FastAPI 直接返回数据，
 * 但若后端引入了统一的 { code: 200, data: T, msg: "" } 包装结构，需在此处适配。
 * 目前 FlowBeat 后端设计为直接返回 Pydantic Model 序列化后的 JSON，故直接使用泛型。
 */
export type ApiResponse<T> = T;

/**
 * 登录接口响应
 * 对应后端 app.schemas.token.Token
 */
export interface TokenResponse {
    access_token: string;
    token_type: string; // 通常为 "bearer"
}

/**
 * 登录表单数据结构
 * 对应后端 OAuth2PasswordRequestForm
 */
export interface LoginRequest {
    username: string; // 注意：OAuth2 标准表单字段名为 username，实际传的是邮箱
    password: string;
}

/**
 * 注册表单数据结构
 * 对应后端 app.schemas.user.UserCreate
 */
export interface RegisterRequest {
    email: string;
    username: string;
    password: string;
}