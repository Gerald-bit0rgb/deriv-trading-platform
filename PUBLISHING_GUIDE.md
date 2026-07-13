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

0. **App stopped working — check these first**
1. Accounts you need
2. First time setup — push code to GitHub
3. How to create a database on Render (detailed)
4. Generate secret key
5. Get Deriv App ID and PAT token
6. Deploy backend on Render
7. Build the APK
8. First time app setup on phone
9. How to update the app in future
10. What to do when things expire
11. How to update your Deriv PAT token in the app
12. How to upgrade Render from Free to Paid
13. Troubleshooting
14. All important links
15. Environment variables reference
16. Quick renewal checklist
17. Moving to a new Render account — Full Guide
18. **SESSION EXPIRY — Why it happens and how to fix it**

---

## PART 0 — APP STOPPED WORKING — CHECK THESE FIRST

Before doing anything else, go through this list in order.
These cover 95% of all problems.

---

### Check 1 — Is the backend awake?

Open this link in your browser:
```
https://deriv-trading-platform-mxic.onrender.com/health
```

What you see:
- `{"status":"ok"}` → backend is running. Problem is elsewhere.
- Page loads slowly (30-60 sec) then shows ok → server was sleeping. Wait and try app again.
- Page shows error or does not load → backend is down. Check Render logs.

---

### Check 2 — Is the database still active?

If the health check fails with a 500 error, the database may have expired.

1. Go to: https://dashboard.render.com
2. Click on your database (deriv-trading-db)
3. Check the status:
   - Green "Available" → database is fine
   - Red "Expired" or "Deleted" → database expired (free tier lasts 90 days)
   - If expired → see Part 10C to create a new one

---

### Check 3 — Is your Deriv PAT token still valid?

If the dashboard loads but Start Bot shows error:

1. Open the app on your phone
2. Go to Profile tab
3. Look at Deriv API Token section
4. If it says "Token is saved and active" in green → token is saved
5. Tap Start Bot — if it still says error, the saved token may be invalid
6. Fix: create a new PAT token and update it in the app (see Part 11)

---

### Check 4 — Is your GitHub token still valid?

Only matters if you are trying to push code or build a new APK.

1. Open Command Prompt on your VPS
2. Run: `git push origin main`
3. If it asks for password and fails → token expired
4. Fix: create new token at https://github.com/settings/tokens (see Part 10A)

---

### Check 5 — Is Render deployed with the latest code?

1. Go to: https://dashboard.render.com
2. Click your backend service
3. Look at the "Last deployed" time
4. If it shows an old date → click Manual Deploy → Deploy latest commit

---

### Summary — most common problems and quick fixes

| Problem | Most likely cause | Quick fix |
|---------|------------------|-----------|
| Dashboard won't load | Server sleeping | Wait 60 sec, pull to refresh |
| Can't log in | Database expired | Create new database (Part 10C) |
| Start Bot says error | PAT token invalid | Create new PAT token (Part 11) |
| Can't push to GitHub | GitHub token expired | New token at github.com/settings/tokens |
| Bot not trading | Bot not started | Go to Dashboard → tap Start Bot |
| Balance shows 0 | Demo account not connected | Check PAT token in Profile |

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
4. Expiration: No expiration (recommended to avoid having to renew)
5. Check: repo (the top checkbox — selects everything below it)
6. Click "Generate token"
7. COPY IT — you cannot see it again after leaving the page
8. Save it in Notepad on your VPS

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
When it asks for password — paste your Personal Access Token (not your GitHub login password)

### Step 5 — Verify
Open: https://github.com/YOUR_USERNAME/deriv-trading-platform
You should see all project files listed.

---

## PART 3 — HOW TO CREATE A DATABASE ON RENDER (DETAILED)

You need to do this the first time AND every 90 days if you are on the free plan.

### Step 1 — Log in to Render
1. Go to: https://dashboard.render.com
2. Log in with your GitHub account

### Step 2 — Create new PostgreSQL database
1. Click the blue button **"New +"** at the top right
2. A dropdown menu appears — click **"PostgreSQL"**

### Step 3 — Fill in the database settings

You will see a form. Fill in exactly:

| Field | What to type |
|-------|-------------|
| Name | `deriv-trading-db` |
| Database | `deriv_trading` |
| User | `deriv_user` |
| Region | Oregon (US West) — same region as your web service |
| PostgreSQL Version | 16 (or whatever is default) |
| Plan | Free (for testing) or Starter for permanent use |

Leave all other fields as default.

### Step 4 — Click "Create Database"

Wait 1-2 minutes. You will see the status change to "Available" in green.

### Step 5 — Copy the database URL

This is the most important step.

1. Click on your newly created database to open it
2. Scroll down until you see the **"Connections"** section
3. You will see several URLs. You need the **"Internal Database URL"**
4. It looks like this:
   ```
   postgresql://deriv_user:SomeRandomPassword@dpg-xxxxxxxxxx-a/deriv_trading
   ```
5. Click the copy icon next to it
6. Paste it in Notepad

### Step 6 — Create TWO versions of the URL

From the URL you copied, create two versions:

**Version 1 — DATABASE_URL** (change `postgresql://` to `postgresql+asyncpg://`):
```
postgresql+asyncpg://deriv_user:SomeRandomPassword@dpg-xxxxxxxxxx-a/deriv_trading
```

**Version 2 — SYNC_DATABASE_URL** (keep exactly as copied):
```
postgresql://deriv_user:SomeRandomPassword@dpg-xxxxxxxxxx-a/deriv_trading
```

