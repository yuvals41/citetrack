import pytest

from ai_visibility.providers.adapters import AdapterResult, StubAdapter
from ai_visibility.providers.gateway import LocationContext
from ai_visibility.runs.execution_core import compute_pipeline_metrics, execute_scan_pipeline
from ai_visibility.runs.scan_strategy import ScanMode, get_strategy_for_mode
from ai_visibility.schema import PromptDefinition


@pytest.mark.asyncio
async def test_execute_scan_pipeline_runs_shared_prompt_fanout() -> None:
    strategy = get_strategy_for_mode(ScanMode.SCHEDULED)
    adapter = StubAdapter(
        result=AdapterResult(
            raw_response=(
                "Acme Corp is a top provider. See https://acme.com/proof for details and "
                "https://trustpilot.com/acme for reviews."
            ),
            citations=[{"url": "https://acme.com/proof", "title": "Proof"}],
            provider="openai",
            model_name="gpt-5.4",
            model_version="gpt-5.4",
            strategy_version="v1",
            reasoning="Acme appears consistently in trusted sources.",
        )
    )

    result = await execute_scan_pipeline(
        providers=["openai"],
        prompts=[
            PromptDefinition(id="p1", template="Compare {brand} vs {competitor}"),
            PromptDefinition(id="p2", template="Who recommends {brand} over {competitor}?"),
        ],
        max_prompts_per_provider=3,
        brand_names=["Acme Corp"],
        competitors=["BrandX", "BrandY"],
        location=LocationContext(),
        strategy=strategy,
        adapters={"chatgpt": adapter, "openai": adapter},
        workspace_slug="workspace-acme",
    )

    metrics = compute_pipeline_metrics(result.successes)

    assert len(result.successes) == 2
    assert result.failures == []
    assert result.provider_results["openai"].status == "completed"
    assert result.provider_results["openai"].ok == 2
    assert adapter.calls[0][0] == "Compare Acme Corp vs BrandX"
    assert adapter.calls[1][0] == "Who recommends Acme Corp over BrandY?"
    assert adapter.calls[0][1] == "workspace-acme"
    assert metrics.visibility_score == 1.0
    assert metrics.total_prompts == 2
    assert metrics.total_mentioned == 2
    assert metrics.total_citations >= 2
