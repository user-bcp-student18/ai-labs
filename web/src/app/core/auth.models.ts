export interface LoginRequest {
  username: string;
  password: string;
  client: string;
}

export interface AuthUser {
  username?: string;
  displayName?: string;
}

export interface LoginResponse {
  token?: string;
  user?: AuthUser;
}

export interface UserPreferences {
  theme: 'light' | 'dark';
  showTips: boolean;
  compact: boolean;
}
