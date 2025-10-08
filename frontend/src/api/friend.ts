import type { FriendsResponse } from "../schemas/friendSchema";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// getFriends: フレンド一覧取得APIを呼び出す関数
export const getFriendsApi = async (
  userId: string,
  accessToken: string
): Promise<FriendsResponse> => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/friends?user_id=${userId}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        error.detail?.message || "フレンド一覧の取得に失敗しました"
      );
    }

    return response.json();
  } catch (error) {
    console.error("フレンド一覧取得エラー:", error);
    throw error;
  }
};
