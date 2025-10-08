import type { LoginFormData, LoginResponse } from "../schemas/loginSchema";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

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
    throw new Error(error.detail?.message || "ログインに失敗しました");
  }

  return response.json();
};

export const verifySession = async (accessToken: string): Promise<boolean> => {
  const response = await fetch(`${API_BASE_URL}/auth/verify`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  return response.ok;
};
