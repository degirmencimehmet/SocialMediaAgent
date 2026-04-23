# AI Sosyal Medya Ajansı — Kullanım Kılavuzu

> SRS: SENG472 Team 2 | Stack: Python + FastAPI + React + Gemini + ChromaDB + Telegram

---

## İçindekiler

1. [Ön Koşullar](#1-ön-koşullar)
2. [Proje Kurulumu](#2-proje-kurulumu)
3. [API Anahtarları Edinme](#3-api-anahtarları-edinme)
4. [Telegram Bot Kurulumu](#4-telegram-bot-kurulumu)
5. [Meta Graph API Kurulumu (Instagram)](#5-meta-graph-api-kurulumu-instagram)
6. [Projeyi Başlatma](#6-projeyi-başlatma)
7. [İlk Kullanım Akışı](#7-i̇lk-kullanım-akışı)
8. [Web Arayüzü Rehberi](#8-web-arayüzü-rehberi)
9. [Telegram ile İçerik Onaylama](#9-telegram-ile-i̇çerik-onaylama)
10. [Marka Verisi Yükleme (RAG)](#10-marka-verisi-yükleme-rag)
11. [Sorun Giderme](#11-sorun-giderme)
12. [Proje Dosya Yapısı](#12-proje-dosya-yapısı)

---

## 1. Ön Koşullar

Başlamadan önce bilgisayarında şunların kurulu olduğunu doğrula:

```bash
python3 --version   # 3.11 veya üstü gerekli
node --version      # 18 veya üstü gerekli
npm --version       # 9 veya üstü gerekli
```

Eksik olanları kur:
- Python: https://www.python.org/downloads/
- Node.js: https://nodejs.org/

---

## 2. Proje Kurulumu

### Adım 1 — .env dosyasını oluştur

```bash
cd ~/Desktop/social-media-agent/backend
cp .env.example .env
```

Şimdi `.env` dosyasını bir metin editörüyle aç. Aşağıdaki bölümleri sırayla dolduracaksın.

### Adım 2 — Python sanal ortamı kur

```bash
cd ~/Desktop/social-media-agent/backend
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### Adım 3 — Frontend bağımlılıklarını kur

```bash
cd ~/Desktop/social-media-agent/frontend
npm install
```

---

## 3. API Anahtarları Edinme

### Gemini API Key (ZORUNLU — LLM motoru)

1. https://aistudio.google.com/ adresine git
2. Google hesabınla giriş yap
3. Sol menüden **"Get API key"** → **"Create API key"**
4. Anahtarı kopyala
5. `.env` dosyasına yaz:
   ```
   GEMINI_API_KEY=AIzaSy...buraya_yapıştır
   GEMINI_MODEL=gemini-1.5-pro
   ```

> **Not:** Gemini API'nin ücretsiz katmanı vardır (dakikada 15 istek). Demo için yeterlidir.

### SerpAPI Key (OPSİYONEL — rakip analizi)

1. https://serpapi.com/ → ücretsiz hesap aç
2. Dashboard → API Key kısmını kopyala
3. `.env` dosyasına yaz:
   ```
   SERPAPI_KEY=...buraya_yapıştır
   ```

> **Not:** SerpAPI olmadan sistem pytrends (Google Trends) ile çalışmaya devam eder. Trend analizi daha basit olur ama çalışır.

---

## 4. Telegram Bot Kurulumu

Bu adım **zorunludur** — onay akışı Telegram üzerinden çalışır.

### Adım 1 — Bot oluştur

1. Telegram'ı aç
2. Arama çubuğuna **@BotFather** yaz, aç
3. `/newbot` komutunu gönder
4. Bot için bir isim gir (örn: `Mavi Koy Sosyal Medya`)
5. Bot için bir kullanıcı adı gir — `_bot` ile bitmeli (örn: `mavikoy_sm_bot`)
6. BotFather sana şöyle bir token verir:
   ```
   123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
7. Bu tokeni `.env` dosyasına yaz:
   ```
   TELEGRAM_BOT_TOKEN=123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### Adım 2 — Kendi chat ID'ni öğren

1. Telegram'da **@userinfobot** yaz, aç
2. Herhangi bir mesaj gönder (örn: `/start`)
3. Bot sana şunu söyler:
   ```
   Your user ID: 987654321
   ```
4. Bu sayıyı `.env` dosyasına yaz:
   ```
   TELEGRAM_OWNER_CHAT_ID=987654321
   ```

### Adım 3 — Botu başlat

1. Az önce oluşturduğun botu Telegram'da bul (`@mavikoy_sm_bot`)
2. `/start` mesajını gönder
3. Backend çalışırken bu bot otomatik olarak aktif olacak

> **Güvenlik notu:** Sistem yalnızca `TELEGRAM_OWNER_CHAT_ID`'deki hesaptan gelen mesajları işler. Başka biri bota mesaj atsa "Yetkisiz erişim" alır.

---

## 5. Meta Graph API Kurulumu (Instagram)

Bu adım **opsiyoneldir** — yapılandırılmadan sistem içerik üretir ve Telegram'dan onaylatır, sadece Instagram'a otomatik yayın yapamaz. Onaylanan içerikleri manuel olarak paylaşabilirsin.

### Adım 1 — Meta Developer hesabı

1. https://developers.facebook.com/apps/ git
2. **"Create App"** → **"Business"** tipi seç
3. App adını gir

### Adım 2 — Instagram Graph API ekle

1. App Dashboard → **"Add Product"** → **Instagram Graph API** → Set Up
2. Sol menü → **Instagram** → **API Setup**

### Adım 3 — Instagram hesabını bağla

1. Instagram hesabın bir **Business** veya **Creator** hesabı olmalı
   - Instagram → Ayarlar → Hesap → Profesyonel hesaba geç
2. Bu Instagram hesabını bir **Facebook Sayfasına** bağla
   - Facebook → Sayfalar → Ayarlar → Instagram

### Adım 4 — Access Token al

1. Meta App Dashboard → **System Users** oluştur
2. System User'a Instagram hesabı için `instagram_basic` ve `instagram_content_publish` izinlerini ver
3. **"Generate Token"** → 60 günlük uzun ömürlü token al
4. `.env` dosyasına yaz:
   ```
   META_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxx...
   ```

### Adım 5 — Instagram Hesap ID'ni bul

```bash
curl "https://graph.facebook.com/v19.0/me/accounts?access_token=SENIN_TOKEN"
```

Dönen JSON'daki `instagram_business_account.id` değerini kopyala:
```
INSTAGRAM_ACCOUNT_ID=17841xxxxxxxxxx
```

> **Not:** Sandbox modunda yayınlar sadece sana görünür. Herkese açık yayın için Meta App Review gerekir.

---

## 6. Projeyi Başlatma

### Tek komutla başlat (önerilen)

```bash
cd ~/Desktop/social-media-agent
./start.sh
```

Bu script:
- Backend'i http://localhost:8000 adresinde başlatır
- Frontend'i http://localhost:5173 adresinde başlatır
- Telegram botunu arka planda çalıştırır

### Manuel başlatma (debug için)

**Terminal 1 — Backend:**
```bash
cd ~/Desktop/social-media-agent/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd ~/Desktop/social-media-agent/frontend
npm run dev
```

### Erişim adresleri

| Servis | URL |
|--------|-----|
| Web Arayüzü | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Dökümantasyonu (Swagger) | http://localhost:8000/docs |

---

## 7. İlk Kullanım Akışı

Sistemi ilk kez çalıştırıyorsun. Şu sırayı izle:

### Aşama 1 — Marka Profilini Doldur (5 dakika)

1. http://localhost:5173/settings adresine git
2. İşletme bilgilerini gir:
   - İşletme adı (örn: "Mavi Koy Butik Otel")
   - İşletme türü
   - Konum (örn: "Bodrum, Türkiye")
   - Açıklama (ne yaptığını, ne sunduğunu)
   - Hedef kitle (örn: "Yurt içi çiftler, tatil aileler")
   - Tercih edilen ton
3. **Kaydet**

### Aşama 2 — Geçmiş İçerik Yükle (OPSİYONEL ama önerilir)

RAG sistemi daha iyi çalışmak için geçmiş Instagram gönderilerine ihtiyaç duyar.
Mevcut gönderilerini API üzerinden yükle:

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "hotel_001",
    "posts": [
      {
        "caption": "Deniz manzaralı odalarımızda eşsiz bir konaklama deneyimi sizi bekliyor.",
        "hashtags": ["#bodrum", "#butikoteli", "#tatil"],
        "platform": "instagram",
        "date": "2025-06-15"
      },
      {
        "caption": "Güne açık büfe kahvaltımızla başlayın!",
        "hashtags": ["#kahvalti", "#otel", "#bodrum"],
        "platform": "instagram",
        "date": "2025-06-20"
      }
    ]
  }'
```

Ne kadar fazla örnek post yüklersan, AI o kadar iyi marka sesi öğrenir.

### Aşama 3 — İlk İçeriği Oluştur

**Yöntem A — Web Arayüzü:**
1. http://localhost:5173/dashboard git
2. "Yeni İçerik Oluştur" kutusuna yaz: `"Yarın akşam yıldız altında havuz partimiz var"`
3. Platform olarak "Instagram" seç
4. **"İçerik Oluştur"** butonuna tıkla
5. ~5-10 saniye içinde taslak gelir

**Yöntem B — Telegram:**
1. Oluşturduğun bota git
2. Direkt mesaj yaz: `"Yarın akşam yıldız altında havuz partimiz var"`
3. Sistem otomatik işler ve sana Telegram'dan taslak gönderir

### Aşama 4 — Onayla veya Reddet

Telegram'dan gelen mesajda:
- **✅ Onayla** → Post yayın kuyruğuna alınır, belirlenen saatte Instagram'a gönderilir
- **❌ Reddet** → Taslak reddedildi olarak loglanır

Web arayüzünden de onaylayabilirsin: Dashboard → "Onayla" butonu.

---

## 8. Web Arayüzü Rehberi

### Dashboard (`/dashboard`)

```
┌─────────────────────────────────────────────────┐
│  İstatistik Kartları (Toplam / Onaylı / Yayında) │
├─────────────────────────────────────────────────┤
│  İçerik Oluşturma Formu                         │
│  ┌─────────────────────────────────┐            │
│  │ "Promosyonumu açıkla..."        │            │
│  └─────────────────────────────────┘            │
│  [Platform seç]  [İçerik Oluştur]               │
├─────────────────────────────────────────────────┤
│  Onay Bekleyen Gönderiler                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ PostCard │ │ PostCard │ │ PostCard │        │
│  │ [✅][❌] │ │ [✅][❌] │ │ [✅][❌] │        │
│  └──────────┘ └──────────┘ └──────────┘        │
└─────────────────────────────────────────────────┘
```

- Her PostCard'da: platform, ton, başlık, hashtag'ler, görsel önerisi, zamanlama
- Onay/Reddet butonları doğrudan kartın üzerinde

### Takvim (`/calendar`)

- Aylık grid görünüm — her hücrede o güne ait gönderiler
- Sol/Sağ oklar ile ay değiştir
- Sağ üstte **PDF** ve **JSON** export butonları
- Renk kodu: Yeşil = Onaylı, Mavi = Yayında, Sarı = Bekliyor

### Analitik (`/analytics`)

- KPI kartları: Toplam içerik, Onay oranı, Ortalama beğeni, Ortalama erişim
- Pasta grafik: İçerik durumu dağılımı
- Bar grafik: Ortalama etkileşim metrikleri

> **Not:** Etkileşim verileri (beğeni, erişim) Meta API bağlantısı gerektirer. Bağlantı yoksa sıfır görünür.

### Ayarlar (`/settings`)

- Marka profili formu
- Telegram kurulum rehberi (adım adım)
- Meta Graph API kurulum rehberi

---

## 9. Telegram ile İçerik Onaylama

### Normal Akış

```
Sen (Telegram'a yaz)
  └─→ "Yarın brunch menümüzü tanıt"
        └─→ Sistem: RAG + Trend + Gemini çalışır
              └─→ Telegram'a taslak gelir (≤10 sn)
                    └─→ Sen: [✅ Onayla] veya [❌ Reddet]
                          └─→ Onaylandıysa: APScheduler kuyruğa alır
                                └─→ Belirlenen saatte Instagram'a yayınlanır
```

### Taslak Formatı

Telegram'dan şu formatta bir mesaj alırsın:

```
📝 Yeni İçerik Taslağı (ID: 42)

📱 Platform: INSTAGRAM
🎭 Ton: promotional

─────────────────────────
Sabahları denizi izlerken sıcak kahvenizi yudumlamak ister misiniz? ☀️
Mavi Koy'un efsanevi açık büfesi her gün 07:00–11:00 arası sizi bekliyor.

#bodrum #kahvalti #butikoteli #tatil #turkey
─────────────────────────
🖼 Görsel öneri: Deniz manzaralı balkonda servis edilen Türk kahvaltısı
🕐 Planlanan yayın: 14 May 2026 09:00

[✅ Onayla]  [❌ Reddet]
```

---

## 10. Bilgi Bankasına İçerik Yükleme (RAG)

Sistem 6 farklı içerik türünü destekler. Her tür ayrı bir ChromaDB koleksiyonunda saklanır.
İçerik oluşturulurken Gemini, sorguyla alakalı tüm koleksiyonlardan otomatik olarak veri çeker.

| `content_type` | Ne için | Örnek |
|---|---|---|
| `brand_voice` | Geçmiş sosyal medya gönderileri (ton öğretimi) | Eski Instagram paylaşımları |
| `recipe` | Yemek / içecek tarifleri | "Fırın sütlaç: süt, pirinç unu, şeker..." |
| `menu` | Menü kalemleri ve fiyatlar | "Izgara levrek — 380 TRY" |
| `local_info` | Yerel gezilecek yerler, kültürel bilgiler | "Bodrum Kalesi 1km uzaklıkta..." |
| `event` | Etkinlikler ve duyurular | "Cuma Latin Gecesi 21:00" |
| `general` | Diğer her türlü bilgi | Ödüller, sertifikalar, hikaye |

### Geçmiş Gönderileri Yükle (brand_voice)

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "hotel_001",
    "content_type": "brand_voice",
    "items": [
      {"caption": "Deniz manzaralı odalarımızda eşsiz bir konaklama...", "hashtags": ["#bodrum"], "platform": "instagram", "date": "2025-06-15"},
      {"caption": "Güne açık büfe kahvaltımızla başlayın!", "hashtags": ["#kahvalti"], "platform": "instagram", "date": "2025-06-20"}
    ]
  }'
```

### Yemek Tariflerini Yükle (recipe)

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "hotel_001",
    "content_type": "recipe",
    "items": [
      {
        "title": "Fırın Sütlaç",
        "text": "Geleneksel Türk fırın sütlacımız; tam yağlı süt, pirinç unu, taze vanilya ve az şekerle hazırlanır. Üzeri kahverengi kızarıncaya kadar fırınlanır. Soğuk servis edilir.",
        "source": "mutfak_ekibi"
      },
      {
        "title": "Ege Kahvaltısı Tabağı",
        "text": "Zeytinyağlı otlar, taze çökelek, siyah zeytin, domates, salatalık, taze ekmek. Hepsi yerel üreticilerden temin edilir.",
        "source": "mutfak_ekibi"
      }
    ]
  }'
```

### Menü Yükle (menu)

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "hotel_001",
    "content_type": "menu",
    "items": [
      {"title": "Izgara Levrek", "text": "Taze Ege levreği, sebze garnitürü ile. 380 TRY"},
      {"title": "Ahtapot Salatası", "text": "Izgara ahtapot, roka, limon sosu. 290 TRY"},
      {"title": "Günlük Tatlı", "text": "Şefin seçimi değişen mevsimsel tatlı. 120 TRY"}
    ]
  }'
```

### Yerel Bilgi Yükle (local_info)

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "hotel_001",
    "content_type": "local_info",
    "items": [
      {"title": "Bodrum Kalesi", "text": "Otelimize 1.2km uzaklıkta. 15. yüzyıldan kalma St. Peter Kalesi. İçinde Sualtı Arkeoloji Müzesi bulunuyor."},
      {"title": "Yalıkavak Marina", "text": "Lüks marina, 8km. Gün batımı için ideal. Yat turları mevcut."}
    ]
  }'
```

### Etkinlik Yükle (event)

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "hotel_001",
    "content_type": "event",
    "items": [
      {"title": "Latin Gecesi", "text": "Her Cuma 21:00-01:00. Canlı müzik, salsa dersleri. Giriş ücretsiz konaklayan misafirler için."},
      {"title": "Şarap Tadımı", "text": "Cumartesi 19:00. Ege bölgesi butik şarapları. Kişi başı 450 TRY, meze dahil."}
    ]
  }'
```

### Yüklenen Koleksiyonları Görüntüle

```bash
curl "http://localhost:8000/api/knowledge-base?tenant_id=hotel_001"
```

Dönen örnek:
```json
[
  {"content_type": "brand_voice", "label": "Geçmiş Sosyal Medya Gönderileri", "count": 24},
  {"content_type": "recipe",      "label": "Yemek / İçecek Tarifleri",        "count": 8},
  {"content_type": "menu",        "label": "Menü Kalemleri",                   "count": 12},
  {"content_type": "local_info",  "label": "Yerel Bilgiler / Gezilecek Yerler","count": 5}
]
```

### Nasıl Çalışır?

```
Kullanıcı: "Sütlacımızı tanıtan bir Instagram postu yaz"
    │
    ▼
BrandVoiceAgent: prompt'a göre TÜM koleksiyonları sorgular
    ├── brand_voice → ton referansı için benzer gönderiler
    ├── recipe      → "Fırın Sütlaç" tarif detayları ← BURAYI BULUR
    └── menu        → fiyat bilgisi
    │
    ▼
Gemini: tarif detaylarını + marka tonunu birleştirip post üretir
→ "Geleneksel fırın sütlacımız, tam yağlı sütten..."
```

Ne kadar fazla ve çeşitli içerik yüklersen, üretilen postlar o kadar özgün ve detaylı olur.

---

## 11. Sorun Giderme

### "Gemini API hatası" alıyorum

- `.env` dosyasında `GEMINI_API_KEY` doğru mu?
- https://aistudio.google.com/ → API key aktif mi?
- Ücretsiz katman limitini aştın mı? (dakikada 15 istek)

### Telegram botu mesajlara yanıt vermiyor

- `.env` dosyasında `TELEGRAM_BOT_TOKEN` doğru mu?
- `TELEGRAM_OWNER_CHAT_ID` senin gerçek Telegram ID'n mi?
- Backend çalışıyor mu? → http://localhost:8000/docs adresini kontrol et
- Terminalde hata var mı? → Backend loglarını kontrol et

### Frontend açılmıyor

```bash
cd ~/Desktop/social-media-agent/frontend
npm install          # bağımlılıkları yeniden kur
npm run dev
```

### "chromadb" hatası alıyorum

```bash
cd ~/Desktop/social-media-agent/backend
source .venv/bin/activate
pip install chromadb --upgrade
```

### Instagram yayını çalışmıyor

- Meta token'ın süresi dolmuş olabilir (60 gün) → yeni token al
- Instagram hesabın Business hesabı mı? → Ayarlar → Profesyonel Hesap
- App Review tamamlandı mı? → Sandbox'ta sadece test kullanıcılarına görünür

### Backend başlamıyor — "port already in use"

```bash
lsof -ti:8000 | xargs kill -9
```

---

## 12. Proje Dosya Yapısı

```
social-media-agent/
│
├── start.sh                          ← Tek komutla başlatma scripti
│
├── backend/
│   ├── .env.example                  ← API anahtar şablonu (bunu kopyala → .env)
│   ├── .env                          ← Gerçek API anahtarların (git'e ekleme!)
│   ├── requirements.txt              ← Python bağımlılıkları
│   ├── config.py                     ← Tüm ayarlar (pydantic-settings)
│   ├── database.py                   ← SQLite modelleri (Post, Metrics, Brand)
│   ├── schemas.py                    ← Pydantic şemaları (SocialMediaPost vb.)
│   ├── main.py                       ← FastAPI app + tüm API route'ları
│   │
│   ├── agents/
│   │   ├── brand_voice_agent.py      ← RAG ile marka sesi öğrenme (FR-01)
│   │   ├── trend_agent.py            ← SerpAPI + pytrends (FR-02)
│   │   ├── content_generation_agent.py ← Gemini ile içerik üretimi (FR-01)
│   │   └── orchestrator.py           ← Tüm agent'ları koordine eder
│   │
│   ├── modules/
│   │   ├── rag_engine.py             ← ChromaDB vektör veritabanı
│   │   ├── telegram_bot.py           ← Bot, onay butonları (FR-03)
│   │   ├── publishing.py             ← Meta Graph API / Instagram (FR-04)
│   │   ├── scheduler.py              ← APScheduler ile zamanlama (FR-04)
│   │   ├── calendar_export.py        ← PDF + JSON takvim export (FR-05)
│   │   └── metrics_collector.py      ← Instagram engagement metrikleri (FR-06)
│   │
│   └── utils/
│       └── sanitizer.py              ← Prompt injection koruması (NFR-SEC-04)
│
└── frontend/
    ├── src/
    │   ├── api/client.js             ← Backend API çağrıları
    │   ├── App.jsx                   ← Router
    │   ├── pages/
    │   │   ├── Dashboard.jsx         ← İçerik oluştur + onayla
    │   │   ├── Calendar.jsx          ← Aylık takvim grid
    │   │   ├── Analytics.jsx         ← Metrik grafikleri
    │   │   └── Settings.jsx          ← Marka profili + API rehberleri
    │   └── components/
    │       ├── Layout.jsx            ← Sidebar + sayfa iskeleti
    │       ├── PostCard.jsx          ← Tekil gönderi kartı
    │       └── StatCard.jsx          ← KPI sayı kartı
    └── ...config dosyaları
```

---

## API Referansı (Özet)

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `POST` | `/api/generate` | Yeni içerik oluştur |
| `GET` | `/api/posts` | Tüm gönderileri listele |
| `POST` | `/api/posts/{id}/approve` | Gönderiyi onayla |
| `POST` | `/api/posts/{id}/reject` | Gönderiyi reddet |
| `GET` | `/api/analytics` | Analitik verileri |
| `GET` | `/api/calendar` | Aylık takvim |
| `GET` | `/api/calendar/pdf` | PDF export (indir) |
| `GET` | `/api/calendar/json` | JSON export (indir) |
| `PUT` | `/api/brand` | Marka profilini güncelle |
| `POST` | `/api/ingest` | Geçmiş postları RAG'a yükle |
| `GET` | `/api/trends` | Güncel trend analizi |

Tüm endpoint detayları için: **http://localhost:8000/docs**

---

*SENG472 Team 2 — Mehmet Değirmenci, İrem Nur Koçak, Umay Şamlı, Türkay Selim Delikanlı*
