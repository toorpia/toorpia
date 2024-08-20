import pytest
import pandas as pd
import json
import os
from toorpia.client import toorPIA

def test_fit_transform():
    # APIキーを環境変数から取得するか、ダミーの値を使用
    api_key = os.environ.get("TOORPIA_API_KEY", "dummy_api_key")
    toorpia_client = toorPIA(api_key=api_key)

    # テストデータを読み込む
    df = pd.read_csv("./test/rawdata/biopsy.csv")
    df = df.drop(columns=["No", "ID", "Diagnosis"])

    # fit_transformメソッドを呼び出す
    result = toorpia_client.fit_transform(df)

    # 結果の検証
    assert result is not None
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert toorpia_client.mapNo is not None

def test_addplot():
    api_key = os.environ.get("TOORPIA_API_KEY", "dummy_api_key")
    toorpia_client = toorPIA(api_key=api_key)

    # テストデータを読み込む
    df = pd.read_csv("./test/rawdata/biopsy.csv")
    df = df.drop(columns=["No", "ID", "Diagnosis"])

    # まずfit_transformを呼び出してマップを作成
    toorpia_client.fit_transform(df)

    # addplotメソッドを呼び出す
    add_result = toorpia_client.addplot(df)

    # 結果の検証
    assert add_result is not None
    assert isinstance(add_result, pd.DataFrame)
    assert not add_result.empty

def test_list_map():
    api_key = os.environ.get("TOORPIA_API_KEY", "dummy_api_key")
    toorpia_client = toorPIA(api_key=api_key)

    maps = toorpia_client.list_map()

    # 結果の検証
    assert maps is not None
    assert isinstance(maps, list)

def test_export_import_map():
    api_key = os.environ.get("TOORPIA_API_KEY", "dummy_api_key")
    toorpia_client = toorPIA(api_key=api_key)

    # 1. まず、マップを作成する
    df = pd.read_csv("./test/rawdata/biopsy.csv")
    df = df.drop(columns=["No", "ID", "Diagnosis"])
    toorpia_client.fit_transform(df)
    original_map_no = toorpia_client.mapNo

    # 2. 作成したマップをエクスポートする
    export_dir = "./test/exported_map"
    exported_map = toorpia_client.export_map(original_map_no, export_dir)
    assert exported_map is not None, "マップのエクスポートに失敗しました"

    # 3. エクスポートしたマップを再度インポートする
    new_map_no = toorpia_client.import_map(export_dir)
    assert new_map_no is not None, "マップのインポートに失敗しました"
    assert new_map_no != original_map_no, "新しいマップ番号が元のマップ番号と同じです"

    # 4. エクスポートされたマップの内容を確認
    assert os.path.exists(export_dir), "エクスポートディレクトリが存在しません"
    assert len(os.listdir(export_dir)) > 0, "エクスポートディレクトリが空です"

    print("Export/Import test completed successfully")

if __name__ == "__main__":
    test_fit_transform()
    test_addplot()
    test_list_map()
    test_export_import_map()
