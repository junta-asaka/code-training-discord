import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getMessagesApi, createMessageApi } from "../api/message";
import { useAuthStore } from "../stores/authStore";
import type {
  MessagesResponse,
  MessageCreateRequest,
  MessageCreateResponse,
} from "../schemas/messageSchema";

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

// メッセージ作成のカスタムフック
export const useCreateMessage = () => {
  const { accessToken } = useAuthStore();
  // useQueryClient: React Queryのクエリクライアントを取得するためのフック
  const queryClient = useQueryClient();

  return useMutation<MessageCreateResponse, Error, MessageCreateRequest>({
    mutationFn: (messageData) => {
      if (!accessToken) {
        throw new Error("アクセストークンがありません");
      }
      return createMessageApi(messageData, accessToken);
    },
    onSuccess: (variables) => {
      // メッセージ送信成功時に、該当チャンネルのメッセージ一覧を更新
      // invalidateQueries: 指定したクエリキーに関連するキャッシュを無効化し、再フェッチを促す
      queryClient.invalidateQueries({
        queryKey: ["messages", variables.channel_id],
      });
    },
  });
};
