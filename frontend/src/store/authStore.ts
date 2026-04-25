import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { AuthUser } from "../types";

interface AuthStore {
  token: string | null;
  user: AuthUser | null;
  setToken: (token: string) => void;
  setUser: (user: AuthUser | null) => void;
  clearAuth: () => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),
      clearAuth: () => set({ token: null, user: null }),
      logout: () => set({ token: null, user: null }),
    }),
    {
      name: "skillos-auth",
    }
  )
);
