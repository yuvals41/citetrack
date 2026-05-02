"""Tests for the stateless scan executor."""

from unittest.mock import MagicMock, patch

import pytest

from ai_visibility.providers.adapters.base import AdapterResult
from ai_visibility.scan_executor import execute_scan
from ai_visibility.schema import (
    LocationContext,
    MentionResult,
    PromptDefinition,
    ScanInput,
    ScanMetrics,
    ScanOutput,
    ScanProgress,
)

# --- Helper fixtures ---


def _make_adapter_result(
    raw_response: str = "Test response mentioning Acme Corp as a top provider.",
    provider: str = "openai",
    model_name: str = "gpt-5.4",
    citations: list | None = None,
    reasoning: str = "",
) -> AdapterResult:
    return AdapterResult(
        raw_response=raw_response,
        citations=citations or [],
        provider=provider,
        model_name=model_name,
        model_version=model_name,
        strategy_version="v1",
        reasoning=reasoning,
    )


def _make_stub_adapter(result: AdapterResult | None = None) -> MagicMock:
    adapter = MagicMock()
    adapter.execute.return_value = result or _make_adapter_result()
    return adapter


def _make_scan_input(
    brand_name: str = "Acme Corp",
    domain: str = "acme.com",
    providers: list[str] | None = None,
    prompts: list[PromptDefinition] | None = None,
    competitors: list[str] | None = None,
    job_id: str = "test-job-1",
) -> ScanInput:
    return ScanInput(
        job_id=job_id,
        brand_name=brand_name,
        domain=domain,
        providers=providers or ["openai"],
        prompts=prompts
        or [
            PromptDefinition(id="p1", template="Best {brand} in the market?"),
            PromptDefinition(id="p2", template="Compare {brand} vs {competitor}"),
        ],
        competitors=competitors or ["BrandX"],
        max_prompts_per_provider=3,
    )


# --- Tests for execute_scan ---


