import requests
import json
import os
import base64
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
    def addplot(self, data, mapNo=None, mapDataDir=None):
        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}

        data_json = data.to_json(orient='split')
        data_dict = json.loads(data_json)
        
        # mapDataDirが指定されている場合、ディレクトリからマップデータを読み込む
        if mapDataDir is not None:
            map_data = self._read_map_data_from_directory(mapDataDir)
            data_dict['mapData'] = map_data
        elif mapNo is not None:
            data_dict['mapNo'] = mapNo
        elif self.mapNo is not None:
            data_dict['mapNo'] = self.mapNo
        else:
            print("Error: Both mapNo and mapDataDir are undefined.")
            return None

        response = requests.post(f"{API_URL}/data/addplot", json=data_dict, headers=headers)
        if response.status_code == 200:
            addXyData = response.json()['resdata']
            np_array = np.array(addXyData) 
            return np_array 
        elif response.status_code == 400:
            print("Error: Bad request. Both mapNo and mapData are missing.")
            return None
        elif response.status_code == 401:
            print("Error: Unauthorized. Invalid session key or map number.")
            return None
        else:
            error_message = response.json().get('message', 'Unknown error')
            print(f"Data addition failed. Server responded with error: {error_message}")
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
    def export_map(self, map_no, output_dir):
        """指定されたマップをエクスポート（ダウンロード）し、指定されたディレクトリに保存する"""
        headers = {'session-key': self.session_key}
        
        response = requests.get(f"{API_URL}/maps/export/{map_no}", headers=headers)
        if response.status_code == 200:
            map_data = response.json()
            
            # 出力ディレクトリが存在しない場合は作成
            os.makedirs(output_dir, exist_ok=True)
            
            # マップデータを複数のファイルとして保存
            for filename, file_content in map_data.items():
                file_path = os.path.join(output_dir, filename)
                with open(file_path, 'w') as f:
                    if isinstance(file_content, str):
                        f.write(file_content)
                    else:
                        json.dump(file_content, f, indent=2)
            
            print(f"Map exported and saved to {output_dir}")
            return map_data
        else:
            error_message = response.json().get('message', 'Unknown error')
            print(f"Failed to export map. Server responded with error: {error_message}")
            return None

    @pre_authentication
    def import_map(self, input_dir):
        """指定されたディレクトリからマップデータを読み込み、インポート（アップロード）する"""
        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}
        
        map_data = self._read_map_data_from_directory(input_dir)
        
        response = requests.post(f"{API_URL}/maps/import", headers=headers, json=map_data)
        
        if response.status_code == 201:
            result = response.json()
            print(f"Map imported successfully. New map number: {result['mapNo']}")
            return result['mapNo']
        else:
            error_message = response.json().get('message', 'Unknown error')
            print(f"Failed to import map. Server responded with error: {error_message}")
            return None

    def _read_map_data_from_directory(self, directory):
        """指定されたディレクトリからマップデータを読み込む"""
        map_data = {}
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    map_data[filename] = base64.b64encode(file_content).decode('utf-8')
        return map_data
