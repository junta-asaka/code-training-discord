import { useQuery } from "@tanstack/react-query";
import { getFriendsApi } from "../api/friend";
import { useAuthStore } from "../stores/authStore";
import type { FriendsResponse } from "../schemas/friendSchema";

// フレンド一覧取得のカスタムフック
export const useFriends = () => {
  const { user, accessToken } = useAuthStore();

  return useQuery<FriendsResponse>({
    queryKey: ["friends", user?.id],
    queryFn: () => {
      if (!user?.id || !accessToken) {
        throw new Error("ユーザー情報またはアクセストークンがありません");
      }
      return getFriendsApi(user.id, accessToken);
    },
    enabled: !!user?.id && !!accessToken, // ユーザーIDとトークンがある場合のみクエリを実行
    staleTime: 5 * 60 * 1000, // 5分間キャッシュ
    retry: 2,
  });
};
