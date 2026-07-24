# リリース手順

toorPIA Python クライアントのバージョンアップと PyPI 公開の手順。

## 通常のリリースフロー

1. **バージョン更新**: `pyproject.toml` の `[project] version` を更新する（例: `1.4.0`）
2. **リリースノート作成**: `docs/release-notes/vX.Y.Z_jp.md` を作成する（既存のノートの形式に従う）
3. **PR → main へマージ**
4. **タグ付け**: マージコミットに注釈付きタグを付けて push する

   ```bash
   git tag -a vX.Y.Z -m "toorPIA Python Client vX.Y.Z — 変更概要"
   git push origin vX.Y.Z
   ```

5. **GitHub Release 公開**:

   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z" --notes-file docs/release-notes/vX.Y.Z_jp.md
   ```

6. Release の公開をトリガーに `.github/workflows/publish.yml` が自動で sdist + wheel を
   ビルドし、PyPI へアップロードする（タグとパッケージバージョンの不一致はビルドが
   失敗して検出される）。進捗は Actions タブで確認できる

## PyPI Trusted Publisher の初期設定（初回のみ）

publish ワークフローは APIトークンではなく [Trusted Publishing (OIDC)](https://docs.pypi.org/trusted-publishers/) を使う。
初回は PyPI 側での登録が必要:

1. PyPI にログインし（組織/会社管理のアカウント推奨。2FA 必須）、
   [Publishing](https://pypi.org/manage/account/publishing/) ページの
   「Add a new pending publisher」で以下を登録する:
   - **PyPI Project Name**: `toorpia`
   - **Owner**: `toorpia`
   - **Repository name**: `toorpia`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
2. GitHub リポジトリの Settings → Environments で `pypi` という environment を作成する
   （必要に応じて protection rule で承認者を設定）
3. 初回公開は Actions タブから「Publish to PyPI」を手動実行（workflow_dispatch）するか、
   次回の Release 公開を待つ。公開に成功すると pending publisher が正式な
   Trusted Publisher に昇格する

## ローカルでのビルド確認

```bash
python3 -m venv .venv && .venv/bin/pip install build twine
.venv/bin/python -m build          # dist/ に sdist と wheel を生成
.venv/bin/python -m twine check dist/*
tar tzf dist/toorpia-*.tar.gz      # 同梱物の確認（秘密情報が入っていないこと）
```

## 注意事項

- **一度 PyPI に公開したバージョン番号は再利用できない**（削除しても再アップロード不可、
  yank のみ可能）。公開前にバージョン・内容を必ず確認すること
- サンプルデータ・APIキー（`samples/env.sh` 等）はパッケージに含めない。
  wheel には `toorpia/` パッケージのみが入る構成を維持すること
