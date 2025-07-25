import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

// Types for API responses
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

class ApiClient {
  private client: AxiosInstance;
  private refreshPromise: Promise<string> | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // Add correlation ID for request tracking
        const correlationId = crypto.randomUUID();
        config.headers['X-Correlation-ID'] = correlationId;
        
        // Log outgoing requests in development
        if (import.meta.env.DEV) {
          console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
            correlationId,
            headers: config.headers,
            data: config.data,
          });
        }
        
        return config;
      },
      (error) => {
        console.error('[API Request Error]', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle auth errors and logging
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log successful responses in development
        if (import.meta.env.DEV) {
          const correlationId = response.config.headers['X-Correlation-ID'];
          console.log(`[API Response] ${response.status} ${response.config.url}`, {
            correlationId,
            data: response.data,
          });
        }
        
        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };
        
        // Log errors
        console.error('[API Response Error]', {
          status: error.response?.status,
          url: error.config?.url,
          message: error.message,
          data: error.response?.data,
        });

        // Handle 401 unauthorized errors
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            const newAccessToken = await this.refreshAccessToken();
            if (newAccessToken && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            console.error('[Token Refresh Error]', refreshError);
            // Clear tokens and redirect to login
            this.clearTokens();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        // Handle other error responses
        const apiError = this.createApiError(error);
        return Promise.reject(apiError);
      }
    );
  }

  private createApiError(error: AxiosError): Error {
    const status = error.response?.status;
    const data = error.response?.data as any;
    
    let message = 'An unexpected error occurred';
    
    if (status) {
      switch (status) {
        case 400:
          message = data?.message || 'Bad request';
          break;
        case 401:
          message = 'Authentication required';
          break;
        case 403:
          message = 'Access denied';
          break;
        case 404:
          message = 'Resource not found';
          break;
        case 422:
          message = data?.detail?.[0]?.msg || 'Validation error';
          break;
        case 429:
          message = 'Rate limit exceeded. Please try again later.';
          break;
        case 500:
          message = 'Internal server error';
          break;
        default:
          message = data?.message || error.message || message;
      }
    } else if (error.code === 'NETWORK_ERROR') {
      message = 'Network error. Please check your connection.';
    } else if (error.code === 'TIMEOUT') {
      message = 'Request timeout. Please try again.';
    }

    const apiError = new Error(message);
    (apiError as any).status = status;
    (apiError as any).code = error.code;
    (apiError as any).response = error.response?.data;
    
    return apiError;
  }

  private async refreshAccessToken(): Promise<string | null> {
    // Prevent multiple simultaneous refresh requests
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return null;
    }

    this.refreshPromise = this.client
      .post<AuthTokens>('/auth/refresh', {
        refresh_token: refreshToken,
      })
      .then((response) => {
        const { access_token, refresh_token } = response.data;
        this.setTokens(access_token, refresh_token);
        return access_token;
      })
      .catch((error) => {
        console.error('Failed to refresh token:', error);
        this.clearTokens();
        throw error;
      })
      .finally(() => {
        this.refreshPromise = null;
      });

    return this.refreshPromise;
  }

  // Token management
  private getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  public setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  public clearTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  public isAuthenticated(): boolean {
    const token = this.getAccessToken();
    if (!token) return false;

    try {
      // Check if token is expired (basic check)
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      return payload.exp > currentTime;
    } catch {
      return false;
    }
  }

  // HTTP methods
  public async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<ApiResponse<T>>(url, config);
    return (response.data as any).data || response.data as T;
  }

  public async post<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.post<ApiResponse<T>>(url, data, config);
    return (response.data as any).data || response.data as T;
  }

  public async put<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.put<ApiResponse<T>>(url, data, config);
    return (response.data as any).data || response.data as T;
  }

  public async patch<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.patch<ApiResponse<T>>(url, data, config);
    return (response.data as any).data || response.data as T;
  }

  public async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<ApiResponse<T>>(url, config);
    return (response.data as any).data || response.data as T;
  }

  // File upload with progress
  public async uploadFile<T>(
    url: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<ApiResponse<T>>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = (progressEvent.loaded / progressEvent.total) * 100;
          onProgress(Math.round(progress));
        }
      },
    });

    return (response.data as any).data || response.data as T;
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient();

// Convenience exports for common API calls
export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post<AuthTokens>('/auth/login', { email, password }),
  
  register: (userData: { email: string; password: string; full_name?: string }) =>
    apiClient.post<AuthTokens>('/auth/register', {
      email: userData.email,
      password: userData.password,
      name: userData.full_name || ''
    }),
  
  refresh: (refreshToken: string) =>
    apiClient.post<AuthTokens>('/auth/refresh', { refresh_token: refreshToken }),
  
  getCurrentUser: () =>
    apiClient.get<any>('/auth/me'),
  
  changePassword: (oldPassword: string, newPassword: string) =>
    apiClient.post('/auth/change-password', {
      current_password: oldPassword,
      new_password: newPassword,
    }),
  
  logout: () => {
    apiClient.clearTokens();
  },
};

export default apiClient;