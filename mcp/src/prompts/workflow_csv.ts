import { Server } from "@modelcontextprotocol/sdk/server/index.js";

const CSV_WORKFLOW_PROMPT = `# CSV データ処理ワークフロー

CSVデータを使用したtoorPIA分析のためのステップバイステップガイド：

## 基本ワークフロー

### 1. ファイル確認
まず、処理したいファイルの場所と形式を確認してください：

\`\`\`
locate_file: ファイル存在確認と絶対パス取得
- baseDir (optional): ベースディレクトリ
- path: ファイルパス

detect_file_type: ファイル形式判定
- path: ファイルパス
- 戻り値: kind="csv" の場合のみ以下のワークフローを続行
\`\`\`

### 2. ベースマップ作成 (fit_transform)
CSVデータからベースマップを作成：

\`\`\`
fit_transform: DataFrame形式のデータからベースマップ作成
- data: pandas orient="split" 形式のデータ
  - columns: カラム名リスト
  - data: 数値データの2次元配列
  - index (optional): インデックス
- label (optional): マップのラベル
- tag (optional): タグ
- description (optional): 説明
- random_seed (optional): 乱数シード
- weight_option_str (optional): 重み付けオプション
- type_option_str (optional): タイプオプション
- identna_resolution (optional): 解像度パラメータ
- identna_effective_radius (optional): 有効半径パラメータ

戻り値: { xyData, mapNo, shareUrl }
\`\`\`

### 3. データ追加 (addplot)
既存のマップに新しいデータを追加：

\`\`\`
addplot: 既存マップへのデータ追加
- data: pandas orient="split" 形式のデータ
- mapNo (optional): マップ番号（省略時は前回のfit_transformのmapNoを使用）
- mode: "xy" | "full" (default: "full")
  - "xy": xyDataのみを返す
  - "full": 全ての結果データを返す
- weight_option_str, type_option_str: 重み・タイプオプション
- detabn_*: 異常検知パラメータ

戻り値: { xyData, addPlotNo, abnormalityStatus, abnormalityScore, shareUrl }
\`\`\`

### 4. 結果分析
結果の詳細分析：

\`\`\`
get_addplot_features: 特徴量取得
- mapNo, addplotNo: マップとAddplot番号
- use_tscore (optional): t-score使用（default: z-score）

get_addplot: Addplotの詳細情報取得
list_addplots: マップの全Addplot一覧
\`\`\`

## データ形式の例

pandas orient="split" 形式：
\`\`\`json
{
  "columns": ["feature1", "feature2", "feature3"],
  "data": [
    [1.0, 2.5, 3.1],
    [1.2, 2.3, 3.4],
    [0.9, 2.7, 2.8]
  ],
  "index": ["sample1", "sample2", "sample3"]  // optional
}
\`\`\`

## 注意事項

- 他の形式のファイル（WAV等）が検出された場合は、適切なワークフローに誘導してください
- エラーハンドリングでは統一された { ok: false, code, reason } 形式が返されます
- 全てのツール呼び出しはログ出力されます（[TOOL] name: status (time)）

## 次のステップ

ワークフローが完了したら、以下の操作も可能です：
- export_map: マップデータのエクスポート
- 結果の可視化や更なる分析
`;

export function registerWorkflowCsvPrompt(server: Server): void {
  // プロンプト登録の実装
  // Note: 実際のMCP SDK のプロンプト機能が利用可能な場合に実装
  console.error("[PROMPT] workflow_csv registered");
}

export const csvWorkflowPrompt = CSV_WORKFLOW_PROMPT;
