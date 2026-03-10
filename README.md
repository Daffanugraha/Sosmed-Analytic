# 📡 SocialHub — Social Media Manager

Aplikasi manajemen konten untuk content creator. Upload sekali, publish ke Instagram, TikTok, Facebook, dan YouTube secara otomatis dengan fitur penjadwalan dan analitik performa.

---

## 🚀 Fitur Utama

| Fitur | Deskripsi |
|---|---|
| **Multi-platform upload** | Publish ke Instagram, TikTok, Facebook, YouTube sekaligus |
| **Penjadwalan** | Tentukan tanggal & jam publikasi |
| **OAuth Login per platform** | Koneksi aman via OAuth 2.0 |
| **Analitik** | Views, likes, komentar, share per hari |
| **Multi-akun** | Hubungkan beberapa akun per platform |
| **Scheduler otomatis** | APScheduler berjalan di background tiap menit |

---

## 📁 Struktur Proyek

```
social_media_manager/
├── app.py                    # Entry point Flask
├── config.py                 # Konfigurasi & env vars
├── scheduler_worker.py       # Background job: publish & analytics sync
├── requirements.txt
├── .env.example              # Template environment variable
├── database/
│   └── models.py             # User, PlatformAccount, Post, Analytics
├── routes/
│   ├── auth.py               # Login / Register / Logout
│   ├── dashboard.py          # Dashboard overview
│   ├── platforms.py          # OAuth connect/disconnect
│   ├── content.py            # Upload, Posts list, Delete
│   └── analytics.py          # Analytics API & page
├── services/
│   ├── base_service.py       # Abstract base class
│   ├── instagram_service.py  # Instagram Graph API
│   ├── tiktok_service.py     # TikTok for Developers API
│   ├── facebook_service.py   # Facebook Graph API
│   └── youtube_service.py    # YouTube Data API v3
├── utils/
│   ├── auth_helper.py
│   └── file_helper.py
├── static/
│   ├── css/main.css
│   └── js/{main,upload,analytics}.js
└── templates/
    ├── base.html
    ├── auth/{login,register}.html
    ├── dashboard/index.html
    ├── content/{upload,posts}.html
    ├── platforms/connect.html
    └── analytics/index.html
```

---

## ⚙️ Setup & Instalasi

### 1. Clone / Extract
```bash
cd social_media_manager
```

### 2. Buat virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate.bat     # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Konfigurasi environment
```bash
cp .env.example .env
# Edit .env dan isi OAuth credentials
```

### 5. Jalankan aplikasi
```bash
python app.py
```

Buka browser: **http://localhost:5000**

---

## 🔑 Cara Dapat OAuth Credentials

### Instagram / Facebook
1. Buka https://developers.facebook.com/
2. Buat App baru → tambahkan produk **Instagram Graph API** dan **Facebook Login**
3. Salin App ID dan App Secret ke `.env`
4. Tambahkan Redirect URI: `http://localhost:5000/platforms/callback`

### TikTok
1. Buka https://developers.tiktok.com/
2. Buat App → aktifkan **Login Kit** dan **Content Posting API**
3. Salin Client Key dan Client Secret

### YouTube
1. Buka https://console.cloud.google.com/
2. Buat Project → enable **YouTube Data API v3** dan **YouTube Analytics API**
3. Buat OAuth 2.0 Client ID (Web Application)
4. Tambahkan Redirect URI: `http://localhost:5000/platforms/callback`

---

## 📊 Alur Kerja

```
User Login → Hubungkan Platform (OAuth) → Upload Konten
→ Pilih Platform + Jadwal → Scheduler publish otomatis
→ Analytics sync tiap jam → Dashboard & Chart
```

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask, SQLAlchemy, APScheduler
- **Database**: SQLite (mudah diganti ke PostgreSQL)
- **Frontend**: HTML5, Bootstrap 5, Vanilla JS, Chart.js
- **Auth**: Flask-Login, Werkzeug password hashing
- **APIs**: Instagram Graph, TikTok for Developers, Facebook Graph, YouTube Data v3