You will paste both of these into Render environment variables in Part 6.

### Step 7 — Update Render if replacing an expired database

If you are creating a new database to replace an expired one:

1. Go to your backend service on Render
2. Click **"Environment"** tab
3. Find **DATABASE_URL** — click the pencil icon to edit it
4. Delete the old value completely
5. Type the new DATABASE_URL (with +asyncpg)
6. Find **SYNC_DATABASE_URL** — edit it
7. Delete the old value
8. Type the new SYNC_DATABASE_URL (without +asyncpg)
9. Click **"Save Changes"**
10. Render will redeploy automatically
11. Wait for status to say **"Live"**

---

## PART 4 — GENERATE SECRET KEY

Open Command Prompt on your VPS:
```
python -c "import secrets; print(secrets.token_hex(64))"
```
Copy the long string it prints. Save it in Notepad.

This is your SECRET_KEY. Rules:
- Never share it with anyone
- Never change it after the app is live — it will log out all users
- If you lose it, generate a new one but all users will be logged out

---

## PART 5 — GET DERIV APP ID AND PAT TOKEN

### Get your App ID (one time only — does not expire)
1. Go to: https://developers.deriv.com
2. Sign up — use a different email from app.deriv.com
3. Go to: Registered Apps in the dashboard
4. Click "Create new app"
5. Fill in:
   - App name: TradingBot (no special characters)
   - Redirect URL: https://deriv-trading-platform-mxic.onrender.com
   - Scopes: check trade and account_manage
6. Click Create
7. Your App ID appears in the list — looks like: 33O8kU94RkSPJmJNahuno
8. Save it — you need it in Render environment variables

Your current App ID is: **33O8kU94RkSPJmJNahuno**
This does not expire. You only create it once.

### Get a PAT Token (renew every 3-6 months)
1. Go to: https://developers.deriv.com
2. Log in
3. Click "API Tokens" in the left menu
4. Click "Create new token"
5. Select scopes: trade and account_manage
6. Click Create
7. Copy the token immediately — it starts with pat_
8. You CANNOT see it again after leaving the page
9. Save it in Notepad
10. Paste it into the app (see Part 11 for how to update it)

---

## PART 6 — DEPLOY BACKEND ON RENDER

### Create Web Service
1. Render dashboard → New + → Web Service
2. Select: Build and deploy from a Git repository
3. Connect to: deriv-trading-platform
   - If not visible, click "Configure account" → give Render access to your repos
4. Fill in:
   - Name: deriv-trading-backend
   - Region: Oregon (same as database)
   - Branch: main
   - Runtime: Docker
   - Instance Type: Free (or Starter for 24/7)

### Add Environment Variables
Click "Add Environment Variable" for each row:

| Key | Value | Notes |
|-----|-------|-------|
| APP_ENV | production | |
| DEBUG | false | |
| SECRET_KEY | paste your generated key | the long random string from Part 4 |
| ALGORITHM | HS256 | |
| ACCESS_TOKEN_EXPIRE_MINUTES | 60 | |
| REFRESH_TOKEN_EXPIRE_DAYS | 30 | |
| DATABASE_URL | postgresql+asyncpg://user:pass@host/db | from Part 3 Step 6 Version 1 |
| SYNC_DATABASE_URL | postgresql://user:pass@host/db | from Part 3 Step 6 Version 2 |
| DERIV_APP_ID | 33O8kU94RkSPJmJNahuno | your App ID from Part 5 |
| DERIV_WS_URL | wss://ws.derivws.com/websockets/v3 | |
| CORS_ORIGINS | https://deriv-trading-platform-mxic.onrender.com | your Render URL |
| LOG_LEVEL | INFO | |

### Deploy and verify
1. Click "Create Web Service"
2. Watch the Logs tab — wait for: `INFO: Application startup complete.`
3. Status turns green and shows "Live"
4. Test it: open https://YOUR-SERVICE.onrender.com/health
5. You should see: `{"status":"ok","service":"Deriv AI Trading Platform"}`

---

## PART 7 — BUILD THE APK

GitHub Actions builds the APK automatically every time you push code.
No Flutter needed on your VPS.

### Update backend URL in app (only needed if your Render URL changes)
Open this file on your VPS:
```
C:\Users\Administrator\deriv-trading-platform\frontend\lib\core\constants\app_constants.dart
```
Find this line and change to your actual URL:
```dart
defaultValue: 'https://deriv-trading-platform-mxic.onrender.com',
```

### Trigger APK build
```
cd C:\Users\Administrator\deriv-trading-platform
git add .
git commit -m "trigger build"
git push origin main
```

### Download APK
1. Go to: https://github.com/Gerald-bit0rgb/deriv-trading-platform
2. Click: Actions tab
3. Click the latest "Flutter CI" run
4. Wait for green tick (10-15 minutes)
5. Scroll to bottom → Artifacts → click "debug-apk"
6. Extract the zip → get app-debug.apk

### Send APK to phone
**Via Telegram:**
1. Open: https://web.telegram.org on VPS browser
2. Log in → click Saved Messages
3. Click paperclip → attach app-debug.apk → send
4. On phone: Telegram → Saved Messages → download → tap to install

**Via Google Drive:**
1. Open: https://drive.google.com on VPS browser
2. New → File upload → upload app-debug.apk
3. On phone: Google Drive → download → install

**Allow installation on phone first:**
Settings → search "Install unknown apps" → allow Telegram or your file manager

