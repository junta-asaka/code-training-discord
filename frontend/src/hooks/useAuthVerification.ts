import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { useEffect } from "react";
import { useAuthStore } from "../stores/authStore";
import { verifySession } from "../api/auth";

// 認証が失敗したかどうか
const isAuthError = (querry: UseQueryResult<boolean, Error>) => {
  return querry.isError || (querry.isSuccess && !querry.data);
};

// 認証状態の検証カスタムフック
export const useAuthVerification = () => {
  const { accessToken, isAuthenticated, logout } = useAuthStore();

  // useQuery: データの取得とキャッシュ管理を行うためのフック
  // queryFn: 実際にデータ取得を行う関数
  const query = useQuery({
    queryKey: ["authVerification", accessToken],
    queryFn: () => verifySession(accessToken!),
    enabled: isAuthenticated && !!accessToken,
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 5 * 60 * 1000, // 5分間はキャッシュを使用
  });

  // useEffect: 副作用の処理（DOMの書き換え、変数代入、API通信などUI構築以外の処理）を行うためのフック
  useEffect(() => {
    if (isAuthError(query)) {
      // 認証失敗時にログアウト処理
      logout();
    }
  }, [query, logout]);

  return query;
};
