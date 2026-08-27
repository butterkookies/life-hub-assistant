import html
import json
import logging
import os
import re
import smtplib
from datetime import datetime, timezone, timedelta
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional, Tuple
import urllib.request
import urllib.error

from config import settings

logger = logging.getLogger("email_service")

class EmailService:
    """Service to handle formatting and delivering rich HTML email notifications and daily briefings."""

    def __init__(self):
        pass

    def is_configured(self) -> bool:
        """Check if minimum required email credentials are configured."""
        has_recipient = bool(settings.NOTIFICATION_EMAIL_TO)
        has_smtp = bool(settings.SMTP_USER and settings.SMTP_PASSWORD)
        has_resend = bool(settings.RESEND_API_KEY)
        return has_recipient and (has_smtp or has_resend)

    def markdown_to_html_body(self, text: str) -> str:
        """Convert markdown text with bullet points, links, and bolding into clean HTML for email."""
        if not text:
            return ""

        # Escape raw HTML
        formatted = html.escape(text)

        # Convert markdown links [text](url) -> <a href="url" ...>text</a>
        def replace_link(match):
            title = match.group(1)
            url = html.unescape(match.group(2))
            return f'<a href="{url}" style="color: #2563eb; text-decoration: underline; font-weight: 500;">{title}</a>'
        
        formatted = re.sub(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)', replace_link, formatted)

        # Convert bold (**text** or *text*)
        formatted = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', formatted)
        formatted = re.sub(r'(?<!\w)\*([^\*\n]+?)\*(?!\w)', r'<strong>\1</strong>', formatted)

        # Convert italics (_text_)
        formatted = re.sub(r'(?<!\w)_([^\_\n]+?)_(?!\w)', r'<em>\1</em>', formatted)

        # Convert code (`code`)
        formatted = re.sub(r'`([^`]+)`', r'<code style="background-color: #f1f5f9; padding: 2px 5px; border-radius: 4px; font-family: monospace; font-size: 0.9em; color: #0f172a;">\1</code>', formatted)

        # Process lines for headers, list items, and paragraphs
        lines = formatted.split('\n')
        html_lines = []
        in_list = False

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                continue

            # Header check (### or ## or #)
            header_match = re.match(r'^(#{1,6})\s+(.*)$', trimmed)
            if header_match:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                h_text = header_match.group(2)
                html_lines.append(f'<h3 style="margin-top: 18px; margin-bottom: 8px; font-size: 16px; color: #1e293b; font-weight: 700;">{h_text}</h3>')
                continue

            # List item check (* or - or •)
            list_match = re.match(r'^[\*\-•]\s+(.*)$', trimmed)
            if list_match:
                if not in_list:
                    html_lines.append('<ul style="margin: 6px 0 12px 0; padding-left: 20px; color: #334155; line-height: 1.6;">')
                    in_list = True
                item_text = list_match.group(1)
                html_lines.append(f'<li style="margin-bottom: 4px;">{item_text}</li>')
                continue

            # Regular paragraph
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f'<p style="margin: 6px 0; color: #334155; line-height: 1.6;">{trimmed}</p>')

        if in_list:
            html_lines.append("</ul>")

        return '\n'.join(html_lines)

    def render_briefing_template(self, body_markdown: str, date_display: str) -> str:
        """Wrap the briefing content into a modern, responsive email container."""
        content_html = self.markdown_to_html_body(body_markdown)
        
        template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Andrei's Daily Morning Briefing</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 30px 10px;">
    <tr>
      <td align="center">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); border: 1px solid #e2e8f0;">
          
          <!-- Header Banner -->
          <tr>
            <td style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 28px 24px; text-align: left;">
              <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td>
                    <div style="font-size: 20px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;">
                      🌅 Andrei's Daily Briefing
                    </div>
                    <div style="font-size: 13px; color: #94a3b8; margin-top: 4px; font-weight: 500;">
                      Notion Life Hub • {date_display}
                    </div>
                  </td>
                  <td align="right" style="vertical-align: middle;">
                    <span style="background-color: rgba(255, 255, 255, 0.12); color: #38bdf8; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 20px; border: 1px solid rgba(56, 189, 248, 0.3);">
                      AI Assistant
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main Briefing Content -->
          <tr>
            <td style="padding: 28px 24px; color: #1e293b; font-size: 15px; line-height: 1.65;">
              {content_html}
            </td>
          </tr>

          <!-- Quick Action Buttons -->
          <tr>
            <td style="padding: 0 24px 24px 24px;">
              <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f1f5f9; border-radius: 8px; padding: 14px 18px;">
                <tr>
                  <td style="font-size: 13px; color: #475569;">
                    <strong>📱 Quick Shortcuts:</strong>
                  </td>
                  <td align="right">
                    <a href="https://app.notion.com" style="display: inline-block; background-color: #0f172a; color: #ffffff; text-decoration: none; font-size: 12px; font-weight: 600; padding: 6px 14px; border-radius: 6px; margin-left: 6px;">Open Notion</a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 18px 24px; text-align: center; font-size: 12px; color: #64748b;">
              Delivered automatically by your <strong>Telegram Notion AI Bot</strong>.<br>
              To manage briefing times, use <code>/briefing status</code> on Telegram.
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
        return template

    def _send_via_smtp(self, to_email: str, subject: str, html_body: str, plain_body: str) -> Tuple[bool, str]:
        """Send email via SMTP (Gmail, SendGrid, Brevo, Outlook, etc.)."""
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            return False, "SMTP_USER or SMTP_PASSWORD is not set in environment."

        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
        msg["To"] = to_email

        # Attach plaintext and HTML versions
        part1 = MIMEText(plain_body, "plain", "utf-8")
        part2 = MIMEText(html_body, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        try:
            logger.info(f"Connecting to SMTP server {settings.SMTP_HOST}:{settings.SMTP_PORT}...")
            if settings.SMTP_PORT == 465:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
                server.ehlo()
                server.starttls()
                server.ehlo()

            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM_ADDRESS, [to_email], msg.as_string())
            server.quit()
            logger.info(f"Email successfully delivered via SMTP to {to_email}")
            return True, "Email delivered successfully via SMTP."
        except Exception as e:
            err_msg = f"SMTP dispatch failed: {str(e)}"
            logger.error(err_msg, exc_info=True)
            return False, err_msg

    def _send_via_resend(self, to_email: str, subject: str, html_body: str, plain_body: str) -> Tuple[bool, str]:
        """Send email via Resend REST API."""
        if not settings.RESEND_API_KEY:
            return False, "RESEND_API_KEY is not set."

        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
            "text": plain_body
        }

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                logger.info(f"Email successfully delivered via Resend API to {to_email} (ID: {data.get('id')})")
                return True, f"Email delivered via Resend (ID: {data.get('id')})"
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            err_msg = f"Resend API Error ({e.code}): {err_body}"
            logger.error(err_msg)
            return False, err_msg
        except Exception as e:
            err_msg = f"Resend HTTP request failed: {str(e)}"
            logger.error(err_msg)
            return False, err_msg

    def send_email(self, subject: str, html_body: str, plain_body: str, to_email: Optional[str] = None) -> Tuple[bool, str]:
        """Dispatch email using configured SMTP or Resend provider with graceful fallback."""
        recipient = (to_email or settings.NOTIFICATION_EMAIL_TO).strip()
        if not recipient:
            return False, "No recipient email configured. Please set NOTIFICATION_EMAIL_TO in .env."

        # 1. Try Resend if configured
        if settings.RESEND_API_KEY:
            success, msg = self._send_via_resend(recipient, subject, html_body, plain_body)
            if success:
                return True, msg
            logger.warning(f"Resend delivery failed ({msg}), attempting SMTP fallback...")

        # 2. Try SMTP
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            return self._send_via_smtp(recipient, subject, html_body, plain_body)

        return False, "Email notification credentials (SMTP_USER/SMTP_PASSWORD or RESEND_API_KEY) are not configured."

    def send_briefing_email(self, briefing_markdown: str, date_display: str = "", to_email: Optional[str] = None) -> Tuple[bool, str]:
        """Deliver the morning daily briefing as a formatted HTML email."""
        if not date_display:
            tz = timezone(timedelta(hours=settings.UTC_OFFSET_HOURS))
            date_display = datetime.now(tz).strftime("%A, %B %d, %Y")

        subject = f"🌅 Morning Briefing: {date_display}"
        html_content = self.render_briefing_template(briefing_markdown, date_display)
        plain_content = briefing_markdown

        return self.send_email(subject, html_content, plain_content, to_email)

    def send_notification_email(self, subject: str, message_markdown: str, to_email: Optional[str] = None) -> Tuple[bool, str]:
        """Deliver a general notification or alert as an email."""
        tz = timezone(timedelta(hours=settings.UTC_OFFSET_HOURS))
        date_display = datetime.now(tz).strftime("%B %d, %Y • %I:%M %p")
        
        full_subject = f"🔔 {subject}"
        html_content = self.render_briefing_template(message_markdown, date_display)
        plain_content = message_markdown

        return self.send_email(full_subject, html_content, plain_content, to_email)

email_service = EmailService()