---

## PART 8 — FIRST TIME APP SETUP ON PHONE

1. Open Deriv AI Trader
2. Tap Sign Up
3. Fill in: email, username, password
   - Password must have: uppercase letter + number + minimum 8 characters
   - Example: Gerald2024!
4. Tap Create Account
5. Go to Profile tab → Deriv API Token section
6. Paste your pat_ token → tap Save Token → green message = success
7. Go to Risk settings → set safe limits for testing:
   - Default Stake: 1
   - Max Stake: 5
   - Max Daily Loss: 20
   - Max Daily Trades: 10
8. Go to Dashboard → select your trading pair → tap Change to pick one
9. Make sure Account Type shows DEMO (not Real)
10. Tap Start Bot → wait 10-15 seconds → status shows RUNNING

---

## PART 9 — HOW TO UPDATE THE APP IN FUTURE

### Update backend code
1. Make your code changes on the VPS
2. Run:
```
cd C:\Users\Administrator\deriv-trading-platform
git add .
git commit -m "describe your change"
git push origin main
```
3. Go to Render → Manual Deploy → Deploy latest commit
4. Wait for Live

### Update Flutter app
1. Make your changes on the VPS
2. Run:
```
cd C:\Users\Administrator\deriv-trading-platform
git add .
git commit -m "describe your change"
git push origin main
```
3. GitHub Actions builds new APK automatically
4. Download from Actions → Artifacts
5. Install on phone (replaces old version)

---

## PART 10 — WHAT TO DO WHEN THINGS EXPIRE

---

### 10A — GitHub Personal Access Token expires

Signs it has expired:
- git push fails with "Authentication failed"
- Cannot push code to GitHub

How to fix:
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: VPS-Renewed
4. Expiration: No expiration (set this to never have this problem again)
5. Check: repo (top checkbox)
6. Click "Generate token"
7. COPY IT immediately
8. Save in Notepad
9. Next time you run git push, enter your GitHub username and paste the new token as password

Permanent fix: Always set expiration to "No expiration" when creating tokens.

---

### 10B — Render Free Database expires (every 90 days)

Signs it has expired:
- Cannot log in to the app
- Health check at /health returns 500 error
- Render logs show "database does not exist" or connection errors

How to fix:
1. Follow Part 3 completely to create a new database
2. Copy the new database URL (two versions)
3. Go to Render → deriv-trading-backend → Environment tab
4. Update DATABASE_URL with the new URL (with +asyncpg)
5. Update SYNC_DATABASE_URL with the new URL (without +asyncpg)
6. Click Save Changes
7. Wait for Render to redeploy → status shows Live
8. All old accounts and trades are gone — register a new account in the app

Note: Render emails you 14 days before expiry. Watch your email.
Permanent fix: Upgrade database to Starter plan ($7/month) — never expires.

---

### 10C — Deriv PAT token becomes invalid

Signs it is invalid:
- Start Bot shows error
- Bot status goes from "connecting" to "error"
- You see "The token is invalid" or similar message

How to fix:
1. Create a new PAT token (see Part 5 — Get PAT Token section)
2. Then follow Part 11 below to put it in the app

---

## PART 11 — HOW TO UPDATE YOUR DERIV PAT TOKEN IN THE APP

This is what you do every time you create a new PAT token.

### Step 1 — Create the new token first
1. Go to: https://developers.deriv.com
2. Click "API Tokens" in the left menu
3. Find your old token → click the trash/delete icon to remove it
4. Click "Create new token"
5. Select scopes: trade AND account_manage (both must be checked)
6. Click Create
7. The new token appears — copy it immediately (starts with pat_)
8. You cannot see it again — if you miss it, delete and create another

### Step 2 — Stop the bot if it is running
1. Open the app on your phone
2. Go to Dashboard
3. If bot is Running or Paused → tap Stop Bot
4. Wait for status to show STOPPED

### Step 3 — Delete the old token in the app
1. Go to Profile tab (bottom of screen)
2. Scroll to "Deriv API Token" section
3. Tap the eye icon to show the token field
4. Select all the text in the field and delete it
5. The field should be empty

### Step 4 — Paste the new token
1. The field is now empty
2. Tap inside the field
3. Paste your new pat_ token
4. Make sure there are no spaces before or after the token
5. Tap Save Token
6. You should see a green message: "Deriv token saved!"

### Step 5 — Verify it works
1. Go to Dashboard
2. Tap Start Bot
3. Wait 10-15 seconds
4. Status should turn green and show RUNNING
5. Balance should load from your Deriv account

If it still shows error after doing all this — double check you copied the full token and did not miss any characters at the beginning or end.

---

## PART 12 — HOW TO UPGRADE RENDER FROM FREE TO PAID

### Why upgrade?

| What you get | Free plan | Starter ($7/month) |
|-------------|-----------|-------------------|
| Service sleep | Sleeps every 15 min | Never sleeps — 24/7 |
| Database expiry | Expires after 90 days | Never expires |
| Deploy speed | Slow (10+ min) | Fast |
| Uptime | Not guaranteed | 99.9% uptime |
| Good for trading bot | No | Yes |

For a trading bot that needs to run while you sleep — you must upgrade.

### Upgrade the web service (so it never sleeps)
1. Go to: https://dashboard.render.com
2. Click your backend service: deriv-trading-backend
3. Click the "Settings" tab
4. Find "Instance Type" section
5. Click "Change Plan" or "Upgrade"
6. Select "Starter" — $7/month
7. Add a payment card when prompted
8. Click "Upgrade"
9. Service restarts — it will never sleep again

