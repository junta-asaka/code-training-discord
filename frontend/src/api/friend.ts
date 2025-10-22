import type { FriendsResponse } from "../schemas/friendSchema";
import { authFetch } from "@/utils/authFetch";

// getFriends: フレンド一覧取得APIを呼び出す関数
export const getFriendsApi = async (
  userId: string
): Promise<FriendsResponse> => {
  const response = await authFetch(`/api/friends/${userId}`, {
    method: "GET",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(
      error.detail?.message || "フレンド一覧の取得に失敗しました"
    );
  }

  return response.json();
};

// createFriend: フレンド追加APIを呼び出す関数
export const createFriendApi = async (
  username: string,
  relatedUsername: string
): Promise<void> => {
  const response = await authFetch(`/api/friend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username,
      related_username: relatedUsername,
      type: "friend",
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "フレンドの追加に失敗しました");
  }
};
