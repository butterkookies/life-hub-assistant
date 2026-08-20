import logging
import requests
from fastapi import FastAPI, Form, Response, Request, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse

from config import settings
from gemini_agent import gemini_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("whatsapp_bot")

app = FastAPI(title="Notion WhatsApp AI Assistant", version="1.0.0")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head><title>Notion WhatsApp AI Assistant</title></head>
        <body style="font-family: sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; line-height: 1.6;">
            <h2>🤖 Notion WhatsApp AI Assistant is Running!</h2>
            <p>Ready to receive WhatsApp webhooks from Twilio and process them with Google Gemini and Notion.</p>
            <ul>
                <li><strong>Webhook URL:</strong> <code>/webhook</code></li>
                <li><strong>Health Check:</strong> <code>/health</code></li>
            </ul>
        </body>
    </html>
    """

@app.get("/health")
async def health():
    return {"status": "ok", "service": "notion-whatsapp-bot"}

@app.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(""),
    NumMedia: int = Form(0),
    MediaUrl0: str = Form(None),
    MediaContentType0: str = Form(None)
):
    """Webhook endpoint called by Twilio when an incoming WhatsApp message is received."""
    logger.info(f"Incoming WhatsApp message from {From}. Body: '{Body}', NumMedia: {NumMedia}")

    # 1. Check Phone Authorization Whitelist
    if not settings.is_authorized(From):
        logger.warning(f"Unauthorized access attempt from {From}")
        resp = MessagingResponse()
        resp.message("⛔ *Access Denied:* Your phone number is not authorized to interact with this Notion workspace.")
        return Response(content=str(resp), media_type="application/xml")

    reply_text = ""

    # 2. Check for Voice / Audio Media
    if NumMedia > 0 and MediaUrl0:
        logger.info(f"Received media message ({MediaContentType0}) from {From}: {MediaUrl0}")
        try:
            # Twilio media might require basic auth with Twilio account SID and Auth token
            auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN) if settings.TWILIO_ACCOUNT_SID else None
            media_resp = requests.get(MediaUrl0, auth=auth, timeout=30)
            if media_resp.status_code == 200:
                audio_bytes = media_resp.content
                mime_type = MediaContentType0 or "audio/ogg"
                reply_text = gemini_agent.process_voice_message(user_id=From, audio_bytes=audio_bytes, mime_type=mime_type)
            else:
                reply_text = f"⚠️ Could not download audio attachment (HTTP {media_resp.status_code})."
        except Exception as e:
            logger.error(f"Error downloading media: {e}", exc_info=True)
            reply_text = f"⚠️ Failed to process voice note: {str(e)}"
    
    # 3. Process Text Message
    elif Body:
        reply_text = gemini_agent.process_text_message(user_id=From, message_text=Body)
    else:
        reply_text = "👋 Hello! Send me a text or voice note with any Notion task, question, or note to record."

    # 4. Respond with TwiML
    twiml_resp = MessagingResponse()
    twiml_resp.message(reply_text)
    return Response(content=str(twiml_resp), media_type="application/xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("whatsapp_bot:app", host="0.0.0.0", port=settings.PORT, reload=True)
