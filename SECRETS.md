# 🔐 Credentials Management Guide

**IMPORTANT**: Never commit credentials to git. Follow this guide for secure management.

## Setup (Do This Once)

### 1. Create `.env.local` (Never Commit)

```bash
cp .env.example .env.local

# Edit .env.local and add your credentials:
# - WYZE_KEY_ID
# - WYZE_API_KEY
# - WYZE_EMAIL
# - WYZE_PASSWORD
# - ONEDRIVE_ACCESS_TOKEN
# - FIREBASE_CREDENTIALS_JSON path
```

### 2. Store Firebase Credentials Safely

```bash
# Save the JSON file locally (outside git)
# Do NOT commit firebase-credentials.json to repo

# Instead:
# 1. Save locally: ./firebase-credentials.json
# 2. Add to .gitignore (already done)
# 3. Reference in .env.local
```

### 3. Verify Secrets Are Protected

```bash
# Check that .gitignore includes secrets
cat .gitignore | grep -E "\.env\.local|firebase-credentials|\.env\.secrets"

# Double-check nothing was committed by accident
git log --all -- '.env.local' '.env' 'firebase-credentials.json'
# Should return nothing
```

## Loading Credentials

### Option A: Load from `.env.local` (Recommended for Local Dev)

```python
# config.py already does this with python-dotenv
from dotenv import load_dotenv
import os

# Automatically loads from .env.local if it exists
load_dotenv('.env.local', override=True)

wyze_key = os.getenv('WYZE_KEY_ID')
wyze_api = os.getenv('WYZE_API_KEY')
```

### Option B: Use Environment Variables (For Docker/Production)

```bash
# When running in Docker or on server, pass as env vars:
docker run -e WYZE_KEY_ID=xxx -e WYZE_API_KEY=yyy thinkcam:latest
```

### Option C: GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
env:
  WYZE_KEY_ID: ${{ secrets.WYZE_KEY_ID }}
  WYZE_API_KEY: ${{ secrets.WYZE_API_KEY }}
```

## Your Credentials

**Wyze API (Valid until 07-06-2027):**
```
Key ID:  06310c1e-1115-4122-814d-209f3b17d742
API Key: WPwnoZ0e1tQlMvZ6XDgesVkUl9wzOX0AkOHSdxCjYC1V0VbJSYPDSrsWUHvs
```

✅ **Added to `.env.local` (local only, not committed)**

## Security Checklist

- [ ] `.env.local` created and in `.gitignore`
- [ ] Never commit `.env` or `.env.local`
- [ ] Never share credentials in Discord/Slack/Email
- [ ] `firebase-credentials.json` in `.gitignore`
- [ ] Run `git log` to verify no secrets were committed
- [ ] If secrets are leaked, rotate them immediately:
  - Wyze: Request new API key
  - OneDrive: Revoke token, get new one
  - Firebase: Delete service account, create new

## Testing

```bash
# Test that credentials load correctly
python -c "from config import get_config; c=get_config(); print(f'Wyze URL: {c.wyze_rtsp_url}')"
# Should NOT print actual credentials
```

## Troubleshooting

**"ModuleNotFoundError: No module named 'dotenv'"**
```bash
pip install python-dotenv
```

**"WYZE_KEY_ID is None"**
1. Check `.env.local` exists in ThinkCam directory
2. Check credentials are there: `cat .env.local | grep WYZE`
3. Verify no spaces around `=`

**"Still shows credentials in git"**
```bash
# If you accidentally committed, remove from history:
git filter-branch --tree-filter 'rm .env.local' HEAD
# Then force push (dangerous - only if private repo)
git push -f origin main
```

---

**Your Wyze credentials are now safely stored locally and protected!** 🔒
