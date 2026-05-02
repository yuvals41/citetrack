from __future__ import annotations

import re
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, cast

from typing_extensions import override

from ai_visibility.providers.gateway import ProviderGateway, ProviderResponse

from .base import AdapterResult, ScanAdapter

if TYPE_CHECKING:
    from ai_visibility.providers.gateway import LocationContext
    from ai_visibility.runs.scan_strategy import ProviderConfig

URL_PATTERN = re.compile(r"https?://[^\s\)\]\,\"\']+")


class GatewayScanAdapter(ScanAdapter):
    gateway: ProviderGateway
    run_async: Callable[[Coroutine[object, object, ProviderResponse]], ProviderResponse]
    strategy_version: str

    def __init__(
        self,
        gateway: ProviderGateway,
        run_async: Callable[[Coroutine[object, object, ProviderResponse]], ProviderResponse],
        *,
        strategy_version: str,
    ) -> None:
        self.gateway = gateway
        self.run_async = run_async
        self.strategy_version = strategy_version

    @override
    def execute(
        self,
        prompt_text: str,
        workspace_slug: str,
        strategy_config: ProviderConfig,
        location: LocationContext | None = None,
    ) -> AdapterResult:
        _ = workspace_slug
        _ = strategy_config
        response = self.run_async(self.gateway.execute_prompt(prompt_text, {}, location=location))
        citations: list[dict[str, object]] = [
            {"url": cast(object, url)} for url in cast(list[str], URL_PATTERN.findall(response.content))
        ]
        return AdapterResult(
            raw_response=response.content,
            citations=citations,
            provider=response.provider,
            model_name=response.model,
            model_version=response.model,
            strategy_version=self.strategy_version,
        )