class TestExecuteScan:
    @pytest.mark.asyncio
    async def test_basic_scan_with_stub_adapter(self):
        """Test execute_scan with a mocked adapter that returns a positive mention."""
        scan_input = _make_scan_input()
        stub_adapter = _make_stub_adapter()

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"chatgpt": stub_adapter, "openai": stub_adapter},
        ):
            output = await execute_scan(scan_input)

        assert isinstance(output, ScanOutput)
        assert isinstance(output.job_id, str)
        assert output.status == "success"
        assert len(output.mentions) > 0
        assert output.duration >= 0  # May be 0.0 with fast mocks

    @pytest.mark.asyncio
    async def test_scan_collects_mentions(self):
        """Test that mentions from adapter results are properly collected."""
        stub_adapter = _make_stub_adapter(
            _make_adapter_result(raw_response="Acme Corp is the best choice for enterprise solutions.")
        )
        scan_input = _make_scan_input(
            prompts=[
                PromptDefinition(id="p1", template="Best {brand} in market?"),
            ]
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"chatgpt": stub_adapter, "openai": stub_adapter},
        ):
            output = await execute_scan(scan_input)

        assert len(output.mentions) == 1
        mention = output.mentions[0]
        assert mention.provider == "openai"
        assert mention.brand_mentioned is True
        assert mention.prompt_id == "p1"

    @pytest.mark.asyncio
    async def test_scan_with_no_mentions(self):
        """Test scan where brand is not mentioned."""
        stub_adapter = _make_stub_adapter(
            _make_adapter_result(raw_response="There are many competitors in the market.")
        )
        scan_input = _make_scan_input(
            prompts=[
                PromptDefinition(id="p1", template="Best {brand} in market?"),
            ]
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"chatgpt": stub_adapter, "openai": stub_adapter},
        ):
            output = await execute_scan(scan_input)

        assert len(output.mentions) == 1
        assert output.mentions[0].brand_mentioned is False

    @pytest.mark.asyncio
    async def test_scan_with_adapter_failure(self):
        """Test scan where the adapter raises an exception."""
        stub_adapter = MagicMock()
        stub_adapter.execute.side_effect = Exception("Provider unavailable")
        scan_input = _make_scan_input(
            prompts=[
                PromptDefinition(id="p1", template="Best {brand} in market?"),
            ]
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"chatgpt": stub_adapter, "openai": stub_adapter},
        ):
            output = await execute_scan(scan_input)

        # Should not crash — returns empty results
        assert output.status == "failed"
        assert len(output.mentions) == 0

    @pytest.mark.asyncio
    async def test_scan_calls_progress_callback(self):
        """Test that progress callback is invoked during scan."""
        progress_events: list[ScanProgress] = []

        def on_progress(p: ScanProgress) -> None:
            progress_events.append(p)

        stub_adapter = _make_stub_adapter()
        scan_input = _make_scan_input(
            prompts=[
                PromptDefinition(id="p1", template="Best {brand} in market?"),
            ]
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"chatgpt": stub_adapter, "openai": stub_adapter},
        ):
            await execute_scan(scan_input, on_progress=on_progress)

        assert len(progress_events) > 0
        stages = [p.stage for p in progress_events]
        assert "scanning" in stages
        assert "complete" in stages

    @pytest.mark.asyncio
    async def test_scan_multiple_providers(self):
        """Test scan with multiple providers."""
        openai_adapter = _make_stub_adapter(_make_adapter_result(provider="openai", raw_response="Acme Corp is great."))
        anthropic_adapter = _make_stub_adapter(
            _make_adapter_result(
                provider="anthropic", model_name="claude-sonnet-4-6", raw_response="I recommend Acme Corp."
            )
        )

        scan_input = _make_scan_input(
            providers=["openai", "anthropic"],
            prompts=[PromptDefinition(id="p1", template="Best {brand}?")],
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={
                "chatgpt": openai_adapter,
                "openai": openai_adapter,
                "anthropic": anthropic_adapter,
            },
        ):
            output = await execute_scan(scan_input)

        assert len(output.mentions) == 2
        providers_seen = {m.provider for m in output.mentions}
        assert "openai" in providers_seen
        assert "anthropic" in providers_seen

    @pytest.mark.asyncio
    async def test_scan_with_citations(self):
        """Test that citations from adapter results are collected."""
        stub_adapter = _make_stub_adapter(
            _make_adapter_result(
                raw_response="Acme Corp is recommended. See https://acme.com/about for details.",
                citations=[{"url": "https://acme.com/about"}],
            )
        )
        scan_input = _make_scan_input(
            prompts=[
                PromptDefinition(id="p1", template="Best {brand}?"),
            ]
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"chatgpt": stub_adapter, "openai": stub_adapter},
        ):
            output = await execute_scan(scan_input)

        assert len(output.mentions) == 1
        assert len(output.mentions[0].citations) > 0

    @pytest.mark.asyncio
    async def test_scan_with_reasoning(self):
        """Test that reasoning from adapter is passed through."""
        stub_adapter = _make_stub_adapter(
            _make_adapter_result(
                raw_response="Acme Corp is a leader.",
                reasoning="I chose Acme because of their market position.",
            )
        )
        scan_input = _make_scan_input(
            prompts=[
                PromptDefinition(id="p1", template="Best {brand}?"),
            ]
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"chatgpt": stub_adapter, "openai": stub_adapter},
        ):
            output = await execute_scan(scan_input)

        assert output.mentions[0].reasoning is not None
        assert "market position" in output.mentions[0].reasoning

    @pytest.mark.asyncio
    async def test_scan_metrics_computed(self):
        """Test that metrics are properly computed."""
        stub_adapter = _make_stub_adapter(
            _make_adapter_result(raw_response="Acme Corp is the best. BrandX is also good.")
        )
        scan_input = _make_scan_input(
            prompts=[
                PromptDefinition(id="p1", template="Best {brand}?"),
                PromptDefinition(id="p2", template="Compare {brand} vs {competitor}"),
            ],
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"chatgpt": stub_adapter, "openai": stub_adapter},
        ):
            output = await execute_scan(scan_input)

        assert output.metrics.total_prompts == 2
        assert output.metrics.visibility_score > 0

    @pytest.mark.asyncio
    async def test_scan_with_location(self):
        """Test scan with location context."""
        stub_adapter = _make_stub_adapter()
        scan_input = _make_scan_input()
        scan_input.location = LocationContext(country_code="US", city="New York", region="NY")

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"chatgpt": stub_adapter, "openai": stub_adapter},
        ):
            output = await execute_scan(scan_input)

        assert output.status == "success"

    @pytest.mark.asyncio
    async def test_scan_provider_results_populated(self):
        """Test that provider_results dict is populated."""
        stub_adapter = _make_stub_adapter()
        scan_input = _make_scan_input(
            prompts=[
                PromptDefinition(id="p1", template="Best {brand}?"),
            ]
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"chatgpt": stub_adapter, "openai": stub_adapter},
        ):
            output = await execute_scan(scan_input)

        assert "openai" in output.provider_results
        assert output.provider_results["openai"]["status"] in ("completed", "partial")


