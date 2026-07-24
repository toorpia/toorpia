import requests
import json
import os
import base64
import functools
from .config import API_URL
from .job import Job
from .utils.authentication import get_api_key
import numpy as np
import hashlib
import glob

# デコレータを定義
def pre_authentication(method):
    @functools.wraps(method)
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

    @staticmethod
    def _async_params(async_mode):
        """async_mode=True のとき非同期ジョブモード指定のクエリパラメータを返す"""
        return {'async': 'true'} if async_mode else None

    def _handle_job_submission(self, response, parser):
        """?async=true 投入レスポンスを処理し、Job ハンドルを返す

        認証エラー(401)・アクティブジョブ数超過(429)・アップロードサイズ超過(413/415)
        などは投入時に同期で返るため、ここでエラー表示して None を返す。
        非同期モード未対応の旧サーバーは ?async=true を無視して同期実行の 200 を
        返すため、その場合は同期実行時と同じ返り値をそのまま返す。
        """
        if response.status_code == 202:
            body = response.json()
            return Job(self, body['jobId'], parser)
        if response.status_code == 200:
            print("Note: server does not support asynchronous job mode; the request was executed synchronously.")
            return parser(response)
        try:
            error_message = response.json().get('message', 'Unknown error')
        except:
            error_message = f"HTTP {response.status_code}: {response.text}"
        print(f"Job submission failed. Server responded with error: {error_message}")
        return None

    @pre_authentication
    def get_job(self, job_id):
        """非同期ジョブ (async_mode=True) の現在の状態を取得する

        Args:
            job_id (str): ジョブ投入時に返された jobId

        Returns:
            dict: ジョブ情報 (jobId, type, status, createdAt, startedAt, finishedAt,
                  expiresAt。status が done のとき httpStatus と result、failed のとき
                  httpStatus と error を含む。result / error は同期実行時のレスポンス
                  ボディと同形)。取得に失敗した場合は None。
                  結果は完了後24時間（サーバー設定による）保持され、期限後は404となる
        """
        headers = {'Content-Type': 'application/json', 'session-key': self.session_key}
        try:
            response = requests.get(f"{API_URL}/jobs/{job_id}", headers=headers)
            if response.status_code == 401:
                # 長時間ジョブのポーリング中にセッションが切れることがあるため一度だけ再認証する
                self.session_key = self.authenticate()
                if self.session_key:
                    headers['session-key'] = self.session_key
                    response = requests.get(f"{API_URL}/jobs/{job_id}", headers=headers)
        except requests.exceptions.RequestException as e:
            print(f"Network error while polling job {job_id}: {str(e)}")
            return None
        if response.status_code == 200:
            return response.json()
        try:
            error_message = response.json().get('message', 'Unknown error')
        except:
            error_message = f"HTTP {response.status_code}"
        print(f"Failed to get job {job_id}. Server responded with error: {error_message}")
        return None

    @pre_authentication
    def fit_transform(self, data, label=None, tag=None, description=None, random_seed=42, weight_option_str=None, type_option_str=None, identna_resolution=None, identna_effective_radius=None, identna_er_method=None, identna_knn_k=None, vector_normalization=None, async_mode=False):
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
        if identna_resolution is not None:
            data_dict['identna_resolution'] = identna_resolution
        if identna_effective_radius is not None:
            data_dict['identna_effective_radius'] = identna_effective_radius
        if identna_er_method is not None:
            data_dict['identna_er_method'] = identna_er_method
        if identna_knn_k is not None:
            data_dict['identna_knn_k'] = int(identna_knn_k)

        # vector_normalization: 明示指定された場合のみ送信（サーバー側デフォルトはtrue）
        if vector_normalization is not None:
            data_dict['vector_normalization'] = bool(vector_normalization)

        response = requests.post(f"{API_URL}/data/fit_transform", json=data_dict, headers=headers,
                                 params=self._async_params(async_mode))
        if async_mode:
            return self._handle_job_submission(response, self._handle_fit_transform_response)
        return self._handle_fit_transform_response(response)

    def _handle_fit_transform_response(self, response):
        """fit_transform のレスポンス処理（同期・非同期ジョブ結果の共通処理）"""
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
    def fit_transform_waveform(self, files,
                              # mkfftSeg parameters
                              mkfftseg_di=1, mkfftseg_hp=-1.0, mkfftseg_lp=-1.0,
                              mkfftseg_nm=0, mkfftseg_ol=50.0, mkfftseg_sr=48000,
                              mkfftseg_wf="hanning", mkfftseg_wl=65536,
                              # identna parameters (same as existing)
                              identna_resolution=None, identna_effective_radius=None,
                              identna_er_method=None, identna_knn_k=None,
                              # toorpia binary option
                              vector_normalization=None,
                              # metadata
                              label=None, tag=None, description=None):
        """
        DEPRECATED: Process WAV or CSV files directly to generate base map

        This method is deprecated. Use basemap_waveform() instead for a unified API
        that returns structured metadata along with coordinate data.

        Args:
            files (list): List of WAV/CSV file paths
            mkfftseg_di (int): Data Index (starting from 1, for CSV files)
            mkfftseg_hp (float): High pass filter (-1 to disable)
            mkfftseg_lp (float): Low pass filter (-1 to disable)
            mkfftseg_nm (int): nMovingAverage (0 for auto-setting)
            mkfftseg_ol (float): Overlap ratio (%)
            mkfftseg_sr (int): Sample rate (for CSV files)
            mkfftseg_wf (str): Window function ("hanning" or "hamming")
            mkfftseg_wl (int): Window length
            identna_resolution (int): Mesh resolution (default: 100)
            identna_effective_radius (float or "auto"): Effective radius. "auto" for automatic determination (default: 0.1)
            identna_er_method (str): Bandwidth method when effective_radius="auto": "silverman" (default) or "knn"
            identna_knn_k (int): k for knn method (0 = auto ceil(sqrt(n)))
            vector_normalization (bool, optional): Enable/disable L2 vector normalization in the toorpia binary. Default server-side is True. Pass False to disable (adds the `-u` flag). The chosen value is persisted on the basemap and inherited by subsequent addplot calls.
            label (str): Map label
            tag (str): Map tag
            description (str): Map description

        Returns:
            numpy.ndarray: Coordinate data (each row is [x, y])
        """
        import warnings
        warnings.warn(
            "fit_transform_waveform is deprecated. Use basemap_waveform() instead for unified API.",
            DeprecationWarning,
            stacklevel=2
        )
        # File existence and format check
        if not files or not isinstance(files, list):
            print("Error: files must be a non-empty list of file paths")
            return None
        
        files_to_upload = []
        for file_path in files:
            if not os.path.exists(file_path):
                print(f"Error: File not found: {file_path}")
                return None
            
            # File format check (.wav, .csv)
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ['.wav', '.csv']:
                print(f"Error: Unsupported file format: {ext}. Only .wav and .csv files are supported.")
                return None
            
            files_to_upload.append(('files', open(file_path, 'rb')))
        
        try:
            # Prepare mkfftSeg options in JSON format
            mkfftseg_options = {
                'di': int(mkfftseg_di),
                'hp': float(mkfftseg_hp),
                'lp': float(mkfftseg_lp),
                'nm': int(mkfftseg_nm),
                'ol': float(mkfftseg_ol),
                'sr': int(mkfftseg_sr),
                'wf': str(mkfftseg_wf),
                'wl': int(mkfftseg_wl)
            }
            
            # Prepare identna parameters
            identna_params = {}
            if identna_resolution is not None:
                identna_params['resolution'] = int(identna_resolution)
            if identna_effective_radius is not None:
                identna_params['effectiveRadius'] = identna_effective_radius if identna_effective_radius == 'auto' else float(identna_effective_radius)
            if identna_er_method is not None:
                identna_params['erMethod'] = identna_er_method
            if identna_knn_k is not None:
                identna_params['knnK'] = int(identna_knn_k)
            if identna_er_method is not None:
                identna_params['erMethod'] = identna_er_method
            if identna_knn_k is not None:
                identna_params['knnK'] = int(identna_knn_k)

            # Send as form-data
            form_data = {
                'mkfftseg_options': json.dumps(mkfftseg_options),
                'identna_options': json.dumps(identna_params) if identna_params else '{}',
                'label': label or '',
                'tag': tag or '',
                'description': description or ''
            }

            # vector_normalization: multipart は文字列で送信
            if vector_normalization is not None:
                form_data['vector_normalization'] = 'true' if bool(vector_normalization) else 'false'

            headers = {'session-key': self.session_key}  # Content-Type is auto-set by requests
            response = requests.post(
                f"{API_URL}/data/fit_transform_waveform",
                files=files_to_upload,
                data=form_data,
                headers=headers
            )
            
            if response.status_code == 200:
                response_data = response.json()
                baseXyData = response_data['resdata']['baseXyData']
                self.mapNo = response_data['resdata']['mapNo']
                self.shareUrl = response_data.get('shareUrl')  # Save share URL
                
                np_array = np.array(baseXyData)  # Convert baseXyData to NumPy array
                return np_array  # Return converted NumPy array
            else:
                try:
                    error_message = response.json().get('message', 'Unknown error')
                except:
                    error_message = f"HTTP {response.status_code}: {response.text}"
                print(f"Waveform data transformation failed. Server responded with error: {error_message}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network error during file upload: {str(e)}")
            return None
        except Exception as e:
            print(f"Error processing waveform files: {str(e)}")
            return None
        finally:
            # Ensure file handles are closed
            for _, file_handle in files_to_upload:
                try:
                    file_handle.close()
                except:
                    pass

    @pre_authentication
    def fit_transform_csvform(self, files, weight_option_str=None, type_option_str=None,
                            drop_columns=None, label=None, tag=None, description=None,
                            random_seed=42, identna_resolution=None, identna_effective_radius=None,
                            identna_er_method=None, identna_knn_k=None,
                            vector_normalization=None):
        """
        DEPRECATED: Process CSV files directly to generate base map using form data upload

        This method is deprecated. Use basemap_csvform() instead for a unified API
        that returns structured metadata along with coordinate data.

        Args:
            files (str or list): CSV file path or list of CSV file paths (required)
            weight_option_str (str, optional): Weight options for columns (e.g., "1:1,2:0,3:1")
            type_option_str (str, optional): Type options for columns (e.g., "1:float,2:none,3:int")
            drop_columns (list, optional): List of column names to drop/exclude
            label (str, optional): Map label
            tag (str, optional): Map tag
            description (str, optional): Map description
            random_seed (int, optional): Random seed for reproducibility (default: 42)
            identna_resolution (int, optional): Mesh resolution (default: 100)
            identna_effective_radius (float or "auto", optional): Effective radius. "auto" for automatic determination (default: 0.1)
            identna_er_method (str, optional): Bandwidth method when effective_radius="auto": "silverman" (default) or "knn"
            identna_knn_k (int, optional): k for knn method (0 = auto ceil(sqrt(n)))
            vector_normalization (bool, optional): Enable/disable L2 vector normalization in the toorpia binary. Default server-side is True. Pass False to disable (adds the `-u` flag). The chosen value is persisted on the basemap and inherited by subsequent addplot calls.

        Returns:
            numpy.ndarray: Coordinate data (each row is [x, y]) or None on failure
        """
        import warnings
        warnings.warn(
            "fit_transform_csvform is deprecated. Use basemap_csvform() instead for unified API.",
            DeprecationWarning,
            stacklevel=2
        )
        # File existence and format check (accept both string and list, same as waveform)
        if isinstance(files, str):
            files = [files]  # Convert single file to list
        
        if not files or not isinstance(files, list):
            print("Error: files must be a file path (string) or list of file paths")
            return None
        
        files_to_upload = []
        for file_path in files:
            if not os.path.exists(file_path):
                print(f"Error: File not found: {file_path}")
                return None
            
            # File format check (.csv only)
            ext = os.path.splitext(file_path)[1].lower()
            if ext != '.csv':
                print(f"Error: Unsupported file format: {ext}. Only .csv files are supported.")
                return None
            
            files_to_upload.append(('files', open(file_path, 'rb')))
        
        try:
            
            # Prepare form data (same pattern as fit_transform_waveform)
            form_data = {
                'label': label or '',
                'tag': tag or '',
                'description': description or ''
            }
            
            if random_seed != 42:
                form_data['randomSeed'] = str(random_seed)
            
            # Add weight and type options
            if weight_option_str is not None:
                form_data['weight_option_str'] = weight_option_str
            if type_option_str is not None:
                form_data['type_option_str'] = type_option_str
            
            # Add drop_columns if specified
            if drop_columns is not None and isinstance(drop_columns, list):
                form_data['drop_columns'] = json.dumps(drop_columns)
            
            # Add identna parameters
            identna_params = {}
            if identna_resolution is not None:
                identna_params['resolution'] = int(identna_resolution)
            if identna_effective_radius is not None:
                identna_params['effectiveRadius'] = identna_effective_radius if identna_effective_radius == 'auto' else float(identna_effective_radius)
            if identna_er_method is not None:
                identna_params['erMethod'] = identna_er_method
            if identna_knn_k is not None:
                identna_params['knnK'] = int(identna_knn_k)
            if identna_params:
                form_data['identna_params'] = json.dumps(identna_params)

            # vector_normalization: multipart は文字列で送信
            if vector_normalization is not None:
                form_data['vector_normalization'] = 'true' if bool(vector_normalization) else 'false'

            # Send as multipart/form-data (same pattern as fit_transform_waveform)
            headers = {'session-key': self.session_key}  # Content-Type is auto-set by requests
            response = requests.post(
                f"{API_URL}/data/fit_transform_csvform",
                files=files_to_upload,
                data=form_data,
                headers=headers
            )
            
            if response.status_code == 200:
                response_data = response.json()
                baseXyData = response_data['resdata']['baseXyData']
                self.mapNo = response_data['resdata']['mapNo']
                self.shareUrl = response_data.get('shareUrl')  # Save share URL
                
                np_array = np.array(baseXyData)  # Convert baseXyData to NumPy array
                return np_array  # Return converted NumPy array
            else:
                try:
                    error_message = response.json().get('message', 'Unknown error')
                except:
                    error_message = f"HTTP {response.status_code}: {response.text}"
                print(f"CSV form data transformation failed. Server responded with error: {error_message}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network error during CSV file upload: {str(e)}")
            return None
        except Exception as e:
            print(f"Error processing CSV form file: {str(e)}")
            return None
        finally:
            # Ensure file handles are closed (same pattern as fit_transform_waveform)
            for _, file_handle in files_to_upload:
                try:
                    file_handle.close()
                except:
                    pass

    @pre_authentication
    def addplot(self, data, *args, weight_option_str=None, type_option_str=None, identna_resolution=None, identna_effective_radius=None, identna_er_method=None, identna_knn_k=None, detabn_max_window=None, detabn_rate_threshold=None, detabn_threshold=None, detabn_print_score=None, async_mode=False):
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
        
        # identnaパラメータを追加
        identna_params = {}
        if identna_resolution is not None:
            identna_params['resolution'] = identna_resolution
        if identna_effective_radius is not None:
            identna_params['effectiveRadius'] = identna_effective_radius
        if identna_er_method is not None:
            identna_params['erMethod'] = identna_er_method
        if identna_knn_k is not None:
            identna_params['knnK'] = int(identna_knn_k)
        if identna_params:
            data_dict['identnaParams'] = identna_params

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

        response = requests.post(f"{API_URL}/data/addplot", json=data_dict, headers=headers,
                                 params=self._async_params(async_mode))
        if async_mode:
            return self._handle_job_submission(response, self._handle_addplot_response)
        return self._handle_addplot_response(response)

    def _handle_addplot_response(self, response):
        """addplot のレスポンス処理（同期・非同期ジョブ結果の共通処理）"""
        if response.status_code == 200:
            return self._build_addplot_result(response.json())
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

    def _build_addplot_result(self, response_data):
        """addplot系レスポンスボディから返り値の辞書を組み立て、クライアント属性を更新する"""
        addXyData = response_data['resdata']
        self.currentAddPlotNo = response_data.get('addPlotNo')  # 追加プロット番号を保存
        self.shareUrl = response_data.get('shareUrl')  # シェアURLを保存

        # 座標データをNumPy配列に変換
        np_array = np.array(addXyData)

        # 拡張された返り値：座標データと異常度情報を含む辞書を返す
        return {
            'xyData': np_array,
            'addPlotNo': self.currentAddPlotNo,
            'abnormalityStatus': response_data.get('abnormalityStatus'),  # 'normal', 'abnormal', 'unknown'
            'abnormalityScore': response_data.get('abnormalityScore'),    # 異常度スコア
            'diagnosticScore': response_data.get('diagnosticScore'),     # 複合診断スコア
            'shareUrl': self.shareUrl
        }

    def _handle_addplot_file_response(self, response, kind):
        """addplot_waveform / addplot_csvform / addplot_embedding のレスポンス処理
        （同期・非同期ジョブ結果の共通処理）

        Args:
            kind (str): 'waveform', 'csvform', 'embedding' のいずれか
        """
        error_labels = {'waveform': 'Waveform addplot', 'csvform': 'CSV addplot', 'embedding': 'Embedding addplot'}
        if response.status_code == 200:
            return self._build_addplot_result(response.json())
        elif response.status_code == 400:
            if kind == 'waveform':
                try:
                    error_response = response.json()
                    error_code = error_response.get('error', '')
                    if error_code == 'MKFFTSEG_OPTIONS_NOT_ALLOWED':
                        print("Error: mkfftSeg options are not allowed in addplot_waveform.")
                        print("The system automatically uses the basemap's mkfftSeg options for data consistency.")
                    else:
                        print("Error: Bad request. Invalid parameters or missing map.")
                except:
                    print("Error: Bad request. Invalid parameters or missing map.")
            else:
                print("Error: Bad request. Invalid parameters or missing map.")
            return None
        elif response.status_code == 401:
            print("Error: Unauthorized. Invalid session key or map number.")
            return None
        else:
            try:
                error_message = response.json().get('message', 'Unknown error')
            except:
                error_message = f"HTTP {response.status_code}: {response.text}"
            print(f"{error_labels[kind]} failed. Server responded with error: {error_message}")
            return None

    @pre_authentication
    def addplot_waveform(self, files, mapNo=None,
                        # identna parameters
                        identna_resolution=None, identna_effective_radius=None,
                        identna_er_method=None, identna_knn_k=None,
                        # detabn parameters
                        detabn_max_window=5, detabn_rate_threshold=1.0,
                        detabn_threshold=None, detabn_print_score=True,
                        # async job mode
                        async_mode=False,
                        # Legacy mkfftSeg parameters (deprecated - for backward compatibility warnings)
                        mkfftseg_di=None, mkfftseg_hp=None, mkfftseg_lp=None,
                        mkfftseg_nm=None, mkfftseg_ol=None, mkfftseg_sr=None,
                        mkfftseg_wf=None, mkfftseg_wl=None):
        """
        Process WAV or CSV files for addplot (additional plot) analysis
        
        IMPORTANT: For data consistency, this function automatically uses the same mkfftSeg 
        options as the basemap. mkfftSeg parameters can no longer be specified manually 
        to ensure that basemap and addplot use identical preprocessing parameters.
        
        Args:
            files (list): List of WAV/CSV file paths
            mapNo (int, optional): Target map number. If None, uses current mapNo
            identna_resolution (int, optional): Custom resolution for identna
            identna_effective_radius (float or "auto", optional): Custom effective radius. "auto" for automatic determination
            identna_er_method (str, optional): Bandwidth method when effective_radius="auto": "silverman" (default) or "knn"
            identna_knn_k (int, optional): k for knn method (0 = auto ceil(sqrt(n)))
            detabn_max_window (int): Maximum window size for abnormality detection
            detabn_rate_threshold (float): Rate threshold for abnormality detection
            detabn_threshold (float, optional): Threshold for relative normal area value. When omitted (None), the server auto-derives it from detabn's coverage default (0.90)
            detabn_print_score (bool): Whether to print abnormality score
            async_mode (bool, optional): If True, submit in the server's asynchronous job
                mode (?async=true) and return a Job handle immediately instead of blocking.
                Call job.wait() to get the same return value as the synchronous call. Default: False.

        Returns:
            dict: Dictionary containing:
                - xyData: Coordinate data as NumPy array (each row is [x, y])
                - addPlotNo: Additional plot number
                - abnormalityStatus: 'normal', 'abnormal', or 'unknown'
                - abnormalityScore: Abnormality score (float or None)
                - diagnosticScore: Composite diagnostic score (dict or None), containing:
                    - detabn: detabn evaluation details (normalityScore, abnormalityScore, status, params, identnaParams)
                    - distance: Distance analysis (meanDistance, distanceStd, radiusOfGyration, normalizedDistance, exceedanceRatio, threshold, status)
                    - compositeStatus: Combined status ('normal', 'warning', 'danger')
                - shareUrl: Share URL for the map with this addplot
            When async_mode=True, a toorpia.job.Job handle is returned instead.

        Note:
            mkfftSeg options (filters, window settings, etc.) are automatically inherited
            from the basemap to ensure data consistency and accurate anomaly detection.
        """
        # Check for deprecated mkfftSeg parameters and warn users
        deprecated_params = [
            ('mkfftseg_di', mkfftseg_di), ('mkfftseg_hp', mkfftseg_hp),
            ('mkfftseg_lp', mkfftseg_lp), ('mkfftseg_nm', mkfftseg_nm),
            ('mkfftseg_ol', mkfftseg_ol), ('mkfftseg_sr', mkfftseg_sr),
            ('mkfftseg_wf', mkfftseg_wf), ('mkfftseg_wl', mkfftseg_wl)
        ]
        
        used_deprecated = [name for name, value in deprecated_params if value is not None]
        if used_deprecated:
            print("WARNING: mkfftSeg parameters are deprecated and will be ignored.")
            print("For data consistency, the system automatically uses the basemap's mkfftSeg options.")
            print(f"Deprecated parameters used: {', '.join(used_deprecated)}")
            print("Please remove these parameters from your code.")
        
        # Determine target map number
        target_mapNo = mapNo if mapNo is not None else self.mapNo
        if target_mapNo is None:
            print("Error: Map number is not specified. Please provide mapNo or use fit_transform() first.")
            return None
        
        # File existence and format check
        if not files or not isinstance(files, list):
            print("Error: files must be a non-empty list of file paths")
            return None
        
        files_to_upload = []
        for file_path in files:
            if not os.path.exists(file_path):
                print(f"Error: File not found: {file_path}")
                return None
            
            # File format check (.wav, .csv)
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ['.wav', '.csv']:
                print(f"Error: Unsupported file format: {ext}. Only .wav and .csv files are supported.")
                return None
            
            files_to_upload.append(('files', open(file_path, 'rb')))
        
        try:
            # Prepare identna parameters
            identna_params = {}
            if identna_resolution is not None:
                identna_params['resolution'] = int(identna_resolution)
            if identna_effective_radius is not None:
                identna_params['effectiveRadius'] = identna_effective_radius if identna_effective_radius == 'auto' else float(identna_effective_radius)
            if identna_er_method is not None:
                identna_params['erMethod'] = identna_er_method
            if identna_knn_k is not None:
                identna_params['knnK'] = int(identna_knn_k)
            
            # Prepare detabn parameters
            # threshold は明示指定時のみ送信する。省略時はサーバ側で detabn の
            # -coverage デフォルト(0.90)から自動導出される（0 を送るとそれが無効になる）
            detabn_params = {
                'maxWindow': int(detabn_max_window),
                'rateThreshold': float(detabn_rate_threshold),
                'printScore': bool(detabn_print_score)
            }
            if detabn_threshold is not None:
                detabn_params['threshold'] = float(detabn_threshold)
            
            # Send as form-data
            form_data = {
                'mapNo': str(target_mapNo),
                'detabn_options': json.dumps(detabn_params)
            }
            if identna_params:
                form_data['identna_options'] = json.dumps(identna_params)
            
            headers = {'session-key': self.session_key}  # Content-Type is auto-set by requests
            response = requests.post(
                f"{API_URL}/data/addplot_waveform",
                files=files_to_upload,
                data=form_data,
                headers=headers,
                params=self._async_params(async_mode)
            )

            if async_mode:
                return self._handle_job_submission(
                    response, lambda r: self._handle_addplot_file_response(r, 'waveform'))
            return self._handle_addplot_file_response(response, 'waveform')

        except requests.exceptions.RequestException as e:
            print(f"Network error during file upload: {str(e)}")
            return None
        except Exception as e:
            print(f"Error processing waveform addplot: {str(e)}")
            return None
        finally:
            # Ensure file handles are closed
            for _, file_handle in files_to_upload:
                try:
                    file_handle.close()
                except:
                    pass

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

        エクスポートされるファイル:
        - 必須ファイル: segments.csv, xy.dat
        - ステータスファイル: status.mi, status-02.mi, status-03.mi, ...
        - オプションファイル: normal_area.dat, seed-segments.csv, seed-xy.dat
        - input/ディレクトリ: csvform/waveform形式の元データ（存在する場合）

        除外されるファイル:
        - 追加プロットファイル (segments-add-*.csv, xy-add-*.dat, rawdata_add_*.csv, normalarea-add-*.dat)
        - 追加プロット用入力ディレクトリ (input_add_*/)
        - 一時ファイルディレクトリ (chunks/)
        - ログファイル (*.log)

        注意: エクスポートされたマップをインポートした後、追加プロットは再作成する必要があります。

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
            # ファイル名に__が含まれる場合はディレクトリ構造を復元
            for filename, file_content_b64 in map_data.items():
                try:
                    # __をディレクトリ区切り文字に戻す
                    original_path = filename.replace('__', os.sep)
                    file_path = os.path.join(export_dir, original_path)

                    # サブディレクトリが必要な場合は作成
                    file_dir = os.path.dirname(file_path)
                    if file_dir:
                        os.makedirs(file_dir, exist_ok=True)

                    # バイナリモードで書き出す。WAV などのバイナリファイルを UTF-8 として
                    # decode しようとすると失敗するため、bytes をそのまま書き込む。
                    # テキストファイル (segments.csv, mkdmatrix_meta.json 等) もバイト列として
                    # 正しく記録される。受け側 (_read_map_data_from_directory) は既に 'rb' で
                    # 読むので、import_map での再アップロードも問題なく動作する。
                    file_bytes = base64.b64decode(file_content_b64)
                    with open(file_path, 'wb') as f:
                        f.write(file_bytes)
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

        必須ファイル:
        - segments.csv: セグメントファイル（必須）
        - xy.dat: 座標データファイル（必須）

        オプションファイル:
        - status.mi, status-02.mi, ... : ステータスファイル
        - normal_area.dat: 正常領域ファイル
        - input/ディレクトリ: csvform/waveform形式の元データ
        - seed-segments.csv, seed-xy.dat: クラスタリングファイル（両方必須）

        除外されるファイル:
        - 追加プロットファイル (segments-add-*.csv, xy-add-*.dat, rawdata_add_*.csv, normalarea-add-*.dat)
        - ログファイル (*.log)

        注意:
        - ディレクトリに追加プロットファイルが含まれていても、それらはインポートされません
        - インポート後にaddplotメソッドを使用して追加プロットを再作成する必要があります
        - input/などのサブディレクトリがある場合、ディレクトリ構造も自動的にアップロードされます
        - クラスタリングマップの場合、seed-segments.csvとseed-xy.datの両方が必要です

        Args:
            input_dir: インポートするマップファイルが含まれているディレクトリ

        Returns:
            インポートされた新しいマップ番号
            インポートに失敗した場合はNone
        """
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
    def addplot_csvform(self, files, mapNo=None,
                       # identna parameters
                       identna_resolution=None, identna_effective_radius=None,
                       identna_er_method=None, identna_knn_k=None,
                       # detabn parameters
                       detabn_max_window=5, detabn_rate_threshold=1.0,
                       detabn_threshold=None, detabn_print_score=True,
                       # async job mode
                       async_mode=False):
        """
        Process CSV files for addplot (additional plot) analysis
        Uses the same CSV processing options as the base map (stored in database)
        
        Args:
            files (str or list): CSV file path or list of CSV file paths
            mapNo (int, optional): Target map number. If None, uses current mapNo
            identna_resolution (int, optional): Custom resolution for identna
            identna_effective_radius (float or "auto", optional): Custom effective radius. "auto" for automatic determination
            identna_er_method (str, optional): Bandwidth method when effective_radius="auto": "silverman" (default) or "knn"
            identna_knn_k (int, optional): k for knn method (0 = auto ceil(sqrt(n)))
            detabn_max_window (int): Maximum window size for abnormality detection
            detabn_rate_threshold (float): Rate threshold for abnormality detection
            detabn_threshold (float, optional): Threshold for relative normal area value. When omitted (None), the server auto-derives it from detabn's coverage default (0.90)
            detabn_print_score (bool): Whether to print abnormality score
            async_mode (bool, optional): If True, submit in the server's asynchronous job
                mode (?async=true) and return a Job handle immediately instead of blocking.
                Call job.wait() to get the same return value as the synchronous call. Default: False.

        Returns:
            dict: Dictionary containing:
                - xyData: Coordinate data as NumPy array (each row is [x, y])
                - addPlotNo: Additional plot number
                - abnormalityStatus: 'normal', 'abnormal', or 'unknown'
                - abnormalityScore: Abnormality score (float or None)
                - diagnosticScore: Composite diagnostic score (dict or None), containing:
                    - detabn: detabn evaluation details (normalityScore, abnormalityScore, status, params, identnaParams)
                    - distance: Distance analysis (meanDistance, distanceStd, radiusOfGyration, normalizedDistance, exceedanceRatio, threshold, status)
                    - compositeStatus: Combined status ('normal', 'warning', 'danger')
                - shareUrl: Share URL for the map with this addplot
            When async_mode=True, a toorpia.job.Job handle is returned instead.
        """
        # Determine target map number
        target_mapNo = mapNo if mapNo is not None else self.mapNo
        if target_mapNo is None:
            print("Error: Map number is not specified. Please provide mapNo or use basemap_csvform() first.")
            return None

        # File existence and format check (accept both string and list, same as csvform)
        if isinstance(files, str):
            files = [files]  # Convert single file to list
        
        if not files or not isinstance(files, list):
            print("Error: files must be a file path (string) or list of file paths")
            return None
        
        files_to_upload = []
        for file_path in files:
            if not os.path.exists(file_path):
                print(f"Error: File not found: {file_path}")
                return None
            
            # File format check (.csv only)
            ext = os.path.splitext(file_path)[1].lower()
            if ext != '.csv':
                print(f"Error: Unsupported file format: {ext}. Only .csv files are supported.")
                return None
            
            files_to_upload.append(('files', open(file_path, 'rb')))
        
        try:
            # Prepare identna parameters
            identna_params = {}
            if identna_resolution is not None:
                identna_params['resolution'] = int(identna_resolution)
            if identna_effective_radius is not None:
                identna_params['effectiveRadius'] = identna_effective_radius if identna_effective_radius == 'auto' else float(identna_effective_radius)
            if identna_er_method is not None:
                identna_params['erMethod'] = identna_er_method
            if identna_knn_k is not None:
                identna_params['knnK'] = int(identna_knn_k)
            
            # Prepare detabn parameters
            # threshold は明示指定時のみ送信する。省略時はサーバ側で detabn の
            # -coverage デフォルト(0.90)から自動導出される（0 を送るとそれが無効になる）
            detabn_params = {
                'maxWindow': int(detabn_max_window),
                'rateThreshold': float(detabn_rate_threshold),
                'printScore': bool(detabn_print_score)
            }
            if detabn_threshold is not None:
                detabn_params['threshold'] = float(detabn_threshold)
            
            # Send as form-data
            form_data = {
                'mapNo': str(target_mapNo),
                'detabn_options': json.dumps(detabn_params)
            }
            if identna_params:
                form_data['identna_options'] = json.dumps(identna_params)
            
            headers = {'session-key': self.session_key}  # Content-Type is auto-set by requests
            response = requests.post(
                f"{API_URL}/data/addplot_csvform",
                files=files_to_upload,
                data=form_data,
                headers=headers,
                params=self._async_params(async_mode)
            )

            if async_mode:
                return self._handle_job_submission(
                    response, lambda r: self._handle_addplot_file_response(r, 'csvform'))
            return self._handle_addplot_file_response(response, 'csvform')

        except requests.exceptions.RequestException as e:
            print(f"Network error during file upload: {str(e)}")
            return None
        except Exception as e:
            print(f"Error processing CSV addplot: {str(e)}")
            return None
        finally:
            # Ensure file handles are closed
            for _, file_handle in files_to_upload:
                try:
                    file_handle.close()
                except:
                    pass

    @pre_authentication
    def addplot_embedding(self, files, mapNo=None,
                         # identna parameters
                         identna_resolution=None, identna_effective_radius=None,
                         identna_er_method=None, identna_knn_k=None,
                         # detabn parameters
                         detabn_max_window=5, detabn_rate_threshold=1.0,
                         detabn_threshold=None, detabn_print_score=True,
                         # async job mode
                         async_mode=False):
        """
        Process embedding data for addplot (additional plot) analysis

        Preprocessing options (l2_normalization, id_columns) are automatically
        inherited from the base map on the server side and cannot be specified
        here. This guarantees that basemap and addplot use identical
        preprocessing and consistent dimension names.

        Accepts CSV file path(s) (.csv or gzip-compressed .csv.gz) or in-memory
        embedding data (2D numpy.ndarray or pandas.DataFrame), with the same
        CSV conversion and upload conventions as basemap_embedding()
        (%.7g serialization + gzip compression, with uncompressed fallback).

        Args:
            files (str, list, numpy.ndarray or pandas.DataFrame): CSV file path(s) or in-memory embedding data
            mapNo (int, optional): Target map number. If None, uses current mapNo
            identna_resolution (int, optional): Custom resolution for identna
            identna_effective_radius (float or "auto", optional): Custom effective radius. "auto" for automatic determination
            identna_er_method (str, optional): Bandwidth method when effective_radius="auto": "silverman" (default) or "knn"
            identna_knn_k (int, optional): k for knn method (0 = auto ceil(sqrt(n)))
            detabn_max_window (int): Maximum window size for abnormality detection
            detabn_rate_threshold (float): Rate threshold for abnormality detection
            detabn_threshold (float, optional): Threshold for relative normal area value. When omitted (None), the server auto-derives it from detabn's coverage default (0.90)
            detabn_print_score (bool): Whether to print abnormality score
            async_mode (bool, optional): If True, submit in the server's asynchronous job
                mode (?async=true) and return a Job handle immediately instead of blocking.
                Call job.wait() to get the same return value as the synchronous call. Default: False.

        Returns:
            dict: Dictionary containing:
                - xyData: Coordinate data as NumPy array (each row is [x, y])
                - addPlotNo: Additional plot number
                - abnormalityStatus: 'normal', 'abnormal', or 'unknown'
                - abnormalityScore: Abnormality score (float or None)
                - diagnosticScore: Composite diagnostic score (dict or None), containing:
                    - detabn: detabn evaluation details (normalityScore, abnormalityScore, status, params, identnaParams)
                    - distance: Distance analysis (meanDistance, distanceStd, radiusOfGyration, normalizedDistance, exceedanceRatio, threshold, status)
                    - compositeStatus: Combined status ('normal', 'warning', 'danger')
                - shareUrl: Share URL for the map with this addplot
            When async_mode=True, a toorpia.job.Job handle is returned instead.
        """
        # Determine target map number
        target_mapNo = mapNo if mapNo is not None else self.mapNo
        if target_mapNo is None:
            print("Error: Map number is not specified. Please provide mapNo or use basemap_embedding() first.")
            return None

        # ndarray/DataFrame direct input: convert to a temporary CSV file
        temp_csv_path = None
        if not isinstance(files, (str, list)):
            temp_csv_path = self._convert_inmemory_embedding(files)
            if temp_csv_path is None:
                return None
            files = [temp_csv_path]

        # File existence and format check (accept both string and list, same as csvform)
        if isinstance(files, str):
            files = [files]  # Convert single file to list

        if not files or not isinstance(files, list):
            print("Error: files must be a file path (string) or list of file paths")
            return None

        for file_path in files:
            if not os.path.exists(file_path):
                print(f"Error: File not found: {file_path}")
                return None

            # File format check (.csv / .csv.gz)
            lower_path = file_path.lower()
            if not (lower_path.endswith('.csv') or lower_path.endswith('.csv.gz')):
                print(f"Error: Unsupported file format: {os.path.splitext(file_path)[1]}. "
                      "Only .csv / .csv.gz files are supported.")
                return None

        try:
            # Prepare identna parameters
            identna_params = {}
            if identna_resolution is not None:
                identna_params['resolution'] = int(identna_resolution)
            if identna_effective_radius is not None:
                identna_params['effectiveRadius'] = identna_effective_radius if identna_effective_radius == 'auto' else float(identna_effective_radius)
            if identna_er_method is not None:
                identna_params['erMethod'] = identna_er_method
            if identna_knn_k is not None:
                identna_params['knnK'] = int(identna_knn_k)

            # Prepare detabn parameters
            # threshold は明示指定時のみ送信する。省略時はサーバ側で detabn の
            # -coverage デフォルト(0.90)から自動導出される（0 を送るとそれが無効になる）
            detabn_params = {
                'maxWindow': int(detabn_max_window),
                'rateThreshold': float(detabn_rate_threshold),
                'printScore': bool(detabn_print_score)
            }
            if detabn_threshold is not None:
                detabn_params['threshold'] = float(detabn_threshold)

            # Send as form-data
            form_data = {
                'mapNo': str(target_mapNo),
                'detabn_options': json.dumps(detabn_params)
            }
            if identna_params:
                form_data['identna_options'] = json.dumps(identna_params)

            # Send as multipart/form-data to the addplot_embedding endpoint
            # (falls back to uncompressed upload on servers without .csv.gz support)
            response = self._post_embedding_files('/data/addplot_embedding', files, form_data,
                                                  params=self._async_params(async_mode))

            if async_mode:
                return self._handle_job_submission(
                    response, lambda r: self._handle_addplot_file_response(r, 'embedding'))
            return self._handle_addplot_file_response(response, 'embedding')

        except requests.exceptions.RequestException as e:
            print(f"Network error during file upload: {str(e)}")
            return None
        except Exception as e:
            print(f"Error processing embedding addplot: {str(e)}")
            return None
        finally:
            # Remove the temporary CSV file created from ndarray/DataFrame input
            if temp_csv_path is not None:
                try:
                    os.remove(temp_csv_path)
                except:
                    pass

    def _handle_basemap_response(self, response, error_prefix):
        """basemap_csvform / basemap_waveform / basemap_embedding のレスポンス処理
        （同期・非同期ジョブ結果の共通処理）

        Args:
            error_prefix (str): エラーメッセージの先頭に付ける処理名
        """
        if response.status_code == 200:
            response_data = response.json()
            baseXyData = response_data['resdata']['baseXyData']
            self.mapNo = response_data['resdata']['mapNo']
            self.shareUrl = response_data.get('shareUrl')  # Save share URL

            np_array = np.array(baseXyData)  # Convert baseXyData to NumPy array

            # Return unified structure similar to addplot methods
            return {
                'xyData': np_array,
                'mapNo': self.mapNo,
                'shareUrl': self.shareUrl
            }
        else:
            try:
                error_message = response.json().get('message', 'Unknown error')
            except:
                error_message = f"HTTP {response.status_code}: {response.text}"
            print(f"{error_prefix}. Server responded with error: {error_message}")
            return None

    @pre_authentication
    def basemap_csvform(self, files, weight_option_str=None, type_option_str=None,
                    drop_columns=None, label=None, tag=None, description=None,
                    random_seed=42, identna_resolution=None, identna_effective_radius=None,
                    identna_er_method=None, identna_knn_k=None,
                    vector_normalization=None, async_mode=False):
        """
        Create base map from CSV files directly with unified return structure
        
        Args:
            files (str or list): CSV file path or list of CSV file paths (required)
            weight_option_str (str, optional): Weight options for columns (e.g., "1:1,2:0,3:1")
            type_option_str (str, optional): Type options for columns (e.g., "1:float,2:none,3:int")
            drop_columns (list, optional): List of column names to drop/exclude
            label (str, optional): Map label
            tag (str, optional): Map tag  
            description (str, optional): Map description
            random_seed (int, optional): Random seed for reproducibility (default: 42)
            identna_resolution (int, optional): Mesh resolution (default: 100)
            identna_effective_radius (float or "auto", optional): Effective radius. "auto" for automatic determination (default: 0.1)
            identna_er_method (str, optional): Bandwidth method when effective_radius="auto": "silverman" (default) or "knn"
            identna_knn_k (int, optional): k for knn method (0 = auto ceil(sqrt(n)))
            vector_normalization (bool, optional): Enable/disable L2 vector normalization in the toorpia binary. Default server-side is True. Pass False to disable (adds the `-u` flag). The chosen value is persisted on the basemap and inherited by subsequent addplot calls.
            async_mode (bool, optional): If True, submit in the server's asynchronous job
                mode (?async=true) and return a Job handle immediately instead of blocking.
                Call job.wait() to get the same return value as the synchronous call. Default: False.

        Returns:
            dict: Dictionary containing:
                - xyData: Coordinate data as NumPy array (each row is [x, y])
                - mapNo: Map number
                - shareUrl: Share URL for the map
            When async_mode=True, a toorpia.job.Job handle is returned instead.
        """
        # File existence and format check (accept both string and list)
        if isinstance(files, str):
            files = [files]  # Convert single file to list

        if not files or not isinstance(files, list):
            print("Error: files must be a file path (string) or list of file paths")
            return None

        files_to_upload = []
        for file_path in files:
            if not os.path.exists(file_path):
                print(f"Error: File not found: {file_path}")
                return None

            # File format check (.csv only)
            ext = os.path.splitext(file_path)[1].lower()
            if ext != '.csv':
                print(f"Error: Unsupported file format: {ext}. Only .csv files are supported.")
                return None

            files_to_upload.append(('files', open(file_path, 'rb')))

        try:
            # Prepare form data
            form_data = {
                'label': label or '',
                'tag': tag or '',
                'description': description or ''
            }
            
            if random_seed != 42:
                form_data['randomSeed'] = str(random_seed)
            
            # Add weight and type options
            if weight_option_str is not None:
                form_data['weight_option_str'] = weight_option_str
            if type_option_str is not None:
                form_data['type_option_str'] = type_option_str
            
            # Add drop_columns if specified
            if drop_columns is not None and isinstance(drop_columns, list):
                form_data['drop_columns'] = json.dumps(drop_columns)
            
            # Add identna parameters
            identna_params = {}
            if identna_resolution is not None:
                identna_params['resolution'] = int(identna_resolution)
            if identna_effective_radius is not None:
                identna_params['effectiveRadius'] = identna_effective_radius if identna_effective_radius == 'auto' else float(identna_effective_radius)
            if identna_er_method is not None:
                identna_params['erMethod'] = identna_er_method
            if identna_knn_k is not None:
                identna_params['knnK'] = int(identna_knn_k)
            if identna_params:
                form_data['identna_params'] = json.dumps(identna_params)

            # vector_normalization: multipart は文字列で送信
            if vector_normalization is not None:
                form_data['vector_normalization'] = 'true' if bool(vector_normalization) else 'false'

            # Send as multipart/form-data to new basemap_csvform endpoint
            headers = {'session-key': self.session_key}  # Content-Type is auto-set by requests
            response = requests.post(
                f"{API_URL}/data/basemap_csvform",
                files=files_to_upload,
                data=form_data,
                headers=headers,
                params=self._async_params(async_mode)
            )

            if async_mode:
                return self._handle_job_submission(
                    response, lambda r: self._handle_basemap_response(r, 'CSV basemap creation failed'))
            return self._handle_basemap_response(response, 'CSV basemap creation failed')

        except requests.exceptions.RequestException as e:
            print(f"Network error during CSV file upload: {str(e)}")
            return None
        except Exception as e:
            print(f"Error processing CSV basemap file: {str(e)}")
            return None
        finally:
            # Ensure file handles are closed
            for _, file_handle in files_to_upload:
                try:
                    file_handle.close()
                except:
                    pass

    @pre_authentication
    def basemap_embedding(self, files, l2_normalization=None, id_columns=None,
                    label=None, tag=None, description=None,
                    identna_resolution=None, identna_effective_radius=None,
                    identna_er_method=None, identna_knn_k=None, async_mode=False):
        """
        Create base map from embedding vectors with unified return structure

        Accepts CSV file path(s) (.csv or gzip-compressed .csv.gz) or in-memory
        embedding data (2D numpy.ndarray or pandas.DataFrame). Input rows are
        samples and columns are embedding dimensions; header rows are
        auto-detected and leading non-numeric columns are auto-detected as
        ID/label columns. An ndarray is uploaded as a headerless CSV so that
        dimension names are auto-generated consistently between basemap and
        addplot; a DataFrame keeps its header. In-memory data is serialized
        with 7 significant digits (%.7g) and gzip-compressed for upload, which
        shrinks the transfer to roughly 1/4 of a full-precision plain CSV; on
        servers without .csv.gz support the upload transparently falls back to
        uncompressed CSV.

        Note:
            vector_normalization is not applicable to embedding maps (the
            engine always uses the euclidean distance mode).

        Args:
            files (str, list, numpy.ndarray or pandas.DataFrame): CSV file path(s) or in-memory embedding data
            l2_normalization (bool, optional): Enable/disable L2 normalization of each input vector. Default server-side is True. Pass False for embeddings whose norm carries information.
            id_columns (int, optional): Number of leading ID/label columns. Usually unnecessary: leading non-numeric columns are auto-detected. Set only when the ID columns look numeric.
            label (str, optional): Map label
            tag (str, optional): Map tag
            description (str, optional): Map description
            identna_resolution (int, optional): Mesh resolution (default: 100)
            identna_effective_radius (float or "auto", optional): Effective radius. "auto" for automatic determination (default: 0.1)
            identna_er_method (str, optional): Bandwidth method when effective_radius="auto": "silverman" (default) or "knn"
            identna_knn_k (int, optional): k for knn method (0 = auto ceil(sqrt(n)))
            async_mode (bool, optional): If True, submit in the server's asynchronous job
                mode (?async=true) and return a Job handle immediately instead of blocking.
                Call job.wait() to get the same return value as the synchronous call. Default: False.

        Returns:
            dict: Dictionary containing:
                - xyData: Coordinate data as NumPy array (each row is [x, y])
                - mapNo: Map number
                - shareUrl: Share URL for the map
            When async_mode=True, a toorpia.job.Job handle is returned instead.
        """
        # ndarray/DataFrame direct input: convert to a temporary CSV file
        temp_csv_path = None
        if not isinstance(files, (str, list)):
            temp_csv_path = self._convert_inmemory_embedding(files)
            if temp_csv_path is None:
                return None
            files = [temp_csv_path]

        # File existence and format check (accept both string and list)
        if isinstance(files, str):
            files = [files]  # Convert single file to list

        if not files or not isinstance(files, list):
            print("Error: files must be a file path (string) or list of file paths")
            return None

        for file_path in files:
            if not os.path.exists(file_path):
                print(f"Error: File not found: {file_path}")
                return None

            # File format check (.csv / .csv.gz)
            lower_path = file_path.lower()
            if not (lower_path.endswith('.csv') or lower_path.endswith('.csv.gz')):
                print(f"Error: Unsupported file format: {os.path.splitext(file_path)[1]}. "
                      "Only .csv / .csv.gz files are supported.")
                return None

        try:
            # Prepare form data
            form_data = {
                'label': label or '',
                'tag': tag or '',
                'description': description or ''
            }

            # 前処理オプション: 明示指定された場合のみ送信（サーバー側デフォルトに委ねる）
            if l2_normalization is not None:
                form_data['l2_normalization'] = 'true' if bool(l2_normalization) else 'false'
            if id_columns is not None:
                form_data['id_columns'] = str(int(id_columns))

            # Add identna parameters
            identna_params = {}
            if identna_resolution is not None:
                identna_params['resolution'] = int(identna_resolution)
            if identna_effective_radius is not None:
                identna_params['effectiveRadius'] = identna_effective_radius if identna_effective_radius == 'auto' else float(identna_effective_radius)
            if identna_er_method is not None:
                identna_params['erMethod'] = identna_er_method
            if identna_knn_k is not None:
                identna_params['knnK'] = int(identna_knn_k)
            if identna_params:
                form_data['identna_params'] = json.dumps(identna_params)

            # Send as multipart/form-data to the basemap_embedding endpoint
            # (falls back to uncompressed upload on servers without .csv.gz support)
            response = self._post_embedding_files('/data/basemap_embedding', files, form_data,
                                                  params=self._async_params(async_mode))

            if async_mode:
                return self._handle_job_submission(
                    response, lambda r: self._handle_basemap_response(r, 'Embedding basemap creation failed'))
            return self._handle_basemap_response(response, 'Embedding basemap creation failed')

        except requests.exceptions.RequestException as e:
            print(f"Network error during embedding CSV upload: {str(e)}")
            return None
        except Exception as e:
            print(f"Error processing embedding basemap file: {str(e)}")
            return None
        finally:
            # Remove the temporary CSV file created from ndarray/DataFrame input
            if temp_csv_path is not None:
                try:
                    os.remove(temp_csv_path)
                except:
                    pass

    @pre_authentication
    def basemap_waveform(self, files,
                        # mkfftSeg parameters
                        mkfftseg_di=1, mkfftseg_hp=-1.0, mkfftseg_lp=-1.0,
                        mkfftseg_nm=0, mkfftseg_ol=50.0, mkfftseg_sr=48000,
                        mkfftseg_wf="hanning", mkfftseg_wl=65536,
                        # identna parameters
                        identna_resolution=None, identna_effective_radius=None,
                        identna_er_method=None, identna_knn_k=None,
                        # toorpia binary option
                        vector_normalization=None,
                        # metadata
                        label=None, tag=None, description=None,
                        # async job mode
                        async_mode=False):
        """
        Create base map from WAV or CSV files directly with unified return structure
        
        Args:
            files (list): List of WAV/CSV file paths
            mkfftseg_di (int): Data Index (starting from 1, for CSV files)
            mkfftseg_hp (float): High pass filter (-1 to disable)
            mkfftseg_lp (float): Low pass filter (-1 to disable)
            mkfftseg_nm (int): nMovingAverage (0 for auto-setting)
            mkfftseg_ol (float): Overlap ratio (%)
            mkfftseg_sr (int): Sample rate (for CSV files)
            mkfftseg_wf (str): Window function ("hanning" or "hamming")
            mkfftseg_wl (int): Window length
            identna_resolution (int): Mesh resolution (default: 100)
            identna_effective_radius (float or "auto"): Effective radius. "auto" for automatic determination (default: 0.1)
            identna_er_method (str): Bandwidth method when effective_radius="auto": "silverman" (default) or "knn"
            identna_knn_k (int): k for knn method (0 = auto ceil(sqrt(n)))
            vector_normalization (bool, optional): Enable/disable L2 vector normalization in the toorpia binary. Default server-side is True. Pass False to disable (adds the `-u` flag). The chosen value is persisted on the basemap and inherited by subsequent addplot calls.
            label (str): Map label
            tag (str): Map tag
            description (str): Map description
            async_mode (bool, optional): If True, submit in the server's asynchronous job
                mode (?async=true) and return a Job handle immediately instead of blocking.
                Call job.wait() to get the same return value as the synchronous call. Default: False.

        Returns:
            dict: Dictionary containing:
                - xyData: Coordinate data as NumPy array (each row is [x, y])
                - mapNo: Map number
                - shareUrl: Share URL for the map
            When async_mode=True, a toorpia.job.Job handle is returned instead.
        """
        # File existence and format check
        if not files or not isinstance(files, list):
            print("Error: files must be a non-empty list of file paths")
            return None
        
        files_to_upload = []
        for file_path in files:
            if not os.path.exists(file_path):
                print(f"Error: File not found: {file_path}")
                return None
            
            # File format check (.wav, .csv)
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ['.wav', '.csv']:
                print(f"Error: Unsupported file format: {ext}. Only .wav and .csv files are supported.")
                return None
            
            files_to_upload.append(('files', open(file_path, 'rb')))
        
        try:
            # Prepare mkfftSeg options in JSON format
            mkfftseg_options = {
                'di': int(mkfftseg_di),
                'hp': float(mkfftseg_hp),
                'lp': float(mkfftseg_lp),
                'nm': int(mkfftseg_nm),
                'ol': float(mkfftseg_ol),
                'sr': int(mkfftseg_sr),
                'wf': str(mkfftseg_wf),
                'wl': int(mkfftseg_wl)
            }
            
            # Prepare identna parameters
            identna_params = {}
            if identna_resolution is not None:
                identna_params['resolution'] = int(identna_resolution)
            if identna_effective_radius is not None:
                identna_params['effectiveRadius'] = identna_effective_radius if identna_effective_radius == 'auto' else float(identna_effective_radius)
            if identna_er_method is not None:
                identna_params['erMethod'] = identna_er_method
            if identna_knn_k is not None:
                identna_params['knnK'] = int(identna_knn_k)
            
            # Send as form-data to new basemap_waveform endpoint
            form_data = {
                'mkfftseg_options': json.dumps(mkfftseg_options),
                'identna_options': json.dumps(identna_params) if identna_params else '{}',
                'label': label or '',
                'tag': tag or '',
                'description': description or ''
            }

            # vector_normalization: multipart は文字列で送信
            if vector_normalization is not None:
                form_data['vector_normalization'] = 'true' if bool(vector_normalization) else 'false'

            headers = {'session-key': self.session_key}  # Content-Type is auto-set by requests
            response = requests.post(
                f"{API_URL}/data/basemap_waveform",
                files=files_to_upload,
                data=form_data,
                headers=headers,
                params=self._async_params(async_mode)
            )

            if async_mode:
                return self._handle_job_submission(
                    response, lambda r: self._handle_basemap_response(r, 'Waveform basemap creation failed'))
            return self._handle_basemap_response(response, 'Waveform basemap creation failed')

        except requests.exceptions.RequestException as e:
            print(f"Network error during file upload: {str(e)}")
            return None
        except Exception as e:
            print(f"Error processing waveform basemap files: {str(e)}")
            return None
        finally:
            # Ensure file handles are closed
            for _, file_handle in files_to_upload:
                try:
                    file_handle.close()
                except:
                    pass

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
        
        Note: This function is not supported for waveform-based maps.
        
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
            elif response.status_code == 400:
                try:
                    error_response = response.json()
                    error_code = error_response.get('error', '')
                    if error_code == 'WAVEFORM_GETFEAT_NOT_SUPPORTED':
                        print("Error: Feature analysis is not supported for waveform-based maps.")
                    else:
                        print(f"Failed to get add plot features: {error_response.get('message', 'Bad request')}")
                except:
                    print("Failed to get add plot features: Bad request")
                return None
            else:
                try:
                    error_message = response.json().get('message', 'Unknown error')
                except:
                    error_message = f"HTTP {response.status_code}"
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
        指定されたディレクトリからマップデータを再帰的に読み込む

        注意: このメソッドはベースマップファイルのみを読み込みます。
        追加プロットファイル (segments-add-*.csv, xy-add-*.dat, rawdata_add_*.csv) や
        ログファイル (*.log) は除外されます。クラスタリング解析で生成された
        全てのファイルはベースマップの一部として含まれます。

        input/サブディレクトリがある場合も再帰的に読み込まれ、
        ファイル名はinput__filename.csvのように__区切りでエンコードされます。
        """
        map_data = {}
        add_plot_count = 0

        def read_directory_recursive(current_dir, relative_path=''):
            nonlocal add_plot_count

            for item in os.listdir(current_dir):
                item_path = os.path.join(current_dir, item)
                rel_path = os.path.join(relative_path, item) if relative_path else item

                if os.path.isdir(item_path):
                    # input/ディレクトリのみ再帰的に処理、他のディレクトリは除外
                    # chunks/, input_add_*/ などは除外
                    if rel_path == 'input':
                        read_directory_recursive(item_path, rel_path)
                    elif rel_path.startswith('input_add_') or rel_path == 'chunks':
                        continue  # これらのディレクトリはスキップ
                elif os.path.isfile(item_path):
                    # 追加プロットファイルとログファイルを除外
                    if (item.startswith('segments-add-') or
                        item.startswith('xy-add-') or
                        item.startswith('rawdata_add_') or
                        item.startswith('normalarea-add-') or
                        item.endswith('.log')):
                        add_plot_count += 1
                        continue

                    with open(item_path, 'rb') as f:
                        file_content = f.read()
                        # パス区切り文字を__に変換してエンコード
                        file_key = rel_path.replace(os.sep, '__')
                        map_data[file_key] = base64.b64encode(file_content).decode('utf-8')

        read_directory_recursive(directory)

        # ディレクトリ内に追加プロットファイルが存在する場合警告を表示
        if add_plot_count > 0:
            print(f"Warning: {add_plot_count} add plot related files were found but not included in the import/export.")
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
                # 文字列がdate-likeかどうかをチェック
                sample = df[col_name].dropna()
                is_date = False
                if len(sample) > 0:
                    try:
                        pd.to_datetime(sample.head(10), format='mixed')
                        is_date = True
                    except (ValueError, TypeError):
                        pass
                if is_date:
                    type_options.append(f"{col_idx}:date")    # 日付文字列型用の設定
                    weight_options.append(f"{col_idx}:0")     # 日付文字列型の重みは0
                else:
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

    def _convert_inmemory_embedding(self, data):
        """
        Convert in-memory embedding data (2D numpy.ndarray or pandas.DataFrame)
        into a temporary gzip-compressed CSV file (.csv.gz) for multipart upload
        (embedding methods only).

        An ndarray is written WITHOUT a header so that the server auto-generates
        consistent dimension names, keeping base and add column names
        aligned. A DataFrame is written WITH its header.

        Float values are serialized with the ``%.7g`` format (7 significant
        digits, on par with float32 precision) instead of the full float64
        repr, which roughly halves the CSV size. The map engine's run-to-run
        variability is far larger than this rounding, so the resulting
        coordinates are unaffected. gzip (level 6) further shrinks the numeric
        CSV to roughly 1/2-1/4, reducing upload time accordingly.

        Args:
            data (numpy.ndarray or pandas.DataFrame): Embedding data (rows=samples, columns=dimensions)

        Returns:
            str: Path of the temporary .csv.gz file, or None on failure.
                 The caller is responsible for removing the file.
        """
        temp_path = None
        try:
            import tempfile
            import pandas as pd  # pandasはndarray/DataFrame入力時のみ必要

            compression = {'method': 'gzip', 'compresslevel': 6}
            if isinstance(data, np.ndarray):
                if data.ndim != 2:
                    print("Error: ndarray input must be 2-dimensional (rows=samples, columns=dimensions)")
                    return None
                fd, temp_path = tempfile.mkstemp(suffix='.csv.gz')
                os.close(fd)
                # headerless output: the server auto-generates the dimension names,
                # which keeps headerless add data compatible with the basemap's column names
                pd.DataFrame(data).to_csv(temp_path, index=False, header=False,
                                          float_format='%.7g', compression=compression)
                return temp_path
            elif isinstance(data, pd.DataFrame):
                fd, temp_path = tempfile.mkstemp(suffix='.csv.gz')
                os.close(fd)
                # DataFrame keeps its own header
                data.to_csv(temp_path, index=False,
                            float_format='%.7g', compression=compression)
                return temp_path
            else:
                print("Error: files must be a file path (string), list of file paths, 2D numpy.ndarray, or pandas.DataFrame")
                return None
        except Exception as e:
            print(f"Error converting in-memory embedding data to CSV: {str(e)}")
            if temp_path is not None:
                try:
                    os.remove(temp_path)
                except:
                    pass
            return None

    def _post_embedding_files(self, endpoint, file_paths, form_data, params=None):
        """
        POST embedding CSV files (.csv / .csv.gz) to an embedding endpoint as
        multipart/form-data.

        Servers that do not yet accept gzip-compressed CSV reject ``.csv.gz``
        uploads with 415 UNSUPPORTED_FILE_TYPE; in that case the files are
        transparently decompressed and re-sent uncompressed, so the client
        stays compatible with older backends.

        Args:
            endpoint (str): Endpoint path (e.g. "/data/basemap_embedding")
            file_paths (list): Paths of the CSV files to upload
            form_data (dict): Additional form fields
            params (dict, optional): Query parameters (e.g. {'async': 'true'})

        Returns:
            requests.Response: The server response (of the retry, if one occurred)
        """
        headers = {'session-key': self.session_key}  # Content-Type is auto-set by requests

        def _post(paths):
            handles = [('files', open(p, 'rb')) for p in paths]
            try:
                return requests.post(f"{API_URL}{endpoint}", files=handles,
                                     data=form_data, headers=headers, params=params)
            finally:
                for _, handle in handles:
                    try:
                        handle.close()
                    except:
                        pass

        response = _post(file_paths)

        has_gzip = any(p.lower().endswith('.csv.gz') for p in file_paths)
        if has_gzip and response.status_code == 415:
            # サーバーが .csv.gz 未対応（gzip対応前のバージョン）: 展開して再送する
            import gzip
            import shutil
            import tempfile

            print("Note: server does not accept gzip-compressed CSV; retrying with uncompressed upload.")
            fallback_paths, fallback_temps = [], []
            try:
                for p in file_paths:
                    if p.lower().endswith('.csv.gz'):
                        fd, tmp = tempfile.mkstemp(suffix='.csv')
                        os.close(fd)
                        fallback_temps.append(tmp)
                        with gzip.open(p, 'rb') as src, open(tmp, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                        fallback_paths.append(tmp)
                    else:
                        fallback_paths.append(p)
                response = _post(fallback_paths)
            finally:
                for tmp in fallback_temps:
                    try:
                        os.remove(tmp)
                    except:
                        pass

        return response

