# Complete Publishing Guide
## Deriv AI Trading Platform — Full Setup, Maintenance & Renewal

Last updated: July 2026

---

## YOUR PROJECT DETAILS

| Item | Value |
|------|-------|
| GitHub Repo | https://github.com/Gerald-bit0rgb/deriv-trading-platform |
| Backend URL | https://deriv-trading-platform-mxic.onrender.com |
| Deriv Developer App ID | 33O8kU94RkSPJmJNahuno |
| Deriv Developer Portal | https://developers.deriv.com |
| Deriv Trading Account | https://app.deriv.com |

---

## TABLE OF CONTENTS

1. Accounts you need
2. First time setup — push code to GitHub
3. Deploy database on Render
4. Generate secret key
5. Get Deriv App ID and PAT token
6. Deploy backend on Render
7. Build the APK
8. First time app setup on phone
9. How to update the app in future
10. **What to do when things expire**
11. How to upgrade Render from Free to Paid
12. Troubleshooting
13. All important links
14. Environment variables reference

---

## PART 1 — ACCOUNTS YOU NEED

### GitHub — where your code lives
- URL: https://github.com
- Sign up free
- Your account: Gerald-bit0rgb

### Render — where backend runs 24/7
- URL: https://render.com
- Sign up with GitHub (click "Sign up with GitHub")
- Links automatically to your GitHub repos

### Deriv Trading Account
- URL: https://app.deriv.com
- Your real or demo trading account
- Always test on DEMO first — never risk real money without testing

### Deriv Developer Portal
- URL: https://developers.deriv.com
- Separate from your trading account
- Used for App ID and PAT tokens
- Use a different email from app.deriv.com OR change your legacy email first

---

## PART 2 — PUSH CODE TO GITHUB

