import pytest
import pandas as pd
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
