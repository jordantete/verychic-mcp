import pytest
from verychic_mcp.errors import CloudflareBlocked, NotFound, UpstreamError
from verychic_mcp.http_client import classify_block, VeryChicClient


class FakeResp:
    def __init__(self, status, body="{}", headers=None):
        self.status_code = status
        self.text = body
        self.headers = headers or {}
        import json as _j
        self._j = _j

    def json(self):
        return self._j.loads(self.text)


class FakeSession:
    """Session factice : renvoie des réponses préprogrammées et journalise les appels."""
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        return self._responses.pop(0)


def test_classify_block_cloudflare():
    with pytest.raises(CloudflareBlocked):
        classify_block(403, {"cf-mitigated": "challenge"}, "<html>Just a moment...</html>")


def test_classify_block_404():
    with pytest.raises(NotFound):
        classify_block(404, {}, '{"error":true}')


def test_classify_block_5xx():
    with pytest.raises(UpstreamError):
        classify_block(500, {}, "oops")


def test_classify_block_ok_does_not_raise():
    assert classify_block(200, {}, "{}") is None


def test_get_json_returns_parsed_payload():
    sess = FakeSession([FakeResp(200, '{"content":[1,2]}')])
    client = VeryChicClient(session=sess, sleep=lambda s: None)
    assert client.get_json("https://x/y", {"a": "b"}) == {"content": [1, 2]}
    assert sess.calls[0][0] == "https://x/y"
    assert sess.calls[0][1] == {"a": "b"}


def test_get_json_raises_on_404():
    sess = FakeSession([FakeResp(404, "{}")])
    client = VeryChicClient(session=sess, sleep=lambda s: None)
    with pytest.raises(NotFound):
        client.get_json("https://x/missing")


def test_rate_limit_sleeps_between_calls():
    # horloge factice qui n'avance pas → la 2e requête doit dormir ~min_interval
    slept = []
    ticks = iter([100.0, 100.0, 100.0, 100.0])
    client = VeryChicClient(
        session=FakeSession([FakeResp(200, "{}"), FakeResp(200, "{}")]),
        min_interval=1.0, clock=lambda: next(ticks), sleep=slept.append,
    )
    client.get_json("https://x/1")
    client.get_json("https://x/2")
    assert slept and abs(slept[-1] - 1.0) < 0.01
