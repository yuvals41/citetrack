"""Tests for PromptLibrary."""

import pytest
from ai_visibility.prompts.library import PromptLibrary
from ai_visibility.prompts.default_set import DEFAULT_PROMPTS


class TestPromptLibrary:
    """Test suite for PromptLibrary."""

    @pytest.fixture
    def library(self) -> PromptLibrary:
        """Provide a PromptLibrary instance."""
        return PromptLibrary(prompts=DEFAULT_PROMPTS)

    def test_list_prompts_returns_all_prompts(self, library: PromptLibrary) -> None:
        """Test that list_prompts returns all prompts."""
        prompts = library.list_prompts()
        assert len(prompts) > 0
        assert len(prompts) >= 15  # At least 15 prompts

    def test_list_prompts_returns_dict_with_required_fields(self, library: PromptLibrary) -> None:
        """Test that each prompt has required fields."""
        prompts = library.list_prompts()
        for prompt in prompts:
            assert "id" in prompt
            assert "category" in prompt
            assert "version" in prompt
            assert "template" in prompt

    def test_get_prompt_by_id_returns_prompt(self, library: PromptLibrary) -> None:
        """Test that get_prompt returns a prompt by id."""
        prompts = library.list_prompts()
        first_prompt_id = prompts[0]["id"]

        prompt = library.get_prompt(first_prompt_id)
        assert prompt is not None
        assert prompt["id"] == first_prompt_id

    def test_get_prompt_by_id_raises_on_missing(self, library: PromptLibrary) -> None:
        """Test that get_prompt raises KeyError for missing id."""
        with pytest.raises(KeyError):
            library.get_prompt("nonexistent_id")

    def test_get_prompt_set_returns_dict_by_name(self, library: PromptLibrary) -> None:
        """Test that get_prompt_set returns prompts grouped by category."""
        prompt_set = library.get_prompt_set("buying_intent")
        assert isinstance(prompt_set, list)
        assert len(prompt_set) > 0
        for prompt in prompt_set:
            assert prompt["category"] == "buying_intent"

    def test_get_prompt_set_raises_on_missing_category(self, library: PromptLibrary) -> None:
        """Test that get_prompt_set raises KeyError for missing category."""
        with pytest.raises(KeyError):
            library.get_prompt_set("nonexistent_category")

    def test_list_categories_returns_all_categories(self, library: PromptLibrary) -> None:
        """Test that list_categories returns all unique categories."""
        categories = library.list_categories()
        assert "buying_intent" in categories
        assert "comparison" in categories
        assert "recommendation" in categories
        assert "informational" in categories

    def test_prompts_have_semantic_versions(self, library: PromptLibrary) -> None:
        """Test that all prompts have semantic version strings."""
        prompts = library.list_prompts()
        for prompt in prompts:
            version = prompt["version"]
            # Check semantic version format (e.g., "1.0.0")
            parts = version.split(".")
            assert len(parts) == 3, f"Version {version} is not semantic"
            for part in parts:
                assert part.isdigit(), f"Version {version} contains non-numeric parts"

    def test_templates_contain_brand_variable(self, library: PromptLibrary) -> None:
        """Test that templates contain {brand} placeholder."""
        prompts = library.list_prompts()
        for prompt in prompts:
            template = prompt["template"]
            assert "{brand}" in template, f"Prompt {prompt['id']} missing {{brand}} placeholder"

    def test_some_templates_contain_competitor_variable(self, library: PromptLibrary) -> None:
        """Test that some templates contain {competitor} placeholder."""
        prompts = library.list_prompts()
        competitor_prompts = [p for p in prompts if "{competitor}" in p["template"]]
        assert len(competitor_prompts) > 0, "No prompts with {competitor} placeholder found"
