"""
サンプルコード: 追加プロットの特徴量分析API使用例
"""

import pandas as pd
import matplotlib.pyplot as plt
from toorpia import toorPIA

# toorPIAクライアントの初期化
client = toorPIA()

# マップの作成またはロード
# ここでは既存マップを使用する例を示します
# 実際の使用では、fit_transform()でマップを作成するか、
# 既存のマップ番号を指定する必要があります
client.mapNo = 31  # 実際のマップ番号に置き換えてください

# 追加プロットの利用
# すでに実行済みのaddplotを使用する例を示します
# 実際の使用では、addplot()で追加プロットを作成するか、
# 既存の追加プロット番号を指定する必要があります
# client.addplot(data)  # 新しい追加プロットを作成
client.currentAddPlotNo = 1  # 既存の追加プロット番号

# 追加プロットの特徴量分析を取得
features = client.get_addplot_features(use_tscore=False)  # Zスコア使用

if features:
    print(f"分析結果: マップ {features['mapNo']}, 追加プロット {features['addPlotNo']}")
    print(f"スコアタイプ: {features['scoreType']}")
    print(f"レコード数: {features['numRecords']}")
    
    # 特徴量をスコアの絶対値で降順ソート
    score_field = features['scoreType']
    top_features = sorted(
        features['features'], 
        key=lambda x: abs(x.get(score_field, 0)), 
        reverse=True
    )[:10]  # 上位10件を表示
    
    print("\n上位10件の特徴量:")
    for i, feat in enumerate(top_features, 1):
        print(f"{i}. {feat['item']}: {feat[score_field]:.3f} (平均値: {feat['average']:.3f})")
    
    # DataFrameに変換
    df = client.to_dataframe(features)
    print("\nDataFrame形式:")
    print(df.head())
    
    try:
        # 可視化
        plt.figure(figsize=(12, 6))
        df_plot = df.iloc[:10].copy()  # 上位10件のみを使用
        
        # プロット用にデータを準備
        df_plot.loc[:, 'abs_score'] = df_plot[score_field].abs()
        df_plot = df_plot.sort_values('abs_score', ascending=True)
        
        # バープロット
        bars = plt.barh(df_plot['item'], df_plot[score_field])
        
        # バーの色を設定（正の値は青、負の値は赤）
        for i, bar in enumerate(bars):
            if df_plot.iloc[i][score_field] > 0:
                bar.set_color('steelblue')
            else:
                bar.set_color('firebrick')
        
        plt.xlabel(f'{score_field.upper()}')
        plt.title('追加プロットの上位特徴量')
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"グラフの表示中にエラーが発生しました: {str(e)}")
else:
    print("特徴量分析の取得に失敗しました。エラーメッセージを確認してください。")
