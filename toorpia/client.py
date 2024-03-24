import requests
from .config import API_URL
from .utils.authentication import get_api_key

class toorPIA:
    def __init__(self, api_key=None):
        self.api_key = api_key if api_key else get_api_key()

    def fit_transform(self, data):
        # APIへのリクエストを行い、データを解析するコードをここに記述
        pass