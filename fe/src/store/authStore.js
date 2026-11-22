import { create } from 'zustand';
import axiosClient, { setCsrfToken } from '../api/axiosClient';

export const useAuthStore = create((set, get) => ({
  user: null, ready: false, checking: false,
  restore: async () => {
    if (get().checking || get().ready) return;
    set({ checking: true });
    try {
      const response = await axiosClient.get('/auth/me');
      setCsrfToken(response.csrf_token);
      set({ user: response.user });
    } catch { setCsrfToken(null); set({ user: null }); }
    finally { set({ checking: false, ready: true }); }
  },
  login: async (email, password) => {
    const response = await axiosClient.post('/auth/login', { email, password });
    setCsrfToken(response.csrf_token);
    set({ user: response.user, ready: true });
  },
  logout: async () => {
    await axiosClient.post('/auth/logout');
    setCsrfToken(null);
    set({ user: null });
  },
}));

export { canOperate } from '../utils/access';
