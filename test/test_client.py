import pytest
import pandas as pd
import json
from toorpia.client import toorPIA

def test_fit_transform():
    # テスト用のAPIキー（実際には機能しないダミーのキー）
    #api_key = "dummy_api_key"
    #client = toorPIA(api_key=api_key)
    toorpia_client = toorPIA()
    print(toorpia_client.api_key)

    # 仮のデータを作成（実際のテストでは、適切なデータを用意してください）
    df = pd.read_csv("./test/rawdata/biopsy.csv")
    df = df.drop(columns=["No", "ID", "Diagnosis"])

    # fit_transformメソッドを呼び出す
    result = toorpia_client.fit_transform(df)
    print(result)
    print(toorpia_client.mapNo)

    # 期待される結果に対して実際の結果をテストする
    # この部分は、fit_transformメソッドの実装に応じて適切に書き換えてください
    assert result is not None

def test_addplot():
    toorpia_client = toorPIA()

    # 仮のデータを作成（実際のテストでは、適切なデータを用意してください）
    df = pd.read_csv("./test/rawdata/biopsy.csv")
    df = df.drop(columns=["No", "ID", "Diagnosis"])

    # fit_transformメソッドを呼び出す
    result = toorpia_client.fit_transform(df)
    mapNo = toorpia_client.mapNo
    add_result = toorpia_client.addplot(df, mapNo)

    # 期待される結果に対して実際の結果をテストする
    # この部分は、fit_transformメソッドの実装に応じて適切に書き換えてください
    assert add_result is not None

def test_list_map():
    toorpia_client = toorPIA()
    maps = toorpia_client.list_map()
    print(maps)

    assert maps is not None

def test_export_import_map():
    toorpia_client = toorPIA()

    # 1. まず、マップを作成する
    df = pd.read_csv("./test/rawdata/biopsy.csv")
    df = df.drop(columns=["No", "ID", "Diagnosis"])
    result = toorpia_client.fit_transform(df)
    original_map_no = toorpia_client.mapNo

    # 2. 作成したマップをエクスポートする（圧縮なし）
    exported_map = toorpia_client.export_map(original_map_no, compress=False)
    assert exported_map is not None, "マップのエクスポートに失敗しました"

    # 3. エクスポートしたマップを再度インポートする（圧縮なし）
    new_map_no = toorpia_client.import_map(exported_map, compress=False)
    assert new_map_no is not None, "マップのインポートに失敗しました"
    assert new_map_no != original_map_no, "新しいマップ番号が元のマップ番号と同じです"

    # 4. 圧縮ありでエクスポート
    exported_map_compressed = toorpia_client.export_map(original_map_no, compress=True)
    assert exported_map_compressed is not None, "圧縮ありのマップエクスポートに失敗しました"

    # 5. 圧縮ありでインポート
    new_map_no_compressed = toorpia_client.import_map(exported_map_compressed, compress=True)
    assert new_map_no_compressed is not None, "圧縮ありのマップインポートに失敗しました"
    assert new_map_no_compressed != original_map_no, "新しいマップ番号（圧縮）が元のマップ番号と同じです"

    # 6. エクスポートされたマップの内容を確認
    assert isinstance(exported_map, dict), "エクスポートされたマップがdict型ではありません"
    assert "mapNo" in exported_map, "エクスポートされたマップにmapNoキーがありません"
    assert "data" in exported_map, "エクスポートされたマップにdataキーがありません"

    print("Export/Import test completed successfully")

if __name__ == "__main__":
    test_fit_transform()
    test_addplot()
    test_list_map()
    test_export_import_map()
