import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getFriendsApi, createFriendApi } from "../api/friend";
import { useAuthStore } from "../stores/authStore";
import type { FriendsResponse } from "../schemas/friendSchema";

// フレンド一覧取得のカスタムフック
export const useFriends = () => {
  const { user, accessToken } = useAuthStore();

  return useQuery<FriendsResponse>({
    queryKey: ["friends", user?.id],
    queryFn: () => {
      if (!user?.id) {
        throw new Error("ユーザー情報がありません");
      }
      return getFriendsApi(user.id);
    },
    enabled: !!user?.id && !!accessToken, // ユーザーIDとトークンがある場合のみクエリを実行
    staleTime: 5 * 60 * 1000, // 5分間キャッシュ
    retry: 2,
  });
};

// フレンド追加のカスタムフック
export const useCreateFriend = () => {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (relatedUsername: string) => {
      if (!user?.username) {
        throw new Error("ユーザー情報がありません");
      }
      return createFriendApi(user.username, relatedUsername);
    },
    onSuccess: () => {
      // フレンド追加成功時にフレンド一覧を再取得
      queryClient.invalidateQueries({ queryKey: ["friends"] });
    },
  });
};
