# 方法①：最も簡単（パス指定）
uv add ../yklibpy

## 特徴
- Gitである必要はない（単なるローカルディレクトリでOK）
- 最速
- 開発中ライブラリ向け
# 方法②：editableモード（開発用途）
# ローカルPC上のgitリポジトリをdependencyに追加する
uv add --editable ../some-local-repo

＋ .venv 内では editable install になります。

## おすすめ用途
- モノレポ
- ローカルライブラリ開発
- CLIツール共通基盤

# 方法③：ローカルGitリポジトリを git URL 形式で指定
uv add "git+file:///C:/path/to/yklibpy"
uv add "git+file:///C:/path/to/yklibpy@main"

## メリット
- ブランチ固定可能
- タグ固定可能
- コミットハッシュ固定可能

# 方法④：直接 pyproject.toml に書く（上級者向け
[project]
dependencies = [
    "yklibpy @ git+file:///C:/path/to/yklibpy@main"
]

uv sync

## 実務ベストプラクティス
### ローカル開発中
uv add --editable ../yklibpy

### リリース前
uv add git+https://github.com/yourname/yklibpy@v1.0.0

# よくあるハマりポイント
-1️ pyproject.toml が無い
→ ローカルリポジトリ側にも pyproject.toml が必要

-2 パッケージ名とディレクトリ名が違う
→ project.name が依存名になります

-3 mypy で import-not-found
→ editable指定していない可能性大
