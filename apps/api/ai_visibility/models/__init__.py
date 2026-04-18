"""Domain models for AI Visibility."""

from ai_visibility.models.workspace import Workspace, WorkspaceCreate
from ai_visibility.models.brand import Brand, Competitor
from ai_visibility.models.onboarding import (
    OnboardingBrand,
    OnboardingCompetitor,
    OnboardingCompleteResponse,
    OnboardingEngine,
    OnboardingPayload,
)
from ai_visibility.models.prompt import Prompt, PromptVersion, PromptSet
from ai_visibility.models.mention import Mention, MentionType, CitationRecord
from ai_visibility.models.run import Run, RunStatus, RunResult
from ai_visibility.models.metric import MetricSnapshot, CompetitorComparison
from ai_visibility.models.recommendation import Recommendation, RuleTrigger
from ai_visibility.models.degraded import DegradedState, ErrorCode, FailedProvider
from ai_visibility.models.user import User, UserCreate, UserResponse

__all__ = [
    # Workspace
    "Workspace",
    "WorkspaceCreate",
    "User",
    "UserCreate",
    "UserResponse",
    # Brand
    "Brand",
    "Competitor",
    "OnboardingBrand",
    "OnboardingCompetitor",
    "OnboardingCompleteResponse",
    "OnboardingEngine",
    "OnboardingPayload",
    # Prompt
    "Prompt",
    "PromptVersion",
    "PromptSet",
    # Mention
    "Mention",
    "MentionType",
    "CitationRecord",
    # Run
    "Run",
    "RunStatus",
    "RunResult",
    # Metric
    "MetricSnapshot",
    "CompetitorComparison",
    # Recommendation
    "Recommendation",
    "RuleTrigger",
    # Degraded
    "DegradedState",
    "ErrorCode",
    "FailedProvider",
]
