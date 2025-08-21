# toorPIA MCP Server

This is a Model Context Protocol (MCP) server that provides access to toorPIA API endpoints as MCP tools. It enables seamless integration of toorPIA's data analysis capabilities into applications supporting MCP, such as Claude Desktop.

## 機能概要

toorPIA MCPサーバーは、toorPIA APIの機能をMCPツールとして公開し、以下の操作を提供します：

### データ分析機能
- **fit_transform**: DataFrameからベースマップを作成
- **addplot**: 既存マップにデータを追加（異常検知を含む）
- **fit_transform_waveform**: WAV/CSVファイルからベースマップを作成
- **addplot_waveform**: WAV/CSVファイルを既存マップに追加

### マップ管理機能
- **list_map**: 利用可能なマップの一覧表示
- **export_map**: マップのエクスポート（ローカル保存）
- **import_map**: マップのインポート（ローカルから読み込み）

### 追加プロット機能
- **list_addplots**: マップの追加プロット一覧表示
- **get_addplot**: 特定の追加プロットの詳細取得
- **get_addplot_features**: 追加プロットの特徴量分析

### 認証・ヘルス機能
- **whoami**: 認証状態の確認

## セットアップ

### 1. 依存関係のインストール

```bash
cd mcp
npm install
```

### 2. TypeScriptのビルド

```bash
npm run build
```

### 3. 環境変数の設定

以下の環境変数を設定してください：

```bash
export TOORPIA_API_KEY="your-api-key-here"
export TOORPIA_API_URL="http://localhost:3000"  # オプション（デフォルトは http://localhost:3000）
```

### 4. Claude Desktop との連携

Claude Desktopの設定ファイル（通常`~/Library/Application Support/Claude/claude_desktop_config.json`）に以下を追加：

```json
{
  "mcpServers": {
    "toorpia": {
      "command": "node",
      "args": ["./dist/index.js"],
      "cwd": "/path/to/your/toorpia/mcp",
      "env": {
        "TOORPIA_API_KEY": "your-actual-api-key",
        "TOORPIA_API_URL": "http://localhost:3000"
      }
    }
  }
}
```

**重要**: 
- `/path/to/your/toorpia/mcp` を実際のパスに変更してください
- `your-actual-api-key` を実際のAPIキーに変更してください

## 利用可能なツール

### データ処理系

#### fit_transform
DataFrame（pandas orient='split'形式）からベースマップを作成します。

**パラメータ:**
- `data`: DataFrame（orient='split'形式）
- `label`, `tag`, `description`: メタデータ（オプション）
- `weight_option_str`, `type_option_str`: カラムの重み・型設定（オプション）
- `identna_resolution`, `identna_effective_radius`: identnaパラメータ（オプション）

#### addplot
既存のマップにDataFrameデータを追加し、異常検知を実行します。

**パラメータ:**
- `data`: DataFrame（orient='split'形式）
- `mapNo`: 対象マップ番号（オプション、省略時は最後のfit_transformで作成されたマップを使用）
- `detabn_*`: 異常検知パラメータ（オプション）
- `mode`: 'xy'（座標データのみ）または'full'（全情報、デフォルト）

#### fit_transform_waveform
WAVまたはCSVファイルからベースマップを作成します。

**パラメータ:**
- `files`: ファイルパスの配列
- `mkfftseg_*`: FFTセグメント化パラメータ（オプション）
- `identna_*`: identnaパラメータ（オプション）
- `label`, `tag`, `description`: メタデータ（オプション）

#### addplot_waveform
WAVまたはCSVファイルを既存マップに追加し、異常検知を実行します。

**パラメータ:**
- `files`: ファイルパスの配列
- `mapNo`: 対象マップ番号（オプション）
- `mkfftseg_*`: FFTセグメント化パラメータ（オプション）
- `detabn_*`: 異常検知パラメータ（オプション）

### マップ管理系

#### list_map
利用可能なマップの一覧を取得します。

#### export_map
指定されたマップをローカルディレクトリにエクスポートします。

**パラメータ:**
- `mapNo`: エクスポートするマップ番号
- `exportDir`: エクスポート先ディレクトリパス

#### import_map
ローカルディレクトリからマップをインポートします。

**パラメータ:**
- `inputDir`: インポート元ディレクトリパス

### 追加プロット管理系

#### list_addplots
指定されたマップの追加プロット一覧を取得します。

**パラメータ:**
- `mapNo`: 対象マップ番号

#### get_addplot
特定の追加プロットの詳細情報を取得します。

**パラメータ:**
- `mapNo`: 対象マップ番号
- `addplotNo`: 追加プロット番号

#### get_addplot_features
追加プロットの特徴量分析結果を取得します。

**パラメータ:**
- `mapNo`: 対象マップ番号
- `addplotNo`: 追加プロット番号
- `use_tscore`: Tスコアを使用するかどうか（デフォルト: false、Zスコア使用）

## 開発・デバッグ

### 開発モード
```bash
npm run dev
```

### ビルド
```bash
npm run build
```

### 本番実行
```bash
npm start
```

## client.pyとの対応関係

このMCPサーバーは、toorPIA Python client.pyの機能をほぼ完全にカバーしています：

| Python client.py | MCP Tool | 説明 |
|------------------|----------|------|
| `fit_transform()` | `fit_transform` | DataFrameからベースマップ作成 |
| `addplot()` | `addplot` | DataFrameの追加プロット |
| `fit_transform_waveform()` | `fit_transform_waveform` | 波形ファイルからベースマップ作成 |
| `addplot_waveform()` | `addplot_waveform` | 波形ファイルの追加プロット |
| `list_map()` | `list_map` | マップ一覧取得 |
| `export_map()` / `download_map()` | `export_map` | マップエクスポート |
| `import_map()` / `upload_map()` | `import_map` | マップインポート |
| `list_addplots()` | `list_addplots` | 追加プロット一覧取得 |
| `get_addplot()` | `get_addplot` | 追加プロット詳細取得 |
| `get_addplot_features()` | `get_addplot_features` | 特徴量分析 |
| `authenticate()` | 自動実行 | 認証（各ツール実行時に自動実行） |

## 注意事項

1. **ファイルパス**: 波形ファイル処理時は、MCPサーバーからアクセス可能なファイルパスを指定してください
2. **認証**: 各ツール実行時に自動で認証が行われます（明示的な認証は不要）
3. **セッション管理**: セッションキーは自動で管理されます
4. **エラーハンドリング**: APIエラーはMCPツールのエラーとして適切に報告されます

## トラブルシューティング

### 認証エラー
- `TOORPIA_API_KEY` 環境変数が正しく設定されているか確認
- APIキーが有効であることを確認
- `whoami` ツールで認証状態を確認

### 接続エラー
- `TOORPIA_API_URL` が正しいか確認
- toorPIA APIサーバーが起動しているか確認
- ネットワーク接続を確認

### ファイルアクセスエラー
- 指定したファイルパスが存在するか確認
- MCPサーバーからファイルへの読み取り権限があるか確認

## ライセンス

このMCPサーバーは、toorPIA APIクライアントライブラリの一部として提供されています。
