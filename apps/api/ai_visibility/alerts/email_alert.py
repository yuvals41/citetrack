import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from loguru import logger


def _build_alerts_html(workspace_slug: str, alerts: list[dict[str, str]]) -> str:
    rows: list[str] = []
    for alert in alerts:
        alert_type = escape(str(alert.get("type", "unknown")))
        severity = escape(str(alert.get("severity", "info"))).upper()
        message = escape(str(alert.get("message", "")))
        row = (
            "<tr>"
            + f"<td style='padding:8px;border:1px solid #ddd'>{alert_type}</td>"
            + f"<td style='padding:8px;border:1px solid #ddd'>{severity}</td>"
            + f"<td style='padding:8px;border:1px solid #ddd'>{message}</td>"
            + "</tr>"
        )
        rows.append(row)

    table_body = (
        "".join(rows) if rows else "<tr><td colspan='3' style='padding:8px;border:1px solid #ddd'>No alerts</td></tr>"
    )
    return (
        "<html><body>"
        f"<h2>AI Visibility Alert - {escape(workspace_slug)}</h2>"
        "<table style='border-collapse:collapse;width:100%'>"
        "<thead><tr>"
        "<th style='padding:8px;border:1px solid #ddd;text-align:left'>Type</th>"
        "<th style='padding:8px;border:1px solid #ddd;text-align:left'>Severity</th>"
        "<th style='padding:8px;border:1px solid #ddd;text-align:left'>Message</th>"
        "</tr></thead>"
        f"<tbody>{table_body}</tbody>"
        "</table>"
        "</body></html>"
    )


async def send_email_alert(alerts: list[dict[str, str]], workspace_slug: str) -> bool:
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port_raw = os.getenv("SMTP_PORT", "").strip()
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    alert_email_to = os.getenv("ALERT_EMAIL_TO", "").strip()
    alert_email_from = os.getenv("ALERT_EMAIL_FROM", "").strip()

    required = [smtp_host, smtp_port_raw, smtp_username, smtp_password, alert_email_to, alert_email_from]
    if not all(required):
        logger.debug("[email-alert] Missing SMTP env vars, skipping email alert delivery")
        return False

    if not alerts:
        logger.debug("[email-alert] No alerts to send")
        return False

    try:
        smtp_port = int(smtp_port_raw)
    except ValueError:
        logger.debug("[email-alert] Invalid SMTP_PORT value, skipping email alert delivery")
        return False

    subject = f"AI Visibility Alert — {workspace_slug}"
    html_body = _build_alerts_html(workspace_slug, alerts)
    plain_lines = [f"AI Visibility Alert — {workspace_slug}"]
    for alert in alerts:
        plain_lines.append(
            f"- {str(alert.get('type', 'unknown'))} | {str(alert.get('severity', 'info')).upper()} | {str(alert.get('message', ''))}"
        )
    plain_body = "\n".join(plain_lines)

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = alert_email_from
    message["To"] = alert_email_to
    message.attach(MIMEText(plain_body, "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        _ = server.starttls()
        _ = server.login(smtp_username, smtp_password)
        _ = server.sendmail(alert_email_from, [alert_email_to], message.as_string())
        _ = server.quit()
        logger.debug("[email-alert] Email alert sent successfully")
        return True
    except Exception as e:  # noqa: BLE001
        logger.debug(f"[email-alert] Failed to send email alert: {type(e).__name__}: {e}")
        return False
