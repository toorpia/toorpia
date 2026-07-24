import json
import time


class _JobHttpResponse:
    """ジョブ結果 (httpStatus + body) を requests.Response 互換の形に包む薄いラッパ

    非同期ジョブの result / error は同期実行時のレスポンスボディと同形なので、
    これで包むことで同期用のレスポンス処理ロジックをそのまま流用できる。
    """

    def __init__(self, status_code, body):
        self.status_code = status_code if status_code is not None else 500
        self._body = body if body is not None else {}

    def json(self):
        return self._body

    @property
    def text(self):
        return json.dumps(self._body, ensure_ascii=False)


class Job:
    """?async=true で投入した非同期ジョブのハンドル

    fit_transform / addplot / basemap_* / addplot_* 系メソッドに async_mode=True を
    渡すと返される。wait() で完了までポーリングすると、同期実行時と同じ形の
    返り値が得られる（client.mapNo などの属性更新も同期実行時と同様に行われる）。

    Example:
        job = client.basemap_csvform(["data.csv"], async_mode=True)
        result = job.wait()  # {'xyData': ..., 'mapNo': ..., 'shareUrl': ...}
    """

    # wait() がポーリング失敗（ネットワークエラー・404等）を連続で許容する回数
    MAX_CONSECUTIVE_POLL_FAILURES = 3

    def __init__(self, client, job_id, parser, job_type=None):
        self.client = client
        self.job_id = job_id
        self.type = job_type
        self.status = 'queued'
        self.raw = None  # 直近の GET /jobs/:jobId レスポンスボディ
        self._parser = parser
        self._result = None
        self._parsed = False

    def __repr__(self):
        return f"<toorPIA Job {self.job_id} type={self.type} status={self.status}>"

    def refresh(self):
        """ジョブの現在の状態を1回問い合わせて反映する

        Returns:
            str: 現在のステータス ('queued', 'running', 'done', 'failed')。
                 問い合わせに失敗した場合は None
        """
        info = self.client.get_job(self.job_id)
        if info is None:
            return None
        self.raw = info
        self.status = info.get('status', self.status)
        self.type = info.get('type', self.type)
        return self.status

    @property
    def finished(self):
        return self.status in ('done', 'failed')

    def result(self):
        """完了済みジョブの結果を同期実行時と同じ形で返す

        未完了の場合は一度だけ状態を更新し、それでも未完了なら None を返す。
        failed の場合も同期実行時と同様にエラーメッセージを表示して None を返す。
        """
        if not self.finished:
            self.refresh()
        if not self.finished:
            print(f"Job {self.job_id} is not finished yet (status: {self.status}).")
            return None
        if not self._parsed:
            body = self.raw.get('result') if self.status == 'done' else self.raw.get('error')
            self._result = self._parser(_JobHttpResponse(self.raw.get('httpStatus'), body))
            self._parsed = True
        return self._result

    def wait(self, poll_interval=5, timeout=None):
        """完了までポーリングし、同期実行時と同じ形の結果を返す

        Args:
            poll_interval (float): ポーリング間隔（秒、デフォルト5秒）
            timeout (float, optional): 最大待ち時間（秒）。None で無制限。
                超過してもジョブ自体はサーバー側で継続し、後から result() や
                client.get_job() で結果を取得できる（結果保持は完了後24時間）

        Returns:
            同期実行時と同じ返り値。タイムアウトまたはジョブ失敗時は None
        """
        start = time.monotonic()
        failures = 0
        while True:
            status = self.refresh()
            if status is None:
                failures += 1
                if failures >= self.MAX_CONSECUTIVE_POLL_FAILURES:
                    print(f"Error: Failed to poll job {self.job_id} {failures} times in a row. Giving up.")
                    return None
            else:
                failures = 0
                if self.finished:
                    return self.result()
            if timeout is not None and time.monotonic() - start >= timeout:
                print(f"Timeout: Job {self.job_id} did not finish within {timeout} seconds (status: {self.status}).")
                return None
            time.sleep(poll_interval)
