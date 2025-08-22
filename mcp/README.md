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

### 重要: TOORPIA_API_KEY 設定

**CSVワークフローでPythonスクリプト実行時に必要:**

1. **環境変数として設定**（推奨）：
   ```bash
   export TOORPIA_API_KEY="your_actual_api_key_here"
   ```

2. **MCPサーバー起動時に指定**：
   ```json
   {
     "env": {
       "TOORPIA_API_KEY": "your_actual_api_key_here"
     }
   }
   ```

3. **Python環境での前提条件**：
   - `python3` コマンドが利用可能
   - `pip install toorpia` でパッケージインストール済み
   - `TOORPIA_API_KEY` 環境変数が設定済み

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

## CSVワークフロー

完全なインタラクティブCSVデータ処理パイプライン：

### csv.preview
CSVファイルの自動型推論とスキーマ初期化

```json
// 入力
{
  "path": "/absolute/path/to/file.csv",
  "nRows": 5  // optional, default: 5
}

// 出力
{
  "ok": true,
  "filePath": "/absolute/path/to/file.csv",
  "rowCount": 20,
  "columns": [
    {
      "name": "timestamp",
      "type": "datetime",
      "weight": 0.8,
      "use": true
    },
    {
      "name": "temperature", 
      "type": "number",
      "weight": 1.0,
      "use": true
    }
  ],
  "sampleData": [
    ["2024-01-01T10:00:00", 23.5],
    ["2024-01-01T10:05:00", 23.7]
  ]
}
```

### csv.apply_schema_patch
カラムスキーマの調整（型・重み・使用フラグ）

```json
// 入力
{
  "path": "/absolute/path/to/file.csv",
  "patches": [
    {
      "columnName": "sensor_id",
      "updates": {
        "type": "string",
        "weight": 0.0,
        "use": false,
        "description": "Exclude sensor ID from analysis"
      }
    }
  ]
}

// 出力  
{
  "ok": true,
  "updatedColumns": ["sensor_id"]
}
```

### csv.get_schema
現在のスキーマ状態確認

```json
// 入力
{
  "path": "/absolute/path/to/file.csv"
}

// 出力
{
  "ok": true,
  "schema": {
    "filePath": "/absolute/path/to/file.csv",
    "columns": [...],
    "rowCount": 20,
    "sampleData": [...],
    "description": "CSV file with 20 rows and 7 columns"
  }
}
```

### csv.generate_runner
toorPIA準拠Pythonスクリプト生成

```json
// 入力
{
  "path": "/absolute/path/to/file.csv",
  "outputPath": "/path/to/script.py"  // optional
}

// 出力
{
  "ok": true,
  "script": "#!/usr/bin/env python3\n# Auto-generated script...",
  "scriptPath": "/path/to/script.py"
}
```

### csv.run_runner
Pythonスクリプト同期実行

```json
// 入力
{
  "scriptContent": "import pandas as pd\nfrom toorpia import toorPIA\n..."
}

// 出力（成功）
{
  "ok": true,
  "stdout": "Loading CSV data...\nAnalysis complete!",
  "stderr": "",
  "exitCode": 0
}

// 出力（エラー）
{
  "ok": false,
  "code": "RUNTIME_ERROR",
  "reason": "Python script failed with exit code 1: ModuleNotFoundError: No module named 'toorpia'"
}
```

### 完全ワークフロー例

testdata/sensor_log.csv を使用：

```bash
# 1. ファイル確認
locate_file -> 絶対パス取得
detect_file_type -> CSV確認

# 2. スキーマ初期化  
csv.preview -> 自動型推論、サンプルデータ表示

# 3. スキーマ調整（任意）
csv.apply_schema_patch -> 不要カラム除外、重み調整

# 4. Pythonスクリプト生成
csv.generate_runner -> DROP_COLUMNS自動設定、toorPIA呼び出し

# 5. 実行
csv.run_runner -> 分析実行、結果取得
```

### エラーコード

CSVワークフロー専用エラー：
- `NOT_FOUND`: ファイルまたはデータが見つからない
- `SCHEMA_NOT_INITIALIZED`: スキーマが未初期化（csv.preview必須）
- `SCHEMA_NOT_READY`: スキーマが準備未完了
- `UNKNOWN_COLUMN`: 指定カラムが存在しない
- `RUNTIME_ERROR`: 実行時エラー
- `PYTHON_NOT_FOUND`: python3コマンド未発見

## 実装状況

### ✅ 完了
- **ファイル分割リファクタリング**: 単一ファイルから構造化アーキテクチャ
- **API互換性保持**: 既存10ツール完全互換
- **新規ツール**: locate_file, detect_file_type
- **CSVワークフロー**: プレビュー→調整→生成→実行の完全パイプライン
  - csv.preview: 自動型推論とスキーマ初期化
  - csv.apply_schema_patch: インタラクティブスキーマ調整
  - csv.get_schema: スキーマ状態確認
  - csv.generate_runner: toorPIA準拠スクリプト生成
  - csv.run_runner: Python同期実行
- **統一エラーレスポンス**: {ok, code, reason}形式
- **ログ機能**: [TOOL] name: status (duration)ms
- **ENABLE_WAV制御**: 環境変数による機能制御
- **プロンプト登録**: 完全ワークフロー案内

### 🚧 未実装（今後のPR）
- WAV機能の詳細実装
- プロンプトの実際の登録（MCP SDK対応時）
- 追加データ処理パイプライン

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
