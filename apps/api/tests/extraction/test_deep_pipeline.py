from typing import cast

from ai_visibility.extraction.pipeline import ExtractionPipeline


def make_text(body: str) -> str:
    suffix = " Additional context to ensure parser input is long enough for non-fallback execution."
    return f"{body}{suffix}."


def test_extract_multiple_brand_names_finds_all_mentions() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara", "Acme", "Globex"])
    text = make_text("Solara competes with Acme while Globex is also in the shortlist")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert all(mention.mentioned for mention in result.mentions)
    assert [mention.brand_name for mention in result.mentions] == ["Solara", "Acme", "Globex"]


def test_extract_is_case_insensitive_for_brand_matching() -> None:
    pipeline = ExtractionPipeline(brand_names=["solara", "SOLARA", "SoLaRa"])
    text = make_text("We evaluated Solara as a platform")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert [mention.mentioned for mention in result.mentions] == [True, True, True]


def test_extract_multiple_brand_occurrences_tracks_first_position() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    text = make_text("Before Solara appears again Solara and then Solara once more")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert len(result.mentions) == 1
    assert result.mentions[0].mentioned is True
    assert result.mentions[0].position_in_response == text.lower().find("solara")


def test_extract_no_brand_mentions_returns_unmentioned_entries() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara", "Acme"])
    text = make_text("This answer discusses general project management software only")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert [mention.mentioned for mention in result.mentions] == [False, False]
    assert [mention.sentiment for mention in result.mentions] == ["unknown", "unknown"]


def test_extract_very_short_text_without_terminal_punctuation_falls_back() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])

    result = pipeline.extract("Solara maybe")

    assert result.parser_status == "fallback"
    assert result.error_message == "Input appears truncated or malformed"
    assert result.mentions == []


def test_extract_very_long_text_over_5000_chars_preserves_position() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    prefix = "x" * 5200
    text = f"{prefix} Solara is included here with a trailing sentence that ends properly."

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert result.mentions[0].mentioned is True
    assert result.mentions[0].position_in_response == text.lower().find("solara")


def test_extract_unicode_text_with_brand_name() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    text = make_text("Resena: Solara funciona bien para equipos internacionales con senales claras")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert result.mentions[0].mentioned is True


def test_extract_with_emoji_does_not_crash() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    text = make_text("We like Solara because deployment is smooth 🚀 and onboarding is simple")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert result.mentions[0].mentioned is True


def test_extract_empty_string_handles_gracefully_as_fallback() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])

    result = pipeline.extract("")

    assert result.parser_status == "fallback"
    assert result.error_message == "Input appears truncated or malformed"


def test_extract_none_brand_names_handles_gracefully() -> None:
    pipeline = ExtractionPipeline(brand_names=cast(list[str], cast(object, None)))
    text = make_text("Solara appears in this response with enough content for parsing path")

    result = pipeline.extract(text)

    assert result.parser_status == "fallback"
    assert result.error_message is not None


def test_url_extraction_standard_http_https_urls() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    text = make_text("Read http://example.com and https://docs.solara.ai/setup for more context about Solara")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert [citation.url for citation in result.citations] == ["http://example.com", "https://docs.solara.ai/setup"]
    assert [citation.status for citation in result.citations] == ["found", "found"]


def test_url_extraction_with_query_params_and_fragment() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    url = "https://docs.solara.ai/path?source=test&x=1#section"
    text = make_text(f"A detailed source is {url} and Solara is referenced nearby")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert result.citations[0].url == url
    assert result.citations[0].domain == "docs.solara.ai"


def test_url_extraction_no_urls_returns_no_citation_status() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    text = make_text("Solara is recommended based on feature coverage but there are no direct links")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert len(result.citations) == 1
    assert result.citations[0].status == "no_citation"


def test_url_extraction_multiple_urls_extracts_all() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    text = make_text(
        "Sources: https://a.example.com/x, https://b.example.com/y, and https://c.example.com/z while mentioning Solara"
    )

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert len(result.citations) == 3
    assert [citation.domain for citation in result.citations] == ["a.example.com", "b.example.com", "c.example.com"]


def test_sentiment_positive_keywords_results_in_positive() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    text = make_text("Solara is the best and most trusted choice for teams")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert result.mentions[0].sentiment == "positive"


def test_sentiment_negative_keywords_results_in_negative() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    text = make_text("Solara can be unreliable and expensive for this specific use case")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert result.mentions[0].sentiment == "negative"


def test_sentiment_no_keywords_results_in_neutral_for_non_empty_snippet() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    text = make_text("Solara appears in a factual list of vendors without adjectives")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert result.mentions[0].sentiment == "neutral"


def test_sentiment_mixed_keywords_tie_results_in_neutral() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    text = make_text("Solara is great but also expensive for some teams")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert result.mentions[0].sentiment == "neutral"


def test_context_snippet_has_approximately_200_character_window() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    text = f"{'a' * 300} Solara {'b' * 300}."

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    snippet = result.mentions[0].context_snippet
    assert snippet is not None
    assert len(snippet) <= 100 + len("Solara") + 100


def test_context_snippet_when_brand_at_start_is_trimmed_correctly() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    text = make_text("Solara is listed first and followed by supporting discussion")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert result.mentions[0].context_snippet is not None
    assert result.mentions[0].position_in_response == 0


def test_context_snippet_when_brand_at_end_is_trimmed_correctly() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    text = (
        "This response includes enough lead-in content to avoid malformed checks and place the brand at the end "
        "for boundary validation with Solara."
    )

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert result.mentions[0].context_snippet is not None
    assert result.mentions[0].position_in_response == text.lower().find("solara")


def test_position_in_response_tracks_first_mention_index() -> None:
    pipeline = ExtractionPipeline(brand_names=["Solara"])
    text = make_text("aaa Solara bbb Solara ccc")

    result = pipeline.extract(text)

    assert result.parser_status == "parsed"
    assert result.mentions[0].position_in_response == 4
