# Complete Publishing Guide
## Deriv AI Trading Platform — Step by Step

This document contains everything you need to redeploy this project from scratch.
All links, API keys, App IDs, and exact steps that work.

---

## YOUR PROJECT DETAILS (save this)

| Item | Value |
|------|-------|
| GitHub Repo | https://github.com/Gerald-bit0rgb/deriv-trading-platform |
| Backend URL | https://deriv-trading-platform-mxic.onrender.com |
| Deriv Developer App ID | 33O8kU94RkSPJmJNahuno |
| Deriv Developer Portal | https://developers.deriv.com |
| Deriv Trading Account | https://app.deriv.com |

---

## ACCOUNTS YOU NEED

### 1. GitHub
- URL: https://github.com
- Used for: storing your code and building the APK automatically
- Your account: Gerald-bit0rgb

### 2. Render
- URL: https://render.com
- Used for: running the backend server 24/7
- Sign up with GitHub (click "Sign up with GitHub")

### 3. Deriv Trading Account
- URL: https://app.deriv.com
- Used for: actual trading (demo or real)
- Always test on DEMO first

### 4. Deriv Developer Portal
- URL: https://developers.deriv.com
- Used for: getting your App ID and PAT tokens
- IMPORTANT: Use a different email from app.deriv.com OR change your legacy email first

---

## PART 1 — PUSH CODE TO GITHUB

### Prerequisites
- Git installed: https://git-scm.com/download/win
- Python installed: https://python.org/downloads (check "Add to PATH")

### Steps

