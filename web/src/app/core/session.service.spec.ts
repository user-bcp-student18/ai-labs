import '@angular/compiler';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { SESSION_STORAGE_KEYS } from './app-config';
import { SessionService } from './session.service';

class MemoryStorage {
  private readonly values = new Map<string, string>();

  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }

  removeItem(key: string): void {
    this.values.delete(key);
  }
}

describe('SessionService', () => {
  let storage: MemoryStorage;

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns default preferences when none are stored', () => {
    storage = setStorage();
    expect(new SessionService().getPreferences()).toEqual({
      theme: 'light',
      showTips: true,
      compact: false
    });
  });

  it('loads only supported preference values', () => {
    storage = setStorage();
    storage.setItem(SESSION_STORAGE_KEYS.preferences, JSON.stringify({
      theme: 'dark',
      showTips: false,
      compact: true,
      unexpected: 'ignored'
    }));

    expect(new SessionService().getPreferences()).toEqual({
      theme: 'dark',
      showTips: false,
      compact: true
    });
  });

  it('uses defaults and reports malformed stored preferences', () => {
    storage = setStorage();
    storage.setItem(SESSION_STORAGE_KEYS.preferences, '{');
    const warning = vi.spyOn(console, 'warn').mockImplementation(() => undefined);

    expect(new SessionService().getPreferences()).toEqual({
      theme: 'light',
      showTips: true,
      compact: false
    });
    expect(warning).toHaveBeenCalled();
  });

  it('saves and reads session values and clears only session values', () => {
    storage = setStorage();
    const session = new SessionService();
    const user = { username: 'student', displayName: 'Student' };
    const preferences = { theme: 'dark' as const, showTips: false, compact: true };

    session.saveSession('test-token', user, preferences);

    expect(session.getToken()).toBe('test-token');
    expect(session.getUser()).toEqual(user);
    expect(session.getPreferences()).toEqual(preferences);
    session.clearSession();
    expect(session.getToken()).toBeNull();
    expect(session.getUser()).toEqual({});
    expect(session.getPreferences()).toEqual(preferences);
  });

  it('reports malformed stored user data and returns an empty user', () => {
    storage = setStorage();
    storage.setItem(SESSION_STORAGE_KEYS.user, '{');
    const warning = vi.spyOn(console, 'warn').mockImplementation(() => undefined);

    expect(new SessionService().getUser()).toEqual({});
    expect(warning).toHaveBeenCalled();
  });

  it('reports non-object stored user data and returns an empty user', () => {
    storage = setStorage();
    storage.setItem(SESSION_STORAGE_KEYS.user, 'null');
    const warning = vi.spyOn(console, 'warn').mockImplementation(() => undefined);

    expect(new SessionService().getUser()).toEqual({});
    expect(warning).toHaveBeenCalled();
  });

  it('reports non-object preferences and uses defaults', () => {
    storage = setStorage();
    storage.setItem(SESSION_STORAGE_KEYS.preferences, 'null');
    const warning = vi.spyOn(console, 'warn').mockImplementation(() => undefined);

    expect(new SessionService().getPreferences()).toEqual({
      theme: 'light',
      showTips: true,
      compact: false
    });
    expect(warning).toHaveBeenCalled();
  });

  it('returns defaults for stored preference values with invalid types', () => {
    storage = setStorage();
    storage.setItem(SESSION_STORAGE_KEYS.preferences, JSON.stringify({
      theme: 'unexpected',
      showTips: 'yes',
      compact: null
    }));

    expect(new SessionService().getPreferences()).toEqual({
      theme: 'light',
      showTips: true,
      compact: false
    });
  });

  it('keeps the token out of localStorage and out of a new session instance', () => {
    storage = setStorage();
    const session = new SessionService();

    session.saveSession('test-token', { username: 'student' }, {
      theme: 'light',
      showTips: true,
      compact: false
    });

    expect(storage.getItem(SESSION_STORAGE_KEYS.token)).toBeNull();
    expect(new SessionService().getToken()).toBeNull();
  });

  it('removes a token persisted by a previous version', () => {
    storage = setStorage();
    storage.setItem(SESSION_STORAGE_KEYS.token, 'legacy-token');

    expect(new SessionService().getToken()).toBeNull();
    expect(storage.getItem(SESSION_STORAGE_KEYS.token)).toBeNull();
  });
});

function setStorage(): MemoryStorage {
  const memoryStorage = new MemoryStorage();
  Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: memoryStorage });
  return memoryStorage;
}
