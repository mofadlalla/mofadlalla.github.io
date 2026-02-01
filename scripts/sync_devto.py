import requests
import os
import datetime

# Configuration
DEVTO_USERNAME = "mofadlalla"
POSTS_DIR = "_posts"
DEVTO_API_URL = f"https://dev.to/api/articles?username={DEVTO_USERNAME}"

def fetch_articles():
    response = requests.get(DEVTO_API_URL)
    response.raise_for_status()
    return response.json()

def save_article(article):
    # Extract data
    title = article["title"]
    description = article["description"]
    published_at_str = article["published_at"]
    url = article["url"]
    slug = article["slug"]
    body_markdown = article["body_markdown"]
    
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

if __name__ == "__main__":
    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)
        
    articles = fetch_articles()
    for article in articles:
        save_article(article)
