import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";
import { useAuthVerification } from "../hooks/useAuthVerification";

// Propsの型定義
interface AuthGuardProps {
  children: React.ReactNode;
}

// 認証ガードコンポーネント
const AuthGuard = ({ children }: AuthGuardProps) => {
  // useNavigate: イベント発生時にプログラム的に画面遷移を行うためのフック
  // useLocation: 現在のURL情報を取得するためのフック
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated } = useAuthStore();
  const { isLoading, isError, data: isSessionValid } = useAuthVerification();

  //   useEffect: 副作用の処理（DOMの書き換え、変数代入、API通信などUI構築以外の処理）を行うためのフック
  useEffect(() => {
    // ローカルの認証状態がfalseの場合、即座にログインページに遷移
    if (!isAuthenticated) {
      navigate("/login", {
        state: { from: location.pathname },
        replace: true,
      });
      return;
    }

    // セッション認証でエラーが発生した場合、またはセッションが無効な場合
    if (isError || isSessionValid === false) {
      navigate("/login", {
        state: { from: location.pathname },
        replace: true,
      });
    }
  }, [isAuthenticated, isError, isSessionValid, navigate, location.pathname]);

  // 認証チェック中の場合はローディング表示
  if (!isAuthenticated || isLoading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          fontSize: "18px",
        }}
      >
        認証を確認中...
      </div>
    );
  }

  // 認証済みの場合は子コンポーネントを表示
  return <>{children}</>;
};

export default AuthGuard;
