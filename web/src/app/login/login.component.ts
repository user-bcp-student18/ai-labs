import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../core/auth.service';
import { AuthUser, UserPreferences } from '../core/auth.models';
import { SessionService } from '../core/session.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  username = '';
  password = '';
  busy = false;
  message = '';
  preferences: UserPreferences;

  constructor(
    private readonly router: Router,
    private readonly authService: AuthService,
    private readonly sessionService: SessionService
  ) {
    this.preferences = this.sessionService.getPreferences();
  }

  async login(): Promise<void> {
    this.message = '';
    if (!this.username.trim()) {
      this.message = 'Ingrese un usuario.';
      return;
    }
    if (!this.password.trim()) {
      this.message = 'Ingrese una contraseña.';
      return;
    }

    this.busy = true;
    try {
      const response = await this.authService.login({
        username: this.username,
        password: this.password
      });
      if (!response.token) {
        this.message = 'El backend respondió sin token.';
        return;
      }
      const user: AuthUser = response.user ?? {};
      this.sessionService.saveSession(response.token, user, this.preferences);
      await this.router.navigate(['/dashboard']);
    } catch {
      this.message = `No se pudo autenticar a ${this.username}.`;
    } finally {
      this.busy = false;
    }
  }
}
