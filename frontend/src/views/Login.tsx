const Login = () => {
  return (
    <div className="login-container">
      <div className="login-form">
        <h1>ログイン</h1>
        <form>
          <div className="form-group">
            <label htmlFor="username">ユーザー名</label>
            <input
              type="text"
              id="username"
              name="username"
              placeholder="ユーザー名を入力してください"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">パスワード</label>
            <input
              type="password"
              id="password"
              name="password"
              placeholder="パスワードを入力してください"
              required
            />
          </div>

          <button type="submit" className="login-button">
            ログイン
          </button>
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
