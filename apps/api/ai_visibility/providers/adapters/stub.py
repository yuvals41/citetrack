from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, override

from .base import AdapterResult, ScanAdapter

if TYPE_CHECKING:
    from ai_visibility.providers.gateway import LocationContext
    from ai_visibility.runs.scan_strategy import ProviderConfig


class StubAdapter(ScanAdapter):
    _result: AdapterResult | None
    _sequence: list[AdapterResult]
    calls: list[tuple[str, str, ProviderConfig, LocationContext | None]]

    def __init__(
        self,
        result: AdapterResult | None = None,
        *,
        sequence: Sequence[AdapterResult] | None = None,
    ) -> None:
        self._result = result
        self._sequence = list(sequence or [])
        self.calls = []

    @override
    def execute(
        self,
        prompt_text: str,
        workspace_slug: str,
        strategy_config: ProviderConfig,
        location: LocationContext | None = None,
    ) -> AdapterResult:
        self.calls.append((prompt_text, workspace_slug, strategy_config, location))
        if self._sequence:
            return self._sequence.pop(0)
        if self._result is not None:
            return self._result
        return AdapterResult(
            raw_response="stub response",
            citations=[],
            provider=strategy_config.provider,
            model_name=strategy_config.model_name,
            model_version=strategy_config.model_name,
            strategy_version="v1",
        )
