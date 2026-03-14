# `fix` 安全検証手順

## 1. 目的
- `gistx fix` を実ユーザの `%APPDATA%` / `%LOCALAPPDATA%` に触れずに確認する。
- 次の仕様を安全に確認する。
  - `gistlist/` 配下の空ディレクトリ削除
  - `fetch.yaml` の余剰キー削除
  - `fetch.yaml` の欠損キー補完
  - 数値ディレクトリ 0 件時の空マッピング化
  - `fetch.yaml` 不在時の新規作成

## 2. 前提
- 実行場所はリポジトリルート `E:\Ccur\python3\gistx`
- コマンドは PowerShell で実行する。
- 検証中は同じ PowerShell セッションを使い続ける。

## 3. 安全方針
- 検証用に `$env:APPDATA` と `$env:LOCALAPPDATA` を一時的に退避先へ切り替える。
- 検証対象ユーザ名は `fix-test-user` を使う。
- 実ユーザの設定や既存 gist データは参照しない。

## 4. 共通準備
以下を PowerShell に貼り付けて実行する。

```powershell
Set-Location E:\Ccur\python3\gistx

$script:OriginalAppData = $env:APPDATA
$script:OriginalLocalAppData = $env:LOCALAPPDATA

$script:SandboxRoot = Join-Path (Get-Location) ".tmp\fix-validation"
$env:APPDATA = Join-Path $script:SandboxRoot "appdata"
$env:LOCALAPPDATA = Join-Path $script:SandboxRoot "localappdata"
$script:TestUser = "fix-test-user"

Remove-Item $script:SandboxRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $env:APPDATA | Out-Null
New-Item -ItemType Directory -Force -Path $env:LOCALAPPDATA | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $env:APPDATA "gistx") | Out-Null

@"
gists: gists
url_api: https://api.github.com
user: $script:TestUser
"@ | Set-Content -Encoding UTF8 (Join-Path $env:APPDATA "gistx\config.yaml")

$script:Workspace = Join-Path $env:LOCALAPPDATA "gistx\$script:TestUser"
$script:GistlistTop = Join-Path $script:Workspace "gistlist"
$script:FetchPath = Join-Path $script:Workspace "fetch.yaml"

function Reset-FixSandbox {
    Remove-Item $script:Workspace -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $script:GistlistTop | Out-Null
}
```

共通準備後、次の確認が通ること。

```powershell
Test-Path (Join-Path $env:APPDATA "gistx\config.yaml")
Test-Path $script:GistlistTop
```

両方 `True` なら準備完了。

## 5. 実行コマンド
各ケースのデータ投入後、次を実行する。

```powershell
uv run gistx fix -v
```

## 6. ケース 1: 空ディレクトリ削除
### 準備
```powershell
Reset-FixSandbox
New-Item -ItemType Directory -Force -Path (Join-Path $script:GistlistTop "1\gistrepo\1\public\emptydir") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $script:GistlistTop "1\gistrepo\1\public\keepdir") | Out-Null
Set-Content -Encoding UTF8 (Join-Path $script:GistlistTop "1\gistrepo\1\public\keepdir\dummy.txt") "ok"
@"
'1':
  - '2026-03-09 10:00:00'
  - 1
"@ | Set-Content -Encoding UTF8 $script:FetchPath
```

### 実行
```powershell
uv run gistx fix -v
```

### 確認
```powershell
Test-Path (Join-Path $script:GistlistTop "1\gistrepo\1\public\emptydir")
Test-Path (Join-Path $script:GistlistTop "1\gistrepo\1\public\keepdir")
Test-Path $script:GistlistTop
Get-Content $script:FetchPath
```

### 期待結果
- `emptydir` は `False`
- `keepdir` は `True`
- `gistlist` ルートは `True`
- `fetch.yaml` はそのまま `'1'` を保持する