### Step 1 — Configure Git on your VPS
```
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

### Step 2 — Get a GitHub Personal Access Token
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: VPS
4. Expiration: 90 days
5. Check: repo (top checkbox)
6. Click "Generate token"
7. COPY IT — you cannot see it again
8. Save it in Notepad

### Step 3 — Create GitHub repository
1. Go to: https://github.com/new
2. Name: deriv-trading-platform
3. Set to: Private
4. Do NOT check any initialise boxes
5. Click "Create repository"

### Step 4 — Push code
```
cd C:\Users\Administrator\deriv-trading-platform
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/deriv-trading-platform.git
git push -u origin main
```
When asked for password — paste your Personal Access Token

### Step 5 — Verify
Open: https://github.com/YOUR_USERNAME/deriv-trading-platform
You should see all files listed.

---

## PART 3 — DEPLOY DATABASE ON RENDER

1. Go to: https://dashboard.render.com
2. Click: New + → PostgreSQL
3. Fill in:
   - Name: deriv-trading-db
   - Database: deriv_trading
   - User: deriv_user
   - Region: Oregon (US West)
   - Plan: Free (or Starter for production)
4. Click: Create Database
5. Wait 2 minutes for status "Available"
6. Click on the database → scroll to Connections
7. Copy the "Internal Database URL"
   - Looks like: postgresql://deriv_user:PASSWORD@dpg-xxxxx-a/deriv_trading
8. Save it in Notepad

---

## PART 4 — GENERATE SECRET KEY

Open Command Prompt on your VPS:
```
python -c "import secrets; print(secrets.token_hex(64))"
```
Copy the output. Save it in Notepad.
This is your SECRET_KEY — never share it.

---

## PART 5 — GET DERIV APP ID AND PAT TOKEN

### Get App ID
1. Go to: https://developers.deriv.com
2. Sign up with email (use different email from app.deriv.com)
3. Go to: Registered Apps → Create new app
4. Fill in:
   - App name: TradingBot
   - Redirect URL: https://YOUR-SERVICE-NAME.onrender.com
   - Scopes: trade, account_manage
5. Click Create
6. Your App ID appears — looks like: 33O8kU94RkSPJmJNahuno
7. Save it

### Get PAT Token
1. In the same developer dashboard click: API Tokens
2. Click Create new token
3. Select scopes: trade, account_manage
4. Click Create
5. Copy the token — starts with pat_
6. Save it — this goes into the app on your phone
7. NEVER share this token — it gives access to your trading account

---

## PART 6 — DEPLOY BACKEND ON RENDER

### Create Web Service
1. Render dashboard → New + → Web Service
2. Click: Build and deploy from a Git repository
3. Click: Connect next to deriv-trading-platform
4. Fill in:
   - Name: deriv-trading-backend
   - Region: Oregon
   - Branch: main
   - Runtime: Docker
   - Instance Type: Free (or Starter for 24/7)

### Add Environment Variables
Click "Add Environment Variable" for each:

| Key | Value |
|-----|-------|
| APP_ENV | production |
| DEBUG | false |
| SECRET_KEY | your generated key |
| ALGORITHM | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 60 |
| REFRESH_TOKEN_EXPIRE_DAYS | 30 |
| DATABASE_URL | postgresql+asyncpg://user:pass@host/db |
| SYNC_DATABASE_URL | postgresql://user:pass@host/db |
| DERIV_APP_ID | 33O8kU94RkSPJmJNahuno |
| DERIV_WS_URL | wss://ws.derivws.com/websockets/v3 |
| CORS_ORIGINS | https://YOUR-SERVICE.onrender.com |
| LOG_LEVEL | INFO |

DATABASE_URL note:
- If database URL is: postgresql://user:pass@host/db
- DATABASE_URL = postgresql+asyncpg://user:pass@host/db (change prefix)
- SYNC_DATABASE_URL = postgresql://user:pass@host/db (keep original)

### Deploy and Test
1. Click "Create Web Service"
2. Watch Logs tab — wait for: INFO: Application startup complete.
3. Test: open https://YOUR-SERVICE.onrender.com/health
4. You should see: {"status":"ok"}

---

## PART 7 — BUILD THE APK

### How GitHub Actions builds it automatically
Every time you push code to GitHub, the APK builds automatically on GitHub's servers.
No Flutter installation needed on your VPS.

### Update backend URL in app
Open file:
```
C:\Users\Administrator\deriv-trading-platform\frontend\lib\core\constants\app_constants.dart
```
Change this line to your actual Render URL:
```dart
defaultValue: 'https://deriv-trading-platform-mxic.onrender.com',
```

### Trigger build
```
cd C:\Users\Administrator\deriv-trading-platform
git add .
git commit -m "Set backend URL"
git push origin main
```

### Download APK
1. Go to: https://github.com/YOUR_USERNAME/deriv-trading-platform
2. Click: Actions tab
3. Click the latest Flutter CI run
4. Wait for green tick (10-15 minutes)
5. Scroll to bottom → Artifacts → click debug-apk
6. Extract the zip → get app-debug.apk

### Send to phone and install
Via Telegram:
- Open: https://web.telegram.org
- Saved Messages → attach APK → send
- On phone: Telegram → Saved Messages → download → tap to install

Via Google Drive:
- Open: https://drive.google.com
- Upload APK → on phone download and install

Enable unknown apps on phone:
- Settings → search "Install unknown apps" → Allow

---

## PART 8 — FIRST TIME APP SETUP

1. Open Deriv AI Trader on phone
2. Tap Sign Up → fill in email, username, password
   - Password must have: uppercase letter + number + min 8 chars
   - Example: Gerald2024!
3. Tap Create Account
4. Go to Profile tab → Deriv API Token section
5. Paste your pat_ token → tap Save Token
6. Go to Risk settings → set safe limits:
   - Default Stake: 1
   - Max Stake: 5
   - Max Daily Loss: 20
   - Max Daily Trades: 10
7. On Dashboard → choose your trading pair
8. Make sure Account Type shows DEMO
9. Tap Start Bot → wait for RUNNING status

---

## PART 9 — HOW TO UPDATE THE APP IN FUTURE

### Update backend
```
cd C:\Users\Administrator\deriv-trading-platform
git add .
git commit -m "describe your change"
git push origin main
```
Then: Render → Manual Deploy → Deploy latest commit

### Update Flutter app
```
cd C:\Users\Administrator\deriv-trading-platform
git add .
git commit -m "describe your change"
git push origin main
```
GitHub Actions builds new APK automatically.
Download from Actions → Artifacts → install on phone.

---

## PART 10 — WHAT TO DO WHEN THINGS EXPIRE

This is the most important section. Read it carefully.

---

### 10A — GitHub Personal Access Token expires

Symptoms:
- `git push` fails with "Authentication failed"
- Cannot push code to GitHub anymore

How to fix:
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: VPS-New
4. Expiration: 90 days (or "No expiration" to avoid this problem)
5. Check: repo
6. Click "Generate token"
7. Copy the new token
8. Next time you push, use the new token as password

To avoid this problem in future:
- When creating the token, set Expiration to "No expiration"
- Or set it to 1 year so you only need to renew once a year

---

### 10B — Deriv PAT token expires or gets invalidated

Symptoms:
- App shows "Token is invalid" when starting the bot
- Bot fails to connect to Deriv
- Start Bot shows error on dashboard

How to fix:
1. Go to: https://developers.deriv.com
2. Click API Tokens in the dashboard menu
3. Delete the old token (click the trash icon)
4. Click Create new token
5. Select scopes: trade, account_manage
6. Click Create
7. Copy the new token (starts with pat_)
8. Open your phone app
9. Go to Profile tab
10. Delete the old token in the field
11. Paste the new token
12. Tap Save Token
13. Go to Dashboard → tap Start Bot

Note: Deriv PAT tokens do not have a set expiry date but they can be
invalidated if you change your Deriv password or revoke them manually.
Best practice: create a new token every 3-6 months for security.

---

### 10C — Render Free Database expires (90 days)

Render's free PostgreSQL database expires after 90 days. When it expires:
- All your trades and user accounts are deleted
- The backend will crash on startup with database errors

Symptoms:
- App cannot log in
- "Database connection failed" in Render logs
- Health check returns 500 error

How to fix — Option A (Free — lose data):
1. Go to: https://dashboard.render.com
2. Delete the old expired database
3. Create a new PostgreSQL database (follow Part 3 again)
4. Copy the new database URL
5. Go to your backend service → Environment tab
6. Update DATABASE_URL and SYNC_DATABASE_URL with new values
7. Click Save Changes
8. Render redeploys automatically
9. All previous data is lost — you start fresh

How to fix — Option B (Paid — keep data):
1. Before the 90 days are up, upgrade to a paid database plan
2. Go to: https://dashboard.render.com
3. Click your database → Settings → Change Plan
4. Select "Starter" ($7/month) or higher
5. The database never expires and your data is safe

Render sends you an email warning 14 days before expiry.
Watch for emails from Render and act before it expires.

---

### 10D — Render Free Web Service goes to sleep

The free Render web service sleeps after 15 minutes of no activity.
When asleep, the first request takes 30-60 seconds to wake up.

Symptoms:
- App shows "Server is starting up. Pull down to refresh."
- Bot cannot start because server is sleeping
- Dashboard takes 60 seconds to load

This is NOT an expiry — it happens every time you don't use the app for 15+ minutes.

Temporary fix: Pull down to refresh on the dashboard and wait 60 seconds.

Permanent fix — Upgrade to Starter:
1. Go to: https://dashboard.render.com
2. Click your backend service → Settings → Change Plan
3. Select "Starter" ($7/month)
4. Service runs 24/7, never sleeps
5. Required for a trading bot that needs to run overnight

---

### 10E — Render Starter plan renewal (monthly)

If you upgrade to Starter ($7/month):
- Render charges your card automatically every month
- No manual action needed
- If payment fails, service downgrades to free tier

How to update payment:
1. Go to: https://dashboard.render.com
2. Click your profile icon → Billing
3. Update card details if needed

---

### 10F — Deriv Developer App ID

Your App ID (33O8kU94RkSPJmJNahuno) does not expire.
You only need to create a new one if:
- You delete your developers.deriv.com account
- You want to create a different app

If you ever lose it:
1. Go to: https://developers.deriv.com
2. Click Registered Apps
3. Your App ID is shown in the table

---

### 10G — Complete system restart from scratch

If everything breaks and you need to start completely from scratch:

1. Create new GitHub token (Part 2)
2. Create new Render database (Part 3)
3. Generate new SECRET_KEY (Part 4)
4. Create new Deriv PAT token (Part 5)
5. Create new Render web service (Part 6)
   - Use the same Deriv App ID: 33O8kU94RkSPJmJNahuno
6. Push code to GitHub (Part 2, Step 4)
7. Build new APK (Part 7)
8. Register new account in app (Part 8)

The code in your GitHub repo never expires — it is always there.
Only the tokens, database, and hosting need renewal.

---

## PART 11 — HOW TO UPGRADE RENDER FROM FREE TO PAID

### Why upgrade?

| Feature | Free | Starter ($7/month) |
|---------|------|-------------------|
| Web service sleep | Sleeps after 15 min | Never sleeps |
| Database expiry | 90 days | Never expires |
| Deploy speed | Slow | Fast |
| Support | Community | Email support |
| Custom domains | No | Yes |

For a trading bot that needs to run 24/7 — you must upgrade.

### How to upgrade the web service

1. Go to: https://dashboard.render.com
2. Click your backend service (deriv-trading-backend)
3. Click the "Settings" tab
4. Scroll to "Instance Type"
5. Click "Change Plan"
6. Select "Starter" ($7/month)
7. Add a payment card if not already added
8. Click "Upgrade"
9. Service restarts and never sleeps again

### How to upgrade the database

1. Go to: https://dashboard.render.com
2. Click your database (deriv-trading-db)
3. Click "Update Instance" or "Change Plan"
4. Select "Starter" ($7/month)
5. Click "Upgrade"
6. Database never expires

Total cost for full 24/7 operation: $14/month (web + database)

---

## PART 12 — TROUBLESHOOTING

### "Authentication failed" when doing git push
- Your GitHub Personal Access Token expired
- Fix: generate new token (Part 10A)

### "The token is invalid" when starting bot
- Your Deriv PAT token is expired or wrong
- Fix: create new PAT token (Part 10B)

### "Could not connect to database"
- Render free database expired after 90 days
- Fix: create new database (Part 10C)

### "Server is starting up" on dashboard
- Render free service is asleep
- Fix: pull down to refresh and wait 60 seconds, or upgrade to Starter (Part 11)

### "Failed to load dashboard"
- Server sleeping or crashed
- Fix: wait 60 seconds and refresh

### Bot says error when starting
- Check Profile → make sure PAT token is saved
- Check Dashboard → make sure Account Type is set (Demo or Real)
- Check Dashboard → make sure a trading pair is selected

### APK won't install on phone
- Settings → search "Install unknown apps" → allow Telegram or file manager

### GitHub Actions build fails
- Go to GitHub → Actions tab → click the failed run → copy error → fix it

### Render deploy fails
- Go to Render → your service → Logs tab → look for red errors

---

## PART 13 — ALL IMPORTANT LINKS

| Service | URL | Used for |
|---------|-----|---------|
| GitHub | https://github.com | Code storage |
| GitHub Tokens | https://github.com/settings/tokens | Create/renew Personal Access Token |
| GitHub Actions | https://github.com/Gerald-bit0rgb/deriv-trading-platform/actions | APK build status |
| Render Dashboard | https://dashboard.render.com | Backend and database hosting |
| Render Billing | https://dashboard.render.com/billing | Upgrade plan, update card |
| Backend Health | https://deriv-trading-platform-mxic.onrender.com/health | Check if backend is running |
| Deriv Trading | https://app.deriv.com | Your trading account |
| Deriv API Tokens | https://app.deriv.com/account/api-token | Get/renew trading tokens |
| Deriv Developer | https://developers.deriv.com | App ID and PAT tokens |
| Deriv Dev Tokens | https://developers.deriv.com (API Tokens section) | Renew PAT token |

---

## PART 14 — ENVIRONMENT VARIABLES REFERENCE

These go in Render → deriv-trading-backend → Environment.

```
APP_ENV = production
DEBUG = false
SECRET_KEY = [your 128 char random key — never change after first deploy]
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

