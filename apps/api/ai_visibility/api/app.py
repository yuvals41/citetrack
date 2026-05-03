from fastapi.middleware.cors import CORSMiddleware

from ai_visibility.api.routes import create_app as _create_routes_app


def create_app():
    app = _create_routes_app()
    app.title = "Citetrack AI API"
    app.description = (
        "Track how AI cites your brand across ChatGPT, Claude, Perplexity, Gemini, Grok, and AI Overviews."
    )
    app.version = "0.0.0"

    # CORS allowlist:
    # - localhost:3002 is the canonical dev port (apps/web/vite.config.ts).
    # - localhost:3003 is the auto-fallback when 3002 is taken.
    # - localhost:3000 stays for legacy/direct workflows.
    # See AGENTS.md and apps/web/playwright.config.ts for port conventions.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3002",
            "http://localhost:3003",
            "https://citetrack.ai",
            "https://www.citetrack.ai",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = create_app()
