import requests
import os
import datetime
import time

# Configuration
DEVTO_USERNAME = "mofadlalla"
POSTS_DIR = "_posts"
DEVTO_API_URL = f"https://dev.to/api/articles?username={DEVTO_USERNAME}"

def fetch_articles():
    response = requests.get(DEVTO_API_URL)
    response.raise_for_status()
    return response.json()

def fetch_article_details(article_id):
    url = f"https://dev.to/api/articles/{article_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def save_article(article_summary):
    # Extract basic data to check existence first
    published_at_str = article_summary["published_at"]
    slug = article_summary["slug"]
    
    # Parse date
    published_at = datetime.datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
    date_str = published_at.strftime("%Y-%m-%d")
    
    # Construct filename
    filename = f"{date_str}-{slug}.md"
    filepath = os.path.join(POSTS_DIR, filename)
    
    # Check if file exists
    if os.path.exists(filepath):
        print(f"Skipping existing article: {filename}")
        return

    # Fetch full details to get body_markdown
    print(f"Fetching details for: {article_summary['title']}")
    details = fetch_article_details(article_summary["id"])
    
    title = details["title"]
    description = details["description"]
    url = details["url"]
    body_markdown = details["body_markdown"]

    # Create Jekyll Frontmatter
    frontmatter = f"""---
layout: post
title: "{title}"
description: "{description}"
date: {published_at_str}
canonical_url: {url}
---
"""
    
    # Write to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter)
        f.write(body_markdown)
    
    print(f"Saved new article: {filename}")
    time.sleep(1) # Rate limit courtesy

if __name__ == "__main__":
    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)
        
    articles = fetch_articles()
    for article in articles:
        save_article(article)
