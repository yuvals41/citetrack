import os

import httpx
from dotenv import load_dotenv
from loguru import logger

_ = load_dotenv()


async def send_webhook(alerts: list[dict[str, str]], workspace_slug: str) -> bool:
    webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")
    if not webhook_url or not alerts:
        return False

    lines = [f"**AI Visibility Alert — {workspace_slug}**\n"]
    for alert in alerts:
        severity = alert.get("severity", "info").upper()
        message = alert.get("message", "")
        lines.append(f"[{severity}] {message}")

    text = "\n".join(lines)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if "hooks.slack.com" in webhook_url:
                payload = {"text": text}
            elif "discord.com" in webhook_url:
                payload = {"content": text}
            else:
                payload = {"text": text, "alerts": alerts, "workspace": workspace_slug}

            resp = await client.post(webhook_url, json=payload)
            return resp.status_code < 300
    except Exception as e:
        logger.debug(f"[webhook] Failed to send webhook: {type(e).__name__}: {e}")
        return False
