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
  4. ベースマップ座標系仕様（重心 ≈ 原点）:
       |sqrt(x_j² + y_j²) − distancesPerPoint[j]| / Rg が十分小さい
       (=ベース重心が原点近傍にあることの間接確認)
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

# ベース重心が原点近傍にあることの相対許容（|G| / Rg の許容上限）
# toorPIA エンジンは構築時に基本的に重心が原点に位置するよう規格化されるが、
# 数値計算上の小さな残差 (実測例: ~5e-4 × Rg) を伴うため、絶対零ではなく
# 相対許容で「原点近傍」性を検証する。
CENTROID_REL_TOL = 1e-2


# 検証結果を集約するためのリスト（全フェーズ共通）
_failed = []


def _check(label, ok, detail=""):
    mark = "✓" if ok else "✗"
    print(f"  {mark} {label}" + (f"  ({detail})" if detail else ""))
    if not ok:
        _failed.append(label)
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

    print("\n--- Phase 4: 座標系仕様 (重心 ≈ 原点) の検証 ---")
    xy = result["xyData"]
    norms_from_origin = np.linalg.norm(xy, axis=1)
    max_diff_origin = float(np.abs(norms_from_origin - dpp).max())
    rel_offset = max_diff_origin / rg if rg > 0 else float("inf")
    print(f"  max |sqrt(x²+y²) − d_j|  = {max_diff_origin:.2e}")
    print(f"  / radiusOfGyration       = {rel_offset:.2e}  (= ベース重心の原点からの実効距離 ÷ Rg の上限)")
    _check(
        f"重心が原点近傍にある (相対残差 < {CENTROID_REL_TOL:.0e} × Rg)",
        rel_offset < CENTROID_REL_TOL,
        f"observed = {rel_offset:.2e}",
    )
    print(
        "  (注) toorPIA コアバイナリ内部 (倍精度) では重心を厳密に原点に揃えていますが、\n"
        "       座標出力 (xy.dat) は下4桁程度の精度で書き出されるため、xy.dat ベースで\n"
        "       観測される残差は典型的に 1e-3 × Rg 程度となります。addplot もこの xy.dat\n"
        "       を入力として点単位距離を評価するため、server から返る distancesPerPoint\n"
        "       はこの座標系における厳密値です（xyData との近似一致はその副産物）。"
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

    if _failed:
        print(f"\n❌ 検証失敗: {len(_failed)} 件")
        for label in _failed:
            print(f"   - {label}")
        if api.shareUrl:
            print(f"  shareUrl: {api.shareUrl}")
        return 1

    print("\n=== 検証完了: すべての項目を満たしました ===")
    if api.shareUrl:
        print(f"  shareUrl: {api.shareUrl}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
