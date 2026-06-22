from verychic_mcp.errors import (
    CloudflareBlocked,
    NotFound,
    UpstreamError,
    VeryChicError,
)


def test_hierarchy():
    for exc in (CloudflareBlocked, NotFound, UpstreamError):
        assert issubclass(exc, VeryChicError)


def test_default_messages_are_actionable():
    assert "Cloudflare" in str(CloudflareBlocked())
    assert "not found" in str(NotFound())
    assert "VeryChic" in str(UpstreamError())


def test_messages_can_be_overridden():
    assert str(NotFound("offer 42 not found")) == "offer 42 not found"
