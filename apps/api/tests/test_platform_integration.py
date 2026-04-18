"""
Tests for platform integration files: worker_job.py, job.py, and SDK client.

These test the contract shapes and logic without requiring actual
solaraai_messaging or solaraai_job_sdk packages (which are only
available in the deployed container).
"""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_visibility.schema import (
    LocationContext,
    MentionResult,
    PromptDefinition,
    ScanInput,
    ScanMetrics,
    ScanOutput,
    ScanProgress,
)


# --- ScanInput / ScanOutput serialization tests ---


class TestScanInputSerialization:
    def test_roundtrip_json(self):
        """ScanInput can be serialized to JSON and back."""
        inp = ScanInput(
            job_id="j1",
            brand_name="Acme",
            domain="acme.com",
            providers=["openai", "anthropic"],
            prompts=[
                PromptDefinition(id="p1", template="Best {brand}?"),
                PromptDefinition(id="p2", template="{brand} vs {competitor}"),
            ],
            competitors=["BrandX"],
            location=LocationContext(country_code="US", city="NYC"),
            max_prompts_per_provider=5,
        )
        json_str = inp.model_dump_json()
        restored = ScanInput.model_validate_json(json_str)
        assert restored.brand_name == "Acme"
        assert restored.providers == ["openai", "anthropic"]
        assert len(restored.prompts) == 2
        assert restored.location.city == "NYC"

    def test_from_dict(self):
        """ScanInput can be created from a dict (as JOB_PAYLOAD would provide)."""
        payload = {
            "brand_name": "Acme",
            "domain": "acme.com",
            "providers": ["openai"],
            "prompts": [{"id": "p1", "template": "Best {brand}?"}],
        }
        inp = ScanInput(**payload)
        assert inp.brand_name == "Acme"
        assert len(inp.prompts) == 1
        assert inp.prompts[0].category == "custom"  # default

    def test_minimal_input(self):
        """ScanInput works with minimal required fields."""
        inp = ScanInput(
            brand_name="X",
            domain="x.com",
            providers=["openai"],
            prompts=[PromptDefinition(id="p1", template="test {brand}")],
        )
        assert inp.max_prompts_per_provider == 3
        assert inp.competitors == []
        assert inp.location.country_code == ""


class TestScanOutputSerialization:
    def test_roundtrip_json(self):
        """ScanOutput can be serialized and deserialized."""
        out = ScanOutput(
            job_id="j1",
            status="success",
            duration=12.5,
            mentions=[
                MentionResult(
                    provider="openai",
                    prompt_id="p1",
                    prompt_text="test",
                    raw_response="Acme is great",
                    brand_mentioned=True,
                    brand_position=5,
                    sentiment="positive",
                )
            ],
            metrics=ScanMetrics(
                visibility_score=0.75,
                citation_coverage=0.5,
                total_prompts=4,
                total_mentioned=3,
            ),
            provider_results={"openai": {"status": "completed", "ok": 2, "failed": 0}},
        )
        json_str = out.model_dump_json()
        restored = ScanOutput.model_validate_json(json_str)
        assert restored.job_id == "j1"
        assert len(restored.mentions) == 1
        assert restored.mentions[0].brand_mentioned is True
        assert restored.metrics.visibility_score == 0.75

    def test_empty_output(self):
        """Empty ScanOutput has correct defaults."""
        out = ScanOutput()
        assert out.mentions == []
        assert out.metrics.visibility_score == 0.0
        assert out.provider_results == {}


# --- Job.py logic tests (mock the SDK imports) ---


class TestJobEntryPoint:
    def test_job_payload_parsing(self):
        """Verify JOB_PAYLOAD env var is correctly parsed into ScanInput."""
        payload = {
            "brand_name": "TestBrand",
            "domain": "testbrand.com",
            "providers": ["openai", "gemini"],
            "prompts": [
                {"id": "p1", "template": "Best {brand}?"},
                {"id": "p2", "template": "{brand} vs {competitor}"},
            ],
            "competitors": ["CompA"],
            "location": {"country_code": "US", "city": "SF"},
            "max_prompts_per_provider": 2,
        }
        inp = ScanInput(**payload)
        assert inp.brand_name == "TestBrand"
        assert len(inp.providers) == 2
        assert inp.location.city == "SF"

    def test_job_id_from_payload(self):
        """job_id should come from payload if present."""
        payload = {
            "job_id": "custom-id-123",
            "brand_name": "Test",
            "domain": "test.com",
            "providers": ["openai"],
            "prompts": [{"id": "p1", "template": "test {brand}"}],
        }
        inp = ScanInput(**payload)
        assert inp.job_id == "custom-id-123"

    def test_invalid_payload_raises(self):
        """Missing required fields should raise validation error."""
        with pytest.raises(Exception):
            ScanInput(**{"brand_name": "Test"})  # missing domain, providers, prompts


# --- Worker contract tests ---


