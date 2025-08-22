# toorPIA MCP Server

toorPIA APIをMCPツールとして提供するサーバー実装。

## 新しい構成

単一ファイル実装から以下の構造に分割：

```
src/
├─ server.ts                 # エントリポイント（MCPサーバ起動）
├─ tools/
│  ├─ common.ts             # 共通ツール（locate_file, detect_file_type, etc.）
│  ├─ csv.ts                # CSVワークフロー（fit_transform, addplot）
│  └─ wav.ts                # WAVワークフロー（ENABLE_WAV制御）
├─ prompts/
│  ├─ workflow_csv.ts       # CSVワークフロー案内
│  └─ workflow_wav.ts       # WAVワークフロー案内
├─ client/
│  └─ toorpia.ts            # toorPIA APIクライアント
└─ types.ts                 # 共通型定義
```

## 起動方法

### 開発モード
```bash
npm run dev
```

### プロダクションビルド
```bash
npm run build
npm start
```

## 環境変数

`.env.example`を`.env`にコピーして設定：

```bash
# toorPIA API設定
TOORPIA_API_KEY=your_api_key_here
TOORPIA_API_URL=http://localhost:3000

# 機能制御
ENABLE_WAV=true
```

### ENABLE_WAV による制御

- `ENABLE_WAV=true` (デフォルト): WAV機能有効
- `ENABLE_WAV=false`: WAV機能無効（NOT_IMPLEMENTED応答）

## 新規ツール

### locate_file
ファイル存在確認と絶対パス取得

```json
// 入力
{
  "baseDir": "/path/to/base", // optional
  "path": "relative/file.csv"
}

// 出力（成功）
{
  "ok": true,
  "absPath": "/path/to/base/relative/file.csv",
  "exists": true
}

// 出力（エラー）
{
  "ok": false,
  "code": "LOCATE_ERROR",
  "reason": "エラー詳細"
}
```

### detect_file_type
ファイル形式判定（CSV/WAV/unknown）

```json
// 入力
{
  "path": "/path/to/file.wav"
}

// 出力（WAV）
{
  "ok": true,
  "kind": "wav",
  "reason": "Detected WAV by RIFF header"
}

// 出力（CSV）
{
  "ok": true,
  "kind": "csv", 
  "reason": "Detected CSV by extension"
}

// 出力（不明）
{
  "ok": true,
  "kind": "unknown",
  "reason": "Unknown file type with extension: .txt"
}
```

## 既存ツール（API互換性保持）

以下の10ツールは完全に互換性を保持：

- `fit_transform`: CSVデータからベースマップ作成
- `addplot`: 既存マップにデータ追加
- `fit_transform_waveform`: WAVファイルからベースマップ作成
- `addplot_waveform`: WAVファイルをマップに追加
- `list_map`: マップ一覧
- `list_addplots`: Addplot一覧  
- `get_addplot`: Addplot詳細取得
- `get_addplot_features`: 特徴量取得
- `export_map`: マップエクスポート
- `import_map`: マップインポート
- `whoami`: 認証確認

## エラーレスポンス統一

全ツールで統一されたエラー形式：

```json
{
  "ok": false,
  "code": "ERROR_CODE",
  "reason": "詳細なエラー説明"
}
```

## ログ出力

各ツール呼び出しでログ出力：
```
[TOOL] tool_name: OK (123ms)
[TOOL] tool_name: ERROR:AUTH_FAILED (45ms)
```

## MCP クライアント設定例

### Claude Desktop
`mcp_settings.json`:
```json
{
  "mcpServers": {
    "toorpia-mcp": {
      "command": "node",
      "args": ["./dist/server.js"],
      "cwd": "/path/to/toorpia-mcp",
      "env": {
        "TOORPIA_API_KEY": "your_key_here",
        "TOORPIA_API_URL": "http://localhost:3000",
        "ENABLE_WAV": "true"
      }
    }
  }
}
```

### MCP Inspector
```bash
node ./dist/server.js
```

## 実装状況

### ✅ 完了
- ファイル分割リファクタリング
- API互換性保持
- 新規ツール（locate_file, detect_file_type）
- 統一エラーレスポンス
- ログ機能
- ENABLE_WAV制御
- プロンプト登録（案内テンプレート）

### 🚧 未実装（今後のPR）
- CSVワークフロー詳細機能：
  - preview_schema: スキーマプレビュー
  - apply_schema: スキーマ適用
  - get_schema: スキーマ取得
  - generate_runner: 実行プラン生成
  - run_runner: 実行プラン実行
- WAV機能の詳細実装
- プロンプトの実際の登録（MCP SDK対応時）

## 開発者向け

### ツール追加
1. `src/tools/[category].ts`にツール実装
2. `src/server.ts`でインポート・登録

### エラーハンドリング
- 統一された`{ok, code, reason}`形式を使用
- ログ関数`logTool(name, result, duration)`を呼び出し

### 環境変数
- 機能制御は環境変数で実装
- `.env.example`に新しい変数を追加
