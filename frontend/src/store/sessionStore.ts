import { create } from 'zustand';

interface SessionStartResponse {
  session_id: string;
  status: string;
}

interface SessionStore {
  session: SessionStartResponse | null;
  status: string | null;
  setSession: (session: SessionStartResponse) => void;
  setStatus: (status: string) => void;
  clearSession: () => void;
}

export const useSessionStore = create<SessionStore>((set) => ({
  session: null,
  status: null,
  setSession: (session) => set({ session }),
  setStatus: (status) => set({ status }),
  clearSession: () => set({ session: null, status: null }),
}));
