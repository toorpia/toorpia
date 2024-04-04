import requests
import json
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
            session_key = response.json().get('sessionKey')
            #print(f"Authentication successful. Session key: {session_key}")
            return session_key
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
            print("Data transformation failed.")
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
            print("Data transformation failed.")
            return None
