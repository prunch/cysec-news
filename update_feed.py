#!/usr/bin/env python3
"""
Daily updater for Cysec News.
Fetches recent cybersecurity posts from the X API and writes posts.json.
Designed to run as a Render Cron Job.

Required environment variables:
  X_BEARER_TOKEN  - X API v2 Bearer token
  GITHUB_TOKEN    - Personal access token with repo scope (to commit/push)
  GITHUB_REPO     - e.g. prunch/cysec-news (owner/repo)
  GITHUB_BRANCH   - usually main
"""

import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone

BEARER = os.environ.get("X_BEARER_TOKEN")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = os.environ.get("GITHUB_REPO", "prunch/cysec-news")
BRANCH = os.environ.get("GITHUB_BRANCH", "main")

QUERY = '(cybersecurity OR "cyber security" OR infosec OR ransomware OR vulnerability OR CVE OR "zero day" OR CISA) (news OR alert OR update OR report OR breach) -is:retweet -is:reply lang:en'

def fetch_x_posts(max_results=30):
    if not BEARER:
        print("X_BEARER_TOKEN not set", file=sys.stderr)
        return []

    url = "https://api.x.com/2/tweets/search/recent?" + urllib.parse.urlencode({
        "query": QUERY,
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics,author_id,entities",
        "user.fields": "name,username",
        "expansions": "author_id"
    })

    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {BEARER}",
        "User-Agent": "CysecNews/1.0"
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"X API error: {e}", file=sys.stderr)
        return []

    users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
    posts = []

    for tweet in data.get("data", []):
        user = users.get(tweet.get("author_id"), {})
        metrics = tweet.get("public_metrics", {})
        text = tweet.get("text", "")

        lower = text.lower()
        if any(k in lower for k in ["critical", "cvss 10", "zero-day", "0-day", "actively exploited"]):
            severity = "critical"
        elif any(k in lower for k in ["high", "ransomware", "breach", "exploit"]):
            severity = "high"
        elif any(k in lower for k in ["medium", "advisory", "patch"]):
            severity = "medium"
        else:
            severity = "info"

        category = "advisory"
        if any(k in lower for k in ["ransomware", "ransom"]):
            category = "ransomware"
        elif any(k in lower for k in ["breach", "leaked", "stolen"]):
            category = "breach"
        elif any(k in lower for k in ["cve", "vulnerability", "rce", "exploit"]):
            category = "vulnerability"
        elif "ai" in lower or "openai" in lower or "anthropic" in lower:
            category = "ai"

        posts.append({
            "id": tweet["id"],
            "author": user.get("name", "Unknown"),
            "handle": "@" + user.get("username", ""),
            "time": tweet.get("created_at", "")[:10],
            "content": text,
            "severity": severity,
            "tags": [],
            "likes": metrics.get("like_count", 0),
            "reposts": metrics.get("retweet_count", 0),
            "link": f"https://x.com/{user.get('username', '')}/status/{tweet['id']}",
            "category": category
        })

    return posts

def update_posts_json(posts):
    path = "posts.json"
    with open(path, "w") as f:
        json.dump(posts, f, indent=2)
    print(f"Wrote {len(posts)} posts to {path}")

def git_commit_and_push():
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN not set — skipping commit", file=sys.stderr)
        return
    print("Configure git in the cron environment and push posts.json")

if __name__ == "__main__":
    posts = fetch_x_posts()
    if posts:
        update_posts_json(posts)
        git_commit_and_push()
    else:
        print("No posts fetched; leaving posts.json unchanged")
        sys.exit(0)
