import { Injectable } from '@angular/core';
import axios from 'axios';
import { environment } from '../../environments/environment';
import { LoginRequest, LoginResponse } from './auth.models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  async login(credentials: Omit<LoginRequest, 'client'>): Promise<LoginResponse> {
    const request: LoginRequest = {
      ...credentials,
      client: environment.clientId
    };
    const response = await axios.post<LoginResponse>(environment.authEndpoint, request, {
      timeout: environment.requestTimeoutMs
    });
    return response.data;
  }
}
