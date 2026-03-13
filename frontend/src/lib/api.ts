import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
  type AxiosResponse,
} from "axios";
import Cookies from "js-cookie";

// ─── Token helpers ────────────────────────────────────────────────────────────

const ACCESS_TOKEN_KEY = "fqtg_access_token";
const REFRESH_TOKEN_KEY = "fqtg_refresh_token";

const configuredApiBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
export const API_BASE = configuredApiBase && configuredApiBase.length > 0
  ? configuredApiBase.replace(/\/+$/, "")
  : "/api/v1";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY) ?? Cookies.get(ACCESS_TOKEN_KEY) ?? null;
}

export function setAuthToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
  }
  Cookies.set(ACCESS_TOKEN_KEY, token, { expires: 1, sameSite: "strict" });
}

export function clearAuthToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  }
  Cookies.remove(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY) ?? Cookies.get(REFRESH_TOKEN_KEY) ?? null;
}

export function setRefreshToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  }
  Cookies.set(REFRESH_TOKEN_KEY, token, { expires: 7, sameSite: "strict" });
}

export function clearRefreshToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
  Cookies.remove(REFRESH_TOKEN_KEY);
}

// ─── Axios instance ───────────────────────────────────────────────────────────

const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

// Request interceptor – attach Bearer token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAuthToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Track in-flight refresh to avoid multiple simultaneous refreshes
let refreshPromise: Promise<string> | null = null;

// Response interceptor – handle 401 / token refresh
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        clearAuthToken();
        clearRefreshToken();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }

      try {
        if (!refreshPromise) {
          refreshPromise = axios
            .post<{ access_token: string }>(`${API_BASE}/auth/refresh`, {
              refresh_token: refreshToken,
            })
            .then((res) => {
              const newToken = res.data.access_token;
              setAuthToken(newToken);
              refreshPromise = null;
              return newToken;
            })
            .catch((err) => {
              refreshPromise = null;
              throw err;
            });
        }

        const newToken = await refreshPromise;
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        return api(originalRequest);
      } catch (_refreshError) {
        clearAuthToken();
        clearRefreshToken();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);

export default api;
