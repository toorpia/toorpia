"""_post_with_busy_retry の単体テスト（サーバー不要・オフラインで実行可能）"""
import os

import pytest

from toorpia.client import toorPIA


class FakeResponse:
    def __init__(self, status_code, headers=None):
        self.status_code = status_code
        self.headers = headers or {}


def make_client(max_busy_wait_min=None):
    return toorPIA(api_key="dummy_api_key", max_busy_wait_min=max_busy_wait_min)


def make_sequence(responses, calls):
    """呼ばれるたびに responses から順に返す do_request を作る"""
    def do_request():
        calls.append(1)
        return responses[len(calls) - 1]
    return do_request


def test_success_passes_through_without_retry(monkeypatch):
    sleeps = []
    monkeypatch.setattr("toorpia.client.time.sleep", sleeps.append)
    client = make_client(max_busy_wait_min=30)
    calls = []
    response = client._post_with_busy_retry(make_sequence([FakeResponse(200)], calls))
    assert response.status_code == 200
    assert len(calls) == 1
    assert sleeps == []


def test_non_busy_errors_are_not_retried(monkeypatch):
    sleeps = []
    monkeypatch.setattr("toorpia.client.time.sleep", sleeps.append)
    client = make_client(max_busy_wait_min=30)
    calls = []
    response = client._post_with_busy_retry(make_sequence([FakeResponse(429)], calls))
    assert response.status_code == 429
    assert len(calls) == 1
    assert sleeps == []


def test_retries_on_503_honoring_retry_after(monkeypatch):
    sleeps = []
    monkeypatch.setattr("toorpia.client.time.sleep", sleeps.append)
    client = make_client(max_busy_wait_min=30)
    calls = []
    resets = []
    responses = [
        FakeResponse(503, {"Retry-After": "7"}),
        FakeResponse(503, {"Retry-After": "3"}),
        FakeResponse(200),
    ]
    response = client._post_with_busy_retry(
        make_sequence(responses, calls), reset=lambda: resets.append(1))
    assert response.status_code == 200
    assert len(calls) == 3
    assert sleeps == [7, 3]
    assert len(resets) == 2  # 再送のたびに巻き戻しが呼ばれる


def test_missing_retry_after_defaults_to_60s(monkeypatch):
    sleeps = []
    monkeypatch.setattr("toorpia.client.time.sleep", sleeps.append)
    client = make_client(max_busy_wait_min=30)
    calls = []
    responses = [FakeResponse(503), FakeResponse(200)]
    response = client._post_with_busy_retry(make_sequence(responses, calls))
    assert response.status_code == 200
    assert sleeps == [60]


def test_gives_up_when_budget_exhausted(monkeypatch):
    sleeps = []
    monkeypatch.setattr("toorpia.client.time.sleep", sleeps.append)
    # 予算 0.5 分 = 30 秒 < Retry-After 60 秒: 1回目の 503 で即あきらめる
    client = make_client(max_busy_wait_min=0.5)
    calls = []
    response = client._post_with_busy_retry(
        make_sequence([FakeResponse(503, {"Retry-After": "60"})], calls))
    assert response.status_code == 503
    assert len(calls) == 1
    assert sleeps == []


def test_zero_budget_disables_retry(monkeypatch):
    sleeps = []
    monkeypatch.setattr("toorpia.client.time.sleep", sleeps.append)
    client = make_client(max_busy_wait_min=0)
    calls = []
    response = client._post_with_busy_retry(
        make_sequence([FakeResponse(503, {"Retry-After": "1"})], calls))
    assert response.status_code == 503
    assert len(calls) == 1
    assert sleeps == []


def test_max_busy_wait_min_configuration(monkeypatch):
    # 引数 > 環境変数 > 既定30 の優先順位
    monkeypatch.delenv("TOORPIA_MAX_BUSY_WAIT_MIN", raising=False)
    assert make_client().max_busy_wait_min == 30.0
    monkeypatch.setenv("TOORPIA_MAX_BUSY_WAIT_MIN", "5")
    assert make_client().max_busy_wait_min == 5.0
    assert make_client(max_busy_wait_min=10).max_busy_wait_min == 10.0
    monkeypatch.setenv("TOORPIA_MAX_BUSY_WAIT_MIN", "not-a-number")
    assert make_client().max_busy_wait_min == 30.0