**1. Configure Git (run in Command Prompt)**
```
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

**2. Get a GitHub Personal Access Token**
- Go to: https://github.com/settings/tokens
- Click "Generate new token (classic)"
- Name it: VPS
- Expiration: 90 days
- Check: repo (top checkbox)
- Click "Generate token"
- COPY IT — you cannot see it again

**3. Create GitHub repository**
- Go to: https://github.com/new
- Name: deriv-trading-platform
- Set to: Private
- Do NOT initialise with README
- Click "Create repository"

**4. Push code from VPS**
```
cd C:\Users\Administrator\deriv-trading-platform
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/deriv-trading-platform.git
git push -u origin main
```
When asked for password — paste your Personal Access Token (not your GitHub password)

**5. Verify**
Open: https://github.com/YOUR_USERNAME/deriv-trading-platform
You should see all project files listed.

---

## PART 2 — DEPLOY DATABASE ON RENDER

**1. Go to Render dashboard**
- URL: https://dashboard.render.com

**2. Create PostgreSQL database**
- Click: New + → PostgreSQL
- Fill in:
  - Name: deriv-trading-db
  - Database: deriv_trading
  - User: deriv_user
  - Region: Oregon (US West)
  - Plan: Free
- Click: Create Database
- Wait 2 minutes until status shows "Available"

**3. Copy the database URL**
- Click on the database
- Scroll to "Connections" section
- Copy the "Internal Database URL"
- It looks like: postgresql://deriv_user:PASSWORD@dpg-xxxxx-a/deriv_trading
- Save it — you need it in the next part

---

## PART 3 — GENERATE SECRET KEY

Open Command Prompt on your VPS and run:
```
python -c "import secrets; print(secrets.token_hex(64))"
```
Copy the long string it prints. Save it.
Example output: 8f3a9b2c1d4e5f6a7b8c9d0e1f2a3b4c5...

---

## PART 4 — GET DERIV APP ID

**1. Go to Deriv developer portal**
- URL: https://developers.deriv.com
- Sign up with email (use different email from app.deriv.com)

**2. Create an application**
- Click: Registered Apps → Create new app
- Fill in:
  - App name: TradingBot
  - Redirect URL: https://YOUR-SERVICE-NAME.onrender.com
  - Scopes: trade, account_manage
- Click: Create
- Your App ID appears in the list — it looks like: 33O8kU94RkSPJmJNahuno
- Save it

**3. Get a PAT token**
- In the same dashboard click: API Tokens
- Create new token
- Select scopes: trade, account_manage
- Copy the token — starts with: pat_
- Save it — this goes into the app on your phone

---

## PART 5 — DEPLOY BACKEND ON RENDER

**1. Create Web Service**
- Render dashboard → New + → Web Service
- Click: Build and deploy from a Git repository
- Click: Connect next to deriv-trading-platform
- If not visible click "Configure account" and give Render access

**2. Fill in settings**

| Field | Value |
|-------|-------|
| Name | deriv-trading-backend |
| Region | Oregon (US West) |
| Branch | main |
| Runtime | Docker |
| Instance Type | Free |

**3. Add Environment Variables**
Click "Add Environment Variable" for each row:

| Key | Value | Notes |
|-----|-------|-------|
| APP_ENV | production | |
| DEBUG | false | |
| SECRET_KEY | paste your generated key | the long random string |
| ALGORITHM | HS256 | |
| ACCESS_TOKEN_EXPIRE_MINUTES | 60 | |
| REFRESH_TOKEN_EXPIRE_DAYS | 30 | |
| DATABASE_URL | paste DB URL — change postgresql:// to postgresql+asyncpg:// | change the prefix |
| SYNC_DATABASE_URL | paste DB URL — keep as postgresql:// | keep original prefix |
| DERIV_APP_ID | 33O8kU94RkSPJmJNahuno | your App ID from developers.deriv.com |
| DERIV_WS_URL | wss://ws.derivws.com/websockets/v3 | |
| CORS_ORIGINS | https://deriv-trading-backend.onrender.com | your actual render URL |
| LOG_LEVEL | INFO | |

**IMPORTANT for DATABASE_URL:**
If your database URL is: postgresql://deriv_user:abc123@dpg-xxx/deriv_trading
- DATABASE_URL = postgresql+asyncpg://deriv_user:abc123@dpg-xxx/deriv_trading
- SYNC_DATABASE_URL = postgresql://deriv_user:abc123@dpg-xxx/deriv_trading

**4. Click "Create Web Service"**

**5. Wait for deployment**
- Watch the Logs tab
- First deployment takes 5-10 minutes
- Look for: INFO: Application startup complete.
- Status turns green and shows "Live"

**6. Test it works**
Open in browser: https://YOUR-SERVICE-NAME.onrender.com/health
You should see: {"status":"ok","service":"Deriv AI Trading Platform"}

**NOTE:** Save your backend URL — you need it for the Flutter app.

---

## PART 6 — BUILD THE APK

The APK is built automatically by GitHub Actions every time you push code.
No Flutter installation needed on your VPS.

**1. Update backend URL in the app**
Open this file:
```
C:\Users\Administrator\deriv-trading-platform\frontend\lib\core\constants\app_constants.dart
```
Find this line:
```dart
defaultValue: 'https://deriv-trading-backend.onrender.com',
```
Change it to your actual Render URL and save.

**2. Push to GitHub**
```
cd C:\Users\Administrator\deriv-trading-platform
git add .
git commit -m "Set backend URL"
git push origin main
```

**3. Watch GitHub Actions build**
- Go to: https://github.com/YOUR_USERNAME/deriv-trading-platform
- Click: Actions tab
- Watch "Flutter CI" workflow
- Wait 10-15 minutes for green tick ✓

**4. Download APK**
- Click on the completed workflow run
- Scroll to bottom → Artifacts section
- Click "debug-apk" to download
- Extract the zip → get app-debug.apk

**5. Send APK to phone**

Via Telegram:
- Open: https://web.telegram.org on VPS browser
- Log in → Saved Messages → attach APK file → send
- On phone: Telegram → Saved Messages → download → install

Via Google Drive:
- Open: https://drive.google.com on VPS browser
- New → File upload → upload APK
- On phone: Google Drive → download → install

**6. Allow unknown apps on phone**
- Phone Settings → search "Install unknown apps"
- Allow your file manager or Telegram

**7. Install**
- Tap the APK file on phone
- Tap Install → Open

---

## PART 7 — FIRST TIME APP SETUP

**1. Register account in app**
- Open Deriv AI Trader on phone
- Tap Sign Up
- Email: your email
- Username: any name (min 3 chars)
- Password: min 8 chars, must have uppercase + number
  Example: Gerald2024!
- Tap Create Account

**2. Save your Deriv PAT token**
- Go to Profile tab (bottom of screen)
- Scroll to "Deriv API Token" section
- Paste your pat_ token from developers.deriv.com
- Tap Save Token
- Green message = success

**3. Set risk limits (important)**
- Go to Risk settings
- Default Stake: 1
- Max Stake: 5
- Max Daily Loss: 20
- Max Daily Trades: 10
- Min AI Confidence: 65%
- Tap Save Risk Settings

**4. Start the bot**
- Go to Dashboard
- Tap Start Bot
- Wait 10-15 seconds
- Status turns green = RUNNING
- Balance loads from your Deriv demo account

---

## PART 8 — UPDATING THE APP IN THE FUTURE

### Update backend code
```
cd C:\Users\Administrator\deriv-trading-platform
git add .
git commit -m "describe your change"
git push origin main
```
Then on Render: Manual Deploy → Deploy latest commit

### Update Flutter app
```
cd C:\Users\Administrator\deriv-trading-platform
git add .
git commit -m "describe your change"
git push origin main
```
Then: GitHub Actions builds new APK automatically → download → install on phone

---

## PART 9 — TROUBLESHOOTING

### "Server is starting up" on dashboard
- The free Render tier sleeps after 15 minutes
- Pull down to refresh and wait 30-60 seconds
- Upgrade to Starter plan ($7/month) for 24/7 uptime

### "Start Bot" says error
- Make sure you saved your PAT token in Profile
- PAT token comes from: https://developers.deriv.com → API Tokens
- NOT from app.deriv.com

### "Failed to load dashboard"
- Wait for server to wake up
- Pull down to refresh

### "Invalid token format" error
- Delete the token in Profile
- Get a fresh one from: https://developers.deriv.com → API Tokens
- Paste it carefully with no extra spaces

### APK won't install
- Phone Settings → Install unknown apps → Allow

### GitHub Actions build fails
- Go to GitHub → Actions tab → click the failed run
- Copy the error and fix it

### Render deploy fails
- Go to Render → your service → Logs tab
- Look for red error lines
- Most common cause: wrong environment variable value

---

## PART 10 — IMPORTANT LINKS SUMMARY

| Service | URL | Used for |
|---------|-----|---------|
| GitHub | https://github.com | Code storage, APK building |
| GitHub Actions | https://github.com/YOUR_USERNAME/deriv-trading-platform/actions | APK build status |
| Render Dashboard | https://dashboard.render.com | Backend hosting |
| Backend Health | https://deriv-trading-platform-mxic.onrender.com/health | Check if backend is running |
| Deriv Trading | https://app.deriv.com | Trading account (demo/real) |
| Deriv Developer Portal | https://developers.deriv.com | App ID and PAT tokens |
| Deriv API Docs | https://developers.deriv.com/docs/intro/api-overview/ | API documentation |

---

## ENVIRONMENT VARIABLES QUICK REFERENCE

These go in Render → deriv-trading-backend → Environment:

```
APP_ENV = production
DEBUG = false
SECRET_KEY = [your 128 char random key]
ALGORITHM = HS256
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30
DATABASE_URL = postgresql+asyncpg://[user]:[pass]@[host]/[dbname]
SYNC_DATABASE_URL = postgresql://[user]:[pass]@[host]/[dbname]
DERIV_APP_ID = 33O8kU94RkSPJmJNahuno
DERIV_WS_URL = wss://ws.derivws.com/websockets/v3
CORS_ORIGINS = https://deriv-trading-platform-mxic.onrender.com
LOG_LEVEL = INFO
```

---

## SECURITY REMINDERS

- NEVER share your SECRET_KEY with anyone
- NEVER share your PAT token with anyone
- NEVER commit .env files to GitHub
- ALWAYS test on demo account before real money
- The bot trades real money if connected to a real account
- No trading system guarantees profits

---

## HOW THE BOT WORKS

The bot uses technical analysis with these indicators:

| Indicator | Signal |
|-----------|--------|
| RSI below 30 | BUY signal |
| RSI above 70 | SELL signal |
| MACD bullish crossover | BUY signal |
| MACD bearish crossover | SELL signal |
| Price above EMA20 > EMA50 | BUY signal |
| Price below EMA20 < EMA50 | SELL signal |
| Price at lower Bollinger Band | BUY signal |
| Price at upper Bollinger Band | SELL signal |

Score above 0.35 = BUY (CALL contract)
Score below -0.35 = SELL (PUT contract)
Everything else = WAIT

Default contract: 5 ticks, $1 stake, Rise/Fall type

---

*Document created: July 2026*
*Backend URL: https://deriv-trading-platform-mxic.onrender.com*
*GitHub: https://github.com/Gerald-bit0rgb/deriv-trading-platform*