### Upgrade the database (so it never expires)
1. Go to: https://dashboard.render.com
2. Click your database: deriv-trading-db
3. Click "Settings" tab or look for "Upgrade" button
4. Select "Starter" — $7/month
5. Click "Upgrade"
6. Database never expires — your data is safe forever

### Total monthly cost
- Web service Starter: $7/month
- Database Starter: $7/month
- Total: $14/month for full 24/7 professional operation

---

## PART 13 — TROUBLESHOOTING

### "Authentication failed" when running git push
GitHub token expired. Fix: Part 10A — generate new token.

### "The token is invalid" when starting bot
Deriv PAT token invalid. Fix: Part 11 — create and update PAT token.

### Cannot log in to app / "Database error"
Render free database expired (90 days). Fix: Part 3 — create new database, update URLs in Render.

### "Server is starting up" on dashboard
Render free service is sleeping. Fix: wait 60 seconds and pull to refresh. Or upgrade (Part 12).

### "Failed to load dashboard" / dashboard shows error
Server sleeping or crashed. Fix: check health at /health URL, wait 60 seconds, refresh.

### Bot starts but immediately shows error
Deriv PAT token invalid. Fix: Part 11.

### Bot runs but never places trades
Normal — bot waits for the MA Bias strategy conditions to align.
4H EMA5 must be above or below EMA13 AND ADX above 20 AND 15M must confirm.
On strong trending days it places many trades. On sideways days it waits.

### APK won't install on phone
Enable unknown apps: Settings → search "Install unknown apps" → allow.

### GitHub Actions build shows red / failed
Go to GitHub → Actions tab → click the failed run → read the error → fix it.

### Render deploy fails
Go to Render → your service → Logs tab → look for lines starting with ERROR.

---

## PART 14 — ALL IMPORTANT LINKS

| What | Link | Used for |
|------|------|---------|
| GitHub | https://github.com | Code storage |
| GitHub tokens | https://github.com/settings/tokens | Create or renew Personal Access Token |
| Your repo | https://github.com/Gerald-bit0rgb/deriv-trading-platform | Your code |
| GitHub Actions | https://github.com/Gerald-bit0rgb/deriv-trading-platform/actions | APK build status |
| Render dashboard | https://dashboard.render.com | Hosting control panel |
| Render billing | https://dashboard.render.com/billing | Upgrade plan or update card |
| Backend health | https://deriv-trading-platform-mxic.onrender.com/health | Check server is running |
| Deriv trading | https://app.deriv.com | Your trading account (demo/real) |
| Deriv developer | https://developers.deriv.com | App ID and PAT tokens |
| Deriv PAT tokens | https://developers.deriv.com (API Tokens section) | Create or renew PAT token |

---

## PART 15 — ENVIRONMENT VARIABLES REFERENCE

These go in Render → deriv-trading-backend → Environment tab.

| Key | Value | Notes |
|-----|-------|-------|
| APP_ENV | production | |
| DEBUG | false | |
| SECRET_KEY | your 128-char random key | generate once, never change |
| ALGORITHM | HS256 | |
| ACCESS_TOKEN_EXPIRE_MINUTES | 60 | |
| REFRESH_TOKEN_EXPIRE_DAYS | 30 | |
| DATABASE_URL | postgresql+asyncpg://... | from Render database — must have +asyncpg |
| SYNC_DATABASE_URL | postgresql://... | same URL without +asyncpg |
| DERIV_APP_ID | 33O8kU94RkSPJmJNahuno | your App ID — does not expire |
| DERIV_WS_URL | wss://ws.derivws.com/websockets/v3 | never changes |
| CORS_ORIGINS | https://deriv-trading-platform-mxic.onrender.com | your backend URL |
| LOG_LEVEL | INFO | |

---

## PART 16 — QUICK RENEWAL CHECKLIST

### Every 90 days (if on free Render plan):
```
[ ] Create new Render database (Part 3)
[ ] Update DATABASE_URL and SYNC_DATABASE_URL in Render environment (Part 3 Step 7)
[ ] Redeploy backend on Render
[ ] Register new account in app (old data is gone)
```

### Every 3-6 months (security best practice):
```
[ ] Create new Deriv PAT token (Part 5)
[ ] Update token in app (Part 11)
[ ] Test: Start Bot → confirm RUNNING status
```

### When git push fails:
```
[ ] Go to github.com/settings/tokens
[ ] Generate new token with "No expiration"
[ ] Use it as password on next git push
```

### When bot stops working (quick check):
```
[ ] Open: https://deriv-trading-platform-mxic.onrender.com/health
    → Shows ok? → Backend is running, check PAT token
    → Shows error? → Check Render database and redeploy
[ ] In app: Profile → is Deriv token saved? → if not, add it (Part 11)
[ ] In app: Dashboard → tap Start Bot → if error → refresh PAT token (Part 11)
```

### Monthly check (if on paid plan):
```
[ ] Check Render billing at dashboard.render.com/billing — card still valid?
[ ] Check backend health URL — shows ok?
[ ] Test the app — can you log in and start the bot?
```

---

## SECURITY REMINDERS

- NEVER share your SECRET_KEY with anyone
- NEVER share your pat_ token — it gives full trading access to your Deriv account
- NEVER commit .env files to GitHub
- NEVER switch to REAL account until the bot has run on DEMO successfully for weeks
- No trading system guarantees profits — always set risk management limits
- The bot trades real money if you switch to Real account — be careful

