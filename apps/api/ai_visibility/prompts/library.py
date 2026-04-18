"""Prompt library with versioning and categorization."""

from typing import Any, List

from ai_visibility.prompts.default_set import Prompt


class PromptLibrary:
    """Manages a library of prompts with versioning and categorization."""

    def __init__(self, prompts: List[Prompt]) -> None:
        """
        Initialize the prompt library.

        Args:
            prompts: List of prompt definitions
        """
        self._prompts = prompts
        self._prompts_by_id = {p["id"]: p for p in prompts}
        self._prompts_by_category = self._build_category_index()

    def _build_category_index(self) -> dict[str, List[Prompt]]:
        """Build an index of prompts by category."""
        index: dict[str, List[Prompt]] = {}
        for prompt in self._prompts:
            category = prompt["category"]
            if category not in index:
                index[category] = []
            index[category].append(prompt)
        return index

    def list_prompts(self) -> List[dict[str, Any]]:
        """
        List all prompts in the library.

        Returns:
            List of prompt dictionaries
        """
        return [dict(p) for p in self._prompts]

    def get_prompt(self, prompt_id: str) -> dict[str, Any]:
        """
        Get a prompt by ID.

        Args:
            prompt_id: The prompt ID

        Returns:
            Prompt dictionary

        Raises:
            KeyError: If prompt not found
        """
        if prompt_id not in self._prompts_by_id:
            raise KeyError(f"Prompt not found: {prompt_id}")
        return dict(self._prompts_by_id[prompt_id])

    def get_prompt_set(self, category: str) -> List[dict[str, Any]]:
        """
        Get all prompts in a category.

        Args:
            category: The category name

        Returns:
            List of prompt dictionaries in the category

        Raises:
            KeyError: If category not found
        """
        if category not in self._prompts_by_category:
            raise KeyError(f"Category not found: {category}")
        return [dict(p) for p in self._prompts_by_category[category]]

    def list_categories(self) -> List[str]:
        """
        List all available categories.

        Returns:
            List of category names
        """
        return sorted(list(self._prompts_by_category.keys()))
