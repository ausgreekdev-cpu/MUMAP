const STORAGE_KEY = 'mumap_api_url';
const DEFAULT_FLAG = 'mumap_use_default';

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

/** True when the user explicitly chose same-origin (skip reachability probe). */
export function isSameOriginChosen(): boolean {
  return localStorage.getItem(DEFAULT_FLAG) === '1';
}

export function markSameOrigin(): void {
  localStorage.setItem(DEFAULT_FLAG, '1');
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
  localStorage.removeItem(DEFAULT_FLAG);
}

export function clearApiUrl(): void {
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem(DEFAULT_FLAG);
}