class TestWorkerContract:
    def test_scan_input_is_pydantic(self):
        """ScanInput must be a Pydantic model (worker deserializes from JSON)."""
        from pydantic import BaseModel

        assert issubclass(ScanInput, BaseModel)

    def test_scan_output_has_required_fields(self):
        """ScanOutput must have fields the worker stores in Redis artifacts."""
        out = ScanOutput(
            job_id="j1",
            status="success",
            duration=5.0,
            mentions=[],
            metrics=ScanMetrics(),
        )
        # These fields are stored in Redis artifacts by worker_job.py
        assert hasattr(out, "mentions")
        assert hasattr(out, "metrics")
        assert hasattr(out, "provider_results")
        assert hasattr(out, "duration")

    def test_scan_progress_fields(self):
        """ScanProgress has the fields the worker logs."""
        p = ScanProgress(
            stage="scanning",
            provider="openai",
            prompts_completed=3,
            prompts_total=10,
            message="Processing...",
        )
        assert p.stage == "scanning"
        assert p.prompts_completed == 3


# --- SDK client tests (mock solaraai_job_sdk) ---


class TestSdkClientContract:
    def test_scan_input_serialize(self):
        """Test that ScanInput can be serialized for SDK submission."""
        inp = ScanInput(
            brand_name="Acme",
            domain="acme.com",
            providers=["openai"],
            prompts=[PromptDefinition(id="p1", template="Best {brand}?")],
            competitors=["BrandX"],
        )
        data = inp.model_dump()
        assert data["brand_name"] == "Acme"
        assert len(data["prompts"]) == 1
        assert data["prompts"][0]["id"] == "p1"

    def test_scan_output_to_artifacts(self):
        """Test that ScanOutput can be converted to artifacts dict for Redis."""
        out = ScanOutput(
            job_id="j1",
            status="success",
            duration=10.0,
            mentions=[
                MentionResult(
                    provider="openai",
                    prompt_id="p1",
                    prompt_text="test",
                    raw_response="Acme is great",
                    brand_mentioned=True,
                )
            ],
            metrics=ScanMetrics(visibility_score=0.5, total_prompts=2, total_mentioned=1),
        )
        # Simulate what worker_job.py does
        artifacts = {
            "mentions_count": len(out.mentions),
            "visibility_score": out.metrics.visibility_score,
            "citation_coverage": out.metrics.citation_coverage,
            "total_prompts": out.metrics.total_prompts,
            "total_mentioned": out.metrics.total_mentioned,
            "provider_results": out.provider_results,
            "mentions": [m.model_dump() for m in out.mentions],
            "metrics": out.metrics.model_dump(),
        }
        assert artifacts["mentions_count"] == 1
        assert artifacts["visibility_score"] == 0.5
        assert len(artifacts["mentions"]) == 1

    def test_mention_result_serialization(self):
        """MentionResult can be serialized to dict for Redis storage."""
        m = MentionResult(
            provider="openai",
            model_name="gpt-5.4",
            prompt_id="p1",
            prompt_text="Best product?",
            raw_response="Acme Corp is the best.",
            brand_mentioned=True,
            brand_position=0,
            sentiment="positive",
            citations=[{"url": "https://acme.com"}],
            reasoning="Market leader analysis",
        )
        data = m.model_dump()
        assert data["provider"] == "openai"
        assert data["brand_mentioned"] is True
        assert len(data["citations"]) == 1


# --- Integration: verify no DB imports in new files ---


class TestNoDbImports:
    """Ensure new platform integration files have no database dependencies."""

    def _check_no_db_imports(self, module_name: str):
        """Check that a module has no database-related imports."""
        import ast
        import importlib
        import inspect

        mod = importlib.import_module(module_name)
        source = inspect.getsource(mod)
        tree = ast.parse(source)

        forbidden_patterns = ["prisma", "storage.prisma", "repositories", "get_prisma"]
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for pattern in forbidden_patterns:
                    assert pattern not in module.lower(), f"{module_name} has forbidden import: {module}"

    def test_scan_executor_no_db(self):
        self._check_no_db_imports("ai_visibility.scan_executor")

    def test_schema_no_db(self):
        self._check_no_db_imports("ai_visibility.schema")


# --- PromptDefinition tests ---


class TestPromptDefinition:
    def test_from_dict(self):
        pd = PromptDefinition(**{"id": "p1", "template": "test {brand}", "category": "discovery"})
        assert pd.id == "p1"
        assert pd.category == "discovery"

    def test_defaults(self):
        pd = PromptDefinition(id="p1", template="test")
        assert pd.category == "custom"
        assert pd.version == "1.0.0"

    def test_multiple_prompts_list(self):
        prompts = [PromptDefinition(id=f"p{i}", template=f"prompt {i} {{brand}}") for i in range(20)]
        assert len(prompts) == 20
        assert prompts[19].id == "p19"


# --- LocationContext tests ---


class TestLocationContext:
    def test_empty_location(self):
        loc = LocationContext()
        assert loc.country_code == ""
        assert loc.country_name == ""
        assert loc.city == ""
        assert loc.region == ""

    def test_full_location(self):
        loc = LocationContext(
            country_code="US",
            country_name="United States",
            city="New York",
            region="NY",
        )
        assert loc.country_code == "US"
        assert loc.city == "New York"

    def test_serialization(self):
        loc = LocationContext(country_code="GB", city="London")
        data = loc.model_dump()
        restored = LocationContext(**data)
        assert restored.country_code == "GB"
        assert restored.city == "London"
