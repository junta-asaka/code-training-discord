import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";

// Propsの型定義
interface AuthGuardProps {
  children: React.ReactNode;
}

// 認証ガードコンポーネント
// ローカルストレージの認証状態のみをチェック
// セッション検証は各APIリクエスト時にauthFetchが自動的に行う
const AuthGuard = ({ children }: AuthGuardProps) => {
  // useNavigate: イベント発生時にプログラム的に画面遷移を行うためのフック
  // useLocation: 現在のURL情報を取得するためのフック
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated } = useAuthStore();

  // useEffect: 副作用の処理（DOMの書き換え、変数代入、API通信などUI構築以外の処理）を行うためのフック
  useEffect(() => {
    // ローカルの認証状態がfalseの場合、ログインページに遷移
    if (!isAuthenticated) {
      navigate("/login", {
        state: { from: location.pathname },
        replace: true,
      });
    }
  }, [isAuthenticated, navigate, location.pathname]);

  // 認証されていない場合はnullを返す（useEffectで即座にリダイレクトされる）
  if (!isAuthenticated) {
    return null;
  }

  // 認証済みの場合は子コンポーネントを表示
  return <>{children}</>;
};

export default AuthGuard;