## 7. ケース 2: `fetch.yaml` の余剰キー削除
### 準備
```powershell
Reset-FixSandbox
New-Item -ItemType Directory -Force -Path (Join-Path $script:GistlistTop "1") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $script:GistlistTop "3") | Out-Null
@"
'1':
  - '2026-03-09 10:00:00'
  - 2
'2':
  - '2026-03-09 10:05:00'
  - 2
'3':
  - '2026-03-09 10:10:00'
  - 2
'9':
  - '2026-03-09 10:20:00'
  - 2
"@ | Set-Content -Encoding UTF8 $script:FetchPath
```

### 実行
```powershell
uv run gistx fix -v
```

### 確認
```powershell
Get-Content $script:FetchPath
```

### 期待結果
- `fetch.yaml` には `'1'` と `'3'` だけが残る
- `'2'` と `'9'` は削除される

## 8. ケース 3: `fetch.yaml` の欠損キー補完
### 準備
```powershell
Reset-FixSandbox
New-Item -ItemType Directory -Force -Path (Join-Path $script:GistlistTop "5") | Out-Null
@"
'1':
  - '2026-03-09 09:00:00'
  - 4
"@ | Set-Content -Encoding UTF8 $script:FetchPath
```

### 実行
```powershell
uv run gistx fix -v
```

### 確認
```powershell
Get-Content $script:FetchPath
```

### 期待結果
- `fetch.yaml` には `'5'` だけが残る
- `'5'` の値は `[timestamp, 0]` 形式で補完される
- 既存の `'1'` は、対応する `gistlist/1` が存在しないため削除される

## 9. ケース 4: 数値ディレクトリ 0 件
### 準備
```powershell
Reset-FixSandbox
New-Item -ItemType Directory -Force -Path (Join-Path $script:GistlistTop "not-a-count") | Out-Null
@"
'1':
  - '2026-03-09 09:00:00'
  - 4
'2':
  - '2026-03-09 09:30:00'
  - 5
"@ | Set-Content -Encoding UTF8 $script:FetchPath
```

### 実行
```powershell
uv run gistx fix -v
```

### 確認
```powershell
Get-Content $script:FetchPath
Test-Path (Join-Path $script:GistlistTop "not-a-count")
```

### 期待結果
- `fetch.yaml` は空マッピングになる
- `not-a-count` は空ディレクトリなので削除される

## 10. ケース 5: `fetch.yaml` 不在
### 準備
```powershell
Reset-FixSandbox
New-Item -ItemType Directory -Force -Path (Join-Path $script:GistlistTop "2") | Out-Null
Remove-Item $script:FetchPath -Force -ErrorAction SilentlyContinue
```

### 実行
```powershell
uv run gistx fix -v
```

### 確認
```powershell
Test-Path $script:FetchPath
Get-Content $script:FetchPath
```

### 期待結果
- `fetch.yaml` が新規作成される
- `fetch.yaml` には `'2'` だけが入る
- `'2'` の値は `[timestamp, 0]` 形式になる

## 11. 補助確認
必要なら各ケースの実行前後で次も使える。

```powershell
Get-ChildItem -Recurse $script:Workspace
```

## 12. 後片付け
```powershell
Remove-Item $script:SandboxRoot -Recurse -Force -ErrorAction SilentlyContinue
$env:APPDATA = $script:OriginalAppData
$env:LOCALAPPDATA = $script:OriginalLocalAppData
Remove-Variable OriginalAppData, OriginalLocalAppData, SandboxRoot, TestUser, Workspace, GistlistTop, FetchPath -Scope Script -ErrorAction SilentlyContinue
Remove-Item Function:\Reset-FixSandbox -ErrorAction SilentlyContinue
```

## 13. 注意
- この手順は実ユーザの gist データを使わない。
- `uv run gistx fix -v` は現在の PowerShell セッション内の `$env:APPDATA` / `$env:LOCALAPPDATA` を参照する。
- 手順の途中で新しいターミナルを開いた場合は、共通準備からやり直す。
