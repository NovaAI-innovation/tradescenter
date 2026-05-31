const DEFAULT_API_BASE_URL = "/api";

export const appConfig = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL,
  authRedirectPath: "/auth/callback",
  requestTimeoutMs: 15000,
};
