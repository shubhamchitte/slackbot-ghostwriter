# GitHub Deployment Guide

## Quick Setup: Push to Private GitHub Repository

### Prerequisites
- GitHub account
- Git installed on your machine

---

## Step 1: Initialize Git Repository (if not already done)

```bash
cd /Users/shubh/Antigravity_apps/slackbot-ghostwriter

# Initialize git
git init

# Add all files (respects .gitignore)
git add .

# Initial commit
git commit -m "Initial commit: Digital Ghostwriter MVP"
```

---

## Step 2: Create Private GitHub Repository

### Option A: Via GitHub Web UI
1. Go to https://github.com/new
2. **Repository name:** `slackbot-ghostwriter` (or your preferred name)
3. **Visibility:** Select **Private** ⭐
4. **Do NOT initialize** with README, .gitignore, or license (we already have these)
5. Click "Create repository"

### Option B: Via GitHub CLI (if installed)
```bash
gh repo create slackbot-ghostwriter --private --source=. --remote=origin
```

---

## Step 3: Link Local Repo to GitHub

After creating the GitHub repo, you'll see a URL like:
```
https://github.com/YOUR_USERNAME/slackbot-ghostwriter.git
```

Run these commands:

```bash
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/slackbot-ghostwriter.git

# Verify remote
git remote -v

# Push to GitHub
git push -u origin main
```

**Note:** If your default branch is `master` instead of `main`, use:
```bash
git branch -M main  # Rename to main
git push -u origin main
```

---

## Step 4: Verify What's Uploaded

Your `.gitignore` file ensures these are **NOT uploaded:**
- ❌ `.env` (your API keys)
- ❌ `data/` directory (your SQLite database)
- ❌ `key.txt` (any private keys)
- ❌ `PITCH_DRAFTS.md` (pitch materials)
- ❌ `FOUNDER_PITCH_PREP.md` (pitch materials)
- ❌ `TECHNICAL_DEEP_DIVE.md` (internal documentation)

These **ARE uploaded:**
- ✅ `.env.example` (template for others)
- ✅ All `.py` files (source code)
- ✅ `requirements.txt` (dependencies)
- ✅ `README.md` (public documentation)
- ✅ `SETUP_GUIDE.md` (installation guide)

---

## Step 5: Future Updates

When you make code changes:

```bash
# Stage changes
git add .

# Commit with message
git commit -m "feat: Add retry button for content regeneration"

# Push to GitHub
git push
```

---

## Security Checklist ✅

Before pushing, verify:

1. **No secrets in code:**
   ```bash
   # Search for potential leaks
   grep -r "xoxb-" .  # Slack bot tokens
   grep -r "xapp-" .  # Slack app tokens
   grep -r "AIzaSy" .  # Gemini API keys
   ```

2. **`.env` is excluded:**
   ```bash
   git status
   # Should NOT show .env in staged files
   ```

3. **Database is excluded:**
   ```bash
   ls -la
   # data/ should exist locally but NOT in git
   ```

---

## Cloning the Repo (For Future Setup)

If you or someone else wants to clone and run this later:

```bash
# Clone repo
git clone https://github.com/YOUR_USERNAME/slackbot-ghostwriter.git
cd slackbot-ghostwriter

# Copy environment template
cp .env.example .env

# Edit .env with your tokens
nano .env  # or use VS Code

# Install dependencies
pip install -r requirements.txt

# Run the bot
python main.py
```

---

## Common Issues

### "remote: Repository not found"
- Make sure the GitHub repo is created
- Check if you're using the correct URL
- Verify authentication (GitHub may ask for personal access token instead of password)

### "Permission denied (publickey)"
If using SSH instead of HTTPS:
```bash
# Switch to HTTPS
git remote set-url origin https://github.com/YOUR_USERNAME/slackbot-ghostwriter.git
```

### ".env still showing up in git"
If you accidentally committed `.env` before:
```bash
# Remove from git (but keep local file)
git rm --cached .env
git commit -m "Remove .env from tracking"
git push
```

---

## Next Steps

1. Add a GitHub Actions workflow for automated testing (optional)
2. Create GitHub Issues for feature tracking
3. Write CONTRIBUTING.md if others will collaborate

Your code is now safely backed up in a private GitHub repository! 🚀
