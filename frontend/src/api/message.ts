import type { MessagesResponse } from "@/schemas/messageSchema";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// getMessages: メッセージ一覧取得APIを呼び出す関数
export const getMessagesApi = async (
  channelId: string,
  accessToken: string
): Promise<MessagesResponse> => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/channel?channel_id=${channelId}`,
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
        error.detail?.message || "メッセージの取得に失敗しました"
      );
    }

    return response.json();
  } catch (error) {
    console.error("メッセージ取得エラー:", error);
    throw error;
  }
};
