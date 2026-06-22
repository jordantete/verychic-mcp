from verychic_mcp.errors import (
    VeryChicError, CloudflareBlocked, NotFound, UpstreamError,
)


def test_hierarchy():
    for exc in (CloudflareBlocked, NotFound, UpstreamError):
        assert issubclass(exc, VeryChicError)


def test_default_messages_are_actionable():
    assert "Cloudflare" in str(CloudflareBlocked())
    assert "introuvable" in str(NotFound())
    assert "VeryChic" in str(UpstreamError())


def test_messages_can_be_overridden():
    assert str(NotFound("offre 42 introuvable")) == "offre 42 introuvable"
