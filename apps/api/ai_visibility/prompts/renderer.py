"""Prompt template renderer with variable injection."""

import re
from typing import Any


class PromptRenderError(Exception):
    """Raised when a required variable is missing during prompt rendering."""

    pass


class PromptRenderer:
    """Renders prompt templates with variable injection."""

    def render(self, template: str, **variables: Any) -> str:
        """
        Render a prompt template with variable injection.

        Args:
            template: Template string with {variable} placeholders
            **variables: Variables to inject into the template

        Returns:
            Rendered template string

        Raises:
            PromptRenderError: If a required variable is missing
        """
        # Find all placeholders in the template
        placeholders = re.findall(r"\{(\w+)\}", template)

        # Check for missing required variables
        missing_vars = [var for var in placeholders if var not in variables]
        if missing_vars:
            raise PromptRenderError(f"Missing required variable(s): {', '.join(missing_vars)}")

        # Render the template
        return template.format(**variables)
