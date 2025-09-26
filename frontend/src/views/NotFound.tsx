import "../styles/views/NotFound.scss";

const NotFound = () => {
  const handleGoHome = () => {
    window.location.href = "/channels/@me";
  };

  const handleGoBack = () => {
    window.history.back();
  };

  return (
    <div className="notfound-container">
      <div className="notfound-content">
        <div className="error-code">404</div>
        <h1 className="error-title">ページが見つかりません</h1>
        <p className="error-message">
          お探しのページは存在しないか、移動された可能性があります。
          <br />
          URLをご確認いただくか、以下のボタンからナビゲートしてください。
        </p>
        <div className="action-buttons">
          <button onClick={handleGoHome} className="primary-button">
            ホームページに戻る
          </button>
          <button onClick={handleGoBack} className="secondary-button">
            前のページに戻る
          </button>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
