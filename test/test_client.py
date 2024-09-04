import pytest
import pandas as pd
import json
import os
import subprocess
import random
import string
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

def test_list_map():
    api_key = os.environ.get("TOORPIA_API_KEY", "dummy_api_key")
    toorpia_client = toorPIA(api_key=api_key)

    maps = toorpia_client.list_map()

    # 結果の検証
    assert maps is not None
    assert isinstance(maps, list)

def test_export_map():
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

    # 3. エクスポートされたファイルの確認
    expected_files = ['rawdata.csv', 'segments.csv', 'segments.csv.log', 'xy.dat', 'xy.dat.log']
    for file in expected_files:
        file_path = os.path.join(export_dir, file)
        assert os.path.exists(file_path), f"{file}が存在しません"
        if not file.endswith('.log'):
            assert os.path.getsize(file_path) > 0, f"{file}が空です"

def test_import_map(capsys):
    api_key = os.environ.get("TOORPIA_API_KEY", "dummy_api_key")
    toorpia_client = toorPIA(api_key=api_key)

    # 1. まず、マップを作成し、エクスポートする
    df = pd.read_csv("./test/rawdata/biopsy.csv")
    df = df.drop(columns=["No", "ID", "Diagnosis"])
    toorpia_client.fit_transform(df)
    original_map_no = toorpia_client.mapNo

    export_dir = "./test/exported_map"
    toorpia_client.export_map(original_map_no, export_dir)

    # 2. エクスポートしたマップを再度インポートする（既存のマップのケース）
    existing_map_no = toorpia_client.import_map(export_dir)
    assert existing_map_no is not None, "マップのインポートに失敗しました"
    assert existing_map_no == original_map_no, "既存のマップ番号が返されませんでした"

    # キャプチャされた出力を取得
    captured = capsys.readouterr()
    
    # 出力に期待する情報が含まれているか確認
    assert f"A matching map was found. No new upload is necessary. Map No: {existing_map_no}" in captured.out

    # 3. エクスポートされたディレクトリにランダムなダミーデータを追加
    dummy_file_path = os.path.join(export_dir, "dummy_data.txt")
    with open(dummy_file_path, 'w') as f:
        random_data = ''.join(random.choices(string.ascii_letters + string.digits, k=100))
        f.write(random_data)

    # 4. 修正したデータを再度インポート（新しいマップのケース）
    new_map_no = toorpia_client.import_map(export_dir)
    assert new_map_no is not None, "マップのインポートに失敗しました"
    assert new_map_no != original_map_no, "新しいマップ番号が元のマップ番号と同じです"

    # キャプチャされた出力を取得
    captured = capsys.readouterr()
    
    # 出力に期待する情報が含まれているか確認
    assert f"Map imported successfully. New map number: {new_map_no}" in captured.out

    print("Import test completed successfully")

def test_calculate_checksum():
    api_key = os.environ.get("TOORPIA_API_KEY", "dummy_api_key")
    toorpia_client = toorPIA(api_key=api_key)

    # テスト用のマップディレクトリを作成
    test_map_dir = "./test/test_map_dir"
    os.makedirs(test_map_dir, exist_ok=True)

    # テスト用のファイルを作成
    test_files = {
        "file1.txt": "Content of file 1",
        "file2.txt": "Content of file 2",
        "subdir/file3.txt": "Content of file 3 in subdirectory"
    }

    for file_path, content in test_files.items():
        full_path = os.path.join(test_map_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)

    # toorPIAのcalculate_checksumメソッドを使用してチェックサムを計算
    checksum_toorpia = toorpia_client.calculate_checksum(test_map_dir)

    # 指定されたコマンドを使用してチェックサムを計算
    command = f"find {test_map_dir} -type f | sort | xargs cat | md5sum"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    checksum_command = result.stdout.split()[0]

    # 結果を比較
    assert checksum_toorpia == checksum_command, f"チェックサムが一致しません。toorPIA: {checksum_toorpia}, コマンド: {checksum_command}"

    print("Calculate checksum test completed successfully")

def test_compare_checksum(capsys):
    api_key = os.environ.get("TOORPIA_API_KEY", "dummy_api_key")
    toorpia_client = toorPIA(api_key=api_key)

    # 1. マップを作成してエクスポート
    df = pd.read_csv("./test/rawdata/biopsy.csv")
    df = df.drop(columns=["No", "ID", "Diagnosis"])
    toorpia_client.fit_transform(df)
    original_map_no = toorpia_client.mapNo

    # 2. 作成したマップをエクスポートする
    export_dir = "./test/exported_map"
    exported_map = toorpia_client.export_map(original_map_no, export_dir)

    # 3. エクスポートされたマップデータのチェックサムを計算
    checksum = toorpia_client.calculate_checksum(export_dir)

    # 4. サーバーとチェックサムを比較
    result = toorpia_client.compare_checksum(checksum)

    # キャプチャされた出力を取得
    captured = capsys.readouterr()

    # 5. 結果の検証
    if result is None:
        print(f"チェックサムの比較に失敗しました。出力: {captured.out}")
        assert False, "チェックサムの比較に失敗しました"
    else:
        assert result == original_map_no, f"一致するマップが見つかりませんでした。結果: {result}, 期待値: {original_map_no}"

    print("Compare checksum test completed successfully")

if __name__ == "__main__":
    test_fit_transform()
    test_addplot()
    test_list_map()
    test_export_map()
    test_import_map()
    test_calculate_checksum()
    test_compare_checksum()
