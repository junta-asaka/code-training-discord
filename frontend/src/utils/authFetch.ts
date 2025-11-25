import { useAuthStore } from "../stores/authStore";
import { refreshTokenApi } from "../api/auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// リフレッシュ処理を実行中かどうかのフラグ
let isRefreshing = false;

// リフレッシュ処理待ちのリクエストを保持するキュー
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: Error) => void;
}> = [];

// キューに溜まっているリクエストを処理する関数
const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

/**
 * 認証付きfetchのラッパー関数
 * 401エラー時に自動的にトークンをリフレッシュしてリトライする
 */
export const authFetch = async (
  url: string,
  options: RequestInit = {}
): Promise<Response> => {
  const { accessToken, refreshToken, setAccessToken, logout } =
    useAuthStore.getState();

  // アクセストークンをヘッダーに追加
  const headers = {
    ...options.headers,
    ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
  };

  // 最初のリクエストを実行
  let response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  });

  // 401エラー（認証エラー）の場合
  if (response.status === 401 && refreshToken) {
    // 既にリフレッシュ処理が実行中の場合
    if (isRefreshing) {
      // リフレッシュ処理が完了するまで待機
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then(() => {
        // リフレッシュ完了後、新しいトークンで再リクエスト
        const newAccessToken = useAuthStore.getState().accessToken;
        return fetch(`${API_BASE_URL}${url}`, {
          ...options,
          headers: {
            ...options.headers,
            Authorization: `Bearer ${newAccessToken}`,
          },
        });
      });
    }

    // リフレッシュ処理を開始
    isRefreshing = true;

    try {
      // リフレッシュトークンを使用して新しいアクセストークンを取得
      const refreshResponse = await refreshTokenApi(refreshToken);

      // 新しいアクセストークンをストアに保存
      setAccessToken(refreshResponse.access_token);

      // キューに溜まっているリクエストを処理
      processQueue(null, refreshResponse.access_token);

      // 新しいアクセストークンで再リクエスト
      response = await fetch(`${API_BASE_URL}${url}`, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${refreshResponse.access_token}`,
        },
      });
    } catch (error) {
      // リフレッシュに失敗した場合、キューのリクエストをすべて拒否
      processQueue(
        error instanceof Error
          ? error
          : new Error("トークンのリフレッシュに失敗しました"),
        null
      );

      // ログアウト処理を実行
      logout();

      // AuthGuardが自動的にログインページにリダイレクト
      return new Response(JSON.stringify({ detail: "認証が必要です" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    } finally {
      isRefreshing = false;
    }
  }

  return response;
};