---

*Document created: July 2026*
*Backend URL: https://deriv-trading-platform-mxic.onrender.com*
*GitHub: https://github.com/Gerald-bit0rgb/deriv-trading-platform*
*Deriv App ID: 33O8kU94RkSPJmJNahuno*

---

---

# ═══════════════════════════════════════════════════════════════
# PART 17 — MOVING TO A NEW RENDER ACCOUNT
# Complete guide — attaching your GitHub repo to a brand new Render account
# ═══════════════════════════════════════════════════════════════

## When would you do this?

- You want to move to a different email or Render account
- Your current Render account has billing or access issues
- You are setting up on a completely new device
- You want to give someone else their own copy of the backend
- Your current free database expired and you want a clean start

---

## WHAT TO PREPARE BEFORE YOU START

Have all of these ready in Notepad before you begin.
If any are missing, find them using the instructions next to each one.

```
1. GitHub repo URL (never changes):
   https://github.com/Gerald-bit0rgb/deriv-trading-platform

2. SECRET_KEY — your long random string
   Where to find it: Render → old service → Environment → SECRET_KEY
   If you cannot find it, generate a new one (warning below):
   python -c "import secrets; print(secrets.token_hex(64))"
   WARNING: a new SECRET_KEY logs out ALL existing app users

3. Deriv App ID (never expires):
   33O8kU94RkSPJmJNahuno
   Where to find it: https://developers.deriv.com → Registered Apps

4. Deriv PAT token
   Where to find it: https://developers.deriv.com → API Tokens
   If yours is old, create a new one — see Part 5 of this guide

5. Your Render database URL (if reusing old database)
   Where to find it: Render → your database → Connections → Internal Database URL
   OR create a brand new database in Step 2 below
```

---

## STEP 1 — CREATE THE NEW RENDER ACCOUNT

1. Open your browser and go to: **https://render.com**
2. Click **"Get Started for Free"**
3. Click **"Sign up with GitHub"**

   ![Sign up screen — click the GitHub button]

4. A GitHub authorisation page opens
5. Click **"Authorize Render"**
6. You are now inside the new Render dashboard
7. The account is linked to your GitHub — your repos are visible

---

## STEP 2 — CREATE THE DATABASE

You must create the database BEFORE the web service.
The web service needs the database URL when you set it up.

### 2a — Open the new database form
1. In the Render dashboard click the **"New +"** button (top right corner)
2. A dropdown appears — click **"PostgreSQL"**

### 2b — Fill in the settings

| Field | What to type |
|-------|-------------|
| Name | `deriv-trading-db` |
| Database | `deriv_trading` |
| User | `deriv_user` |
| Region | **Oregon (US West)** — important: same region as web service |
| PostgreSQL Version | Leave as default |
| Plan | Free (testing) or Starter ($7/month — never expires) |

Leave all other fields empty or as default.

### 2c — Create and wait
1. Click **"Create Database"**
2. Wait 1-2 minutes
3. The status badge changes to **green "Available"**

### 2d — Copy the database URL

This is the most important step — do not skip it.

1. Click on your database to open it
2. Scroll down until you see the section called **"Connections"**
3. You will see several URL options
4. Find **"Internal Database URL"** — this is the one you need
5. It looks exactly like this:
   ```
   postgresql://deriv_user:AbCdEfGhIjKl@dpg-xxxxxxxxxxxxxxxxxx-a/deriv_trading
   ```
6. Click the **copy icon** next to it
7. Paste it in Notepad

### 2e — Make two versions of the URL

You need two versions for two different environment variables.

Take the URL you copied and create:

**Version 1 — for DATABASE_URL**
Change `postgresql://` to `postgresql+asyncpg://` at the very start:
```
postgresql+asyncpg://deriv_user:AbCdEfGhIjKl@dpg-xxxxxxxxxxxxxxxxxx-a/deriv_trading
```

**Version 2 — for SYNC_DATABASE_URL**
Keep exactly as copied — do not change anything:
```
postgresql://deriv_user:AbCdEfGhIjKl@dpg-xxxxxxxxxxxxxxxxxx-a/deriv_trading
```

Save both versions in Notepad. You will paste them in Step 4.

---

## STEP 3 — CREATE THE WEB SERVICE

### 3a — Start a new web service
1. Click **"New +"** (top right)
2. Click **"Web Service"**

### 3b — Connect your GitHub repo
1. The page asks "How would you like to deploy?"
2. Click **"Build and deploy from a Git repository"**
3. You will see a list of your GitHub repos
4. Find **"deriv-trading-platform"** and click **"Connect"**

If you do not see your repo:
- Click **"Configure account"**
- Select your GitHub account
- Tick the checkbox next to `deriv-trading-platform`
- Click **"Save"**
- Go back and click Connect

### 3c — Fill in the service settings

| Field | What to type |
|-------|-------------|
| Name | `deriv-trading-backend` |
| Region | **Oregon (US West)** — must match the database region |
| Branch | `main` |
| Runtime | **Docker** — this is important, select Docker not Python |
| Root Directory | leave empty |
| Instance Type | Free or Starter |

---

## STEP 4 — ADD ALL ENVIRONMENT VARIABLES

This is where the backend gets its configuration.
You must add every single variable — missing even one will break things.

Scroll down to the **"Environment Variables"** section.
Click **"Add Environment Variable"** for each row in the table below.

