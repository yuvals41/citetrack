"""Tests for PromptRenderer."""

import pytest
from ai_visibility.prompts.renderer import PromptRenderer, PromptRenderError


class TestPromptRenderer:
    """Test suite for PromptRenderer."""

    @pytest.fixture
    def renderer(self) -> PromptRenderer:
        """Provide a PromptRenderer instance."""
        return PromptRenderer()

    def test_render_simple_template_with_brand(self, renderer: PromptRenderer) -> None:
        """Test rendering a simple template with brand variable."""
        template = "What is the best {brand}?"
        result = renderer.render(template, brand="HubSpot")
        assert result == "What is the best HubSpot?"

    def test_render_template_with_brand_and_competitor(self, renderer: PromptRenderer) -> None:
        """Test rendering a template with brand and competitor variables."""
        template = "Is {brand} better than {competitor}?"
        result = renderer.render(template, brand="HubSpot", competitor="Salesforce")
        assert result == "Is HubSpot better than Salesforce?"

    def test_render_raises_on_missing_brand(self, renderer: PromptRenderer) -> None:
        """Test that render raises PromptRenderError when brand is missing."""
        template = "What is the best {brand}?"
        with pytest.raises(PromptRenderError) as exc_info:
            renderer.render(template)
        assert "brand" in str(exc_info.value).lower()

    def test_render_raises_on_missing_competitor(self, renderer: PromptRenderer) -> None:
        """Test that render raises PromptRenderError when competitor is missing."""
        template = "Is {brand} better than {competitor}?"
        with pytest.raises(PromptRenderError) as exc_info:
            renderer.render(template, brand="HubSpot")
        assert "competitor" in str(exc_info.value).lower()

    def test_render_error_message_is_descriptive(self, renderer: PromptRenderer) -> None:
        """Test that PromptRenderError has a clear message."""
        template = "Is {brand} better than {competitor}?"
        try:
            renderer.render(template, brand="HubSpot")
            pytest.fail("Expected PromptRenderError")
        except PromptRenderError as e:
            assert "competitor" in str(e).lower()
            assert "required" in str(e).lower() or "missing" in str(e).lower()

    def test_render_with_extra_variables_ignored(self, renderer: PromptRenderer) -> None:
        """Test that extra variables are ignored."""
        template = "What is the best {brand}?"
        result = renderer.render(template, brand="HubSpot", extra="ignored")
        assert result == "What is the best HubSpot?"

    def test_render_multiple_occurrences_of_same_variable(self, renderer: PromptRenderer) -> None:
        """Test rendering when same variable appears multiple times."""
        template = "Compare {brand} with {brand} features"
        result = renderer.render(template, brand="HubSpot")
        assert result == "Compare HubSpot with HubSpot features"

    def test_render_preserves_whitespace(self, renderer: PromptRenderer) -> None:
        """Test that rendering preserves whitespace."""
        template = "What is {brand}?\n\nTell me more."
        result = renderer.render(template, brand="HubSpot")
        assert result == "What is HubSpot?\n\nTell me more."

    def test_render_with_special_characters_in_values(self, renderer: PromptRenderer) -> None:
        """Test rendering with special characters in variable values."""
        template = "Is {brand} better than {competitor}?"
        result = renderer.render(template, brand="HubSpot (CRM)", competitor="Salesforce & Co.")
        assert result == "Is HubSpot (CRM) better than Salesforce & Co.?"
