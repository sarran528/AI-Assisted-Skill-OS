import axiosClient from './axiosClient';

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user?: { id: string; email: string };
}

export const authApi = {
  register: (data: RegisterRequest) =>
    axiosClient.post<{ user_id: string; email: string }>('/auth/register', data),

  login: (data: LoginRequest) =>
    axiosClient.post<TokenResponse>('/auth/login', data),

  refresh: () =>
    axiosClient.post<TokenResponse>('/auth/refresh'),

  logout: () =>
    axiosClient.post('/auth/logout'),
};
