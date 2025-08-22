import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { ENABLE_WAV } from "../tools/wav.js";

const WAV_WORKFLOW_ENABLED_PROMPT = `# WAV 音声データ処理ワークフロー

WAV音声ファイルを使用したtoorPIA分析のためのステップバイステップガイド：

## 基本ワークフロー

### 1. ファイル確認
まず、処理したい音声ファイルの場所と形式を確認してください：

\`\`\`
locate_file: ファイル存在確認と絶対パス取得
- baseDir (optional): ベースディレクトリ
- path: ファイルパス

detect_file_type: ファイル形式判定
- path: ファイルパス
- 戻り値: kind="wav" の場合のみ以下のワークフローを続行
\`\`\`

### 2. ベースマップ作成 (fit_transform_waveform)
WAVファイルからベースマップを作成：

\`\`\`
fit_transform_waveform: WAVファイルからベースマップ作成
- files: WAVファイルパスの配列
- mkfftseg_* パラメータ（FFT設定）:
  - di: decimation interval (default: 1)
  - hp: high-pass filter (default: -1.0)
  - lp: low-pass filter (default: -1.0)
  - nm: noise mode (default: 0)
  - ol: overlap percentage (default: 50.0)
  - sr: sample rate (default: 48000)
  - wf: window function (default: "hanning")
  - wl: window length (default: 65536)
- identna_resolution (optional): 解像度パラメータ
- identna_effective_radius (optional): 有効半径パラメータ
- label, tag, description (optional): メタデータ

戻り値: { xyData, mapNo, shareUrl }
\`\`\`

### 3. 音声データ追加 (addplot_waveform)
既存のマップに新しい音声データを追加：

\`\`\`
addplot_waveform: 既存マップへのWAVデータ追加
- files: WAVファイルパスの配列
- mapNo (optional): マップ番号（省略時は前回のfit_transform_waveformのmapNoを使用）
- mkfftseg_* パラメータ（上記と同様）
- detabn_* パラメータ（異常検知設定）:
  - max_window: 最大ウィンドウ (default: 5)
  - rate_threshold: レート閾値 (default: 1.0)
  - threshold: 閾値 (default: 0)
  - print_score: スコア出力 (default: true)

戻り値: { xyData, addPlotNo, abnormalityStatus, abnormalityScore, shareUrl }
\`\`\`

### 4. 結果分析
結果の詳細分析には共通ツールを使用：

\`\`\`
get_addplot_features: 特徴量取得
get_addplot: Addplotの詳細情報取得
list_addplots: マップの全Addplot一覧
\`\`\`

## パラメータの詳細

### FFTセグメント化パラメータ (mkfftseg_*)
- **di**: データのサンプリング間隔
- **hp/lp**: ハイパス/ローパスフィルタの周波数
- **ol**: セグメント間の重複率（%）
- **sr**: サンプリングレート（Hz）
- **wf**: 窓関数（"hanning", "hamming", "blackman"等）
- **wl**: 窓長（サンプル数）

### 異常検知パラメータ (detabn_*)
- **max_window**: 異常検知用の最大ウィンドウサイズ
- **rate_threshold**: 検知感度の閾値
- **threshold**: 異常判定の閾値
- **print_score**: 詳細スコア出力の有無

## 注意事項

- WAVファイルは有効なRIFFヘッダーを持つ必要があります
- ファイルサイズと処理時間を考慮してください
- エラーハンドリングでは統一された { ok: false, code, reason } 形式が返されます
- 全てのツール呼び出しはログ出力されます（[TOOL] name: status (time)）
`;

const WAV_WORKFLOW_DISABLED_PROMPT = `# WAV 音声データ処理ワークフロー

## 機能無効化のお知らせ

現在、WAV音声データ処理機能は無効化されています。

### 有効化方法

WAV機能を使用するには、以下の手順で有効化してください：

1. \`.env\` ファイルに以下を追加：
   \`\`\`
   ENABLE_WAV=true
   \`\`\`

2. MCPサーバーを再起動

### 無効化時の動作

\`detect_file_type\` で \`kind="wav"\` が検出された場合：

1. WAV関連ツール（\`fit_transform_waveform\`, \`addplot_waveform\`）を呼び出すと：
   \`\`\`json
   {
     "ok": false,
     "code": "NOT_IMPLEMENTED",
     "reason": "WAV workflow is disabled. Set ENABLE_WAV=true in .env to enable [tool_name]"
   }
   \`\`\`

2. ユーザーに機能の有効化方法を案内し、処理を終了してください

### 代替手段

WAV機能が無効な場合の代替案：
- CSVデータへの前処理変換
- 他の音声処理ツールとの連携
- 手動でのデータ準備

## 技術的詳細

WAV機能の無効化は環境変数 \`ENABLE_WAV\` により制御されます：
- \`ENABLE_WAV=true\`: 機能有効（デフォルト）
- \`ENABLE_WAV=false\`: 機能無効
- 設定なし: 機能有効
`;

export function registerWorkflowWavPrompt(server: Server): void {
  // プロンプト登録の実装
  // Note: 実際のMCP SDK のプロンプト機能が利用可能な場合に実装
  const status = ENABLE_WAV ? "enabled" : "disabled";
  console.error(`[PROMPT] workflow_wav registered (${status})`);
}

export const wavWorkflowPrompt = ENABLE_WAV ? WAV_WORKFLOW_ENABLED_PROMPT : WAV_WORKFLOW_DISABLED_PROMPT;