### Complete table of all 12 variables:

| Key | Value | How to get it |
|-----|-------|--------------|
| `APP_ENV` | `production` | Type exactly as shown |
| `DEBUG` | `false` | Type exactly as shown |
| `SECRET_KEY` | your long random string | From Notepad (old key or newly generated) |
| `ALGORITHM` | `HS256` | Type exactly as shown |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Type exactly as shown |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Type exactly as shown |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Version 1 from Step 2e |
| `SYNC_DATABASE_URL` | `postgresql://...` | Version 2 from Step 2e |
| `DERIV_APP_ID` | `33O8kU94RkSPJmJNahuno` | Your App ID — does not change |
| `DERIV_WS_URL` | `wss://ws.derivws.com/websockets/v3` | Type exactly as shown |
| `CORS_ORIGINS` | `https://deriv-trading-backend.onrender.com` | Update after deploy if URL is different |
| `LOG_LEVEL` | `INFO` | Type exactly as shown |

### Detailed explanation of where to find each value:

**SECRET_KEY**
- Best option: use the same key from your old Render account
  - Go to old Render account → your service → Environment → copy the SECRET_KEY value
- If you cannot access the old account: generate a new one:
  ```
  python -c "import secrets; print(secrets.token_hex(64))"
  ```
- If you generate a new key: all existing users will be logged out of the app
- The key must be at least 32 characters long

**DATABASE_URL**
- This is Version 1 from Step 2e above
- Must start with `postgresql+asyncpg://`
- The password in the middle is random — copy it exactly

**SYNC_DATABASE_URL**
- This is Version 2 from Step 2e above
- Must start with `postgresql://` (no +asyncpg)
- The password must be the same as in DATABASE_URL

**DERIV_APP_ID**
- Your existing App ID: `33O8kU94RkSPJmJNahuno`
- This never changes and never expires
- If you cannot find it: go to https://developers.deriv.com → Registered Apps → copy from the table

**CORS_ORIGINS**
- You do not know the exact URL yet at this step
- For now type: `https://deriv-trading-backend.onrender.com`
- After deployment you will get the real URL and update this if needed (Step 7)

---

## STEP 5 — DEPLOY THE SERVICE

1. Scroll to the very bottom of the page
2. Click the big blue button **"Create Web Service"**
3. The service starts deploying — you are taken to the logs page

### What to watch for in the logs:
```
==> Cloning from https://github.com/Gerald-bit0rgb/deriv-trading-platform...   ✓ done
==> Building Docker image...
==> Successfully built image
==> Starting service...
INFO:     Application startup complete.                                          ← this line means success
```

- The green badge at the top changes to **"Live"**
- This takes 5-10 minutes the first time
- If it says "Deploy failed" — check the logs for red error lines

---

## STEP 6 — GET YOUR NEW BACKEND URL

After the service is live:

1. Look at the top of the service page
2. Your URL is shown under the service name
3. It looks like one of these:
   ```
   https://deriv-trading-backend.onrender.com
   ```
   or with a random suffix:
   ```
   https://deriv-trading-backend-xxxx.onrender.com
   ```
4. Copy this URL — you need it in the next steps

---

## STEP 7 — UPDATE CORS_ORIGINS IF URL IS DIFFERENT

If your new URL is different from what you typed in Step 4:

1. Click the **"Environment"** tab on your service page
2. Find the row for **CORS_ORIGINS**
3. Click the **pencil/edit icon** on that row
4. Delete the old value
5. Type your actual new URL (from Step 6)
6. Click **"Save Changes"**
7. Render redeploys automatically — wait for **"Live"**

---

## STEP 8 — TEST THE BACKEND IS WORKING

Open your browser and go to your health check URL:
```
https://YOUR-NEW-URL.onrender.com/health
```

You must see exactly this response:
```json
{"status":"ok","service":"Deriv AI Trading Platform"}
```

If you see that — your backend is fully working on the new account.

If you see an error:
- Wait 30 seconds and try again (service may still be waking up)
- Check the Logs tab on Render for red error lines
- Most common cause: DATABASE_URL is wrong — check it has +asyncpg

---

## STEP 9 — UPDATE THE FLUTTER APP WITH THE NEW URL

Only do this step if your new Render URL is different from the old one.

If the URL is the same as before — skip this step.

### How to check if it changed:
- Old URL: `https://deriv-trading-platform-mxic.onrender.com`
- New URL: whatever you got in Step 6
- If they are different → follow the steps below

### How to update it:
1. On your VPS open Command Prompt
2. Open the constants file in Notepad:
   ```
   notepad C:\Users\Administrator\deriv-trading-platform\frontend\lib\core\constants\app_constants.dart
   ```
3. Find this line:
   ```dart
   defaultValue: 'https://deriv-trading-platform-mxic.onrender.com',
   ```
4. Change the URL to your new one — keep the quotes and comma
5. Save the file (Ctrl+S)
6. Push to GitHub:
   ```
   cd C:\Users\Administrator\deriv-trading-platform
   git add .
   git commit -m "Update backend URL for new Render account"
   git push origin main
   ```
7. GitHub Actions builds a new APK automatically (10-15 minutes)
8. Go to GitHub → Actions tab → download the new APK from Artifacts
9. Send to phone and install (replaces old version)

---

## STEP 10 — SET UP THE APP ON YOUR PHONE

Since you have a brand new database, all old accounts are gone.
You need to create a new account in the app.

