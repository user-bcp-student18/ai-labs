import { Injectable } from '@angular/core';
import { SESSION_STORAGE_KEYS } from './app-config';
import { AuthUser, UserPreferences } from './auth.models';

const DEFAULT_PREFERENCES: UserPreferences = {
  theme: 'light',
  showTips: true,
  compact: false
};

@Injectable({ providedIn: 'root' })
export class SessionService {
  getToken(): string | null {
    return localStorage.getItem(SESSION_STORAGE_KEYS.token);
  }

  getUser(): AuthUser {
    const storedUser = localStorage.getItem(SESSION_STORAGE_KEYS.user);
    if (!storedUser) {
      return {};
    }

    try {
      const parsedUser: unknown = JSON.parse(storedUser);
      if (isRecord(parsedUser)) {
        return {
          username: readString(parsedUser, 'username'),
          displayName: readString(parsedUser, 'displayName')
        };
      }
      console.warn('Stored session user is invalid');
    } catch (error) {
      console.warn('Stored session user could not be read', error);
    }
    return {};
  }

  getPreferences(): UserPreferences {
    const storedPreferences = localStorage.getItem(SESSION_STORAGE_KEYS.preferences);
    if (!storedPreferences) {
      return { ...DEFAULT_PREFERENCES };
    }

    try {
      const parsedPreferences: unknown = JSON.parse(storedPreferences);
      if (!isRecord(parsedPreferences)) {
        console.warn('Stored preferences are invalid');
        return { ...DEFAULT_PREFERENCES };
      }
      return {
        theme: parsedPreferences.theme === 'dark' ? 'dark' : 'light',
        showTips: typeof parsedPreferences.showTips === 'boolean'
          ? parsedPreferences.showTips
          : DEFAULT_PREFERENCES.showTips,
        compact: typeof parsedPreferences.compact === 'boolean'
          ? parsedPreferences.compact
          : DEFAULT_PREFERENCES.compact
      };
    } catch (error) {
      console.warn('Stored preferences could not be read', error);
      return { ...DEFAULT_PREFERENCES };
    }
  }

  saveSession(token: string, user: AuthUser, preferences: UserPreferences): void {
    localStorage.setItem(SESSION_STORAGE_KEYS.token, token);
    localStorage.setItem(SESSION_STORAGE_KEYS.user, JSON.stringify(user));
    localStorage.setItem(SESSION_STORAGE_KEYS.preferences, JSON.stringify(preferences));
  }

  clearSession(): void {
    localStorage.removeItem(SESSION_STORAGE_KEYS.token);
    localStorage.removeItem(SESSION_STORAGE_KEYS.user);
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function readString(record: Record<string, unknown>, key: string): string | undefined {
  const value = record[key];
  return typeof value === 'string' ? value : undefined;
}
