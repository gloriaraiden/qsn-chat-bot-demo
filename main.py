import os
import re
import time
import logging
import unicodedata
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Request, Query, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from google import genai

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
IG_ACCESS_TOKEN: str = os.environ["IG_ACCESS_TOKEN"]
VERIFY_TOKEN: str = os.environ["VERIFY_TOKEN"]
GEMINI_API_KEY: str = os.environ["GEMINI_API_KEY"]
TARGET_THREAD_ID: str = os.environ.get("TARGET_THREAD_ID", "").strip()
DISCOVERY_MODE: bool = TARGET_THREAD_ID in ("", "FIND_ME")
BOT_USERNAME: str = os.environ.get("BOT_USERNAME", "bot_username")
COOLDOWN_SECONDS: int = int(os.environ.get("COOLDOWN_SECONDS", "300"))
IG_SEND_URL: str = "https://graph.instagram.com/v21.0/me/messages"
MAX_RESPONSE_CHARS: int = 900

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("ig-gemini-bot")

# ---------------------------------------------------------------------------
# Gemini setup
# ---------------------------------------------------------------------------
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = (
    "You are an AI assistant in an Instagram group chat. "
    "Your responses must be directly helpful, engaging, and in Turkish. "
    "You MUST keep your responses strictly under 900 characters to prevent "
    "Instagram API truncation errors. Do not use markdown formatting that "
    "looks broken on Instagram (no **, ##, ```, etc.). "
    "Answer directly without filler words."
)



# ---------------------------------------------------------------------------
# Image-generation keyword blocklist (Turkish + English)
# ---------------------------------------------------------------------------
IMAGE_KEYWORDS: list[str] = [
    "görsel oluştur", "resim oluştur", "resim yap", "resim çiz",
    "görsel yap", "görsel çiz", "fotoğraf oluştur", "fotoğraf yap",
    "image oluştur", "generate image", "create image", "draw image",
    "make image", "generate picture", "create picture", "draw picture",
    "dall-e", "dall e", "midjourney", "stable diffusion",
    "görüntü oluştur", "görüntü yap",
]

IMAGE_PATTERN: re.Pattern = re.compile(
    "|".join(re.escape(kw) for kw in IMAGE_KEYWORDS),
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Cooldown state  (in-memory; sufficient for single-instance deployment)
# ---------------------------------------------------------------------------
_last_responses: dict[str, float] = {}


def _cooldown_remaining(sender_id: str) -> float:
    """Return remaining cooldown in seconds (0.0 if expired)."""
    # Eğer bu kişi daha önce mesaj atmadıysa süresini 0.0 kabul et
    last_ts = _last_responses.get(sender_id, 0.0) 
    elapsed = time.time() - last_ts
    remaining = COOLDOWN_SECONDS - elapsed
    return max(remaining, 0.0)


def _record_response(sender_id: str) -> None:
    # Sadece mesaj atan kişinin süresini şu anki zaman olarak kaydet
    _last_responses[sender_id] = time.time()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _normalize(text: str) -> str:
    """Lowercase, strip accents (for loose matching), collapse whitespace."""
    text = text.lower().strip()
    nfkd = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    stripped = re.sub(r"[^\w\s]", "", stripped)
    return re.sub(r"\s+", " ", stripped).strip()


def _is_cooldown_query(text: str) -> bool:
    """Detect the special 'kaç dakika kaldı' command."""
    normalized = _normalize(text)
    bot_tag = _normalize(BOT_USERNAME).replace("@", "")
    normalized = normalized.replace(bot_tag, "").strip()
    return normalized in (
        "kac dakika kaldi",
        "kac dk kaldi",
        "ne kadar kaldi",
        "kac dakika",
    )


def _contains_mention(text: str) -> bool:
    """Check whether the message contains the bot's @username."""
    username = BOT_USERNAME.lstrip("@").lower()
    return f"@{username}" in text.lower()


def _strip_mention(text: str) -> str:
    """Remove the bot mention from the user prompt."""
    username = BOT_USERNAME.lstrip("@")
    return re.sub(rf"@?{re.escape(username)}", "", text, flags=re.IGNORECASE).strip()


def _wants_image(text: str) -> bool:
    return bool(IMAGE_PATTERN.search(text))


async def _send_ig_message(target_id: str, text: str) -> None:
    """Send a text message back to the Instagram thread."""
    payload = {
        "recipient": {"id": target_id},
        "message": {"text": text[:MAX_RESPONSE_CHARS]},
    }
    headers = {
        "Authorization": f"Bearer {IG_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(IG_SEND_URL, json=payload, headers=headers)
        if resp.status_code != 200:
            log.error("IG send failed (%s): %s", resp.status_code, resp.text)
        else:
            log.info("Message sent to thread %s", target_id)


async def _get_ig_user_name(sender_id: str) -> str:
    """Instagram Mesajlaşma API'sindeki sender_id, Facebook Graph API ile uyumlu değil.
    İsim çekme 400 döndüğü için doğrudan Misafir dönüyoruz."""
    return "Misafir"

# Model tanımlama ve soru sorma işlemi
async def _ask_gemini(prompt: str, user_name: str) -> str:
    try:
        # Talimatı prompt içine gömüyoruz (system_instruction API hatası vermez)
        full_prompt = (
            f"{SYSTEM_INSTRUCTION} Kullanıcının adı {user_name}. Ona ismiyle hitap et.\n\n"
            f"Kullanıcı sorusu: {prompt}"
        )
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=full_prompt,
        )
        if response and response.text and response.text.strip():
            return response.text
        else:
            log.warning("Gemini boş yanıt döndürdü.")
            return "Üzgünüm, bu içeriğe şu anda yanıt veremiyorum."
    except Exception as e:
        log.error("Gemini API hatası: %s", e)
        return "Üzgünüm, şu anda yanıt oluşturamıyorum. Lütfen biraz sonra tekrar deneyin."


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_app: FastAPI):
    if DISCOVERY_MODE:
        log.info(
            "========================================================\n"
            "  DISCOVERY MODE ACTIVE\n"
            "  Send a message in your Instagram group chat.\n"
            "  The Thread ID will be printed here in the console.\n"
            "  Then set TARGET_THREAD_ID in .env and restart.\n"
            "========================================================"
        )
    else:
        log.info("Bot started — target thread: %s, cooldown: %ds", TARGET_THREAD_ID, COOLDOWN_SECONDS)
    yield
    log.info("Bot shutting down")


