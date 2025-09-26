import type {
  RegisterFormData,
  RegisterResponse,
} from "../schemas/registerSchema";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// registerApi: 新規ユーザー登録APIを呼び出す関数
export const registerApi = async (
  data: RegisterFormData
): Promise<RegisterResponse> => {
  // 登録用のペイロードを作成
  const payload = {
    name: data.name,
    username: data.username,
    email: data.email,
    password: data.password,
  };

  const response = await fetch(`${API_BASE_URL}/api/user`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || "登録に失敗しました");
  }

  return response.json();
};
