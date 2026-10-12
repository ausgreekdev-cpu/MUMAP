const STORAGE_KEY = 'mumap_api_url';

function normalizeServer(raw: string): string {
  return raw.trim().replace(/\/+$/, '');
}

/** Server origin without /api suffix, or null when using same-origin default. */
export function getConfiguredServer(): string | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  const normalized = normalizeServer(raw);
  return normalized || null;
}

/** Axios base URL: configured server + /api, else same-origin /api. */
export function getApiBase(): string {
  const server = getConfiguredServer();
  if (!server) return '/api';
  if (server.endsWith('/api')) return server;
  return `${server}/api`;
}

/** Absolute health URL for validating a user-entered server URL. */
export function healthUrlFor(server: string): string {
  const normalized = normalizeServer(server);
  if (normalized.endsWith('/api')) {
    return `${normalized.replace(/\/api$/, '')}/health`;
  }
  return `${normalized}/health`;
}

export function setApiUrl(url: string): void {
  localStorage.setItem(STORAGE_KEY, normalizeServer(url));
}

export function clearApiUrl(): void {
  localStorage.removeItem(STORAGE_KEY);
}
