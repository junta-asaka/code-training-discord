# Tox・Pytest・Coverage設定解説

このドキュメントでは、`pyproject.toml`に記載されているtox、pytest、coverageの設定項目について詳しく解説します。

## 🔧 [tool.tox] - Tox設定

### legacy_tox_ini

```toml
[tool.tox]
legacy_tox_ini = """
~
"""
```

- **目的**: 従来のINI形式のtox設定をpyproject.toml内に記述するため
- **理由**: toxはまだpyproject.tomlネイティブサポートが完全ではないため、この方法を使用

### [tox] セクション

```ini
envlist = py312
log_file = tox.log
```

- **`envlist`**: 実行する環境のリスト（Python 3.12環境を指定）
- **`log_file`**: toxの実行ログを保存するファイル名

### [testenv] セクション

```ini
runner = uv-venv-runner
```

- **`runner`**: `tox-uv`プラグインを使用してuvで仮想環境を高速作成

```ini
deps = 
    pytest
    pytest-cov
```

- **`deps`**: テスト実行に必要な依存関係
- `pytest`: テストフレームワーク
- `pytest-cov`: カバレッジ測定プラグイン

```ini
commands = 
    pytest -v --cov=src --cov-report=html --cov-report=term-missing --cov-report=xml tests/
```

- **`commands`**: 実行するコマンド
- `-v`: 詳細出力（verbose）
- `--cov=src`: `src`ディレクトリのカバレッジを測定
- `--cov-report=html`: HTMLレポート生成
- `--cov-report=term-missing`: ターミナルに未カバー行を表示
- `--cov-report=xml`: XMLレポート生成（CI/CD用）
- `tests/`: testsディレクトリ以下のテストを実行

```ini
setenv =
    PYTHONPATH = {toxinidir}/src
    COVERAGE_FILE = {toxworkdir}/.coverage.{envname}
```

- **`setenv`**: 環境変数の設定
- `PYTHONPATH`: srcディレクトリをPythonパスに追加
- `COVERAGE_FILE`: 各環境別のカバレッジファイル

### [testenv:coverage] セクション

```ini
deps = coverage[toml]
commands =
    coverage combine
    coverage report
    coverage html
depends = py312
```

- **`coverage[toml]`**: TOML設定対応のcoverageツール
- **`coverage combine`**: 複数環境のカバレッジデータを統合
- **`coverage report`**: テキストレポート表示
- **`coverage html`**: HTMLレポート生成
- **`depends`**: py312環境の実行後に実行

## 🧪 [tool.pytest.ini_options] - Pytest設定

```toml
testpaths = ["tests"]
```

- **テストディレクトリ**: testsフォルダ以下を対象

```toml
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

- **ファイル命名規則**: `test_*.py`形式
- **クラス命名規則**: `Test*`で始まるクラス
- **関数命名規則**: `test_*`で始まる関数

```toml
addopts = ["--strict-markers", "--strict-config", "--verbose"]
```

- **`--strict-markers`**: 未定義マーカーでエラー
- **`--strict-config`**: 設定エラーで厳密チェック
- **`--verbose`**: 詳細出力

```toml
filterwarnings = ["error", "ignore::UserWarning", "ignore::DeprecationWarning"]
```

- **警告フィルタ**: 
  - 通常の警告はエラーとして扱う
  - UserWarningとDeprecationWarningは無視

## 📊 [tool.coverage.run] - カバレッジ実行設定

```toml
source = ["src"]
branch = true
omit = ["tests/*", "*/test_*", "*/__pycache__/*"]
```

- **`source`**: カバレッジ測定対象ディレクトリ
- **`branch`**: 分岐カバレッジも測定（if文などの条件分岐）
- **`omit`**: 測定除外パターン（テストファイル、キャッシュファイル）

## 📈 [tool.coverage.report] - カバレッジレポート設定

```toml
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
```

- **除外行**: カバレッジ測定から除外するコードパターン
- **`pragma: no cover`**: 明示的な除外コメント
- **デバッグコード**: 通常実行されないコード
- **抽象メソッド**: 実装されないメソッド
- **例外処理**: AssertionError、NotImplementedError
- **デバッグ条件**: if 0:、if __name__ == "__main__":

```toml
show_missing = true
precision = 2
```

- **`show_missing`**: 未カバー行番号を表示
- **`precision`**: パーセンテージの小数点以下桁数

## 🌐 [tool.coverage.html] - HTMLレポート設定

```toml
directory = "htmlcov"
```

- **出力ディレクトリ**: HTMLレポートの保存先

## 💡 使用方法

### 基本的な実行コマンド

```bash
# 全テスト実行（カバレッジ付き）
tox

# 特定の環境でテスト実行
tox -e py312

# カバレッジレポートのみ生成
tox -e coverage

# 並列実行
tox -p auto

# 環境再作成
tox -r

# 詳細ログ付き実行
tox -v
```

### 出力されるレポート

1. **ターミナル出力**: テスト結果とカバレッジサマリー
2. **HTMLレポート**: `htmlcov/index.html`で詳細カバレッジ確認
3. **XMLレポート**: CI/CDツールでの結果統合用

### カバレッジレポートの確認

HTMLレポートを開くには：

```bash
# Windows
start htmlcov/index.html

# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

## 📁 生成されるファイル・ディレクトリ

- `.tox/`: tox実行環境
- `htmlcov/`: HTMLカバレッジレポート
- `.coverage.*`: カバレッジデータファイル
- `tox.log`: tox実行ログ
- `coverage.xml`: XMLカバレッジレポート

## 🎯 設定のメリット

1. **高速実行**: `tox-uv`による仮想環境の高速作成
2. **詳細レポート**: HTML、XML、ターミナル出力の3形式対応
3. **分岐カバレッジ**: 条件分岐も含む包括的なカバレッジ測定
4. **柔軟な除外**: 不要なコードの除外設定
5. **CI/CD対応**: XMLレポートによる自動化対応

この設定により、高品質なテスト環境とカバレッジレポートが自動生成されます！