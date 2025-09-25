import { useQuery } from "@tanstack/react-query";
import { getMessagesApi } from "../api/message";
import { useAuthStore } from "../stores/authStore";
import type { MessagesResponse } from "../schemas/messageSchema";

// メッセージ一覧取得のカスタムフック
export const useMessages = (channelId: string | undefined) => {
  const { accessToken } = useAuthStore();

  return useQuery<MessagesResponse>({
    queryKey: ["messages", channelId],
    queryFn: () => {
      if (!channelId || !accessToken) {
        throw new Error("チャネル情報またはアクセストークンがありません");
      }
      return getMessagesApi(channelId, accessToken);
    },
    enabled: !!channelId && !!accessToken, // チャンネルIDとトークンがある場合のみクエリを実行
    staleTime: 5 * 60 * 1000, // 5分間キャッシュ
    retry: 2,
  });
};
