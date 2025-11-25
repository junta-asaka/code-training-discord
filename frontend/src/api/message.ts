import type {
  MessagesResponse,
  MessageCreateRequest,
  MessageCreateResponse,
} from "@/schemas/messageSchema";
import { authFetch } from "@/utils/authFetch";

// getMessages: メッセージ一覧取得APIを呼び出す関数
export const getMessagesApi = async (
  channelId: string
): Promise<MessagesResponse> => {
  const response = await authFetch(`/api/channels/${channelId}`, {
    method: "GET",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || "メッセージの取得に失敗しました");
  }

  return response.json();
};

// createMessage: メッセージ作成APIを呼び出す関数
export const createMessageApi = async (
  messageData: MessageCreateRequest
): Promise<MessageCreateResponse> => {
  const response = await authFetch(`/api/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(messageData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || "メッセージの送信に失敗しました");
  }

  return response.json();
};
