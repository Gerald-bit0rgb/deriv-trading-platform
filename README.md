# Deriv AI Trading Platform

A production-ready, AI-powered automated trading platform for the Deriv API.

- **Backend**: Python · FastAPI · WebSockets · PostgreSQL · SQLAlchemy
- **Frontend**: Flutter · Material 3 · Riverpod · GoRouter
- **Hosting**: Render (backend) · Android APK (mobile)
- **CI/CD**: GitHub Actions

> ⚠️ **IMPORTANT**: Always test on a **Deriv demo account** before using real money.
> Automated trading carries significant financial risk.

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [How It Works](#2-how-it-works)
3. [Prerequisites](#3-prerequisites)
4. [Get a Deriv API Token](#4-get-a-deriv-api-token)
5. [Local Development Setup](#5-local-development-setup)
6. [GitHub Setup](#6-github-setup)
7. [Deploy Backend to Render](#7-deploy-backend-to-render)
8. [Build the Android APK](#8-build-the-android-apk)
9. [Configure GitHub Actions Secrets](#9-configure-github-actions-secrets)
10. [Environment Variables Reference](#10-environment-variables-reference)
11. [API Reference](#11-api-reference)
12. [Updating the Application](#12-updating-the-application)
13. [Troubleshooting](#13-troubleshooting)
14. [Security Checklist](#14-security-checklist)

---

## 1. Project Structure

```
deriv-trading-platform/
│
├── backend/                        # FastAPI backend (Python)
│   ├── app/
│   │   ├── api/                    # HTTP route handlers
│   │   │   ├── auth.py             # Register, login, token management
│   │   │   ├── trading.py          # Bot control, trade execution
│   │   │   ├── ai.py               # AI signal generation
│   │   │   ├── risk.py             # Risk settings, emergency stop
│   │   │   ├── dashboard.py        # Aggregated dashboard data
│   │   │   └── notifications.py    # Notification history
│   │   ├── core/
│   │   │   ├── config.py           # All settings from environment variables
│   │   │   ├── security.py         # JWT creation/verification, password hashing
│   │   │   ├── logging.py          # Structured JSON logging
│   │   │   └── deps.py             # FastAPI dependency injection
│   │   ├── db/
│   │   │   ├── session.py          # SQLAlchemy async engine + session
│   │   │   └── init_db.py          # Table creation at startup
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── crud/                   # Database query functions
│   │   ├── services/
│   │   │   ├── deriv_client.py     # Deriv WebSocket API client
│   │   │   ├── trading_engine.py   # Automated trading bot
│   │   │   ├── risk_manager.py     # Risk check logic
│   │   │   ├── ai_engine.py        # Technical analysis + signal generation
│   │   │   └── notification_service.py  # Firebase push notifications
│   │   └── main.py                 # FastAPI app factory, startup/shutdown
│   ├── tests/                      # Pytest test suite
│   ├── requirements.txt
│   └── .env.example                # Copy to .env and fill in your values
│
├── frontend/                       # Flutter Android app
│   ├── lib/
│   │   ├── core/
│   │   │   ├── constants/          # App-wide constants, API URL
│   │   │   ├── theme/              # Material 3 dark + light themes
│   │   │   └── utils/              # Router (GoRouter), formatters
│   │   ├── data/
│   │   │   ├── models/             # Freezed data models
│   │   │   ├── services/           # API service classes (Dio)
│   │   │   └── providers/          # Riverpod state providers
│   │   ├── presentation/
│   │   │   ├── screens/            # All app screens
│   │   │   └── widgets/            # Reusable UI components
│   │   └── main.dart               # App entry point
│   ├── android/                    # Android-specific config
│   └── pubspec.yaml                # Flutter dependencies
│
├── .github/workflows/              # GitHub Actions CI/CD
│   ├── backend-ci.yml              # Lint, test, Docker build
│   ├── backend-deploy.yml          # Deploy to Render
│   └── flutter-ci.yml              # Analyse, test, build APK
│
├── Dockerfile                      # Backend container build
├── docker-compose.yml              # Local dev stack
├── render.yaml                     # Render infrastructure-as-code
└── README.md                       # This file
```

---

## 2. How It Works

```
Android App (Flutter)
       │
       │  HTTPS + JWT
       ▼
  FastAPI Backend  ──── PostgreSQL (trades, users, settings)
       │
       │  WebSocket (wss://)
       ▼
  Deriv API  (live market data, contract placement)
       │
       ▼
  AI Engine  (RSI · MACD · Bollinger Bands · EMA · ATR · ADX · Patterns)
       │
       ▼
  BUY / SELL / WAIT  +  confidence score  +  reasoning
```

**Flow when the bot is running:**

1. User taps **Start Bot** in the app.
2. Backend connects to Deriv via WebSocket and authenticates with the user's token.
3. The AI engine fetches 100 candles, computes technical indicators, and scores the market.
4. If the confidence score exceeds the user's minimum threshold (default 65%), the engine places a CALL or PUT contract.
5. A background monitor checks open contracts every 5 seconds and closes them in the database when Deriv reports they are won/lost.
6. Push notifications are sent at every key event (trade open, trade close, stop loss, daily limit reached).

---

## 3. Prerequisites

Install these tools on your computer before starting.

### For backend development

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.11+ | https://python.org/downloads |
| PostgreSQL | 15+ | https://postgresql.org/download |
| Git | Any | https://git-scm.com |
| Docker Desktop | Any (optional) | https://docker.com/products/docker-desktop |

### For Flutter development

| Tool | Version | Download |
|------|---------|----------|
| Flutter SDK | 3.22+ | https://docs.flutter.dev/get-started/install |
| Android Studio | Latest | https://developer.android.com/studio |
| Java JDK | 17 | https://adoptium.net |
| Git | Any | https://git-scm.com |

### Verify your installs

```bash
python --version        # Python 3.11.x
flutter --version       # Flutter 3.22.x
java -version           # openjdk 17.x
git --version           # git 2.x
docker --version        # Docker 24.x (optional)
```

---

## 4. Get a Deriv API Token

You need a Deriv API token to let the backend trade on your behalf.
**Never share this token with anyone and never commit it to Git.**

### Step-by-step

1. Open your browser and go to **https://app.deriv.com**
2. Log in to your account (or create a free demo account).
3. Click your profile icon (top right) → **Account Settings**.
4. In the left menu, click **API Token**.
5. Click **Create new token**.
6. Give it a name, e.g. `TradingBot`.
7. Select these scopes:
   - ✅ **Read** — view account and balance
   - ✅ **Trade** — place and close contracts
   - ✅ **Payments** — view transaction history
8. Click **Create**.
9. Copy the token — it looks like `dxxx_A3xxxxx...`

> **Demo vs Real account**: Deriv gives you a free virtual-money demo account.
> Use a demo account token for all testing. Switch to a real account token
> only when you are completely satisfied the bot works correctly.

### Save the token in the app

After you log in to the mobile app:

1. Go to **Profile** tab → **Deriv API Token** section.
2. Paste the token into the text field.
3. Tap **Save Token**.

The token is stored encrypted in the database. It is never written to logs.

---

## 5. Local Development Setup

### 5a. Clone the project

```bash
# Replace YOUR_USERNAME with your GitHub username after you push it there
git clone https://github.com/YOUR_USERNAME/deriv-trading-platform.git
cd deriv-trading-platform
```

### 5b. Backend — Option A: Docker Compose (easiest)

This starts both PostgreSQL and the FastAPI backend together.

```bash
# 1. Copy the example env file
cp backend/.env.example backend/.env

# 2. Edit backend/.env — fill in SECRET_KEY at minimum:
#    SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(64))">

# 3. Start everything
docker-compose up --build

# Backend is now running at: http://localhost:8000
# API docs at:               http://localhost:8000/docs
```

To stop:
```bash
docker-compose down
```

### 5b. Backend — Option B: Manual (no Docker)

```bash
# 1. Create and activate a virtual environment
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your .env file
copy .env.example .env      # Windows
# cp .env.example .env      # Mac/Linux

# 4. Edit .env — set these values:
#    DATABASE_URL=postgresql+asyncpg://YOUR_USER:YOUR_PASS@localhost:5432/deriv_trading
#    SYNC_DATABASE_URL=postgresql://YOUR_USER:YOUR_PASS@localhost:5432/deriv_trading
#    SECRET_KEY=<run: python -c "import secrets; print(secrets.token_hex(64))">

# 5. Create the database in PostgreSQL
#    Open psql or pgAdmin and run:
#    CREATE DATABASE deriv_trading;

# 6. Start the backend
uvicorn app.main:app --reload --port 8000
```

The backend creates all database tables automatically on first start.

Interactive API docs are available at **http://localhost:8000/docs**

### 5c. Run backend tests

```bash
cd backend
pytest tests/ -v
```

---

## 6. GitHub Setup

You need a GitHub repository to deploy to Render and use CI/CD.

### Step 1 — Create a GitHub account

Go to **https://github.com** and sign up if you don't have an account.

### Step 2 — Create a new repository

1. Click the **+** icon (top right) → **New repository**.
2. Name it: `deriv-trading-platform`
3. Set it to **Private** (recommended — this contains your trading code).
4. Do NOT initialise with README (we already have one).
5. Click **Create repository**.

### Step 3 — Push the project to GitHub

Open a terminal in the project root folder and run these commands one by one:

```bash
# Initialise git (if not already done)
git init

# Add all files
git add .

# Create the first commit
git commit -m "Initial commit — Deriv AI Trading Platform"

# Connect to your GitHub repo (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/deriv-trading-platform.git

# Push to GitHub
git branch -M main
git push -u origin main
```

If prompted, enter your GitHub username and password.
(GitHub now requires a **Personal Access Token** instead of password —
create one at https://github.com/settings/tokens → Generate new token → select `repo` scope)

### Step 4 — Verify

Go to `https://github.com/YOUR_USERNAME/deriv-trading-platform` in your browser.
You should see all the project files there.

---

## 7. Deploy Backend to Render

### Step 1 — Create a Render account

1. Go to **https://render.com** and click **Get Started for Free**.
2. Sign up using your GitHub account (click "Sign up with GitHub").
3. Authorise Render to access your GitHub repositories.

### Step 2 — Create the database first

1. In the Render dashboard, click **New +** → **PostgreSQL**.
2. Fill in:
   - **Name**: `deriv-trading-db`
   - **Database**: `deriv_trading`
   - **User**: `deriv_user`
   - **Region**: Oregon (or closest to you)
   - **Plan**: Free (for testing) or Starter (for production)
3. Click **Create Database**.
4. Wait about 1–2 minutes for it to be ready.
5. Copy the **Internal Database URL** — you will need it later.

### Step 3 — Create the Web Service

1. Click **New +** → **Web Service**.
2. Select **Build and deploy from a Git repository**.
3. Click **Connect** next to your `deriv-trading-platform` repository.
4. Fill in the service settings:

| Field | Value |
|-------|-------|
| **Name** | `deriv-trading-backend` |
| **Region** | Oregon (same as database) |
| **Branch** | `main` |
| **Runtime** | **Docker** |
| **Dockerfile Path** | `./Dockerfile` |
| **Docker Context** | `.` |
| **Plan** | Free (testing) or Starter (production) |

5. Scroll down to **Environment Variables** and add:

| Key | Value | Notes |
|-----|-------|-------|
| `APP_ENV` | `production` | |
| `DEBUG` | `false` | |
| `SECRET_KEY` | *(generate below)* | See command below |
| `ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | |
| `DATABASE_URL` | *(from step 2)* | Replace `postgresql://` with `postgresql+asyncpg://` |
| `SYNC_DATABASE_URL` | *(from step 2)* | Keep as `postgresql://` |
| `DERIV_APP_ID` | `1` | Or your own app ID from api.deriv.com |
| `DERIV_WS_URL` | `wss://ws.derivws.com/websockets/v3` | |
| `CORS_ORIGINS` | `https://deriv-trading-backend.onrender.com` | |
| `LOG_LEVEL` | `INFO` | |

**Generate a SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(64))"
```
Copy the output and paste it as the `SECRET_KEY` value.

6. Click **Create Web Service**.

### Step 4 — Wait for deployment

Render will:
1. Clone your repository.
2. Build the Docker image (takes 3–8 minutes the first time).
3. Start the container.
4. Run database table creation automatically.

Watch the **Logs** tab for progress. A successful deployment ends with:
```
INFO:     Application startup complete.
```

### Step 5 — Test the deployment

Open your service URL (e.g. `https://deriv-trading-backend.onrender.com`) in a browser.

You should see:
```json
{"message": "Welcome to Deriv AI Trading Platform", "health": "/health"}
```

Test the health endpoint:
```
https://deriv-trading-backend.onrender.com/health
```

Response:
```json
{"status": "ok", "service": "Deriv AI Trading Platform"}
```

### Step 6 — Note your backend URL

Your backend URL will be something like:
```
https://deriv-trading-backend.onrender.com
```

You will use this URL in the Flutter app (see next section).

> **Free tier note**: On Render's free tier, the service sleeps after 15 minutes
> of inactivity and takes ~30 seconds to wake up. Upgrade to the Starter plan
> ($7/month) for 24/7 uptime, which is required for a trading bot.

---

## 8. Build the Android APK

### Step 1 — Install Flutter

1. Go to **https://docs.flutter.dev/get-started/install/windows**
2. Download the Flutter SDK zip file.
3. Extract it to `C:\flutter` (avoid paths with spaces).
4. Add Flutter to your PATH:
   - Open **Start** → search "Environment Variables"
   - Click **Edit the system environment variables**
   - Click **Environment Variables**
   - Under **User variables**, find **Path** → **Edit** → **New**
   - Add: `C:\flutter\bin`
   - Click OK on all dialogs.
5. Open a **new** terminal and verify:
   ```
   flutter --version
   ```

### Step 2 — Install Android Studio

1. Download from **https://developer.android.com/studio**
2. Run the installer — use all default options.
3. When Android Studio opens, complete the Setup Wizard.
4. In Android Studio: **File** → **Settings** → **Appearance & Behavior** →
   **System Settings** → **Android SDK**
5. Under **SDK Platforms**, check **Android 14 (API 34)**.
6. Under **SDK Tools**, check:
   - Android SDK Build-Tools
   - Android Emulator
   - Android SDK Platform-Tools
7. Click **Apply** → **OK**.

### Step 3 — Accept Android licenses

```bash
flutter doctor --android-licenses
# Type 'y' and press Enter for each license prompt
```

### Step 4 — Set your backend URL

Open `frontend/lib/core/constants/app_constants.dart` and change this line:

```dart
defaultValue: 'https://deriv-trading-backend.onrender.com',
```

Replace `deriv-trading-backend` with your actual Render service name.

Alternatively, build with the URL as a Dart compile-time constant:
```bash
flutter build apk --dart-define=API_BASE_URL=https://YOUR-SERVICE.onrender.com
```

### Step 5 — Generate Dart code (required before first build)

```bash
cd frontend
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

This generates the `.freezed.dart` and `.g.dart` files from model definitions.

### Step 6 — Build the debug APK (for testing)

```bash
cd frontend
flutter build apk --debug
```

The APK is at:
```
frontend/build/app/outputs/flutter-apk/app-debug.apk
```

### Step 7 — Install on your Android phone

**Option A — USB cable:**
1. On your phone: **Settings** → **About phone** → tap **Build number** 7 times.
2. Go back to **Settings** → **Developer options** → enable **USB debugging**.
3. Connect your phone via USB cable.
4. Run:
   ```bash
   flutter install
   ```

**Option B — Copy the APK file:**
1. Copy `app-debug.apk` to your phone (via USB, email, Google Drive, etc.).
2. On your phone, open the APK file.
3. If prompted "Install unknown apps", allow it for your file manager.
4. Tap **Install**.

### Step 8 — Build the release APK (for production)

The release APK is smaller, faster, and required for sharing.

**8a. Generate a signing keystore (one-time setup):**

```bash
# Run this command (replace the values in angle brackets)
keytool -genkey -v \
  -keystore android/app/release.jks \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -alias trading_key \
  -dname "CN=Your Name, OU=Trading, O=YourCompany, L=City, S=State, C=US"
```

You will be asked to set a keystore password and key password. **Save these passwords somewhere safe** — you cannot recover them if lost, and you need the same keystore to publish future updates.

**8b. Create `frontend/android/key.properties`:**

```properties
storePassword=YOUR_KEYSTORE_PASSWORD
keyPassword=YOUR_KEY_PASSWORD
keyAlias=trading_key
storeFile=release.jks
```

> This file is already in `.gitignore` — it will NOT be committed to Git.

**8c. Build the signed release APK:**

```bash
cd frontend
flutter build apk --release
```

The release APK is at:
```
frontend/build/app/outputs/flutter-apk/app-release.apk
```

This file is ready to install on any Android phone.

### Step 9 — Build app bundles (for Google Play Store — optional)

```bash
flutter build appbundle --release
```

Output: `frontend/build/app/outputs/bundle/release/app-release.aab`

---

## 9. Configure GitHub Actions Secrets

GitHub Actions uses these secrets to run CI/CD pipelines. Without them the
pipelines will skip deployment steps (tests still run).

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
→ **New repository secret** for each one.

### Backend deployment secrets

| Secret name | Where to get it | Required for |
|-------------|----------------|--------------|
| `RENDER_API_KEY` | Render Dashboard → Account Settings → API Keys → Create API Key | Auto-deploy on push |
| `RENDER_SERVICE_ID` | Your Render service URL contains `srv-XXXXXXXXXX` — copy that part | Auto-deploy on push |

### Flutter release build secrets

| Secret name | Value | Required for |
|-------------|-------|--------------|
| `KEYSTORE_BASE64` | Base64-encoded keystore file (see below) | Release APK in CI |
| `KEY_ALIAS` | `trading_key` (or whatever alias you chose) | Release APK in CI |
| `KEY_PASSWORD` | Your key password | Release APK in CI |
| `STORE_PASSWORD` | Your keystore password | Release APK in CI |

**How to encode your keystore as base64:**

```bash
# Windows PowerShell:
[Convert]::ToBase64String([IO.File]::ReadAllBytes("frontend\android\app\release.jks")) | clip
# The base64 string is now in your clipboard — paste it as KEYSTORE_BASE64

# Mac/Linux:
base64 -i frontend/android/app/release.jks | pbcopy   # Mac
base64 -i frontend/android/app/release.jks            # Linux — copy output
```

---

## 10. Environment Variables Reference

All backend settings are loaded from environment variables.
In local development, copy `backend/.env.example` to `backend/.env`.
On Render, set them in the service dashboard.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ | — | JWT signing key. Min 64 chars. Generate with `python -c "import secrets; print(secrets.token_hex(64))"` |
| `DATABASE_URL` | ✅ | — | PostgreSQL async URL. Format: `postgresql+asyncpg://user:pass@host:5432/dbname` |
| `SYNC_DATABASE_URL` | ✅ | — | Same DB, sync URL for Alembic. Format: `postgresql://user:pass@host:5432/dbname` |
| `DERIV_APP_ID` | ✅ | `1` | Your Deriv app ID from https://api.deriv.com/app-registration |
| `DERIV_WS_URL` | | `wss://ws.derivws.com/websockets/v3` | Deriv WebSocket endpoint |
| `APP_ENV` | | `development` | `development` or `production` |
| `DEBUG` | | `false` | Set `true` to enable Swagger UI (`/docs`) |
| `ALGORITHM` | | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | | `60` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | | `30` | Refresh token lifetime |
| `CORS_ORIGINS` | | `http://localhost` | Comma-separated allowed origins |
| `FIREBASE_CREDENTIALS_BASE64` | | — | Base64 Firebase service account JSON (optional) |
| `LOG_LEVEL` | | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

---

## 11. API Reference

The backend exposes a REST API at `https://YOUR-SERVICE.onrender.com/api/v1/`.

In development with `DEBUG=true`, interactive docs are at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc:       `http://localhost:8000/redoc`

### Authentication

All endpoints except `/health`, `/`, `/auth/register`, and `/auth/login`
require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <your_access_token>
```

### Endpoint summary

#### Auth (`/api/v1/auth/`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/register` | Create account. Body: `{email, username, password}` |
| `POST` | `/login` | Sign in. Body: `{email, password}`. Returns tokens + user. |
| `POST` | `/refresh` | Get new access token. Body: `{refresh_token}` |
| `GET`  | `/me` | Get current user profile |
| `PATCH`| `/me` | Update profile. Body: `{full_name?, fcm_token?}` |
| `PUT`  | `/token` | Save Deriv API token. Body: `{deriv_api_token}` |
| `DELETE`| `/token` | Remove Deriv API token |

#### Trading (`/api/v1/trading/`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/start` | Start the trading bot |
| `POST` | `/pause` | Pause (keeps connection, stops new trades) |
| `POST` | `/resume` | Resume a paused bot |
| `POST` | `/stop` | Stop and disconnect |
| `GET`  | `/status` | Get bot status (`running`/`paused`/`stopped`) |
| `GET`  | `/balance` | Live balance from Deriv |
| `POST` | `/trade` | Place a manual trade |
| `DELETE`| `/trade/{id}` | Close an open trade early |
| `GET`  | `/trades/open` | List open trades |
| `GET`  | `/trades` | Trade history (paginated with `?limit=&offset=`) |
| `GET`  | `/trades/{id}` | Single trade details |
| `GET`  | `/summary` | Aggregated statistics |

#### AI Engine (`/api/v1/ai/`)

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/signal/{symbol}` | BUY/SELL/WAIT signal for one symbol |
| `POST` | `/signal/batch` | Signals for up to 10 symbols. Body: `["R_100","R_50"]` |
| `POST` | `/auto-trade/{symbol}` | AI analyses and executes if confident enough |

#### Risk Management (`/api/v1/risk/`)

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/` | Get current risk settings |
| `PUT`  | `/` | Update risk settings |
| `POST` | `/emergency-stop` | Immediately halt all trading |
| `POST` | `/emergency-reset` | Clear emergency stop and re-enable trading |

#### Dashboard (`/api/v1/dashboard/`)

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/` | All dashboard data in one call |

#### Notifications (`/api/v1/notifications/`)

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/` | List notifications (`?unread_only=true`) |
| `POST` | `/read-all` | Mark all as read |
| `DELETE`| `/{id}` | Delete a notification |

---

## 12. Updating the Application

### Update the backend

```bash
# 1. Make your code changes locally

# 2. Test locally
cd backend
pytest tests/ -v

# 3. Commit and push to GitHub
git add .
git commit -m "feat: describe your change"
git push origin main
```

If GitHub Actions is configured (secrets set), the backend deploys to Render
automatically within about 5 minutes.

To deploy manually from the Render dashboard:
1. Go to your service → click **Manual Deploy** → **Deploy latest commit**.

### Update the Flutter app

```bash
# 1. Make your changes to the frontend code

# 2. If you changed any model files, regenerate code
cd frontend
flutter pub run build_runner build --delete-conflicting-outputs

# 3. Test locally
flutter test

# 4. Build a new APK
flutter build apk --release

# 5. Install the new APK on your phone
#    Copy frontend/build/app/outputs/flutter-apk/app-release.apk to your phone
#    Tap to install (existing installation is replaced)

# 6. Commit and push
git add .
git commit -m "feat: update app"
git push origin main
```

GitHub Actions will automatically build a new APK and attach it to the workflow
run as a downloadable artifact.

### Update Flutter dependencies

```bash
cd frontend
flutter pub upgrade           # update all packages within version constraints
flutter pub outdated          # see what has newer major versions available
flutter pub run build_runner build --delete-conflicting-outputs
```

### Update Python dependencies

```bash
cd backend
pip install --upgrade -r requirements.txt
# Test everything still works
pytest tests/ -v
```

---

## 13. Troubleshooting

### Backend won't start — "DATABASE_URL not set"

You forgot to create `backend/.env`. Copy the example:
```bash
cp backend/.env.example backend/.env
```
Then edit the file and fill in your database URL and SECRET_KEY.

### Backend error: "could not connect to server"

PostgreSQL is not running or the credentials in DATABASE_URL are wrong.
```bash
# Check if postgres is running (Linux/Mac)
pg_isready

# Windows — check Services for "postgresql"
```

### "Import could not be resolved" in Python

Your virtual environment is not activated:
```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Flutter build error: "Gradle build failed"

```bash
# Clean the build cache
cd frontend
flutter clean
flutter pub get
flutter build apk --debug
```

### Flutter error: "SDK location not found"

Create `frontend/android/local.properties` with:
```properties
sdk.dir=C:\\Users\\YOUR_NAME\\AppData\\Local\\Android\\Sdk
```
(Replace `YOUR_NAME` with your Windows username)

### "No active trading session" error from API

You must call `POST /trading/start` before placing trades or requesting AI signals.
The bot must be running for live data to be available.

### Render deployment fails: "Docker build failed"

Check the Render deploy log. Common causes:
1. Missing environment variable — add it in the Render dashboard.
2. Python dependency has a compile error — check `requirements.txt`.
3. Out of memory — the free tier has 512MB RAM. Upgrade to Starter if needed.

### App shows "An internal server error occurred"

Check the Render service logs:
1. Go to your Render dashboard → select your service.
2. Click the **Logs** tab.
3. Look for `ERROR` lines.

### Deriv API error: "InvalidToken"

Your Deriv API token is incorrect or has expired. Go to your Deriv account
and generate a new token, then save it in the app Profile screen.

### Deriv API error: "RateLimit"

You are sending too many requests. The bot monitors every 5 seconds — this
should be fine. If you see this, reduce the polling frequency in
`trading_engine.py` (`await asyncio.sleep(5)` → increase to 10 or 15).

---

## 14. Security Checklist

Before going live with real money, verify every item below.

### Secrets

- [ ] `SECRET_KEY` is a random 64+ character string (not the example value)
- [ ] `.env` file is in `.gitignore` and has never been committed to Git
- [ ] `android/key.properties` is in `.gitignore` and has never been committed
- [ ] The Deriv API token is stored only in the database, never in code or logs
- [ ] All Render environment variables are set, not defaulting to empty values

### Network

- [ ] Backend is running on HTTPS (Render provides this automatically)
- [ ] `DEBUG=false` in production (disables Swagger UI)
- [ ] `CORS_ORIGINS` only lists your actual app domain, not `*`

### Authentication

- [ ] Passwords are hashed with bcrypt (already done — never change this)
- [ ] JWT tokens have reasonable expiry times
- [ ] The refresh token endpoint validates the `type: refresh` claim

### Trading safety

- [ ] Tested on a **demo account** for at least 1 week before real money
- [ ] `max_daily_loss` is set to an amount you can afford to lose in one day
- [ ] `emergency_stop` works correctly (test it!)
- [ ] `min_ai_confidence` is set to at least 0.60 (60%)
- [ ] `default_stake` starts low (e.g. $1) while testing
- [ ] You understand that past AI performance does not guarantee future results

### Database

- [ ] Database is on a paid plan for production (free tier expires after 90 days on Render)
- [ ] Regular backups are enabled (Render paid plans include this)

---

## Quick-Start Checklist

Use this checklist when setting up from scratch:

- [ ] Install Python 3.11, Flutter 3.22, Java 17, Android Studio, Git
- [ ] Create a Deriv account and get an API token (demo first!)
- [ ] Create a GitHub account and repository
- [ ] Push this project to GitHub
- [ ] Create a Render account and connect GitHub
- [ ] Create a Render PostgreSQL database
- [ ] Create a Render Web Service with the correct environment variables
- [ ] Wait for deployment and test the `/health` endpoint
- [ ] Set `API_BASE_URL` in the Flutter app to your Render URL
- [ ] Run `flutter pub get` and `flutter pub run build_runner build`
- [ ] Build the debug APK and install on your phone
- [ ] Register an account in the app
- [ ] Go to Profile and save your Deriv API token (demo account)
- [ ] Go to Risk settings and configure your limits
- [ ] Tap Start Bot on the Dashboard
- [ ] Watch it trade on your demo account for several days
- [ ] Review AI signals and trade history
- [ ] Only switch to a real account when you are fully satisfied

---

## License

This project is for personal use. No license is granted to redistribute or
sell this software.

---

*Built with FastAPI · Flutter · PostgreSQL · Deriv API*
