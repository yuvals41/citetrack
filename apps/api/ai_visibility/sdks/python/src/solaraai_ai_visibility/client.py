"""
SDK client for AI Visibility scan jobs.

Follows the solaraai-job-sdk BaseJobClient pattern exactly.
See: /tmp/cgi/sdks/python/src/solaraai_text_to_image/client.py
"""

from typing import Any

from solaraai_job_sdk import (
    ArtifactStore,
    BaseJobClient,
    BaseJobResult,
    JobProvider,
    StatusStore,
)

from .types import ScanInput, ScanOutput, ScanProgress


class ScanClient(BaseJobClient[ScanInput, ScanOutput, ScanProgress]):
    """Client for submitting and tracking AI Visibility scan jobs."""

    def __init__(
        self,
        provider: JobProvider,
        status_store: StatusStore[ScanProgress],
        artifact_store: ArtifactStore | None = None,
    ):
        super().__init__(
            provider=provider,
            status_store=status_store,
            artifact_store=artifact_store,
        )

    def validate_input(self, input_data: ScanInput) -> ScanInput:
        """Validate scan input before submission."""
        if not input_data.brand_name or not input_data.brand_name.strip():
            from solaraai_job_sdk import ValidationError

            raise ValidationError(field="brand_name", message="brand_name cannot be empty")
        if not input_data.domain or not input_data.domain.strip():
            from solaraai_job_sdk import ValidationError

            raise ValidationError(field="domain", message="domain cannot be empty")
        if not input_data.providers:
            from solaraai_job_sdk import ValidationError

            raise ValidationError(field="providers", message="providers list cannot be empty")
        if not input_data.prompts:
            from solaraai_job_sdk import ValidationError

            raise ValidationError(field="prompts", message="prompts list cannot be empty")
        return input_data

    def serialize_input(self, input_data: ScanInput) -> dict[str, Any]:
        """Serialize scan input for job submission."""
        data: dict[str, Any] = {
            "brand_name": input_data.brand_name,
            "domain": input_data.domain,
            "providers": input_data.providers,
            "prompts": [p.model_dump() for p in input_data.prompts],
            "max_prompts_per_provider": input_data.max_prompts_per_provider,
        }
        if input_data.competitors:
            data["competitors"] = input_data.competitors
        if input_data.location:
            data["location"] = input_data.location.model_dump()
        if input_data.job_id:
            data["job_id"] = input_data.job_id
        if input_data.metadata:
            data["metadata"] = input_data.metadata
        return data

    def deserialize_result(self, data: BaseJobResult) -> ScanOutput:
        """Deserialize job result into ScanOutput."""
        raw = data.artifacts or {}
        return ScanOutput(
            job_id=data.job_id,
            status=data.status,
            error=data.error,
            duration=data.duration,
            mentions=raw.get("mentions", []),
            metrics=raw.get("metrics", {}),
            provider_results=raw.get("provider_results", {}),
        )

    def deserialize_progress(self, data: dict[str, Any]) -> ScanProgress:
        """Deserialize progress event."""
        return ScanProgress(
            stage=data.get("stage", "queued"),
            provider=data.get("provider"),
            prompts_completed=data.get("prompts_completed", 0),
            prompts_total=data.get("prompts_total", 0),
            message=data.get("message"),
        )
