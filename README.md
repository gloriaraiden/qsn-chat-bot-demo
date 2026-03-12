# Instagram Gemini Bot

Instagram grup sohbetlerini Google Gemini ile bağlayan FastAPI webhook. Bot, Türkçe yanıt verir, kullanıcı bazlı cooldown uygular, görsel oluşturma isteklerini engeller ve kendi mesajlarını (echo) filtreler.

---

**English:** A FastAPI webhook that connects Instagram group chats to Google Gemini. The bot replies in Turkish, enforces per-user cooldown, blocks image-generation requests, and filters its own echoed messages.

---

## Özellikler / Features

| Özellik | Feature |
|---------|---------|
| Google Gemini 1.5 Flash (v1beta API) | Google Gemini 1.5 Flash (v1beta API) |
| Kullanıcı bazlı cooldown | Per-user cooldown |
| `is_echo` ile sonsuz döngü önleme | Prevents infinite loop via `is_echo` |
| DM ve grup desteği | DM and group chat support |
| Background tasks ile hızlı webhook yanıtı | Fast webhook response with background tasks |
| Görsel oluşturma isteklerini engelleme | Blocks image-generation requests |
| "Kaç dakika kaldı?" komutu | "How many minutes left?" command |

---

## Hızlı Başlangıç / Quick Start

```bash
# 1. Projeyi klonlayın / Clone the project
cd FIproject

# 2. Sanal ortam oluşturun / Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Bağımlılıkları yükleyin / Install dependencies
pip install -r requirements.txt

# 4. .env dosyası oluşturun / Create .env file
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux

# 5. Sunucuyu çalıştırın / Run the server
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Ortam Değişkenleri / Environment Variables

| Variable | Açıklama / Description |
|----------|------------------------|
| `IG_ACCESS_TOKEN` | Instagram sayfa erişim tokenı (`instagram_manage_messages` izni gerekli) |
| `VERIFY_TOKEN` | Meta webhook yapılandırmasında belirlediğiniz doğrulama anahtarı |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) API anahtarı |
| `TARGET_THREAD_ID` | Botun yanıt vereceği grup sohbeti thread ID'si (boş veya `FIND_ME` = Discovery modu) |
| `BOT_USERNAME` | Botun Instagram kullanıcı adı (@ olmadan) |
| `COOLDOWN_SECONDS` | AI yanıtları arası süre (varsayılan `300` = 5 dk) |

---

## Thread ID Nasıl Bulunur? / How to Find Thread ID

**Discovery Modu (Önerilen):** `TARGET_THREAD_ID` boş veya `FIND_ME` olarak ayarlayın, sunucuyu çalıştırın. Grupta mesaj gönderin, konsolda thread ID yazdırılacak.

**API Explorer:** [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/) → `GET /me/conversations?platform=instagram`

---

## Deploy (Render)

1. Repoyu GitHub'a push edin.
2. [render.com](https://render.com) üzerinde **Web Service** oluşturun.
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Environment variables'ı Render paneline ekleyin.
6. Meta App Dashboard'da webhook callback URL: `https://<your-app>.onrender.com/webhook`

---

## Meta Webhook Kurulumu

1. [Meta for Developers](https://developers.facebook.com/) → Uygulamanız → **Webhooks**
2. **Instagram** ürününe abone olun, event: **messages**
3. **Callback URL:** `https://<your-domain>/webhook`
4. **Verify Token:** `.env` içindeki `VERIFY_TOKEN` ile aynı olmalı

---

## API Endpoints

| Method | Path | Açıklama |
|--------|------|----------|
| `GET` | `/webhook` | Meta webhook doğrulama |
| `POST` | `/webhook` | Gelen Instagram mesajları |
| `GET` | `/health` | Durum kontrolü |

---

## Teknolojiler / Tech Stack

- **FastAPI** – Web framework
- **Google Gemini** – AI (gemini-1.5-flash, v1beta)
- **httpx** – HTTP client
- **Instagram Messaging API** – Mesajlaşma
