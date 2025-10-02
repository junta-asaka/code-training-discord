import type {
  MessagesResponse,
  MessageCreateRequest,
  MessageCreateResponse,
} from "@/schemas/messageSchema";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// getMessages: メッセージ一覧取得APIを呼び出す関数
export const getMessagesApi = async (
  channelId: string,
  accessToken: string
): Promise<MessagesResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/channels/${channelId}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

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

// createMessage: メッセージ作成APIを呼び出す関数
export const createMessageApi = async (
  messageData: MessageCreateRequest,
  accessToken: string
): Promise<MessageCreateResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/message`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(messageData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        error.detail?.message || "メッセージの送信に失敗しました"
      );
    }

    return response.json();
  } catch (error) {
    console.error("メッセージ送信エラー:", error);
    throw error;
  }
};
