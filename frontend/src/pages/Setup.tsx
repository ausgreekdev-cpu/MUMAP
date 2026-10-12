import { useState } from 'react';
import { getConfiguredServer, healthUrlFor, setApiUrl } from '../services/config';

export function Setup() {
  const [serverUrl, setServerUrl] = useState(getConfiguredServer() ?? '');
  const [error, setError] = useState('');
  const [isChecking, setIsChecking] = useState(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = serverUrl.trim();
    if (!trimmed) {
      setError('Enter your server URL');
      return;
    }
    let parsed: URL;
    try {
      parsed = new URL(trimmed);
      if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        throw new Error('bad protocol');
      }
    } catch {
      setError('Enter a valid URL, e.g. https://mumap.example.com');
      return;
    }

    setIsChecking(true);
    setError('');
    try {
      const res = await fetch(healthUrlFor(trimmed), { mode: 'cors' });
      if (!res.ok) {
        throw new Error(`Server responded ${res.status}`);
      }
      setApiUrl(trimmed);
      window.location.assign('/login');
    } catch {
      setError(
        'Could not reach the server. Check the URL, that it is running, and that CORS allows this origin (CORS_ORIGINS).'
      );
    } finally {
      setIsChecking(false);
    }
  };

  const handleSameOrigin = () => {
    localStorage.removeItem('mumap_api_url');
    window.location.assign('/login');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f] p-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-2xl font-bold shadow-lg shadow-indigo-500/20 mb-4">
            M
          </div>
          <h1 className="text-2xl font-bold">Connect to your server</h1>
          <p className="text-gray-400 mt-2 text-sm">
            MUMAP runs on your own server. Enter its address to get started.
          </p>
        </div>

        <form onSubmit={handleSave} className="card space-y-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">Server URL</label>
            <input
              type="url"
              value={serverUrl}
              onChange={(e) => setServerUrl(e.target.value)}
              className="input"
              placeholder="https://mumap.example.com"
              autoFocus
              required
            />
            <p className="text-xs text-gray-500">
              Use HTTPS in production. Local Docker instances often run at
              http://localhost:8000.
            </p>
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button type="submit" disabled={isChecking} className="btn btn-primary w-full disabled:opacity-50">
            {isChecking ? 'Checking connection...' : 'Save and continue'}
          </button>

          <button type="button" onClick={handleSameOrigin} className="btn w-full text-sm text-gray-400 hover:text-white">
            Use this site&rsquo;s default server
          </button>
        </form>

        <p className="text-center text-xs text-gray-600 mt-6">
          <a href="/privacy" className="hover:text-gray-400">Privacy</a>
        </p>
      </div>
    </div>
  );
}
