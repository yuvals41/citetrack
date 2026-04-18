from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from ai_visibility.providers.gateway import LocationContext
    from ai_visibility.runs.scan_strategy import ProviderConfig


class AdapterResult(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    raw_response: str = Field(..., min_length=1)
    citations: list[dict[str, object]] = Field(default_factory=list)
    provider: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)
    model_version: str = Field(..., min_length=1)
    strategy_version: str = Field(..., min_length=1)
    reasoning: str = ""


class ScanAdapter(ABC):
    @abstractmethod
    def execute(
        self,
        prompt_text: str,
        workspace_slug: str,
        strategy_config: ProviderConfig,
        location: LocationContext | None = None,
    ) -> AdapterResult:
        raise NotImplementedError
