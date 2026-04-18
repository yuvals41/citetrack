from __future__ import annotations

from email import message_from_string
from email.header import decode_header, make_header
from email.message import Message
from typing import Any, cast

import pytest

from ai_visibility.alerts.email_alert import send_email_alert
from ai_visibility.analysis import crawler_simulation


def _set_smtp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "user")
    monkeypatch.setenv("SMTP_PASSWORD", "pass")
    monkeypatch.setenv("ALERT_EMAIL_TO", "to@example.com")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "from@example.com")


def _decode_message_part(part: Message | Any) -> str:
    payload = part.get_payload(decode=True)
    charset = part.get_content_charset() or "utf-8"
    if isinstance(payload, bytes):
        return payload.decode(charset)
    return ""


@pytest.mark.asyncio
async def test_send_email_alert_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_smtp_env(monkeypatch)

    state: dict[str, Any] = {"sent": False}

    class _SMTPStub:
        def __init__(self, host: str, port: int) -> None:
            state["host"] = host
            state["port"] = port

        def starttls(self) -> None:
            state["tls"] = True

        def login(self, username: str, password: str) -> None:
            state["login"] = (username, password)

        def sendmail(self, sender: str, recipients: list[str], message: str) -> None:
            state["sent"] = True
            state["sender"] = sender
            state["recipients"] = recipients
            state["message"] = message

        def quit(self) -> None:
            state["quit"] = True

    monkeypatch.setattr("ai_visibility.alerts.email_alert.smtplib.SMTP", _SMTPStub)

    ok = await send_email_alert(
        alerts=[{"type": "visibility_drop", "severity": "high", "message": "Visibility down 20%"}],
        workspace_slug="acme",
    )

    assert ok is True
    assert state["host"] == "smtp.example.com"
    assert state["port"] == 587
    assert state["login"] == ("user", "pass")
    assert state["sender"] == "from@example.com"
    assert state["recipients"] == ["to@example.com"]
    assert state["sent"] is True
    assert state["quit"] is True


