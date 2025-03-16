import requests
import json
import os
import base64
from .config import API_URL
from .utils.authentication import get_api_key
import numpy as np
import hashlib
import glob

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
    shareUrl = None  # シェアURL用の属性を追加
    currentAddPlotNo = None  # 追加：現在の追加プロット番号
    addPlots = None  # 追加：マップに関連する追加プロットのリスト

    def __init__(self, api_key=None):
        self.api_key = api_key if api_key else get_api_key()
        self.session_key = None 

    def authenticate(self):
        """バックエンドにAPIキーを送信して検証させ、セッションキーを取得する"""
        response = requests.post(f"{API_URL}/auth/login", json={"apiKey": self.api_key})
        if response.status_code == 200:
            return response.json().get('sessionKey')
        else:
            print(f"Authentication failed. Status code: {response.status_code}")
            print(f"Response content: {response.text}")
            return None

    @pre_authentication
    def fit_transform(self, data, label=None, tag=None, description=None, random_seed=42):
        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}

        # DataFrame形式で与えられたdataをJSON形式に変換して、バックエンドに送信する
        data_json = data.to_json(orient='split')  # split形式でJSON文字列に変換
        data_dict = json.loads(data_json)  # JSON文字列を辞書型に変換

        # オプションパラメータを追加
        if label is not None:
            data_dict['label'] = label
        if tag is not None:
            data_dict['tag'] = tag
        if description is not None:
            data_dict['description'] = description
        if random_seed != 42:
            data_dict['randomSeed'] = random_seed

        response = requests.post(f"{API_URL}/data/fit_transform", json=data_dict, headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            baseXyData = response_data['resdata']['baseXyData']
            self.mapNo = response_data['resdata']['mapNo']
            self.shareUrl = response_data.get('shareUrl')  # シェアURLを保存

            np_array = np.array(baseXyData)  # baseXyDataをNumPy配列に変換
            return np_array  # 変換したNumPy配列を返す
        else:
            error_message = response.json().get('message', 'Unknown error')  # エラーメッセージの取得
            print(f"Data transformation failed. Server responded with error: {error_message}")
            return None

    @pre_authentication
    def addplot(self, data, *args):
        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}

        data_json = data.to_json(orient='split')
        data_dict = json.loads(data_json)
        
        mapNo = None
        mapDataDir = None

        for arg in args:
            if isinstance(arg, int):
                mapNo = arg
            elif isinstance(arg, str):
                mapDataDir = arg

        if mapDataDir is not None:
            map_no = self.import_map(mapDataDir)
            if map_no is not None:
                data_dict['mapNo'] = map_no
            else:
                print("Error: Failed to import map from directory.")
                return None
        elif mapNo is not None:
            data_dict['mapNo'] = mapNo
        elif self.mapNo is not None:
            data_dict['mapNo'] = self.mapNo
        else:
            print("Error: Both mapNo and mapDataDir are undefined.")
            return None

        response = requests.post(f"{API_URL}/data/addplot", json=data_dict, headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            addXyData = response_data['resdata']
            self.currentAddPlotNo = response_data.get('addPlotNo')  # 追加プロット番号を保存
            self.shareUrl = response_data.get('shareUrl')  # シェアURLを保存
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
            maps = response.json()
            # 各マップにシェアURLが含まれている場合はそのまま返す
            return maps
        else:
            error_message = response.json().get('message', 'Unknown error')  # エラーメッセージの取得
            print(f"Failed to list maps. Server responded with error: {error_message}")
            return None

    @pre_authentication
    def export_map(self, map_no, export_dir):
        """指定されたマップをエクスポート（ダウンロード）し、指定されたディレクトリに保存する"""
        headers = {'session-key': self.session_key}
        
        response = requests.get(f"{API_URL}/maps/export/{map_no}", headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            map_data = response_data.get('mapData', {})
            self.shareUrl = response_data.get('shareUrl')  # シェアURLを保存
            
            # 出力ディレクトリが存在しない場合は作成
            os.makedirs(export_dir, exist_ok=True)
            
            # map_dataに含まれる全てのファイルを展開して保存
            for filename, file_content_b64 in map_data.items():
                try:
                    file_content = base64.b64decode(file_content_b64).decode('utf-8')
                    file_path = os.path.join(export_dir, filename)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_content)
                        f.flush()  # バッファをフラッシュ
                        os.fsync(f.fileno())  # ファイルシステムに確実に書き込む
                except Exception as e:
                    print(f"Error saving file {filename}: {str(e)}")
            
            print(f"Map exported and saved to {export_dir}")
            return map_data
        else:
            error_message = response.json().get('message', 'Unknown error')
            print(f"Failed to export map. Server responded with error: {error_message}")
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.text}")
            return None

    # export_mapの別名としてdownload_mapを定義
    download_map = export_map

    @pre_authentication
    def import_map(self, input_dir):
        """指定されたディレクトリからマップデータを読み込み、インポート（アップロード）する"""
        # チェックサムの計算
        checksum = self.calculate_checksum(input_dir)
        
        # サーバーとチェックサムを比較
        existing_map_no = self.compare_checksum(checksum)
        if existing_map_no is not None:
            print(f"A matching map was found. No new upload is necessary. Map No: {existing_map_no}")
            return existing_map_no

        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}
        
        map_data = self._read_map_data_from_directory(input_dir)
        
        data_to_send = {
            'mapData': map_data
        }
        
        response = requests.post(f"{API_URL}/maps/import", headers=headers, json=data_to_send)
        
        if response.status_code == 201:
            response_data = response.json()
            self.shareUrl = response_data.get('shareUrl')  # シェアURLを保存
            print(f"Map imported successfully. New map number: {response_data['mapNo']}")
            return response_data['mapNo']
        else:
            error_message = response.json().get('message', 'Unknown error')
            print(f"Failed to import map. Server responded with error: {error_message}")
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.text}")
            return None

    @pre_authentication
    def list_addplots(self, map_no):
        """指定されたマップの全追加プロット情報を取得する"""
        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}
        response = requests.get(f"{API_URL}/maps/{map_no}/addplots", headers=headers)
        if response.status_code == 200:
            self.addPlots = response.json()
            return self.addPlots
        else:
            error_message = response.json().get('message', 'Unknown error')
            print(f"Failed to list add plots. Server responded with error: {error_message}")
            return None

    @pre_authentication
    def get_addplot(self, map_no, addplot_no):
        """特定の追加プロット情報を取得する"""
        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}
        response = requests.get(f"{API_URL}/maps/{map_no}/addplots/{addplot_no}", headers=headers)
        if response.status_code == 200:
            result = response.json()
            self.shareUrl = result.get('shareUrl')
            # NumPy配列に変換して返す
            np_array = np.array(result.get('xyData', []))
            return {
                'addPlot': result.get('addPlot'),
                'xyData': np_array,
                'shareUrl': self.shareUrl
            }
        else:
            error_message = response.json().get('message', 'Unknown error')
            print(f"Failed to get add plot. Server responded with error: {error_message}")
            return None

    # import_mapの別名としてupload_mapを定義
    upload_map = import_map

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

    def calculate_checksum(self, map_dir):
        """マップデータのチェックサムを計算する"""
        md5 = hashlib.md5()

        # map_dir以下の全ファイルを取得
        files = glob.glob(os.path.join(map_dir, '**/*'), recursive=True)

        # ファイルパスでソートして順序を一定に保つ
        sorted_files = sorted(files)

        for file_path in sorted_files:
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    md5.update(file_content)

        return md5.hexdigest()

    @pre_authentication
    def compare_checksum(self, checksum):
        """サーバーとチェックサムを比較する"""
        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}
        data = {'checksum': checksum}

        response = requests.post(f"{API_URL}/maps/compare-checksum", headers=headers, json=data)
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result['mapNo'] is not None:
                    self.shareUrl = result.get('shareUrl')  # シェアURLを保存
                    return result['mapNo']
                else:
                    return None
            except json.JSONDecodeError:
                print(f"Failed to parse server response as JSON. Response content: {response.text}")
                return None
        else:
            print(f"Checksum comparison failed. Status code: {response.status_code}")
            print(f"Response content: {response.text}")
            return None
