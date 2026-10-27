import '@angular/compiler';
import { ChangeDetectorRef, NgZone } from '@angular/core';
import { Router } from '@angular/router';
import axios from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthService } from '../core/auth.service';
import { SessionService } from '../core/session.service';
import { TasksService } from '../core/tasks.service';
import { LoginComponent } from '../login/login.component';
import { DashboardComponent } from './dashboard.component';

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
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

describe('DashboardComponent', () => {
  let storage: MemoryStorage;
  let navigate: ReturnType<typeof vi.fn>;
  let component: DashboardComponent;
  let session: SessionService;

  beforeEach(() => {
    storage = new MemoryStorage();
    Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: storage });
    navigate = vi.fn().mockResolvedValue(true);
    vi.mocked(axios.get).mockReset();
    vi.mocked(axios.post).mockReset();
    session = new SessionService();
    component = new DashboardComponent(
      { navigate } as unknown as Router,
      { detectChanges: vi.fn() } as unknown as ChangeDetectorRef,
      { run: (callback: () => void) => callback() } as unknown as NgZone,
      session,
      new TasksService()
    );
  });

  it('redirects to login when the stored token is missing', async () => {
    await component.ngOnInit();

    expect(navigate).toHaveBeenCalledWith(['/login']);
    expect(axios.get).not.toHaveBeenCalled();
  });

  it('loads tasks with the stored owner and bearer token, filters and sorts them', async () => {
    session.saveSession('test-token', { username: 'student' }, { theme: 'light', showTips: true, compact: false });
    vi.mocked(axios.get).mockResolvedValue({
      data: [
        { title: 'Low', status: 'TODO', priority: 'low', owner: 'student' },
        { title: 'Archived', status: 'ARCHIVED', priority: 'urgent', owner: 'student' },
        { title: 'High', status: 'IN_PROGRESS', priority: 'high', owner: 'student' }
      ]
    });

    await component.ngOnInit();

    expect(axios.get).toHaveBeenCalledWith(
      'http://localhost:8000/api/tasks',
      { params: { owner: 'student' }, headers: { Authorization: 'Bearer test-token' } }
    );
    expect(component.tasks).toHaveLength(3);
    expect(component.visibleTasks.map((task) => task.title)).toEqual(['Low', 'High']);
    expect(component.visibleTasks[0].label).toBe('LOW · STUDENT');
    expect(component.loading).toBe(false);
    expect(component.error).toBe('');
  });

  it('logs in and loads tasks using the in-memory session without persisting the token', async () => {
    vi.mocked(axios.post).mockResolvedValue({
      data: { token: 'test-token', user: { username: 'student' } }
    });
    const loginNavigate = vi.fn().mockResolvedValue(true);
    const loginComponent = new LoginComponent(
      { navigate: loginNavigate } as unknown as Router,
      new AuthService(),
      session
    );
    loginComponent.username = 'student';
    loginComponent.password = 'Workshop123!';
    vi.mocked(axios.get).mockResolvedValue({
      data: [{ title: 'First task', description: 'Example task', status: 'TODO', owner: 'student' }]
    });

    await loginComponent.login();
    await component.ngOnInit();

    expect(storage.getItem('workshop_token')).toBeNull();
    expect(session.getToken()).toBe('test-token');
    expect(loginNavigate).toHaveBeenCalledWith(['/dashboard']);
    expect(axios.get).toHaveBeenCalledWith(
      'http://localhost:8000/api/tasks',
      { params: { owner: 'student' }, headers: { Authorization: 'Bearer test-token' } }
    );
    expect(component.visibleTasks.map((task) => task.title)).toEqual(['First task']);
    expect(component.loading).toBe(false);
  });

  it('shows a load error and clears loading when the request fails', async () => {
    session.saveSession('test-token', { username: 'student' }, { theme: 'light', showTips: true, compact: false });
    vi.mocked(axios.get).mockRejectedValue({ message: 'network unavailable' });

    await component.ngOnInit();

    expect(component.error).toBe('network unavailable');
    expect(component.loading).toBe(false);
  });

  it('uses the backend task detail when the task request fails', async () => {
    session.saveSession('test-token', { username: 'student' }, { theme: 'light', showTips: true, compact: false });
    vi.mocked(axios.get).mockRejectedValue({
      response: { data: { detail: 'Access denied' } }
    });

    await component.ngOnInit();

    expect(component.error).toBe('Access denied');
  });

  it('shows an invalid-token response without clearing the session or redirecting', async () => {
    session.saveSession('invalid-token', { username: 'student' }, { theme: 'light', showTips: true, compact: false });
    vi.mocked(axios.get).mockRejectedValue({
      response: { status: 401, data: { detail: 'Invalid token' } }
    });

    await component.ngOnInit();

    expect(component.error).toBe('Invalid token');
    expect(component.loading).toBe(false);
    expect(session.getToken()).toBe('invalid-token');
    expect(navigate).not.toHaveBeenCalled();
  });

  it('shows a task request timeout message and clears loading', async () => {
    session.saveSession('test-token', { username: 'student' }, { theme: 'light', showTips: true, compact: false });
    vi.mocked(axios.get).mockRejectedValue({
      code: 'ECONNABORTED',
      message: 'timeout of 5000ms exceeded'
    });

    await component.ngOnInit();

    expect(component.error).toBe('timeout of 5000ms exceeded');
    expect(component.loading).toBe(false);
  });

  it('uses a generic message for an unstructured task error', async () => {
    session.saveSession('test-token', { username: 'student' }, { theme: 'light', showTips: true, compact: false });
    vi.mocked(axios.get).mockRejectedValue(null);

    await component.ngOnInit();

    expect(component.error).toBe('No se pudo cargar el dashboard');
  });

  it('clears the in-memory token and stored user on logout but retains preferences', async () => {
    session.saveSession('test-token', { username: 'student' }, { theme: 'dark', showTips: true, compact: false });

    await component.logout();

    expect(session.getToken()).toBeNull();
    expect(storage.getItem('workshop_user')).toBeNull();
    expect(storage.getItem('workshop_token')).toBeNull();
    expect(JSON.parse(storage.getItem('workshop_preferences') ?? '{}')).toMatchObject({ theme: 'dark' });
    expect(navigate).toHaveBeenCalledWith(['/login']);
  });

  it('maps known task statuses and preserves unknown status labels', () => {
    expect(component.statusLabel('todo')).toBe('Por hacer');
    expect(component.statusLabel('custom')).toBe('custom');
  });
});
