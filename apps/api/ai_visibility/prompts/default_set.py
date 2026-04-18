"""Default AI-visibility prompt set."""

from typing import List, TypedDict

PROMPT_VERSION = "v1"


class Prompt(TypedDict):
    """Prompt definition."""

    id: str
    category: str
    version: str
    template: str


# Default prompt set: 20 prompts across 4 categories
DEFAULT_PROMPTS: List[Prompt] = [
    # Buying Intent (5 prompts)
    {
        "id": "buying_intent_1",
        "category": "buying_intent",
        "version": "1.0.0",
        "template": "What is the best {brand}?",
    },
    {
        "id": "buying_intent_2",
        "category": "buying_intent",
        "version": "1.0.0",
        "template": "Should I use {brand} for my business?",
    },
    {
        "id": "buying_intent_3",
        "category": "buying_intent",
        "version": "1.0.0",
        "template": "Is {brand} worth the cost?",
    },
    {
        "id": "buying_intent_4",
        "category": "buying_intent",
        "version": "1.0.0",
        "template": "What are the main benefits of {brand}?",
    },
    {
        "id": "buying_intent_5",
        "category": "buying_intent",
        "version": "1.0.0",
        "template": "How much does {brand} cost?",
    },
    # Comparison (5 prompts)
    {
        "id": "comparison_1",
        "category": "comparison",
        "version": "1.0.0",
        "template": "Is {brand} better than {competitor}?",
    },
    {
        "id": "comparison_2",
        "category": "comparison",
        "version": "1.0.0",
        "template": "Compare {brand} vs {competitor}",
    },
    {
        "id": "comparison_3",
        "category": "comparison",
        "version": "1.0.0",
        "template": "What are the differences between {brand} and {competitor}?",
    },
    {
        "id": "comparison_4",
        "category": "comparison",
        "version": "1.0.0",
        "template": "Which is better: {brand} or {competitor}?",
    },
    {
        "id": "comparison_5",
        "category": "comparison",
        "version": "1.0.0",
        "template": "How does {brand} compare to {competitor} in terms of features?",
    },
    # Recommendation (5 prompts)
    {
        "id": "recommendation_1",
        "category": "recommendation",
        "version": "1.0.0",
        "template": "Recommend a tool like {brand}",
    },
    {
        "id": "recommendation_2",
        "category": "recommendation",
        "version": "1.0.0",
        "template": "What are alternatives to {brand}?",
    },
    {
        "id": "recommendation_3",
        "category": "recommendation",
        "version": "1.0.0",
        "template": "Which tool should I use instead of {brand}?",
    },
    {
        "id": "recommendation_4",
        "category": "recommendation",
        "version": "1.0.0",
        "template": "Is there a better alternative to {brand}?",
    },
    {
        "id": "recommendation_5",
        "category": "recommendation",
        "version": "1.0.0",
        "template": "What tools are similar to {brand}?",
    },
    # Informational (5 prompts)
    {
        "id": "informational_1",
        "category": "informational",
        "version": "1.0.0",
        "template": "Where can I find information about {brand}?",
    },
    {
        "id": "informational_2",
        "category": "informational",
        "version": "1.0.0",
        "template": "Tell me about {brand}",
    },
    {
        "id": "informational_3",
        "category": "informational",
        "version": "1.0.0",
        "template": "What is {brand} used for?",
    },
    {
        "id": "informational_4",
        "category": "informational",
        "version": "1.0.0",
        "template": "How does {brand} work?",
    },
    {
        "id": "informational_5",
        "category": "informational",
        "version": "1.0.0",
        "template": "What are the features of {brand}?",
    },
]
