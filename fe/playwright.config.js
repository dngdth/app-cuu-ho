import { defineConfig } from '@playwright/test';

const python = process.env.E2E_PYTHON || (process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1, timeout: 60000,
  use: { baseURL: 'http://127.0.0.1:5174', headless: true, viewport: { width: 1440, height: 1000 }, trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  reporter: [['list']],
  webServer: [
    { command: `"${python}" -m uvicorn test.e2e_server:app --host 127.0.0.1 --port 8101`, cwd: '..',
      url: 'http://127.0.0.1:8101/health', timeout: 120000, reuseExistingServer: false,
      env: { GEOCODING_ENABLED: 'false', GEOAPIFY_API_KEY: '', AUTH_COOKIE_SECURE: 'false',
        ALLOWED_ORIGINS: 'http://127.0.0.1:5174', RESCUE_MODEL_DIR: 'ai/artifacts/prototype' } },
    { command: 'npm run build && npm run preview -- --host 127.0.0.1 --port 5174 --strictPort', url: 'http://127.0.0.1:5174',
      reuseExistingServer: false, env: { API_PROXY_TARGET: 'http://127.0.0.1:8101', VITE_API_URL: '/api' } },
  ],
});
