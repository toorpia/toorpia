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
    def fit_transform(self, data, label=None, tag=None, description=None, random_seed=42, weight_option_str=None, type_option_str=None, identna_resolution=None, identna_effective_radius=None):
        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}

        # DataFrameの型に基づいて自動生成（パラメータが指定されていない場合）
        if weight_option_str is None or type_option_str is None:
            auto_weight_option_str, auto_type_option_str = self._generate_type_weight_options(data)
            weight_option_str = weight_option_str or auto_weight_option_str
            type_option_str = type_option_str or auto_type_option_str

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
        data_dict['weight_option_str'] = weight_option_str
        data_dict['type_option_str'] = type_option_str
        
        # identnaパラメータを追加
        identna_params = {}
        if identna_resolution is not None:
            identna_params['resolution'] = identna_resolution
        if identna_effective_radius is not None:
            identna_params['effectiveRadius'] = identna_effective_radius
        if identna_params:
            data_dict['identnaParams'] = identna_params

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
    def addplot(self, data, *args, weight_option_str=None, type_option_str=None, detabn_max_window=None, detabn_rate_threshold=None, detabn_threshold=None, detabn_print_score=None):
        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}

        # DataFrameの型に基づいて自動生成（パラメータが指定されていない場合）
        if weight_option_str is None or type_option_str is None:
            auto_weight_option_str, auto_type_option_str = self._generate_type_weight_options(data)
            weight_option_str = weight_option_str or auto_weight_option_str
            type_option_str = type_option_str or auto_type_option_str

        data_json = data.to_json(orient='split')
        data_dict = json.loads(data_json)
        
        # 重み付けオプションと型オプションを設定
        data_dict['weight_option_str'] = weight_option_str
        data_dict['type_option_str'] = type_option_str
        
        # detabnパラメータを追加
        if detabn_max_window is not None:
            data_dict['detabn_max_window'] = detabn_max_window
        if detabn_rate_threshold is not None:
            data_dict['detabn_rate_threshold'] = detabn_rate_threshold
        if detabn_threshold is not None:
            data_dict['detabn_threshold'] = detabn_threshold
        if detabn_print_score is not None:
            data_dict['detabn_print_score'] = detabn_print_score
        
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
            
            # 座標データをNumPy配列に変換
            np_array = np.array(addXyData)
            
            # 拡張された返り値：座標データと異常度情報を含む辞書を返す
            result = {
                'xyData': np_array,
                'addPlotNo': self.currentAddPlotNo,
                'abnormalityStatus': response_data.get('abnormalityStatus'),  # 'normal', 'abnormal', 'unknown'
                'abnormalityScore': response_data.get('abnormalityScore'),    # 異常度スコア
                'shareUrl': self.shareUrl
            }
            
            return result
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
        """
        APIキーに関連付けられたマップの一覧を取得する
        
        Returns:
            list: マップ情報のリスト。各マップは以下のフィールドを含む辞書です：
                - mapNo: マップの識別番号
                - createdAt: 作成日時
                - nRecord: レコード数
                - nDimension: 次元数
                - label: マップの表示名（オプション）
                - tag: マップの分類タグ（オプション）
                - description: マップの詳細説明（オプション）
                - shareUrl: マップの共有URL
        """
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
        """
        指定されたマップをエクスポート（ダウンロード）し、指定されたディレクトリに保存する
        
        注意: このメソッドはベースマップファイルのみをエクスポートします。
        追加プロットファイル (segments-add-*.csv, xy-add-*.dat, rawdata_add_*.csv) や
        ログファイル (*.log) は除外されます。クラスタリング解析で生成された
        全てのファイルはベースマップの一部として含まれます。
        
        エクスポートされたマップをインポートした後、追加プロットは再作成する必要があります。
        
        Args:
            map_no: エクスポートするマップ番号
            export_dir: エクスポートしたファイルを保存するディレクトリ
            
        Returns:
            エクスポートされたマップデータを含む辞書またはエクスポートに失敗した場合はNone
        """
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
        """
        指定されたディレクトリからマップデータを読み込み、インポート（アップロード）する
        
        注意: このメソッドはベースマップファイルのみをインポートします。
        追加プロットファイル (segments-add-*.csv, xy-add-*.dat, rawdata_add_*.csv) や
        ログファイル (*.log) は除外されます。クラスタリング解析で生成された
        全てのファイルはベースマップの一部として含まれます。
        
        ディレクトリに追加プロットファイルが含まれていても、それらはインポートされず、
        インポート後にaddplotメソッドを使用して再作成する必要があります。
        
        Args:
            input_dir: インポートするマップファイルが含まれているディレクトリ
            
        Returns:
            インポートされた新しいマップ番号、または既存のマップが見つかった場合はその番号
            インポートに失敗した場合はNone
        """
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
        """
        指定されたマップの全追加プロット情報を取得する
        
        Args:
            map_no: 追加プロット情報を取得するマップ番号
            
        Returns:
            list: 追加プロット情報のリスト。各追加プロットは以下のフィールドを含む辞書です：
                - addPlotId: 追加プロットのID
                - mapId: 関連するマップのID
                - addPlotNo: マップ内での追加プロット番号
                - nRecord: レコード数
                - label: 追加プロットのラベル（オプション）
                - status: 追加プロットの正常・異常判定結果
                      "normal"=正常, "abnormal"=異常, null=未評価
                - segmentFile: セグメントファイル名
                - xyFile: XY座標ファイル名
                - rawDataFile: 元データファイル名
                - createdAt: 作成日時
                - updatedAt: 更新日時
                - deletedAt: 削除日時（null=有効）
                - shareUrl: この追加プロットを含むマップの共有URL
        """
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
        """
        特定の追加プロット情報を取得する
        
        Args:
            map_no: 対象のマップ番号
            addplot_no: 取得する追加プロットの番号
            
        Returns:
            dict: 追加プロット情報を含む辞書。以下のキーを含みます：
                - addPlot: 追加プロットのメタデータ（辞書）。以下のフィールドを含みます：
                    * addPlotId: 追加プロットのID
                    * addPlotNo: 追加プロット番号
                    * label: 追加プロットのラベル（オプション）
                    * status: 追加プロットの正常・異常判定結果
                          "normal"=正常, "abnormal"=異常, null=未評価
                    * その他の追加プロットメタデータ
                - xyData: 座標データのNumPy配列（各行は[x, y]座標）
                - shareUrl: 追加プロットの共有URL
        """
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
            
    @pre_authentication
    def get_addplot_features(self, map_no=None, addplot_no=None, use_tscore=False):
        """
        追加プロットの特徴量を分析して取得する
        
        Args:
            map_no (int, optional): マップ番号。指定がない場合は現在のマップ番号を使用
            addplot_no (int, optional): 追加プロット番号。指定がない場合は現在の追加プロット番号を使用
            use_tscore (bool, optional): Tスコアを使用するかどうか（デフォルトはFalse、Zスコアを使用）
        
        Returns:
            dict: 特徴量データの辞書。以下のキーを含む：
                - features: 特徴量の配列。各要素は {'item': 項目名, 'average': 平均値, 'zscore'/'tscore': スコア値}
                - scoreType: 'zscore' または 'tscore'（使用されたスコアタイプ）
                - numRecords: 処理対象のレコード数
                - mapNo: マップ番号
                - addPlotNo: 追加プロット番号
                - timestamp: 分析実行時のタイムスタンプ
                
            分析に失敗した場合はNoneを返す
        """
        # map_noとaddplot_noのチェック
        if map_no is None:
            if self.mapNo is None:
                print("Error: Map number is not specified. Please provide a map_no or use fit_transform() first.")
                return None
            map_no = self.mapNo
        
        if addplot_no is None:
            if self.currentAddPlotNo is None:
                print("Error: Add plot number is not specified. Please provide an addplot_no or use addplot() first.")
                return None
            addplot_no = self.currentAddPlotNo
        
        # リクエストURLとヘッダーの準備
        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}
        
        # クエリパラメータの作成（Tスコア使用フラグ）
        params = {}
        if use_tscore:
            params['tscore'] = 'true'
        
        # APIリクエスト
        try:
            response = requests.get(
                f"{API_URL}/maps/{map_no}/addplots/{addplot_no}/features", 
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                error_message = response.json().get('message', 'Unknown error')
                print(f"Failed to get add plot features. Server responded with error: {error_message}")
                print(f"Response status code: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Network error when requesting add plot features: {str(e)}")
            return None
        except json.JSONDecodeError:
            print(f"Failed to parse server response as JSON. Response content: {response.text}")
            return None
    
    def to_dataframe(self, feature_data):
        """
        特徴量分析結果をPandasのDataFrameに変換する
        
        Args:
            feature_data (dict): get_addplot_features()の返り値
            
        Returns:
            pandas.DataFrame: 特徴量データのDataFrame
            変換に失敗した場合はNone
        """
        try:
            import pandas as pd
            
            if not feature_data or 'features' not in feature_data:
                print("Error: Invalid feature data. Cannot convert to DataFrame.")
                return None
            
            # 特徴量データをDataFrameに変換
            df = pd.DataFrame(feature_data['features'])
            
            # スコア列名を設定
            score_type = feature_data.get('scoreType', 'zscore')
            
            # 列順序を調整
            columns = ['item', 'average', score_type]
            
            return df[columns]
        except ImportError:
            print("Error: pandas is not installed. Please install pandas to use this feature.")
            return None
        except Exception as e:
            print(f"Error converting feature data to DataFrame: {str(e)}")
            return None

    # import_mapの別名としてupload_mapを定義
    upload_map = import_map

    def _read_map_data_from_directory(self, directory):
        """
        指定されたディレクトリからマップデータを読み込む
        
        注意: このメソッドはベースマップファイルのみを読み込みます。
        追加プロットファイル (segments-add-*.csv, xy-add-*.dat, rawdata_add_*.csv) や
        ログファイル (*.log) は除外されます。クラスタリング解析で生成された
        全てのファイルはベースマップの一部として含まれます。
        """
        map_data = {}
        for filename in os.listdir(directory):
            # 追加プロットファイルとログファイルを除外
            if (not filename.startswith('segments-add-') and
                not filename.startswith('xy-add-') and 
                not filename.startswith('rawdata_add_') and
                not filename.endswith('.log')):
                
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                        map_data[filename] = base64.b64encode(file_content).decode('utf-8')
        
        # ディレクトリ内に追加プロットファイルが存在する場合警告を表示
        all_files = os.listdir(directory)
        add_plot_files = [f for f in all_files if 
                           f.startswith('segments-add-') or 
                           f.startswith('xy-add-') or 
                           f.startswith('rawdata_add_')]
        
        if add_plot_files:
            print(f"Warning: {len(add_plot_files)} add plot related files were found but not included in the import/export.")
            print("Add plots must be recreated after importing the map.")
            
        return map_data

    def _generate_type_weight_options(self, df):
        """
        DataFrameの各列のデータ型に基づいて、-w（重み）と-t（型）のオプション文字列を生成する
        
        Args:
            df (pd.DataFrame): 型情報を取得するDataFrame
        
        Returns:
            tuple: (weight_option_str, type_option_str) - 生成された-wと-tのオプション文字列
        """
        import pandas as pd

        weight_options = []
        type_options = []
        
        for i, col_name in enumerate(df.columns):
            col_idx = i + 1  # 列インデックスは1から始まる
            col_type = df[col_name].dtype
            
            # 型に基づいて適切なオプションを決定
            if pd.api.types.is_datetime64_any_dtype(col_type):
                type_options.append(f"{col_idx}:date")    # datetime64型用の設定
                weight_options.append(f"{col_idx}:0")     # datetime64型の重みは0
            
            elif pd.api.types.is_float_dtype(col_type):
                type_options.append(f"{col_idx}:float")   # float型用の設定
                weight_options.append(f"{col_idx}:1")     # float型の重みは1
            
            elif pd.api.types.is_integer_dtype(col_type):
                type_options.append(f"{col_idx}:int")     # int型用の設定
                weight_options.append(f"{col_idx}:1")     # int型の重みは1
            
            elif pd.api.types.is_string_dtype(col_type) or pd.api.types.is_object_dtype(col_type):
                type_options.append(f"{col_idx}:none")    # 文字列型用の設定
                weight_options.append(f"{col_idx}:0")     # 文字列型の重みは0
            
            elif pd.api.types.is_categorical_dtype(col_type):
                type_options.append(f"{col_idx}:enum")    # カテゴリ型用の設定
                weight_options.append(f"{col_idx}:0")     # カテゴリ型の重みは0
            
            elif pd.api.types.is_bool_dtype(col_type):
                type_options.append(f"{col_idx}:enum")    # ブール型用の設定
                weight_options.append(f"{col_idx}:0")     # ブール型の重みは0
            
            else:
                # その他の型は未サポートとして扱う
                type_options.append(f"{col_idx}:none")
                weight_options.append(f"{col_idx}:0")
        
        # コンマ区切りのオプション文字列を生成
        weight_option_str = ",".join(weight_options) if weight_options else ""
        type_option_str = ",".join(type_options) if type_options else ""
        
        return weight_option_str, type_option_str

    def calculate_checksum(self, map_dir):
        """
        マップデータのチェックサムを計算する
        
        注意: このメソッドはベースマップファイルのみを対象とします。
        追加プロットファイル (segments-add-*.csv, xy-add-*.dat, rawdata_add_*.csv) や
        ログファイル (*.log) は除外されます。クラスタリング解析で生成された
        全てのファイルはベースマップの一部として含まれます。
        """
        md5 = hashlib.md5()

        # map_dir以下の全ファイルを取得
        files = glob.glob(os.path.join(map_dir, '**/*'), recursive=True)

        # ファイルパスでソートして順序を一定に保つ
        sorted_files = sorted(files)

        # 追加プロット関連ファイルとログファイルを除外
        for file_path in sorted_files:
            if os.path.isfile(file_path):
                filename = os.path.basename(file_path)
                # 追加プロットファイルとログファイルをスキップ
                if (not filename.startswith('segments-add-') and
                    not filename.startswith('xy-add-') and 
                    not filename.startswith('rawdata_add_') and
                    not filename.endswith('.log')):
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