@pytest.mark.asyncio
async def test_send_email_alert_missing_config_graceful_skip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_PORT", raising=False)
    monkeypatch.delenv("SMTP_USERNAME", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.delenv("ALERT_EMAIL_TO", raising=False)
    monkeypatch.delenv("ALERT_EMAIL_FROM", raising=False)

    ok = await send_email_alert(
        alerts=[{"type": "citation_drop", "severity": "medium", "message": "Dropped"}], workspace_slug="acme"
    )
    assert ok is False


@pytest.mark.asyncio
async def test_send_email_alert_smtp_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_smtp_env(monkeypatch)

    class _FailSMTP:
        def __init__(self, host: str, port: int) -> None:
            _ = (host, port)
            raise ConnectionError("smtp down")

    monkeypatch.setattr("ai_visibility.alerts.email_alert.smtplib.SMTP", _FailSMTP)

    ok = await send_email_alert(
        alerts=[{"type": "competitor_surge", "severity": "high", "message": "Competitor surged"}],
        workspace_slug="acme",
    )
    assert ok is False


@pytest.mark.asyncio
async def test_send_email_alert_content_format_contains_alert_data(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_smtp_env(monkeypatch)

    captured: dict[str, Any] = {}

    class _SMTPCapture:
        def __init__(self, host: str, port: int) -> None:
            _ = (host, port)

        def starttls(self) -> None:
            return None

        def login(self, username: str, password: str) -> None:
            _ = (username, password)

        def sendmail(self, sender: str, recipients: list[str], message: str) -> None:
            captured["sender"] = sender
            captured["recipients"] = recipients
            captured["raw"] = message

        def quit(self) -> None:
            return None

    monkeypatch.setattr("ai_visibility.alerts.email_alert.smtplib.SMTP", _SMTPCapture)

    alerts = [
        {"type": "visibility_drop", "severity": "high", "message": "Visibility dropped"},
        {"type": "citation_drop", "severity": "medium", "message": "Citations dropped"},
    ]
    ok = await send_email_alert(alerts=alerts, workspace_slug="workspace-1")

    assert ok is True
    parsed = message_from_string(cast(str, captured["raw"]))
    decoded_subject = str(make_header(decode_header(str(parsed["Subject"]))))
    assert decoded_subject == "AI Visibility Alert — workspace-1"

    parts = cast(list[Message], parsed.get_payload())
    plain = _decode_message_part(parts[0])
    html = _decode_message_part(parts[1])

    assert "visibility_drop" in plain
    assert "citation_drop" in plain
    assert "Visibility dropped" in html
    assert "Citations dropped" in html
    assert "<table" in html


@pytest.mark.asyncio
async def test_send_email_alert_empty_alerts_list(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_smtp_env(monkeypatch)

    called = {"smtp": False}

    class _SMTPNever:
        def __init__(self, host: str, port: int) -> None:
            _ = (host, port)
            called["smtp"] = True

    monkeypatch.setattr("ai_visibility.alerts.email_alert.smtplib.SMTP", _SMTPNever)

    ok = await send_email_alert(alerts=[], workspace_slug="workspace-1")
    assert ok is False
    assert called["smtp"] is False


class _DummyResponse:
    def __init__(self, *, status_code: int = 200, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


@pytest.mark.asyncio
async def test_check_js_rendering_no_js_required(monkeypatch: pytest.MonkeyPatch) -> None:
    html = "<html><body><h1>Hello</h1><p>" + ("Visible text " * 20) + "</p></body></html>"

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            return None

        async def get(self, url: str, **kwargs: Any) -> _DummyResponse:
            _ = (url, kwargs)
            return _DummyResponse(status_code=200, text=html)

    monkeypatch.setattr("ai_visibility.analysis.crawler_simulation.httpx.AsyncClient", lambda *a, **k: _Client())

    result = await crawler_simulation._check_js_rendering("https://example.com")
    assert result["js_required"] is False
    assert result["signals"] == []


@pytest.mark.asyncio
async def test_check_js_rendering_detects_noscript_signal(monkeypatch: pytest.MonkeyPatch) -> None:
    html = "<html><body><noscript>This content needs JavaScript to load properly.</noscript></body></html>"

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            return None

        async def get(self, url: str, **kwargs: Any) -> _DummyResponse:
            _ = (url, kwargs)
            return _DummyResponse(text=html)

    monkeypatch.setattr("ai_visibility.analysis.crawler_simulation.httpx.AsyncClient", lambda *a, **k: _Client())

    result = await crawler_simulation._check_js_rendering("https://example.com")
    assert result["js_required"] is True
    assert "noscript_content" in cast(list[str], result["signals"])


@pytest.mark.asyncio
async def test_check_js_rendering_detects_react_root_div(monkeypatch: pytest.MonkeyPatch) -> None:
    html = "<html><body><div id='root'></div><script src='app.js'></script></body></html>"

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            return None

        async def get(self, url: str, **kwargs: Any) -> _DummyResponse:
            _ = (url, kwargs)
            return _DummyResponse(text=html)

    monkeypatch.setattr("ai_visibility.analysis.crawler_simulation.httpx.AsyncClient", lambda *a, **k: _Client())

    result = await crawler_simulation._check_js_rendering("https://example.com")
    assert result["js_required"] is True
    assert "spa_root_div" in cast(list[str], result["signals"])


@pytest.mark.asyncio
async def test_check_js_rendering_detects_minimal_text_with_scripts(monkeypatch: pytest.MonkeyPatch) -> None:
    html = "<html><body><div>Hi</div><script></script><script></script><script></script></body></html>"

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            return None

        async def get(self, url: str, **kwargs: Any) -> _DummyResponse:
            _ = (url, kwargs)
            return _DummyResponse(text=html)

    monkeypatch.setattr("ai_visibility.analysis.crawler_simulation.httpx.AsyncClient", lambda *a, **k: _Client())

    result = await crawler_simulation._check_js_rendering("https://example.com")
    assert result["js_required"] is True
    assert "minimal_text_with_scripts" in cast(list[str], result["signals"])


@pytest.mark.asyncio
async def test_check_js_rendering_fetch_failure_graceful(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Client:
        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            return None

        async def get(self, url: str, **kwargs: Any) -> _DummyResponse:
            _ = (url, kwargs)
            raise RuntimeError("network failure")

    monkeypatch.setattr("ai_visibility.analysis.crawler_simulation.httpx.AsyncClient", lambda *a, **k: _Client())

    result = await crawler_simulation._check_js_rendering("https://example.com")
    assert result["js_required"] is False
    assert "fetch_failed" in cast(list[str], result["signals"])
    assert result["text_length"] == 0


@pytest.mark.asyncio
async def test_simulate_crawlers_includes_js_rendering_field(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Client:
        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            return None

        async def get(self, url: str, **kwargs: Any) -> _DummyResponse:
            _ = kwargs
            if url.endswith("/robots.txt"):
                return _DummyResponse(status_code=200, text="User-agent: *\nAllow: /")
            return _DummyResponse(
                status_code=200, text="<html><body><div id='root'></div><script></script></body></html>"
            )

    monkeypatch.setattr("ai_visibility.analysis.crawler_simulation.httpx.AsyncClient", lambda *a, **k: _Client())

    results = await crawler_simulation.simulate_crawlers("https://example.com")
    assert results
    for item in results:
        assert "js_rendering" in item
        assert isinstance(item["js_rendering"], dict)
        assert "js_required" in item["js_rendering"]
        assert "signals" in item["js_rendering"]
        assert "text_length" in item["js_rendering"]
