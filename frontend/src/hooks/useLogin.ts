import { useMutation } from "@tanstack/react-query";
import { useNavigate, useLocation } from "react-router-dom";
import toast from "react-hot-toast";
import { loginApi } from "../api/auth";
import { useAuthStore } from "../stores/authStore";

// ログイン処理のカスタムフック
export const useLogin = () => {
  // useNavigate: イベント発生時にプログラム的に画面遷移を行うためのフック
  // useLocation: 現在のURL情報を取得するためのフック
  // useAuthStore: Zustandの認証ストアを利用するためのフック
  const navigate = useNavigate();
  const location = useLocation();
  const setAuth = useAuthStore((state) => state.setAuth);

  // useMutation: データの変更操作（POST、PUT、DELETEなど）を行うためのフック
  // mutationFn: 実際にデータ変更を行う関数
  // onSuccess: データ変更が成功した場合に実行されるコールバック関数
  // onError: データ変更が失敗した場合に実行されるコールバック関数
  return useMutation({
    mutationFn: loginApi,
    onSuccess: (response) => {
      setAuth(
        {
          id: response.id,
          name: response.name,
          username: response.username,
        },
        response.access_token
      );

      // ログイン成功後、元のページまたはTop画面に遷移
      const from = location.state?.from || "/channels/@me";
      navigate(from, { replace: true });
    },
    onError: (error) => {
      // ログイン失敗時にtoast通知
      const errorMessage =
        error instanceof Error ? error.message : "不明なエラーが発生しました";
      toast.error(`ログインに失敗しました: ${errorMessage}`);
    },
  });
};
