# Instagram Gemini Bot

## Türkçe

Instagram grup sohbetlerini Google Gemini ile bağlayan FastAPI webhook. Bot, Türkçe yanıt verir, kullanıcı bazlı cooldown uygular, görsel oluşturma isteklerini engeller ve kendi mesajlarını (echo) filtreler.

**Özellikler:**
- Google Gemini 1.5 Flash (v1beta API)
- Kullanıcı bazlı cooldown
- `is_echo` ile sonsuz döngü önleme
- DM ve grup desteği
- Background tasks ile hızlı webhook yanıtı
- Görsel oluşturma isteklerini engelleme
- "Kaç dakika kaldı?" komutu

---

## English

A FastAPI webhook that connects Instagram group chats to Google Gemini. The bot replies in Turkish, enforces per-user cooldown, blocks image-generation requests, and filters its own echoed messages.

**Features:**
- Google Gemini 1.5 Flash (v1beta API)
- Per-user cooldown
- Prevents infinite loop via `is_echo`
- DM and group chat support
- Fast webhook response with background tasks
- Blocks image-generation requests
- "How many minutes left?" command

---

## Türkçe — Hızlı Başlangıç

```bash
# 1. Projeyi klonlayın
cd FIproject

# 2. Sanal ortam oluşturun
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. .env dosyası oluşturun
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux

# 5. Sunucuyu çalıştırın
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## English — Quick Start

```bash
# 1. Clone the project
cd FIproject

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux

# 5. Run the server
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Türkçe — Ortam Değişkenleri

| Değişken | Açıklama |
|----------|----------|
| `IG_ACCESS_TOKEN` | Instagram sayfa erişim tokenı (`instagram_manage_messages` izni gerekli) |
| `VERIFY_TOKEN` | Meta webhook yapılandırmasında belirlediğiniz doğrulama anahtarı |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) API anahtarı |
| `TARGET_THREAD_ID` | Botun yanıt vereceği grup sohbeti thread ID'si (boş veya `FIND_ME` = Discovery modu) |
| `BOT_USERNAME` | Botun Instagram kullanıcı adı (@ olmadan) |
| `COOLDOWN_SECONDS` | AI yanıtları arası süre (varsayılan `300` = 5 dk) |

---

## English — Environment Variables

| Variable | Description |
|----------|-------------|
| `IG_ACCESS_TOKEN` | Instagram page access token (requires `instagram_manage_messages` permission) |
| `VERIFY_TOKEN` | Arbitrary string you set in the Meta webhook configuration |
| `GEMINI_API_KEY` | API key from [Google AI Studio](https://aistudio.google.com/apikey) |
| `TARGET_THREAD_ID` | Thread ID the bot should respond in (empty or `FIND_ME` = Discovery mode) |
| `BOT_USERNAME` | Bot's Instagram username (without @) |
| `COOLDOWN_SECONDS` | Seconds between AI responses (default `300` = 5 min) |

---

## Türkçe — Thread ID Nasıl Bulunur?

**Discovery Modu (Önerilen):** `TARGET_THREAD_ID` boş veya `FIND_ME` olarak ayarlayın, sunucuyu çalıştırın. Grupta mesaj gönderin, konsolda thread ID yazdırılacak.

**API Explorer:** [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/) → `GET /me/conversations?platform=instagram`

---

## English — How to Find Thread ID

**Discovery Mode (Recommended):** Set `TARGET_THREAD_ID` to empty or `FIND_ME`, run the server. Send a message in the group chat, the thread ID will be printed in the console.

**API Explorer:** [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/) → `GET /me/conversations?platform=instagram`

---

## Türkçe — Deploy (Render)

1. Repoyu GitHub'a push edin.
2. [render.com](https://render.com) üzerinde **Web Service** oluşturun.
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Ortam değişkenlerini Render paneline ekleyin.
6. Meta App Dashboard'da webhook callback URL: `https://<your-app>.onrender.com/webhook`

---

## English — Deploy (Render)

1. Push the repo to GitHub.
2. Create a **Web Service** on [render.com](https://render.com).
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in the Render dashboard.
6. Webhook callback URL in Meta App Dashboard: `https://<your-app>.onrender.com/webhook`

---

## Türkçe — Meta Webhook Kurulumu

1. [Meta for Developers](https://developers.facebook.com/) → Uygulamanız → **Webhooks**
2. **Instagram** ürününe abone olun, event: **messages**
3. **Callback URL:** `https://<your-domain>/webhook`
4. **Verify Token:** `.env` içindeki `VERIFY_TOKEN` ile aynı olmalı

---

## English — Meta Webhook Setup

1. [Meta for Developers](https://developers.facebook.com/) → Your app → **Webhooks**
2. Subscribe to **Instagram** product, event type: **messages**
3. **Callback URL:** `https://<your-domain>/webhook`
4. **Verify Token:** Must match `VERIFY_TOKEN` in your `.env`

---

## Türkçe — API Endpoints

| Method | Path | Açıklama |
|--------|------|----------|
| `GET` | `/webhook` | Meta webhook doğrulama |
| `POST` | `/webhook` | Gelen Instagram mesajları |
| `GET` | `/health` | Durum kontrolü |

---

## English — API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/webhook` | Meta webhook verification |
| `POST` | `/webhook` | Receives incoming Instagram messages |
| `GET` | `/health` | Health check |

---

## Türkçe — Teknolojiler

- **FastAPI** – Web framework
- **Google Gemini** – AI (gemini-1.5-flash, v1beta)
- **httpx** – HTTP client
- **Instagram Messaging API** – Mesajlaşma

---

## English — Tech Stack

- **FastAPI** – Web framework
- **Google Gemini** – AI (gemini-1.5-flash, v1beta)
- **httpx** – HTTP client
- **Instagram Messaging API** – Messaging