app = FastAPI(title="Instagram Gemini Bot", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Webhook verification (GET)
# ---------------------------------------------------------------------------
@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        log.info("Webhook verified")
        return PlainTextResponse(hub_challenge)
    log.warning("Webhook verification failed (mode=%s)", hub_mode)
    raise HTTPException(status_code=403, detail="Verification failed")


# ---------------------------------------------------------------------------
# Webhook event receiver (POST)
# ---------------------------------------------------------------------------
@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    log.debug("Incoming payload: %s", body)

    for entry in body.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            # İşlemi arka plana atıyoruz, böylece Instagram'a anında 200 döneriz.
            background_tasks.add_task(_handle_message, messaging_event)

    return {"status": "ok"}


async def _handle_message(event: dict) -> None:
    """Core message handler implementing all business rules."""
    message = event.get("message", {})
    text: str | None = message.get("text")
    sender_id: str = event.get("sender", {}).get("id", "")
    thread_id: str = event.get("recipient", {}).get("id", "")

    if not text:
        return

    # --- Echo filtresi: Botun kendi gönderdiği mesajları yoksay (Meta webhook is_echo=true) ---
    if message.get("is_echo") is True:
        log.debug("Echo mesajı yoksayılıyor (is_echo=true)")
        return

    # --- Discovery mode: log thread ID and stop ---
    if DISCOVERY_MODE:
        log.info(
            "\n"
            "========================================================\n"
            "  === THREAD ID FOUND: %s ===\n"
            "  Sender: %s\n"
            "  Message: %s\n"
            "  \n"
            "  Copy the Thread ID above into TARGET_THREAD_ID in\n"
            "  your .env file, then restart the server.\n"
            "========================================================",
            thread_id, sender_id, text[:120],
        )
        return

    # --- Rule 1: Target thread only ---
    #if thread_id != TARGET_THREAD_ID:
    #    log.debug("Ignoring message from non-target thread %s", thread_id)
    #    return

    # --- Rule 2: Mention trigger ---
    #if not _contains_mention(text):
    #    log.debug("Ignoring message without bot mention from %s", sender_id)
    #    return

    # Yanıt alıcısı: DM ve grup için sender_id kullanılır (Instagram API otomatik yönlendirir)
    reply_to_id: str = sender_id

    log.info("Processing message from %s: %s", sender_id, text[:80])

    # --- Rule 4: Special "kaç dakika kaldı" command (always replies) ---
    if _is_cooldown_query(text):
        remaining = _cooldown_remaining(sender_id)
        if remaining <= 0:
            reply = "Şu an bana soru sorabilirsiniz!"
        else:
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            if minutes > 0 and seconds > 0:
                reply = f"Bir sonraki mesaj için {minutes} dakika {seconds} saniye beklemeniz gerekiyor."
            elif minutes > 0:
                reply = f"Bir sonraki mesaj için {minutes} dakika beklemeniz gerekiyor."
            else:
                reply = f"Bir sonraki mesaj için {seconds} saniye beklemeniz gerekiyor."
        await _send_ig_message(reply_to_id, reply)
        return

    # --- Rule 3: Cooldown — stay completely silent to prevent spam ---
    remaining = _cooldown_remaining(sender_id)
    if remaining > 0:
        log.debug("Cooldown active (%.0fs left), silently ignoring message from %s", remaining, sender_id)
        return

    # Strip the @mention from the prompt before processing
    prompt = _strip_mention(text)

    # 1. İsmi çekiyoruz
    user_name = await _get_ig_user_name(sender_id)

    if not prompt:
        await _send_ig_message(reply_to_id, f"Merhaba {user_name}, lütfen bir soru veya mesaj yazın.")
        return

    # --- Rule 5: Image generation prevention ---
    if _wants_image(prompt):
        await _send_ig_message(reply_to_id, f"Üzgünüm {user_name}, şu anlık görsel oluşturamıyorum.")
        return

    # --- Gemini call ---
    # 2. Prompt ve çekilen ismi Gemini'ye yolluyoruz
    reply = await _ask_gemini(prompt, user_name)
    _record_response(sender_id)
    await _send_ig_message(reply_to_id, reply)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "cooldown_seconds": COOLDOWN_SECONDS}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
