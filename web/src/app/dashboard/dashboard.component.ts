import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, NgZone, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthUser } from '../core/auth.models';
import { SessionService } from '../core/session.service';
import { TasksService } from '../core/tasks.service';
import { Task } from '../core/task.models';
import { formatTaskLabel } from '../utils/legacy-format';

const STATUS_LABELS: Record<string, string> = {
  TODO: 'Por hacer',
  IN_PROGRESS: 'En progreso',
  DONE: 'Completado',
  RESUELTO: 'Resuelto',
  COMPLETED: 'Completado'
};

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit {
  tasks: Task[] = [];
  visibleTasks: Task[] = [];
  user: AuthUser = {};
  loading = true;
  error = '';

  constructor(
    private readonly router: Router,
    private readonly cdr: ChangeDetectorRef,
    private readonly zone: NgZone,
    private readonly sessionService: SessionService,
    private readonly tasksService: TasksService
  ) {}

  statusLabel(status: string): string {
    return STATUS_LABELS[status.toUpperCase()] ?? status;
  }

  async ngOnInit(): Promise<void> {
    const token = this.sessionService.getToken();
    this.user = this.sessionService.getUser();
    if (!token) {
      await this.router.navigate(['/login']);
      return;
    }

    try {
      const tasks = await this.tasksService.getTasks(
        'username' in this.user && typeof this.user.username === 'string' ? this.user.username : '',
        token
      );
      const visibleTasks = tasks
        .filter((task) => task.status !== 'ARCHIVED')
        .map((task) => ({ ...task, label: formatTaskLabel(task) }))
        .sort((left, right) => (right.priority ?? '').localeCompare(left.priority ?? ''));

      this.zone.run(() => {
        this.tasks = tasks;
        this.visibleTasks = visibleTasks;
        this.loading = false;
        this.cdr.detectChanges();
      });
    } catch (error: unknown) {
      this.zone.run(() => {
        this.error = readTaskErrorMessage(error);
        this.loading = false;
        this.cdr.detectChanges();
      });
    }
  }

  async logout(): Promise<void> {
    this.sessionService.clearSession();
    await this.router.navigate(['/login']);
  }
}

function readTaskErrorMessage(error: unknown): string {
  if (!isRecord(error)) {
    return 'No se pudo cargar el dashboard';
  }

  const response = error.response;
  if (isRecord(response) && isRecord(response.data) && typeof response.data.detail === 'string') {
    return response.data.detail;
  }
  return typeof error.message === 'string' ? error.message : 'No se pudo cargar el dashboard';
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
