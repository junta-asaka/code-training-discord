import type { LoginFormData, LoginResponse } from "../schemas/loginSchema";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// リフレッシュトークンレスポンスの型定義
export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// loginApi: ログインAPIを呼び出す関数
export const loginApi = async (data: LoginFormData): Promise<LoginResponse> => {
  // FormData: フォームデータを簡単に構築・操作するためのWeb API
  const formData = new FormData();
  formData.append("username", data.username);
  formData.append("password", data.password);

  // fetch: ネットワークリクエストを行うためのWeb API
  const response = await fetch(`${API_BASE_URL}/api/login`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(
      error.detail?.message || error.detail || "ログインに失敗しました"
    );
  }

  return response.json();
};

// refreshTokenApi: リフレッシュトークンを使用して新しいアクセストークンを取得する関数
export const refreshTokenApi = async (
  refreshToken: string
): Promise<RefreshTokenResponse> => {
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "トークンのリフレッシュに失敗しました");
  }

  return response.json();
};