1. Open **Deriv AI Trader** on your phone
2. Tap **Sign Up**
3. Enter your details:
   - Email: your email address
   - Username: choose any name (min 3 characters)
   - Password: must have uppercase + number + min 8 chars (example: Gerald2024!)
4. Tap **Create Account**
5. You land on the Dashboard

6. Go to **Profile** tab
7. Scroll to **Deriv API Token** section
8. Paste your `pat_` token
9. Tap **Save Token**
10. Green message = success

11. Go to **Risk** settings → set your limits
12. Go to **Dashboard** → select your trading pair → tap **Change**
13. Make sure Account Type shows **DEMO**
14. Tap **Start Bot**
15. Wait 10-15 seconds → status shows **RUNNING**

---

## COMPLETE CHECKLIST FOR MOVING TO NEW RENDER ACCOUNT

Print this or save it. Tick each box as you complete it.

```
PREPARATION
[ ] Have GitHub repo URL ready: https://github.com/Gerald-bit0rgb/deriv-trading-platform
[ ] Have SECRET_KEY ready (from old Render or newly generated)
[ ] Have Deriv App ID ready: 33O8kU94RkSPJmJNahuno
[ ] Have Deriv PAT token ready (from developers.deriv.com)

STEP 1 — NEW RENDER ACCOUNT
[ ] Created new account at render.com
[ ] Signed up with GitHub
[ ] Authorized Render to access GitHub

STEP 2 — DATABASE
[ ] Clicked New + → PostgreSQL
[ ] Filled in: Name=deriv-trading-db, Database=deriv_trading, User=deriv_user
[ ] Region set to Oregon
[ ] Database status shows Available
[ ] Copied Internal Database URL
[ ] Created Version 1 (DATABASE_URL) — starts with postgresql+asyncpg://
[ ] Created Version 2 (SYNC_DATABASE_URL) — starts with postgresql://
[ ] Both versions saved in Notepad

STEP 3 — WEB SERVICE
[ ] Clicked New + → Web Service
[ ] Connected to deriv-trading-platform GitHub repo
[ ] Name set to: deriv-trading-backend
[ ] Region set to: Oregon
[ ] Runtime set to: Docker (not Python)
[ ] Branch set to: main

STEP 4 — ENVIRONMENT VARIABLES (all 12 must be added)
[ ] APP_ENV = production
[ ] DEBUG = false
[ ] SECRET_KEY = [your key]
[ ] ALGORITHM = HS256
[ ] ACCESS_TOKEN_EXPIRE_MINUTES = 60
[ ] REFRESH_TOKEN_EXPIRE_DAYS = 30
[ ] DATABASE_URL = postgresql+asyncpg://... [from Step 2]
[ ] SYNC_DATABASE_URL = postgresql://... [from Step 2]
[ ] DERIV_APP_ID = 33O8kU94RkSPJmJNahuno
[ ] DERIV_WS_URL = wss://ws.derivws.com/websockets/v3
[ ] CORS_ORIGINS = https://[your-service-url].onrender.com
[ ] LOG_LEVEL = INFO

STEP 5 — DEPLOY
[ ] Clicked Create Web Service
[ ] Logs show: Application startup complete.
[ ] Status shows: Live (green)

STEP 6 — GET URL
[ ] Copied new backend URL from service page

STEP 7 — UPDATE CORS
[ ] Updated CORS_ORIGINS with actual URL if it was different

STEP 8 — TEST
[ ] Opened https://[new-url].onrender.com/health
[ ] Response shows: {"status":"ok"}

STEP 9 — UPDATE APP (only if URL changed)
[ ] Updated app_constants.dart with new URL
[ ] Pushed to GitHub
[ ] New APK downloaded from Actions → Artifacts
[ ] New APK installed on phone

STEP 10 — APP SETUP
[ ] Registered new account in app
[ ] Saved Deriv PAT token in Profile
[ ] Set Risk settings
[ ] Selected trading pair
[ ] Account type set to DEMO
[ ] Start Bot works — status shows RUNNING
```

---

## THINGS THAT STAY THE SAME WHEN MOVING ACCOUNTS

These do not change — no action needed:

| Item | Where it lives | Changes? |
|------|---------------|---------|
| Your code | GitHub repo | Never changes |
| Deriv App ID | developers.deriv.com | Never expires |
| Deriv PAT token | In the app | Same token works anywhere |
| ALGORITHM value | Type manually | Always HS256 |
| DERIV_WS_URL value | Type manually | Never changes |
| LOG_LEVEL value | Type manually | Always INFO |

## THINGS THAT CHANGE WHEN MOVING ACCOUNTS

| Item | Why it changes | What to do |
|------|---------------|-----------|
| Database URL | New database = new URL and password | Create new DB, copy new URL |
| Backend URL | New service may have different subdomain | Update CORS_ORIGINS and app_constants.dart |
| All user accounts | Stored in database, lost with old DB | Register again in the app |
| All trade history | Stored in database, lost with old DB | Starts fresh |

---

*End of Part 17*

---

---

# ═══════════════════════════════════════════════════════════════
# PART 18 — SESSION EXPIRY
# Why "Session Expired" happens and exactly how to fix it
# ═══════════════════════════════════════════════════════════════

## What is a session?

When you log in to the app, the backend gives your phone two tokens:

```
Access Token  — like a key card, used for every request
Refresh Token — used to get a new access token when the old one expires
```

Both tokens have an expiry time. When the access token expires the app
automatically tries to use the refresh token to get a new one. If that
also fails — you see "Session Expired" and get logged out.