class TestExecuteScanNoDbImports:
    """Verify that scan_executor has no database imports."""

    def test_no_prisma_import(self):
        import ast
        import inspect

        from ai_visibility import scan_executor

        source = inspect.getsource(scan_executor)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = getattr(node, "module", "") or ""
                names = [alias.name for alias in node.names] if hasattr(node, "names") else []
                assert "prisma" not in module.lower(), f"Found prisma import: {module}"
                assert "prisma" not in str(names).lower(), f"Found prisma in names: {names}"

    def test_no_storage_import(self):
        import ast
        import inspect

        from ai_visibility import scan_executor

        source = inspect.getsource(scan_executor)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert "storage" not in module, f"Found storage import: {module}"

    def test_no_repository_import(self):
        import ast
        import inspect

        from ai_visibility import scan_executor

        source = inspect.getsource(scan_executor)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert "repositor" not in module.lower(), f"Found repository import: {module}"


# --- Schema tests ---


class TestSchemaModels:
    def test_scan_input_required_fields(self):
        inp = ScanInput(
            brand_name="Test",
            domain="test.com",
            providers=["openai"],
            prompts=[PromptDefinition(id="p1", template="test {brand}")],
        )
        assert inp.brand_name == "Test"
        assert inp.max_prompts_per_provider == 3

    def test_scan_input_with_all_fields(self):
        inp = ScanInput(
            job_id="j1",
            metadata={"source": "test"},
            brand_name="Test",
            domain="test.com",
            providers=["openai", "anthropic"],
            prompts=[PromptDefinition(id="p1", template="test {brand}")],
            competitors=["Comp1"],
            location=LocationContext(country_code="US", city="NYC"),
            max_prompts_per_provider=5,
        )
        assert inp.brand_name == "Test"
        assert len(inp.competitors) == 1
        assert inp.location.city == "NYC"

    def test_scan_output_defaults(self):
        out = ScanOutput()
        assert out.status == "success"
        assert out.mentions == []
        assert out.metrics.visibility_score == 0.0

    def test_mention_result_defaults(self):
        m = MentionResult(
            provider="openai",
            prompt_id="p1",
            prompt_text="test",
            raw_response="response",
        )
        assert m.brand_mentioned is False
        assert m.citations == []
        assert m.reasoning is None

    def test_scan_progress_stages(self):
        assert ScanProgress(stage="queued").stage == "queued"
        assert ScanProgress(stage="scanning").stage == "scanning"
        assert ScanProgress(stage="extracting").stage == "extracting"
        assert ScanProgress(stage="complete").stage == "complete"

    def test_prompt_definition(self):
        pd = PromptDefinition(id="p1", template="test {brand}")
        assert pd.category == "custom"
        assert pd.version == "1.0.0"

    def test_location_context_defaults(self):
        loc = LocationContext()
        assert loc.country_code == ""
        assert loc.city == ""

    def test_scan_metrics_defaults(self):
        m = ScanMetrics()
        assert m.visibility_score == 0.0
        assert m.total_prompts == 0


