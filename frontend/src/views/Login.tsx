import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { loginSchema, type LoginFormData } from "../schemas/loginSchema";
import { useLogin } from "../hooks/useLogin";

const Login = () => {
  // useForm: フォームの状態管理とバリデーションを簡単に行うためのライブラリ
  // zodResolver: ZodスキーマをReact Hook Formのバリデーションに統合するための関数
  // loginSchema: ログインフォームのバリデーションスキーマ
  // LoginFormData: ログインフォームのデータ型定義
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  // useLogin: ログイン処理を行うカスタムフック
  const loginMutation = useLogin();

  const onSubmit = (data: LoginFormData) => {
    loginMutation.mutate(data);
  };

  return (
    <div className="login-container">
      <div className="login-form">
        <h1>ログイン</h1>
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="form-group">
            <label htmlFor="username">ユーザー名</label>
            <input
              type="text"
              id="username"
              placeholder="ユーザー名を入力してください"
              {...register("username")}
            />
            {errors.username && (
              <p className="error-message">{errors.username.message}</p>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">パスワード</label>
            <input
              type="password"
              id="password"
              placeholder="パスワードを入力してください"
              {...register("password")}
            />
            {errors.password && (
              <p className="error-message">{errors.password.message}</p>
            )}
          </div>

          <button
            type="submit"
            className="login-button"
            disabled={loginMutation.isPending}
          >
            {loginMutation.isPending ? "ログイン中..." : "ログイン"}
          </button>

          {loginMutation.isError && (
            <p className="error-message">
              {loginMutation.error instanceof Error
                ? loginMutation.error.message
                : "ログインに失敗しました"}
            </p>
          )}
        </form>

        <div className="login-footer">
          <p>
            アカウントをお持ちでない方は <a href="/register">新規登録</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
