import request from './axios';
import type {LoginRequest, TokenResponse, RegisterRequest} from '@/types/api';
import type {User} from '@/types/entity';

export const authApi = {
    login: (data: LoginRequest) => {
        const params = new URLSearchParams();
        params.append('username', data.username);
        params.append('password', data.password);
        return request.post<any, TokenResponse>('/auth/login/access-token', params, {
            headers: {'Content-Type': 'application/x-www-form-urlencoded'}
        });
    },

    register: (data: RegisterRequest) => {
        return request.post<any, User>('/users/', data);
    },

    getMe: () => {
        return request.get<any, User>('/users/me');
    }
};