"""FastAPI application for AI Visibility."""

from ai_visibility.api.routes import app, create_app

__all__ = ["create_app", "app"]
