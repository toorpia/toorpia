import pytest
from toorpia.client import toorPIA

def test_fit_transform():
    # テスト用のAPIキー（実際には機能しないダミーのキー）
    api_key = "dummy_api_key"
    client = toorPIA(api_key=api_key)

    # 仮のデータを作成（実際のテストでは、適切なデータを用意してください）
    data = {'dummy': [1, 2, 3]}

    # fit_transformメソッドを呼び出す
    result = client.fit_transform(data)

    # 期待される結果に対して実際の結果をテストする
    # この部分は、fit_transformメソッドの実装に応じて適切に書き換えてください
    assert result is not None
