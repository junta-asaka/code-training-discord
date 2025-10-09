import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { registerApi } from "../api/register";

// 登録処理のカスタムフック
export const useRegister = () => {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: registerApi,
    onSuccess: () => {
      // 登録成功後、ログインページに遷移
      navigate("/login", {
        replace: true,
        state: {
          message: "アカウントが作成されました。ログインしてください。",
        },
      });
    },
    onError: (error) => {
      // 登録失敗時にtoast通知
      const errorMessage =
        error instanceof Error ? error.message : "不明なエラーが発生しました";
      toast.error(`登録に失敗しました -> ${errorMessage}`);
    },
  });
};
