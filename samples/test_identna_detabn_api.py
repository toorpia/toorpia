#!/usr/bin/env python3
"""
toorPIA identna・detabn機能テストスクリプト

このスクリプトは、identna（正常領域同定）とdetabn（異常度判定）機能を
テストするためのサンプルです。

使用方法:
    python test_identna_detabn_api.py

機能:
1. ベースマップ作成（identnaパラメータ付き）
2. 追加プロット（detabnパラメータ付き）
3. 異常度判定結果の確認
"""

import pandas as pd
from toorpia import toorPIA
import numpy as np

def main():
    print("=== toorPIA identna・detabn機能テスト ===")
    
    # toorPIAインスタンスを作成
    api = toorPIA()
    
    # テスト用データを読み込み（通常データ）
    try:
        base_data = pd.read_csv('biopsy.csv')
        base_data = base_data.drop(columns=["No", "ID", "Diagnosis"])  # drop the columns that are not needed
        print(f"✓ ベースデータ読み込み完了: {base_data.shape}")
    except FileNotFoundError:
        print("❌ biopsy.csvが見つかりません。samplesディレクトリで実行してください。")
        return
    
    # 追加プロット用データを読み込み（異常データ）
    try:
        add_data = pd.read_csv('biopsy-add.csv')
        add_data = add_data.drop(columns=["No", "ID", "Diagnosis"])  # drop the columns that are not needed
        print(f"✓ 追加データ読み込み完了: {add_data.shape}")
    except FileNotFoundError:
        print("❌ biopsy-add.csvが見つかりません。samplesディレクトリで実行してください。")
        return
    
    print("\n--- Phase 1: identnaパラメータ付きベースマップ作成 ---")
    
    # identnaパラメータを指定してベースマップを作成
    # 解像度を50に、有効半径を0.15に設定
    base_xy = api.fit_transform(
        base_data,
        label="Identna Test Base Map",
        description="Test map with custom identna parameters",
        identna_resolution=50,        # カスタム解像度
        identna_effective_radius=0.15 # カスタム有効半径
    )
    
    if base_xy is not None:
        print(f"✓ ベースマップ作成完了")
        print(f"  - マップ番号: {api.mapNo}")
        print(f"  - 座標データ形状: {base_xy.shape}")
        print(f"  - 座標範囲: X[{base_xy[:, 0].min():.3f}, {base_xy[:, 0].max():.3f}], Y[{base_xy[:, 1].min():.3f}, {base_xy[:, 1].max():.3f}]")
        if api.shareUrl:
            print(f"  - 共有URL: {api.shareUrl}")
    else:
        print("❌ ベースマップ作成に失敗しました")
        return
    
    print("\n--- Phase 2: detabnパラメータ付き追加プロット ---")
    
    # detabnパラメータを指定して追加プロット
    # より厳しい異常判定パラメータを設定
    result = api.addplot(
        add_data,
        detabn_max_window=3,        # ウィンドウサイズを小さく
        detabn_rate_threshold=0.5,  # 異常率閾値を下げる（より敏感に）
        detabn_threshold=0.1,       # 正常度閾値を上げる
        detabn_print_score=True     # スコア付きで出力
    )
    
    if result is not None:
        print(f"✓ 追加プロット完了")
        print(f"  - 追加プロット番号: {result['addPlotNo']}")
        print(f"  - 座標データ形状: {result['xyData'].shape}")
        print(f"  - 異常度判定結果: {result['abnormalityStatus']}")
        print(f"  - 異常度スコア: {result['abnormalityScore']}")
        if result['shareUrl']:
            print(f"  - 共有URL: {result['shareUrl']}")
            
        # 異常度判定結果の詳細表示
        print(f"\n--- 異常度判定詳細 ---")
        status = result['abnormalityStatus']
        score = result['abnormalityScore']
        
        if status == 'normal':
            print("🟢 判定: 正常")
            print(f"   スコア: {score:.4f} (高いほど正常)")
        elif status == 'abnormal':
            print("🔴 判定: 異常")
            print(f"   スコア: {score:.4f} (低いほど異常)")
        else:
            print("⚠️  判定: 不明")
            print(f"   スコア: {score if score else 'N/A'}")
            
    else:
        print("❌ 追加プロットに失敗しました")
        return
    
    print("\n--- Phase 3: デフォルトパラメータとの比較 ---")
    
    # デフォルトパラメータで別の追加プロットを作成
    print("デフォルトパラメータで追加プロット実行中...")
    default_result = api.addplot(add_data)
    
    if default_result is not None:
        print(f"✓ デフォルトパラメータでの追加プロット完了")
        print(f"  - 追加プロット番号: {default_result['addPlotNo']}")
        print(f"  - 異常度判定結果: {default_result['abnormalityStatus']}")
        print(f"  - 異常度スコア: {default_result['abnormalityScore']}")
        
        # パラメータ比較
        print(f"\n--- パラメータ比較結果 ---")
        print(f"カスタムパラメータ: {result['abnormalityStatus']} (スコア: {result['abnormalityScore']:.4f})")
        print(f"デフォルトパラメータ: {default_result['abnormalityStatus']} (スコア: {default_result['abnormalityScore']:.4f})")
        
        if result['abnormalityStatus'] != default_result['abnormalityStatus']:
            print("📊 パラメータの違いにより判定結果が変わりました")
        else:
            print("📊 パラメータの違いにもかかわらず判定結果は同じでした")
    
    print("\n--- Phase 4: 追加プロット履歴確認 ---")
    
    # 作成した追加プロットの一覧を取得
    addplots = api.list_addplots(api.mapNo)
    if addplots:
        print(f"✓ 追加プロット履歴: {len(addplots)}件")
        for i, ap in enumerate(addplots, 1):
            print(f"  {i}. 追加プロット#{ap['addPlotNo']}: {ap['status']} (レコード数: {ap['nRecord']})")
    
    print("\n=== テスト完了 ===")
    print(f"作成されたマップ番号: {api.mapNo}")
    if api.shareUrl:
        print(f"最終共有URL: {api.shareUrl}")

if __name__ == "__main__":
    main()
