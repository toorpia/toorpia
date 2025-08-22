import { Server } from "@modelcontextprotocol/sdk/server/index.js";

const CSV_WORKFLOW_PROMPT = `# CSVデータ処理ワークフロー完全ガイド

toorPIA MCP サーバーのCSVワークフローは、インタラクティブなデータ分析パイプラインを提供します。

## CSVワークフロー: プレビュー → スキーマ調整 → 確定 → スクリプト生成 → 実行

### ステップ1: ファイル確認と初期化
\`\`\`bash
# ファイルの場所確認
locate_file: ファイル存在確認と絶対パス取得
- path: ファイルパス
- baseDir (optional): ベースディレクトリ

detect_file_type: ファイル形式判定
- path: ファイルパス
- 戻り値: kind="csv" の場合のみCSVワークフローを続行

# CSVプレビューとスキーマ初期化
csv.preview: CSV構造の確認と自動型推論
- path: 絶対ファイルパス（locate_fileで取得）
- nRows: サンプル行数（default: 5）

戻り値例:
{
  "ok": true,
  "filePath": "/path/to/file.csv",
  "rowCount": 100,
  "columns": [
    {"name": "timestamp", "type": "datetime", "weight": 0.8, "use": true},
    {"name": "temperature", "type": "number", "weight": 1.0, "use": true},
    {"name": "sensor_id", "type": "string", "weight": 0.5, "use": true}
  ],
  "sampleData": [["2024-01-01T10:00:00", 23.5, "TEMP_001"], ...]
}
\`\`\`

### ステップ2: スキーマ調整（任意）
\`\`\`bash
# カラムの設定変更
csv.apply_schema_patch: カラム属性の変更
- path: 絶対ファイルパス
- patches: 変更内容の配列
  - columnName: カラム名
  - updates: 
    - type: "integer"|"number"|"boolean"|"datetime"|"string"
    - weight: 重み値（0.0-1.0）
    - use: 使用フラグ（true/false）
    - description: 説明（任意）

# 現在のスキーマ確認
csv.get_schema: スキーマ状態の取得
- path: 絶対ファイルパス
\`\`\`

### ステップ3: スクリプト生成
\`\`\`bash
csv.generate_runner: toorPIA準拠Pythonスクリプト生成
- path: 絶対ファイルパス
- outputPath: 出力パス（任意）

# 自動生成される内容:
# - CSV_PATH: ファイルパス
# - DROP_COLUMNS: use:false または weight:0 のカラム
# - toorPIA().fit_transform(df) 呼び出し
\`\`\`

### ステップ4: スクリプト実行
\`\`\`bash
csv.run_runner: Pythonスクリプトの同期実行
- scriptContent: 実行するPythonコード

# 前提条件:
# - python3 コマンドが利用可能
# - toorpia パッケージがインストール済み
# - TOORPIA_API_KEY 環境変数が設定済み

戻り値:
{
  "ok": true,
  "stdout": "実行結果...",
  "stderr": "エラー出力...",
  "exitCode": 0
}
\`\`\`

## 型推論システム

CSVワークフローは以下の自動型推論を実行：

### サポートされている型
- **integer**: 整数値
- **number**: 浮動小数点数
- **boolean**: true/false, 1/0, yes/no パターン
- **datetime**: Date.parse()成功かつ日時パターン
- **string**: その他の文字列データ

### デフォルト重み
- integer/number: 1.0
- datetime: 0.8  
- boolean: 0.6
- string: 0.5

## エラーハンドリング

統一されたエラーレスポンス形式 \`{ ok: false, code, reason }\`：

- **NOT_FOUND**: ファイルまたはデータが見つからない
- **SCHEMA_NOT_INITIALIZED**: スキーマが初期化されていない
- **SCHEMA_NOT_READY**: スキーマの準備が未完了
- **UNKNOWN_COLUMN**: 指定されたカラムが存在しない
- **RUNTIME_ERROR**: 実行時エラー
- **PYTHON_NOT_FOUND**: Python環境が見つからない

## レガシーツール（下位互換性）

従来の fit_transform と addplot ツールも引き続き利用可能：
- fit_transform: pandas orient="split" データから直接マップ作成
- addplot: 既存マップへのデータ追加

## WAVワークフロー

WAVファイル処理については、現在開発中です。
detect_file_type で kind="wav" が検出された場合は、以下をご確認ください：

- WAVファイル処理機能は workflow_wav プロンプトを参照
- 現在は基本的な検出機能のみ実装済み
- フル機能は ENABLE_WAV 環境変数で制御

## 使用例

testdata/sensor_log.csv を使用したサンプルワークフロー：

1. \`locate_file\` でファイルパスを確認
2. \`detect_file_type\` でCSV形式を確認  
3. \`csv.preview\` でスキーマ初期化
4. 必要に応じて \`csv.apply_schema_patch\` で調整
5. \`csv.generate_runner\` でPythonスクリプト生成
6. \`csv.run_runner\` で分析実行

全てのツールは統一ログ形式 \`[TOOL] name: status (duration)ms\` で記録されます。
`;

export function registerWorkflowCsvPrompt(server: Server): void {
  // プロンプト登録の実装
  // Note: 実際のMCP SDK のプロンプト機能が利用可能な場合に実装
  console.error("[PROMPT] workflow_csv registered");
}

export const csvWorkflowPrompt = CSV_WORKFLOW_PROMPT;
