# Cysec News

Cybersecurity news and informative posts from X.com.

**Domain:** cysec.news

Static site hosted on Render. Daily cron job refreshes `posts.json` from the X API.

## Files

- `index.html` — Spartan frontend
- `posts.json` — Current feed (updated by cron)
- `update_feed.py` — Fetches from X API v2 and rewrites `posts.json`

## Deploy on Render

### 1. Static Site
- New → Static Site
- Connect `prunch/cysec-news`
- Build Command: (blank)
- Publish Directory: `.`
- Custom domain: `cysec.news` (add in Settings after deploy)

### 2. Daily Cron Job
- New → Cron Job
- Same repo
- Schedule: `0 12 * * *` (noon UTC daily; adjust as needed)
- Command: `python update_feed.py`
- Environment variables:
  - `X_BEARER_TOKEN` — from X Developer Console
  - `GITHUB_TOKEN` — fine-grained or classic token with `contents:write` on this repo
  - `GITHUB_REPO` — `prunch/cysec-news`
  - `GITHUB_BRANCH` — `main`

The cron writes `posts.json` and pushes it; the static site auto-deploys.

## X API

- Recent search endpoint (`/2/tweets/search/recent`)
- Pay-per-use (~$0.005 per post returned)
- Typical daily cost for this feed: a few cents to low dollars depending on volume

## Local

```bash
python -m http.server 8000
# open http://localhost:8000
```
