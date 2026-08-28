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

    def _clean_inline_markdown(self, text: str) -> str:
        """Helper to convert inline markdown into clean HTML without entity artifacts."""
        if not text:
            return ""
        
        # 1. Protect & convert links [text](url) -> <a href="url">text</a>
        def replace_link(match):
            title = match.group(1)
            url = html.unescape(match.group(2))
            return f'<a href="{url}" style="color: #2563eb; text-decoration: underline; font-weight: 600;">{title}</a>'
        
        t = re.sub(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)', replace_link, text)
        
        # 2. Bold (**text**)
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
        
        # 3. Italic notes *(_text_)* or *(text)*
        t = re.sub(r'\*\(_(.+?)_\)\*', r'<em>(\1)</em>', t)
        t = re.sub(r'\*\((.+?)\)\*', r'<em>(\1)</em>', t)
        
        # 4. Italics (_text_)
        t = re.sub(r'(?<!\w)_([^_\n]+?)_(?!\w)', r'<em>\1</em>', t)
        
        # 5. Single asterisk bold (*text*)
        t = re.sub(r'(?<!^)(?<!\n)(?<!\w)\*([^*\n]+?)\*(?!\w)', r'<strong>\1</strong>', t)
        
        # 6. Inline code (`code`)
        t = re.sub(r'`([^`]+)`', r'<code style="background-color: #f1f5f9; padding: 2px 5px; border-radius: 4px; font-family: monospace; font-size: 0.9em; color: #0f172a;">\1</code>', t)
        
        return t

    def markdown_to_html_body(self, text: str) -> str:
        """Convert markdown text into structured, curated HTML cards for email."""
        if not text:
            return ""

        paragraphs = text.split("\n\n")
        sections_html = []

        for p in paragraphs:
            p_clean = p.strip()
            if not p_clean:
                continue

            # Section 1: Priorities / Schedule Card
            if "Priorities" in p_clean or "Schedule" in p_clean:
                lines = p_clean.split("\n")
                header = self._clean_inline_markdown(lines[0])
                items = []
                notes = []
                for l in lines[1:]:
                    l_trim = l.strip()
                    if l_trim.startswith("•") or l_trim.startswith("*") or l_trim.startswith("-"):
                        item_text = re.sub(r'^[•\*\-]\s*', '', l_trim)
                        items.append(f'<li style="margin-bottom: 8px; color: #1e293b; line-height: 1.5;">{self._clean_inline_markdown(item_text)}</li>')
                    elif l_trim:
                        notes.append(f'<p style="margin: 6px 0 0 0; font-size: 13px; color: #64748b; font-style: italic;">{self._clean_inline_markdown(l_trim)}</p>')

                items_html = f'<ul style="margin: 10px 0 0 0; padding-left: 20px;">{"".join(items)}</ul>' if items else ""
                notes_html = "".join(notes)

                sections_html.append(f"""
                <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 18px 20px; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                  <div style="font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 6px;">
                    {header}
                  </div>
                  {items_html}
                  {notes_html}
                </div>
                """)
                continue

            # Section 2: Health & Fitness Card
            if "Health" in p_clean or "Fitness" in p_clean or "treadmill" in p_clean.lower():
                lines = p_clean.split("\n")
                header = self._clean_inline_markdown(lines[0]) if len(lines) > 1 and ("Health" in lines[0] or "Fitness" in lines[0]) else "🏃 Health & Fitness Check-in"
                body_lines = lines[1:] if len(lines) > 1 and ("Health" in lines[0] or "Fitness" in lines[0]) else lines
                body_html = "".join([f'<p style="margin: 6px 0; color: #334155; line-height: 1.6;">{self._clean_inline_markdown(l)}</p>' for l in body_lines if l.strip()])

                sections_html.append(f"""
                <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #10b981; border-radius: 8px; padding: 18px 20px; margin-bottom: 18px;">
                  <div style="font-size: 15px; font-weight: 700; color: #166534; margin-bottom: 6px;">
                    {header}
                  </div>
                  {body_html}
                </div>
                """)
                continue

            # Section 3: Motivation Card
            if "Motivation" in p_clean or "Focus on progress" in p_clean or p_clean.startswith('_"') or p_clean.startswith('"'):
                lines = p_clean.split("\n")
                header = self._clean_inline_markdown(lines[0]) if len(lines) > 1 and "Motivation" in lines[0] else "⚡ Daily Motivation"
                body_lines = lines[1:] if len(lines) > 1 and "Motivation" in lines[0] else lines
                quote_text = " ".join([l.strip() for l in body_lines if l.strip()])

                sections_html.append(f"""
                <div style="background-color: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid #f59e0b; border-radius: 8px; padding: 16px 20px; margin-bottom: 18px;">
                  <div style="font-size: 14px; font-weight: 700; color: #92400e; margin-bottom: 6px;">
                    {header}
                  </div>
                  <div style="font-size: 14px; color: #78350f; font-style: italic; line-height: 1.6;">
                    {self._clean_inline_markdown(quote_text)}
                  </div>
                </div>
                """)
                continue

            # General intro / outro text
            sections_html.append(f"""
            <p style="margin: 10px 0; color: #334155; font-size: 15px; line-height: 1.65;">
              {self._clean_inline_markdown(p_clean)}
            </p>
            """)

        return "\n".join(sections_html)

    def render_briefing_template(self, body_markdown: str, date_display: str) -> str:
        """Wrap the briefing content into a modern, responsive newsletter-style email container."""
        content_html = self.markdown_to_html_body(body_markdown)
        
        template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Andrei's Daily Morning Briefing</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f1f5f9; padding: 28px 12px;">
    <tr>
      <td align="center">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 580px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06); border: 1px solid #e2e8f0;">
          
          <!-- Header Banner -->
          <tr>
            <td style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 26px 24px;">
              <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td>
                    <div style="font-size: 20px; font-weight: 700; color: #ffffff; letter-spacing: -0.4px;">
                      🌅 Andrei's Morning Briefing
                    </div>
                    <div style="font-size: 13px; color: #94a3b8; margin-top: 4px; font-weight: 500;">
                      Notion Life Hub • {date_display}
                    </div>
                  </td>
                  <td align="right" style="vertical-align: middle;">
                    <span style="background-color: rgba(56, 189, 248, 0.15); color: #38bdf8; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 16px; border: 1px solid rgba(56, 189, 248, 0.3);">
                      AI ASSISTANT
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main Content -->
          <tr>
            <td style="padding: 24px; color: #1e293b; font-size: 14.5px;">
              {content_html}
            </td>
          </tr>

          <!-- Quick Action Buttons -->
          <tr>
            <td style="padding: 0 24px 24px 24px;">
              <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 18px;">
                <tr>
                  <td style="font-size: 13px; color: #475569;">
                    <strong>📱 Life Hub Shortcuts:</strong>
                  </td>
                  <td align="right">
                    <a href="https://app.notion.com" style="display: inline-block; background-color: #0f172a; color: #ffffff; text-decoration: none; font-size: 12px; font-weight: 600; padding: 6px 14px; border-radius: 6px;">Open Notion</a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 24px; text-align: center; font-size: 11.5px; color: #64748b; line-height: 1.5;">
              Delivered automatically by your <strong>Telegram Notion AI Bot</strong>.<br>
              Adjust schedule or on-demand alerts via <code>/briefing</code> or <code>/email</code>.
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
            "Content-Type": "application/json",
            "User-Agent": "NotionAIBot/1.0"
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
            try:
                err_json = json.loads(err_body)
                err_msg = err_json.get("message", err_body)
            except Exception:
                err_msg = err_body
            formatted_err = f"Resend API Error ({e.code}): {err_msg}"
            logger.error(formatted_err)
            return False, formatted_err
        except Exception as e:
            err_msg = f"Resend HTTP request failed: {str(e)}"
            logger.error(err_msg)
            return False, err_msg

    def send_email(self, subject: str, html_body: str, plain_body: str, to_email: Optional[str] = None) -> Tuple[bool, str]:
        """Dispatch email using configured SMTP or Resend provider with graceful fallback."""
        recipient = (to_email or settings.NOTIFICATION_EMAIL_TO).strip()
        if not recipient:
            return False, "No recipient email configured. Please set NOTIFICATION_EMAIL_TO."

        # 1. Try Resend if configured
        if settings.RESEND_API_KEY:
            success, msg = self._send_via_resend(recipient, subject, html_body, plain_body)
            if success:
                return True, msg
            # If Resend failed and SMTP is NOT configured, return Resend's exact error
            if not (settings.SMTP_USER and settings.SMTP_PASSWORD):
                return False, msg
            logger.warning(f"Resend delivery failed ({msg}), attempting SMTP fallback...")

        # 2. Try SMTP if configured
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
