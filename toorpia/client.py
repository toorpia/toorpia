import requests
from .config import API_URL
from .utils.authentication import get_api_key

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
    def __init__(self, api_key=None):
        self.api_key = api_key if api_key else get_api_key()

    def authenticate(self):
        """バックエンドにAPIキーを送信して検証させ、セッションキーを取得する"""
        response = requests.post(f"{API_URL}/auth/login", json={"apiKey": self.api_key})
        if response.status_code == 200:
            session_key = response.json().get('sessionKey')
            print(f"Authentication successful. Session key: {session_key}")
            return session_key
        else:
            print("Authentication failed.")
            return None

    @pre_authentication
    def fit_transform(self, data):
        # ここで解析処理を行うコードを記述。解析処理のリクエストにはセッションキーを使用する
        pass

