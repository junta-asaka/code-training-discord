"""ログユーティリティモジュール

INIファイルベースでログ設定を管理し、アプリケーション全体で統一されたログ設定を提供します。
"""

import configparser
import logging
import logging.config
import os
from pathlib import Path
from typing import Optional


class LoggerManager:
    """ログマネージャークラス

    INIファイルからログ設定を読み込み、アプリケーション全体で
    統一されたロガーインスタンスを提供します。
    """

    _initialized = False
    _loggers = {}

    @classmethod
    def setup_logging(cls, config_path: Optional[str] = None, env_key: str = "LOG_CONFIG") -> None:
        """ログ設定を初期化

        Args:
            config_path: ログ設定ファイルのパス（優先度1）
            env_key: 環境変数のキー名（優先度2、デフォルト：LOG_CONFIG）

        設定ファイルの検索優先度：
        1. config_pathパラメータで指定されたパス
        2. 環境変数で指定されたパス
        3. デフォルトパス（logging.ini → logging_dev.ini）
        """
        if cls._initialized:
            return

        # 設定ファイルパスを決定
        ini_path = cls._resolve_config_path(config_path, env_key)

        if ini_path and ini_path.exists():
            # ログディレクトリを事前に作成
            cls._ensure_log_directory()

            try:
                # INIファイルをUTF-8で読み込み
                config = configparser.ConfigParser()
                config.read(ini_path, encoding="utf-8")

                # ログ設定を適用
                logging.config.fileConfig(config, disable_existing_loggers=False)
                print(f"ログ設定ファイルを読み込みました: {ini_path}")
            except Exception as e:
                print(f"ログ設定ファイルの読み込みに失敗しました: {e}")
                cls._setup_fallback_logging()
        else:
            print("ログ設定ファイルが見つかりません。デフォルト設定を使用します。")
            cls._setup_fallback_logging()

        cls._initialized = True

    @classmethod
    def _resolve_config_path(cls, config_path: Optional[str], env_key: str) -> Optional[Path]:
        """設定ファイルパスを解決"""
        # 1. 直接指定されたパス
        if config_path:
            return Path(config_path)

        # 2. 環境変数で指定されたパス
        env_path = os.getenv(env_key)
        if env_path:
            return Path(env_path)

        # 3. デフォルトパス
        # プロジェクトルートを基準に検索
        project_root = Path(__file__).parent.parent.parent

        # 本番用設定ファイル
        default_path = project_root / "logging.ini"
        if default_path.exists():
            return default_path

        # 開発用設定ファイル
        dev_path = project_root / "logging_dev.ini"
        if dev_path.exists():
            return dev_path

        return None

    @classmethod
    def _ensure_log_directory(cls) -> None:
        """ログディレクトリの作成を確保"""
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _setup_fallback_logging(cls) -> None:
        """フォールバック用のログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """指定された名前のロガーを取得

        Args:
            name: ロガー名（通常は__name__を使用）

        Returns:
            設定済みのロガーインスタンス
        """
        if not cls._initialized:
            cls.setup_logging()

        if name not in cls._loggers:
            # appロガーを使用するか、標準ロガーを使用するかを判定
            if name.startswith("api.") or name.startswith("usecase.") or name.startswith("repository."):
                logger = logging.getLogger("app")
            else:
                logger = logging.getLogger(name)
            cls._loggers[name] = logger

        return cls._loggers[name]

    @classmethod
    def reset_logging(cls) -> None:
        """ログ設定をリセット（主にテスト用）"""
        cls._initialized = False
        cls._loggers.clear()

        # 全てのハンドラーを削除
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)


def get_logger(name: str = __name__) -> logging.Logger:
    """ロガーを取得するためのヘルパー関数

    Args:
        name: ロガー名（デフォルトは呼び出し元のモジュール名）

    Returns:
        設定済みのロガーインスタンス

    Example:
        >>> from logger_utils import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("アプリケーションが開始されました")
    """
    return LoggerManager.get_logger(name)


def setup_logging(config_path: Optional[str] = None, env_key: str = "LOG_CONFIG") -> None:
    """ログ設定を初期化するためのヘルパー関数

    Args:
        config_path: ログ設定ファイルのパス
        env_key: 環境変数のキー名

    Example:
        >>> from logger_utils import setup_logging
        >>> setup_logging("custom_logging.ini")  # カスタム設定ファイル
        >>> setup_logging()  # デフォルト設定ファイル
    """
    LoggerManager.setup_logging(config_path, env_key)


# アプリケーション起動時に自動的にセットアップ
setup_logging()
