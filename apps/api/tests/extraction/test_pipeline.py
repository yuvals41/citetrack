import json
import subprocess
import sys
from pathlib import Path
from typing import cast

from ai_visibility.extraction.models import CitationResult, MentionResult
from ai_visibility.extraction.pipeline import ExtractionPipeline


def test_extract_mentions_from_clean_response() -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "provider_response.json"
    payload = cast(dict[str, str], json.loads(fixture_path.read_text(encoding="utf-8")))
    text = payload["text"]

    pipeline = ExtractionPipeline(brand_names=["Acme Corp"])
    result = pipeline.extract(text)

    assert len(result.mentions) >= 1
    assert any(mention.brand_name == "Acme Corp" and mention.mentioned for mention in result.mentions)


def test_mention_result_has_required_fields() -> None:
    mention = MentionResult(
        brand_name="Acme Corp",
        mentioned=True,
        sentiment="positive",
        context_snippet="Acme Corp is one of the best options.",
        position_in_response=10,
    )

    assert mention.brand_name == "Acme Corp"
    assert mention.mentioned is True
    assert mention.sentiment in {"positive", "neutral", "negative", "unknown"}
    assert mention.context_snippet is not None
    assert isinstance(mention.position_in_response, int)


def test_extract_citations_from_response() -> None:
    text = "Acme Corp is trusted. More info at https://acmecorp.com and https://docs.acmecorp.com/getting-started."
    pipeline = ExtractionPipeline(brand_names=["Acme Corp"])
    result = pipeline.extract(text)

    assert len(result.citations) >= 1
    for citation in result.citations:
        assert isinstance(citation, CitationResult)
        assert citation.url is not None
        assert citation.domain is not None
        assert citation.status == "found"


def test_no_citation_when_no_urls() -> None:
    text = "Acme Corp is a project management platform."
    pipeline = ExtractionPipeline(brand_names=["Acme Corp"])
    result = pipeline.extract(text)

    assert len(result.citations) == 1
    assert result.citations[0].status == "no_citation"


def test_parser_status_parsed_on_success() -> None:
    text = "Acme Corp is a leading platform with great support."
    pipeline = ExtractionPipeline(brand_names=["Acme Corp"])
    result = pipeline.extract(text)

    assert result.parser_status == "parsed"


def test_parser_status_fallback_on_malformed() -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "malformed_response.txt"
    malformed_text = fixture_path.read_text(encoding="utf-8")

    pipeline = ExtractionPipeline(brand_names=["Acme Corp"])
    result = pipeline.extract(malformed_text)

    assert result.parser_status == "fallback"
    assert result.raw_text == malformed_text


def test_parse_fixture_cli_command() -> None:
    fixture_path = Path("tests/fixtures/provider_response.json")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_visibility.cli",
            "parse-fixture",
            str(fixture_path),
            "--format",
            "json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"stderr: {result.stderr}"
    output = cast(dict[str, object], json.loads(result.stdout))
    assert isinstance(output.get("mentions"), list)
    assert output.get("parser_status") == "parsed"


def test_parse_fixture_malformed_cli() -> None:
    fixture_path = Path("tests/fixtures/malformed_response.txt")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_visibility.cli",
            "parse-fixture",
            str(fixture_path),
            "--format",
            "json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"stderr: {result.stderr}"
    output = cast(dict[str, object], json.loads(result.stdout))
    assert output.get("parser_status") in ("fallback", "failed")
