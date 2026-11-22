import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL;
let csrfToken = null;
export const setCsrfToken = (value) => { csrfToken = value; };

const axiosClient = axios.create({
  baseURL: baseURL,
  timeout: 10000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

/* ================= REQUEST ================= */
axiosClient.interceptors.request.use(
  (config) => {
    if (csrfToken && !['get', 'head', 'options'].includes(config.method?.toLowerCase()))
      config.headers['X-CSRF-Token'] = csrfToken;
    if (import.meta.env.DEV) {
      console.log(
        `[API →] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`
      );
    }
    return config;
  },
  Promise.reject);

/* ================= RESPONSE ================= */
axiosClient.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      const body = response.data;
      const data = body?.data ?? body?.results ?? body?.items ?? body;

      console.log(
        `[API ←] ${response.status} ${response.config.url}`,
        Array.isArray(data)
          ? `Array(${data.length})`
          : typeof data === 'object'
            ? `Object(${Object.keys(data).length} keys)`
            : data
      );
    }

    // normalize response
    return response.data?.data ?? response.data;
  },
  (error) => {
    if (import.meta.env.DEV) {
      console.error(
        `[API ✖] ${error.response?.status} ${error.config?.url}`,
        error.response?.data
      );
    }
    return Promise.reject(error);
  }
);

export default axiosClient;
