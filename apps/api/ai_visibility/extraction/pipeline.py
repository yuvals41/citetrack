import re
from typing import Literal, cast
from urllib.parse import urlparse

from loguru import logger
from ai_visibility.extraction.models import CitationResult, MentionResult, ParseResult

URL_PATTERN = re.compile(r"https?://[^\s\)\]\,\"\']+")
Sentiment = Literal["positive", "neutral", "negative", "unknown"]


class ExtractionPipeline:
    def __init__(self, brand_names: list[str]):
        self.brand_names: list[str] = brand_names

    def extract(self, raw_text: str) -> ParseResult:
        try:
            if self._is_malformed(raw_text):
                return ParseResult(
                    parser_status="fallback",
                    raw_text=raw_text,
                    error_message="Input appears truncated or malformed",
                )

            mentions = self._extract_mentions(raw_text)
            citations = self._extract_citations(raw_text)
            return ParseResult(
                parser_status="parsed",
                mentions=mentions,
                citations=citations,
                raw_text=raw_text,
            )
        except Exception as exc:
            return ParseResult(
                parser_status="fallback",
                raw_text=raw_text,
                error_message=str(exc),
            )

    def _extract_mentions(self, text: str) -> list[MentionResult]:
        results: list[MentionResult] = []
        text_lower = text.lower()
        for brand in self.brand_names:
            brand_lower = brand.lower()
            pos = text_lower.find(brand_lower)
            mentioned = pos >= 0
            snippet = None
            if mentioned:
                start = max(0, pos - 100)
                end = min(len(text), pos + len(brand) + 100)
                snippet = text[start:end].strip()
            sentiment = self._detect_sentiment(snippet or "") if mentioned else "unknown"
            results.append(
                MentionResult(
                    brand_name=brand,
                    mentioned=mentioned,
                    sentiment=sentiment,
                    context_snippet=snippet,
                    position_in_response=pos if mentioned else None,
                )
            )
        return results

    def _extract_citations(self, text: str) -> list[CitationResult]:
        urls = cast(list[str], URL_PATTERN.findall(text))
        if not urls:
            return [CitationResult(status="no_citation")]
        results: list[CitationResult] = []
        for url in urls:
            try:
                domain = str(urlparse(url).netloc)
            except Exception as e:
                logger.debug(f"[pipeline] {type(e).__name__}: {e}")
                domain = None
            results.append(CitationResult(url=url, domain=domain, status="found"))
        return results

    def _detect_sentiment(self, snippet: str) -> Sentiment:
        snippet_lower = snippet.lower()
        positive_words = {
            "best",
            "great",
            "excellent",
            "top",
            "leading",
            "recommended",
            "popular",
            "trusted",
        }
        negative_words = {"worst", "bad", "poor", "avoid", "terrible", "unreliable", "expensive"}
        pos_count = sum(1 for word in positive_words if word in snippet_lower)
        neg_count = sum(1 for word in negative_words if word in snippet_lower)
        if pos_count > neg_count:
            return "positive"
        if neg_count > pos_count:
            return "negative"
        if pos_count == neg_count and pos_count > 0:
            return "neutral"
        return "neutral" if snippet_lower else "unknown"

    def _is_malformed(self, raw_text: str) -> bool:
        stripped = raw_text.strip()
        if not stripped:
            return True
        if len(stripped) < 50 and stripped[-1] not in {".", "!", "?"}:
            return True
        return False
