from verychic_mcp.discovery import extract_channel_version, get_channel_version
from verychic_mcp.config import CHANNEL_VERSION_FALLBACK


def test_extract_channel_version_found():
    html = 'window.__cfg={"channelVersion":"26.06.18.00","x":1}'
    assert extract_channel_version(html) == "26.06.18.00"


def test_extract_channel_version_absent():
    assert extract_channel_version("<html>rien ici</html>") is None


class _Client:
    def __init__(self, text=None, boom=False):
        self._text, self._boom = text, boom

    def get_text(self, url, params=None):
        if self._boom:
            raise RuntimeError("réseau coupé")
        return self._text


def test_get_channel_version_uses_live_value():
    c = _Client(text='channelVersion="27.01.02.03"')
    assert get_channel_version(c) == "27.01.02.03"


def test_get_channel_version_falls_back_on_absence():
    assert get_channel_version(_Client(text="rien")) == CHANNEL_VERSION_FALLBACK


def test_get_channel_version_falls_back_on_error():
    assert get_channel_version(_Client(boom=True)) == CHANNEL_VERSION_FALLBACK
