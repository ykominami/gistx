GitHhub.comにおけるgistの取得方法

1. 認証なし — ユーザー名指定
GET https://api.github.com/users/{username}/gists
認証不要で、publicなgistのみ返る
ページネーション: ?per_page=100&page=1（最大100件/ページ）
curl "https://api.github.com/users/USERNAME/gists?per_page=100&page=1"

2. 認証あり — 自分のgist全取得
GET https://api.github.com/gists
トークン認証が必要（Authorization: Bearer <token> or token <token>）
publicとprivate両方が返る
publicだけ欲しい場合はレスポンスの public フィールドでフィルタする
curl -H "Authorization: Bearer ghp_xxxx" "https://api.github.com/gists?per_page=100&page=1"
レスポンス例（主要フィールド）
{
  "id": "abc123...",
  "description": "My gist [title]",
  "public": true,
  "git_pull_url": "https://gist.github.com/abc123.git",
  "html_url": "https://gist.github.com/abc123",
  "files": { ... },
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-02T00:00:00Z"
}

トークンを使うメリットは レートリミットが60回/時→5000回/時に上がる ことです。

# 認証用トークの取得方法
Fine-grained Personal Access Token（推奨-X Gist）
GitHubにログイン
Settings → Developer settings → Personal access tokens → Fine-grained tokens
Generate new token をクリック
設定：
Token name: 任意の名前（例: gistx）
Expiration: 有効期限を選択
Permissions → Account permissions → Gists: Read-only に設定
Generate token → 表示されたトークン (github_pat_...) をコピー
直接URL: https://github.com/settings/personal-access-tokens/new

Classic Token（従来方式-O Gist）
Settings → Developer settings → Personal access tokens → Tokens (classic)
Generate new token (classic) をクリック
Scopes で gist にチェック
Generate token → 表示されたトークン (ghp_...) をコピー
直接URL: https://github.com/settings/tokens/new
注意点