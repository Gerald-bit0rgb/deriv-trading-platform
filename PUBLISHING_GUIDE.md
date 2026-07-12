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