---

## Why does the session expire early?

There are 4 causes — from most common to least common:

---

### Cause 1 — ACCESS_TOKEN_EXPIRE_MINUTES is too short (most common)

**Default value in the code: 60 minutes**

This means if you do not open the app for 60 minutes, the token expires.
When you open the app again it tries to refresh automatically — but if
Render is sleeping (free tier), the refresh request times out before
Render wakes up, and you get logged out.

**Signs this is the cause:**
- Session expires after exactly 1 hour of not using the app
- Happens frequently when using Render free tier

---

### Cause 2 — Render free tier server is sleeping

**How it works:**
- Render free tier sleeps after 15 minutes of no activity
- When your access token expires and the app tries to refresh it,
  the server takes 30-60 seconds to wake up
- The old code only waited 15 seconds before giving up
- Result: refresh fails → session expired

**Signs this is the cause:**
- Session expires when you have not used the app for a while
- Dashboard shows "Server is starting up" before the session expired message
- Happens more on free tier than paid

---

### Cause 3 — REFRESH_TOKEN_EXPIRE_DAYS is too short

**Default value in the code: 30 days**

The refresh token itself expires after 30 days. After 30 days you must
log in again manually. This is normal behaviour but can be extended.

**Signs this is the cause:**
- You have not logged in for over 30 days
- Both token and refresh token are expired

---

### Cause 4 — SECRET_KEY was changed

If the SECRET_KEY environment variable on Render is changed,
ALL tokens become invalid immediately and everyone gets logged out.

**Signs this is the cause:**
- Everyone using the app gets logged out at the same time
- Happened right after you changed something on Render

---

## The complete fix — what to change on Render

### Step 1 — Log in to Render
1. Go to: https://dashboard.render.com
2. Click your backend service: **deriv-trading-backend**
3. Click the **"Environment"** tab

### Step 2 — Change these two values

Find each variable and update it:

**Change 1 — Make access token last 7 days instead of 1 hour:**

| Key | Old value | New value | What it means |
|-----|-----------|-----------|---------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | `10080` | 7 days (7 × 24 × 60 = 10080 minutes) |

**Change 2 — Make refresh token last 90 days instead of 30:**

| Key | Old value | New value | What it means |
|-----|-----------|-----------|---------------|
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | `90` | 3 months |

### Step 3 — Save and redeploy
1. Click **"Save Changes"**
2. Render redeploys automatically
3. Wait for status to show **"Live"**

### Step 4 — Log out and log back in once
The new token lifetime only applies to NEW tokens. Your current token
still has the old expiry. Log out and log back in to get a fresh token
with the new 7-day lifetime.

1. Open app → Profile tab → Sign Out
2. Sign In with email and password
3. Done — new session lasts 7 days

---

## What the values mean — choosing the right number

| Value | Meaning | Good for |
|-------|---------|---------|
| `ACCESS_TOKEN_EXPIRE_MINUTES = 60` | Token expires every hour | High security, frequent login required |
| `ACCESS_TOKEN_EXPIRE_MINUTES = 1440` | Token expires every day | Balanced |
| `ACCESS_TOKEN_EXPIRE_MINUTES = 10080` | Token expires every 7 days | **Recommended for this app** |
| `ACCESS_TOKEN_EXPIRE_MINUTES = 43200` | Token expires every 30 days | Long-term, very convenient |

| Value | Meaning | Good for |
|-------|---------|---------|
| `REFRESH_TOKEN_EXPIRE_DAYS = 7` | Must re-login every week | High security |
| `REFRESH_TOKEN_EXPIRE_DAYS = 30` | Must re-login every month | Default |
| `REFRESH_TOKEN_EXPIRE_DAYS = 90` | Must re-login every 3 months | **Recommended** |
| `REFRESH_TOKEN_EXPIRE_DAYS = 365` | Must re-login once a year | Very convenient |

---

## Code fix that was already applied

The app code was also updated to wait longer when refreshing the token.

**Old behaviour:**
- Token expires → app tries to refresh → waits 15 seconds → Render still
  waking up → gives up → logs you out

**New behaviour:**
- Token expires → app tries to refresh → waits **60 seconds** → Render
  wakes up in that time → refresh succeeds → you stay logged in

This means even on the free tier, the auto-refresh works correctly now
because it gives the server enough time to wake up.

---

## Summary — minimum steps to never see "Session Expired" again

```
On Render → Environment tab:

1. ACCESS_TOKEN_EXPIRE_MINUTES = 10080   (change from 60)
2. REFRESH_TOKEN_EXPIRE_DAYS = 90        (change from 30)
3. Save Changes → wait for Live

In the app:
4. Profile → Sign Out
5. Sign In again
```

After those 5 steps you will not see "Session Expired" for 7 days.
After 7 days the app auto-refreshes silently in the background.
You only need to manually log in again every 90 days.

---

## Security note

Longer token lifetimes are less secure because if someone steals
your token they have more time to use it. For a personal trading app
on your own phone, 7-day access tokens and 90-day refresh tokens are
a good balance between security and convenience.

If you ever think your tokens are compromised:
1. Go to Render → Environment → change your SECRET_KEY to a new random string
2. This immediately invalidates ALL tokens for ALL users
3. Everyone must log in again
4. Generate new SECRET_KEY:
   ```
   python -c "import secrets; print(secrets.token_hex(64))"
   ```

---

*End of Part 18*
