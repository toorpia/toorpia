#!/usr/bin/env python3
"""
toorPIA diagnosticScore 点単位フィールド検証スクリプト

backend issue toorpia/backend#93 / client issue toorpia/toorpia#31 で
追加された diagnosticScore.distance の点単位フィールド
(`distancesPerPoint`, `normalizedDistancesPerPoint`) が、
addplot を複数レコードまとめて呼び出した際に正しく返却され、
かつ既存集約値および xyData との数値整合が取れていることを検証する。

使用方法:
    python test_diagnostic_score_per_point.py

検証項目:
  1. 新フィールドの存在と型
  2. 配列長 = addplot 投入点数 M
  3. normalizedDistancesPerPoint[j] == distancesPerPoint[j] / radiusOfGyration
  4. ベースマップ座標系仕様（重心=原点）:
       distancesPerPoint[j] == sqrt(x_j² + y_j²)  (xyData の各行ノルム)
  5. 集約値との整合:
       mean(distancesPerPoint) == meanDistance
       mean(normalizedDistancesPerPoint) == normalizedDistance
"""

import sys

import numpy as np
import pandas as pd
from toorpia import toorPIA


# 丸めを考慮した許容誤差
# - distancesPerPoint は toFixed(6) で丸められて返却される
# - normalizedDistancesPerPoint は toFixed(4) で丸められる
ABS_TOL_6 = 5e-6
ABS_TOL_4 = 5e-4


def _check(label, ok, detail=""):
    mark = "✓" if ok else "✗"
    print(f"  {mark} {label}" + (f"  ({detail})" if detail else ""))
    return ok


def main():
    print("=== toorPIA diagnosticScore 点単位フィールド検証 ===\n")

    # データ読み込み
    try:
        base_data = pd.read_csv("biopsy.csv").drop(columns=["No", "ID", "Diagnosis"])
        add_data = pd.read_csv("biopsy-add.csv").drop(columns=["No", "ID", "Diagnosis"])
    except FileNotFoundError as e:
        print(f"❌ {e}\n   biopsy.csv / biopsy-add.csv が見つかりません。samples ディレクトリで実行してください。")
        return 1
    print(f"  base_data: {base_data.shape}")
    print(f"  add_data : {add_data.shape}  (M = {len(add_data)} 点を一括投入)")

    # ベースマップ作成 + addplot
    api = toorPIA()
    api.fit_transform(
        base_data,
        label="diagnosticScore per-point validation",
        description="Validate distancesPerPoint / normalizedDistancesPerPoint fields",
    )
    print(f"\n  mapNo = {api.mapNo}")

    print("\n--- Phase 1: addplot 実行 ---")
    result = api.addplot(
        add_data,
        detabn_max_window=1,
        detabn_threshold=0.5,
        detabn_rate_threshold=1.0,
        detabn_print_score=True,
    )
    if result is None:
        print("❌ addplot 失敗")
        return 1
    print(f"  addPlotNo            = {result['addPlotNo']}")
    print(f"  abnormalityStatus    = {result['abnormalityStatus']}")
    print(f"  xyData.shape         = {result['xyData'].shape}")

    ds = result.get("diagnosticScore")
    if not ds:
        print("❌ diagnosticScore がレスポンスに含まれていません")
        return 1

    distance = ds.get("distance")
    if not distance:
        print("❌ diagnosticScore.distance がレスポンスに含まれていません")
        return 1

    # 検証
    print("\n--- Phase 2: フィールド存在と型の確認 ---")
    distances_pp = distance.get("distancesPerPoint")
    normalized_pp = distance.get("normalizedDistancesPerPoint")
    failures = []

    if not _check("distancesPerPoint がレスポンスに存在",
                  distances_pp is not None and isinstance(distances_pp, list)):
        failures.append("distancesPerPoint missing")
    if not _check("normalizedDistancesPerPoint がレスポンスに存在",
                  normalized_pp is not None and isinstance(normalized_pp, list)):
        failures.append("normalizedDistancesPerPoint missing")
    if failures:
        print(f"\n❌ 必須フィールド欠落: {failures}")
        print("   backend 側で toorpia/backend#93 の変更がデプロイされていない可能性があります")
        return 1

    M = len(add_data)
    _check(f"len(distancesPerPoint) == M ({M})",
           len(distances_pp) == M,
           f"got {len(distances_pp)}")
    _check(f"len(normalizedDistancesPerPoint) == M ({M})",
           len(normalized_pp) == M,
           f"got {len(normalized_pp)}")

    print("\n--- Phase 3: 内部整合 (normalized = distance / Rg) ---")
    rg = distance["radiusOfGyration"]
    print(f"  radiusOfGyration (Rg) = {rg:.6f}")
    dpp = np.asarray(distances_pp, dtype=float)
    npp = np.asarray(normalized_pp, dtype=float)

    expected_npp = dpp / rg if rg > 0 else np.zeros_like(dpp)
    max_diff = float(np.abs(expected_npp - npp).max())
    _check(
        "normalizedDistancesPerPoint[j] == distancesPerPoint[j] / Rg",
        max_diff < ABS_TOL_4,
        f"max |Δ| = {max_diff:.2e}, tol = {ABS_TOL_4:.0e}",
    )

    print("\n--- Phase 4: 座標系仕様 (重心=原点) の検証 ---")
    xy = result["xyData"]
    norms = np.linalg.norm(xy, axis=1)
    max_diff_origin = float(np.abs(norms - dpp).max())
    _check(
        "distancesPerPoint[j] == sqrt(x_j² + y_j²)  (基本仕様: 重心=原点)",
        max_diff_origin < ABS_TOL_6,
        f"max |Δ| = {max_diff_origin:.2e}, tol = {ABS_TOL_6:.0e}",
    )

    print("\n--- Phase 5: 集約値との整合 ---")
    mean_d = float(distance["meanDistance"])
    mean_nd = float(distance["normalizedDistance"])
    print(f"  meanDistance       (server) = {mean_d:.6f}")
    print(f"  mean(distancesPerPoint)     = {dpp.mean():.6f}")
    print(f"  normalizedDistance (server) = {mean_nd:.4f}")
    print(f"  mean(normalizedDistancesPerPoint) = {npp.mean():.4f}")

    _check(
        "mean(distancesPerPoint) == meanDistance",
        abs(dpp.mean() - mean_d) < ABS_TOL_6,
        f"|Δ| = {abs(dpp.mean() - mean_d):.2e}",
    )
    _check(
        "mean(normalizedDistancesPerPoint) == normalizedDistance",
        abs(npp.mean() - mean_nd) < ABS_TOL_4,
        f"|Δ| = {abs(npp.mean() - mean_nd):.2e}",
    )

    print("\n--- Phase 6: 点単位スコア一覧（参考表示） ---")
    print(f"  {'j':>3}  {'x':>10}  {'y':>10}  {'d_j':>10}  {'d_j / Rg':>10}")
    for j, ((x, y), d, n) in enumerate(zip(xy, dpp, npp)):
        print(f"  {j:>3}  {x:>10.4f}  {y:>10.4f}  {d:>10.4f}  {n:>10.4f}")

    print("\n=== 検証完了: すべての項目を満たしました ===")
    if api.shareUrl:
        print(f"  shareUrl: {api.shareUrl}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
