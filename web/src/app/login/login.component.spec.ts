import '@angular/compiler';
import { Router } from '@angular/router';
import axios from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthService } from '../core/auth.service';
import { SessionService } from '../core/session.service';
import { LoginComponent } from './login.component';

vi.mock('axios', () => ({
  default: {
    post: vi.fn()
  }
}));

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

describe('LoginComponent', () => {
  let storage: MemoryStorage;
  let navigate: ReturnType<typeof vi.fn>;
  let component: LoginComponent;

  beforeEach(() => {
    storage = new MemoryStorage();
    Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: storage });
    navigate = vi.fn().mockResolvedValue(true);
    vi.mocked(axios.post).mockReset();
    component = new LoginComponent(
      { navigate } as unknown as Router,
      new AuthService(),
      new SessionService()
    );
    component.username = 'student';
    component.password = 'Workshop123!';
  });

  it('posts credentials and persists the returned session before navigating', async () => {
    vi.mocked(axios.post).mockResolvedValue({
      data: { token: 'test-token', user: { username: 'student' } }
    });

    await component.login();

    expect(axios.post).toHaveBeenCalledWith(
      'http://localhost:8080/auth/login',
      { username: 'student', password: 'Workshop123!', client: 'angular-workshop' },
      { timeout: 5000 }
    );
    expect(storage.getItem('workshop_token')).toBe('test-token');
    expect(JSON.parse(storage.getItem('workshop_user') ?? '{}')).toEqual({ username: 'student' });
    expect(navigate).toHaveBeenCalledWith(['/dashboard']);
    expect(component.busy).toBe(false);
  });

  it('does not submit a blank username', async () => {
    component.username = '  ';

    await component.login();

    expect(axios.post).not.toHaveBeenCalled();
    expect(component.message).toContain('Ingrese un usuario.');
  });

  it('does not submit a blank password', async () => {
    component.password = '  ';

    await component.login();

    expect(axios.post).not.toHaveBeenCalled();
    expect(component.message).toContain('Ingrese una contraseña.');
  });

  it('shows a message when the response does not contain a token', async () => {
    vi.mocked(axios.post).mockResolvedValue({ data: {} });

    await component.login();

    expect(component.message).toContain('El backend respondió sin token.');
    expect(navigate).not.toHaveBeenCalled();
  });

  it('shows a plain-text authentication error without exposing backend details', async () => {
    vi.mocked(axios.post).mockRejectedValue({
      response: { data: { message: 'Credenciales inválidas' } }
    });

    await component.login();

    expect(component.message).toBe('No se pudo autenticar a student.');
    expect(component.message).not.toContain('<');
    expect(component.busy).toBe(false);
  });

  it('shows the generic authentication message when the service is unavailable', async () => {
    vi.mocked(axios.post).mockRejectedValue({
      code: 'ERR_NETWORK',
      message: 'Network Error'
    });

    await component.login();

    expect(component.message).toBe('No se pudo autenticar a student.');
    expect(component.busy).toBe(false);
    expect(storage.getItem('workshop_token')).toBeNull();
    expect(navigate).not.toHaveBeenCalled();
  });

  it('shows the generic authentication message when the login request times out', async () => {
    vi.mocked(axios.post).mockRejectedValue({
      code: 'ECONNABORTED',
      message: 'timeout of 5000ms exceeded'
    });

    await component.login();

    expect(component.message).toBe('No se pudo autenticar a student.');
    expect(component.busy).toBe(false);
    expect(storage.getItem('workshop_token')).toBeNull();
    expect(navigate).not.toHaveBeenCalled();
  });
});