class TestRealAdapterFlow:
    """Integration tests: uses StubAdapter
    injected via the build_adapters seam to verify the full
    adapter → extraction → MentionResult flow."""

    @pytest.mark.asyncio
    async def test_full_flow_with_stub_adapter_brand_mentioned(self):
        from ai_visibility.providers.adapters.stub import StubAdapter

        stub = StubAdapter(
            result=AdapterResult(
                raw_response="Acme Corp is the top provider in the market. Highly recommended.",
                citations=[{"url": "https://acme.com/about"}],
                provider="openai",
                model_name="gpt-5.4",
                model_version="gpt-5.4",
                strategy_version="v1",
            )
        )
        scan_input = _make_scan_input(
            brand_name="Acme Corp",
            prompts=[PromptDefinition(id="p1", template="Best {brand}?")],
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"chatgpt": stub, "openai": stub},
        ):
            output = await execute_scan(scan_input)

        assert len(stub.calls) == 1
        call_prompt, call_slug, call_config, call_loc = stub.calls[0]
        assert "Acme Corp" in call_prompt
        assert call_slug == ""

        assert len(output.mentions) == 1
        m = output.mentions[0]
        assert m.brand_mentioned is True
        assert m.brand_position is not None
        assert m.sentiment == "positive"
        assert m.provider == "openai"
        assert m.model_name == "gpt-5.4"
        assert m.prompt_id == "p1"
        assert "Acme Corp" in m.raw_response
        assert len(m.citations) >= 1
        assert any("acme.com" in c.get("url", "") for c in m.citations)

    @pytest.mark.asyncio
    async def test_full_flow_brand_not_mentioned(self):
        from ai_visibility.providers.adapters.stub import StubAdapter

        stub = StubAdapter(
            result=AdapterResult(
                raw_response="There are many providers in this space. Consider BrandX or BrandY.",
                citations=[],
                provider="anthropic",
                model_name="claude-sonnet-4-6",
                model_version="claude-sonnet-4-6",
                strategy_version="v1",
            )
        )
        scan_input = _make_scan_input(
            brand_name="Acme Corp",
            providers=["anthropic"],
            prompts=[PromptDefinition(id="p1", template="Best {brand}?")],
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"anthropic": stub},
        ):
            output = await execute_scan(scan_input)

        assert len(output.mentions) == 1
        m = output.mentions[0]
        assert m.brand_mentioned is False
        assert m.brand_position is None
        assert output.metrics.visibility_score == 0.0
        assert output.metrics.total_mentioned == 0

    @pytest.mark.asyncio
    async def test_full_flow_extraction_pipeline_citations(self):
        from ai_visibility.providers.adapters.stub import StubAdapter

        stub = StubAdapter(
            result=AdapterResult(
                raw_response=(
                    "Acme Corp is great. See https://acme.com/reviews for details "
                    "and https://trustpilot.com/acme for reviews."
                ),
                citations=[],
                provider="openai",
                model_name="gpt-5.4",
                model_version="gpt-5.4",
                strategy_version="v1",
            )
        )
        scan_input = _make_scan_input(
            brand_name="Acme Corp",
            prompts=[PromptDefinition(id="p1", template="Best {brand}?")],
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"chatgpt": stub, "openai": stub},
        ):
            output = await execute_scan(scan_input)

        m = output.mentions[0]
        assert m.brand_mentioned is True
        urls = [c.get("url", "") for c in m.citations]
        assert any("acme.com" in u for u in urls)
        assert any("trustpilot.com" in u for u in urls)

    @pytest.mark.asyncio
    async def test_full_flow_competitor_substitution(self):
        from ai_visibility.providers.adapters.stub import StubAdapter

        stub = StubAdapter(
            result=AdapterResult(
                raw_response="Acme Corp vs BrandX comparison shows Acme Corp ahead.",
                citations=[],
                provider="openai",
                model_name="gpt-5.4",
                model_version="gpt-5.4",
                strategy_version="v1",
            )
        )
        scan_input = _make_scan_input(
            brand_name="Acme Corp",
            competitors=["BrandX", "BrandY"],
            prompts=[
                PromptDefinition(id="p1", template="Compare {brand} vs {competitor}"),
                PromptDefinition(id="p2", template="{brand} or {competitor}?"),
            ],
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"chatgpt": stub, "openai": stub},
        ):
            await execute_scan(scan_input)

        assert len(stub.calls) == 2
        prompts_sent = [c[0] for c in stub.calls]
        assert "BrandX" in prompts_sent[0]
        assert "BrandY" in prompts_sent[1]

    @pytest.mark.asyncio
    async def test_full_flow_multiple_providers_sequenced(self):
        from ai_visibility.providers.adapters.stub import StubAdapter

        openai_stub = StubAdapter(
            result=AdapterResult(
                raw_response="Acme Corp mentioned by OpenAI.",
                citations=[],
                provider="openai",
                model_name="gpt-5.4",
                model_version="gpt-5.4",
                strategy_version="v1",
            )
        )
        anthropic_stub = StubAdapter(
            result=AdapterResult(
                raw_response="No mention of any specific brand.",
                citations=[],
                provider="anthropic",
                model_name="claude-sonnet-4-6",
                model_version="claude-sonnet-4-6",
                strategy_version="v1",
            )
        )
        scan_input = _make_scan_input(
            brand_name="Acme Corp",
            providers=["openai", "anthropic"],
            prompts=[PromptDefinition(id="p1", template="Best {brand}?")],
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={
                "chatgpt": openai_stub,
                "openai": openai_stub,
                "anthropic": anthropic_stub,
            },
        ):
            output = await execute_scan(scan_input)

        assert len(output.mentions) == 2
        mentioned_providers = {m.provider for m in output.mentions}
        assert mentioned_providers == {"openai", "anthropic"}

        openai_mention = next(m for m in output.mentions if m.provider == "openai")
        anthropic_mention = next(m for m in output.mentions if m.provider == "anthropic")
        assert openai_mention.brand_mentioned is True
        assert anthropic_mention.brand_mentioned is False

        assert output.metrics.visibility_score == 0.5
        assert output.metrics.total_prompts == 2
        assert output.metrics.total_mentioned == 1

        assert output.provider_results["openai"]["status"] == "completed"
        assert output.provider_results["anthropic"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_full_flow_adapter_exception_doesnt_crash(self):
        from ai_visibility.providers.adapters.stub import StubAdapter

        good_stub = StubAdapter(
            result=AdapterResult(
                raw_response="Acme Corp is great.",
                citations=[],
                provider="openai",
                model_name="gpt-5.4",
                model_version="gpt-5.4",
                strategy_version="v1",
            )
        )
        bad_stub = MagicMock()
        bad_stub.execute.side_effect = RuntimeError("API timeout")

        scan_input = _make_scan_input(
            brand_name="Acme Corp",
            providers=["openai", "anthropic"],
            prompts=[PromptDefinition(id="p1", template="Best {brand}?")],
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={
                "chatgpt": good_stub,
                "openai": good_stub,
                "anthropic": bad_stub,
            },
        ):
            output = await execute_scan(scan_input)

        assert output.status == "success"
        assert len(output.mentions) == 1
        assert output.mentions[0].provider == "openai"
        assert output.provider_results["openai"]["status"] == "completed"
        assert output.provider_results["anthropic"]["status"] == "partial"
        assert output.provider_results["anthropic"]["failed"] == 1

    @pytest.mark.asyncio
    async def test_full_flow_reasoning_passthrough(self):
        from ai_visibility.providers.adapters.stub import StubAdapter

        stub = StubAdapter(
            result=AdapterResult(
                raw_response="Acme Corp leads in market share.",
                citations=[],
                provider="openai",
                model_name="gpt-5.4",
                model_version="gpt-5.4",
                strategy_version="v1",
                reasoning="I chose Acme based on recent industry reports showing 40% market share.",
            )
        )
        scan_input = _make_scan_input(
            prompts=[PromptDefinition(id="p1", template="Best {brand}?")],
        )

        with patch(
            "ai_visibility.scan_executor.build_adapters",
            return_value={"chatgpt": stub, "openai": stub},
        ):
            output = await execute_scan(scan_input)

        assert output.mentions[0].reasoning is not None
        assert "industry reports" in output.mentions[0].reasoning