Important notes:
- SECRET_KEY: generate once with python -c "import secrets; print(secrets.token_hex(64))"
- Never change SECRET_KEY after users have registered — it will log everyone out
- DATABASE_URL: must start with postgresql+asyncpg://
- SYNC_DATABASE_URL: must start with postgresql://
- DERIV_APP_ID: your App ID from developers.deriv.com — does not expire

---

## QUICK RENEWAL CHECKLIST

Use this when something stops working:

```
Every 90 days:
[ ] Renew GitHub Personal Access Token (or set to "No expiration")
[ ] Create new Render database if on free tier (or upgrade to paid)
[ ] Create new Deriv PAT token in app (every 3-6 months for security)

Every month (if on paid plan):
[ ] Check Render billing — confirm card is valid
[ ] Check backend health: https://deriv-trading-platform-mxic.onrender.com/health

When bot stops working:
[ ] Check if PAT token is still valid — create new one from developers.deriv.com
[ ] Check Render logs for errors
[ ] Check if database is still active (free tier expires after 90 days)
```

---

## SECURITY REMINDERS

- NEVER share your SECRET_KEY
- NEVER share your PAT token (pat_...) — it gives trading access to your account
- NEVER commit .env files to GitHub
- NEVER switch to REAL account without testing on DEMO for weeks first
- The bot trades real money if connected to a real account
- No trading system guarantees profits — always use risk management settings

---

*Document created: July 2026*
*Backend URL: https://deriv-trading-platform-mxic.onrender.com*
*GitHub: https://github.com/Gerald-bit0rgb/deriv-trading-platform*
