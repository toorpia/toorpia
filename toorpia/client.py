import requests
import json
import gzip
import io
from .config import API_URL
from .utils.authentication import get_api_key
import numpy as np

# デコレータを定義
def pre_authentication(method):
    def wrapper(self, *args, **kwargs):
        if not self.session_key:
            self.session_key = self.authenticate()
            if not self.session_key:
                print("Error: Authentication failed. Cannot proceed.")
                return None
        return method(self, *args, **kwargs)
    return wrapper

class toorPIA:
    # 属性
    mapNo = None

    def __init__(self, api_key=None):
        self.api_key = api_key if api_key else get_api_key()
        self.session_key = None 

    def authenticate(self):
        """バックエンドにAPIキーを送信して検証させ、セッションキーを取得する"""
        response = requests.post(f"{API_URL}/auth/login", json={"apiKey": self.api_key})
        if response.status_code == 200:
            return response.json().get('sessionKey')
        else:
            print("Authentication failed.")
            return None

    @pre_authentication
    def fit_transform(self, data):
        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}

        # DataFrame形式で与えられたdataをJSON形式に変換して、バックエンドに送信する
        data_json = data.to_json(orient='split')  # split形式でJSON文字列に変換
        data_dict = json.loads(data_json)  # JSON文字列を辞書型に変換

        response = requests.post(f"{API_URL}/data/fit_transform", json=data_dict, headers=headers)
        if response.status_code == 200:
            baseXyData = response.json()['resdata']['baseXyData']
            self.mapNo = response.json()['resdata']['mapNo']

            np_array = np.array(baseXyData)  # baseXyDataをNumPy配列に変換
            return np_array  # 変換したNumPy配列を返す
        else:
            error_message = response.json().get('message', 'Unknown error')  # エラーメッセージの取得
            print(f"Data transformation failed. Server responded with error: {error_message}")
            return None

    @pre_authentication
    def addplot(self, data, mapNo=None):
        if mapNo is None:
            mapNo = self.mapNo
        if mapNo is None:
            print("Error: mapNo of basemap is undefined.")
            return None

        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}

        data_json = data.to_json(orient='split')
        data_dict = json.loads(data_json)
        data_dict['mapNo'] = mapNo  # mapNoをリクエストボディに追加

        response = requests.post(f"{API_URL}/data/addplot", json=data_dict, headers=headers)
        if response.status_code == 200:
            addXyData = response.json()['resdata']

            np_array = np.array(addXyData) 
            return np_array 
        else:
            error_message = response.json().get('message', 'Unknown error')  # エラーメッセージの取得
            print(f"Data transformation failed. Server responded with error: {error_message}")
            return None

    @pre_authentication
    def list_map(self):
        """APIキーに関連付けられたマップの一覧を取得する"""
        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}
        response = requests.get(f"{API_URL}/maps", headers=headers)
        if response.status_code == 200:
            return response.json()  # マップの一覧を返す
        else:
            error_message = response.json().get('message', 'Unknown error')  # エラーメッセージの取得
            print(f"Failed to list maps. Server responded with error: {error_message}")
            return None

    @pre_authentication
    def export_map(self, map_no, compress=False, chunk_size=8192):
        """指定されたマップをエクスポート（ダウンロード）する"""
        headers = {'session-key': self.session_key}
        params = {'compress': 'true' if compress else 'false'}
        
        with requests.get(f"{API_URL}/maps/export/{map_no}", headers=headers, params=params, stream=True) as response:
            if response.status_code == 200:
                content = b''
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        content += chunk
                
                if compress:
                    content = gzip.decompress(content)
                
                return json.loads(content.decode('utf-8'))
            else:
                error_message = response.json().get('message', 'Unknown error')
                print(f"Failed to export map. Server responded with error: {error_message}")
                return None

    @pre_authentication
    def import_map(self, map_data, compress=False):
        """マップをインポート（アップロード）する"""
        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}
        params = {'compress': 'true' if compress else 'false'}
        
        if compress:
            map_data = gzip.compress(json.dumps(map_data).encode('utf-8'))
        else:
            map_data = json.dumps(map_data).encode('utf-8')
        
        response = requests.post(f"{API_URL}/maps/import", headers=headers, params=params, data=map_data)
        
        if response.status_code == 201:
            result = response.json()
            print(f"Map imported successfully. New map number: {result['mapNo']}")
            return result['mapNo']
        else:
            error_message = response.json().get('message', 'Unknown error')
            print(f"Failed to import map. Server responded with error: {error_message}")
            return None
