import { create } from "zustand";
import { persist } from "zustand/middleware";

// ユーザー情報の型定義
interface User {
  id: string;
  name: string;
  username: string;
}

// 認証状態の型定義
interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  setAccessToken: (accessToken: string) => void;
  logout: () => void;
}

// Zustandの認証ストア定義
// create: Zustandのストアを作成するための関数
// persist: Zustandのミドルウェアで、ストアの状態をローカルストレージなどに永続化するための関数
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      user: null,
      accessToken: null,
      refreshToken: null,
      setAuth: (user: User, accessToken: string, refreshToken: string) =>
        set({
          isAuthenticated: true,
          user,
          accessToken,
          refreshToken,
        }),
      setAccessToken: (accessToken: string) =>
        set({
          accessToken,
        }),
      logout: () =>
        set({
          isAuthenticated: false,
          user: null,
          accessToken: null,
          refreshToken: null,
        }),
    }),
    {
      name: "auth-storage",
    }
  )
);
