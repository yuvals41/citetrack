import pytest
from typing import Mapping


class _MockResponse:
    _payload: Mapping[str, object]

    def __init__(self, payload: Mapping[str, object]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Mapping[str, object]:
        return self._payload


class _MockAsyncClient:
    _payload: Mapping[str, object]
    _recorder: dict[str, object]

    def __init__(self, payload: Mapping[str, object], recorder: dict[str, object]) -> None:
        self._payload = payload
        self._recorder = recorder

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    async def post(self, url: str, headers: dict[str, str], json: list[dict[str, object]]) -> _MockResponse:
        self._recorder["url"] = url
        self._recorder["headers"] = headers
        self._recorder["json"] = json
        return _MockResponse(self._payload)


@pytest.mark.asyncio
async def test_get_top_pages_uses_endpoint_and_returns_results(monkeypatch: pytest.MonkeyPatch) -> None:
    from ai_visibility.integrations import dataforseo_mentions

    recorder: dict[str, object] = {}
    payload = {
        "tasks": [
            {
                "result": [
                    {"url": "https://example.com/a", "mention_count": 3},
                    {"url": "https://example.com/b", "mention_count": 2},
                ]
            }
        ]
    }

    def _client_factory(timeout: float) -> _MockAsyncClient:
        recorder["timeout"] = timeout
        return _MockAsyncClient(payload, recorder)

    monkeypatch.setattr(dataforseo_mentions.httpx, "AsyncClient", _client_factory)

    result = await dataforseo_mentions.get_top_pages("solara ai")

    assert len(result) == 2
    assert str(recorder["url"]).endswith("/top_pages/live")
    headers = recorder["headers"]
    assert isinstance(headers, dict)
    assert headers["Authorization"] == dataforseo_mentions.DATAFORSEO_AUTH
    sent_payload = recorder["json"]
    assert isinstance(sent_payload, list)
    assert sent_payload[0]["target"][0]["keyword"] == "solara ai"


@pytest.mark.asyncio
async def test_get_top_pages_empty_tasks_returns_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
    from ai_visibility.integrations import dataforseo_mentions

    recorder: dict[str, object] = {}
    payload = {"tasks": []}

    def _client_factory(timeout: float) -> _MockAsyncClient:
        recorder["timeout"] = timeout
        return _MockAsyncClient(payload, recorder)

    monkeypatch.setattr(dataforseo_mentions.httpx, "AsyncClient", _client_factory)

    result = await dataforseo_mentions.get_top_pages("solara ai")
    assert result == []


@pytest.mark.asyncio
async def test_generate_dashboard_pdf_returns_pdf_bytes() -> None:
    from ai_visibility.export.pdf_export import generate_dashboard_pdf

    data: list[dict[str, object]] = [
        {
            "provider": "openai",
            "status": "completed",
            "model": "gpt-5.4",
            "created_at": "2026-03-20 12:00",
            "visibility_score": "72%",
            "citation_coverage": "39%",
            "position": "2.1",
            "sentiment": "0.62",
        }
    ]

    pdf_bytes = await generate_dashboard_pdf(data, "solara")
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 100


@pytest.mark.asyncio
async def test_generate_responses_pdf_returns_pdf_bytes() -> None:
    from ai_visibility.export.pdf_export import generate_responses_pdf

    data: list[dict[str, object]] = [
        {
            "provider": "openai",
            "prompt_text": "Who are the top AI visibility tools?",
            "mention_type": "citation",
            "citation_url": "https://solaraai.com",
        }
    ]

    pdf_bytes = await generate_responses_pdf(data, "solara")
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 100


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["dashboard", "responses"])
async def test_generate_pdf_with_empty_data(kind: str) -> None:
    from ai_visibility.export.pdf_export import generate_dashboard_pdf, generate_responses_pdf

    if kind == "dashboard":
        pdf_bytes = await generate_dashboard_pdf([], "empty-workspace")
    else:
        pdf_bytes = await generate_responses_pdf([], "empty-workspace")

    assert pdf_bytes.startswith(b"%PDF")
