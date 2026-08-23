import os
import warnings
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from urllib.parse import urljoin

# Suppress BS4 XML parsing warning when using html.parser on RSS feeds
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')

# Load links we've already been notified about
def load_seen(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, 'r') as f:
        return f.read().splitlines()

def save_seen(filename, url):
    with open(filename, 'a') as f:
        f.write(url + '\n')

def send_discord_alert(title, url, category):
    if not WEBHOOK_URL:
        print(f"[ALERT - No Webhook] Category: {category} | Title: {title} | Link: {url}")
        return
    data = {"content": f" **New {category} Spotted!**\n**{title}**\n{url}"}
    try:
        requests.post(WEBHOOK_URL, json=data, timeout=10)
    except Exception as e:
        print("Failed to send Discord alert:", e)

ai_seen_file = 'seen_ai_deals.txt'
scholarship_seen_file = 'seen_scholarships.txt'

seen_ai_links = load_seen(ai_seen_file)
seen_scholarship_links = load_seen(scholarship_seen_file)
headers = {'User-Agent': 'script:opportunity-sniper:v1.0.0 (by /u/dokja)'}

# ---------------------------------------------------------
# TARGET 1: AI Subscription Deals (via Reddit RSS Atom API)
# ---------------------------------------------------------
# Checking subreddits like r/OpenAI or r/artificial for keywords
reddit_rss_url = "https://www.reddit.com/r/ArtificialInteligence/search.rss?q=subscription OR discount OR free&restrict_sr=1&sort=new"
try:
    response = requests.get(reddit_rss_url, headers=headers, timeout=10)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        entries = soup.find_all('entry')
        for entry in entries[:5]: # Check the 5 newest
            title = entry.find('title').text.strip() if entry.find('title') else "No Title"
            link_tag = entry.find('link')
            post_url = link_tag.get('href') if link_tag else None
            
            if post_url and post_url not in seen_ai_links:
                send_discord_alert(title, post_url, "AI Deal")
                save_seen(ai_seen_file, post_url)
    else:
        print(f"Could not fetch AI deals (Reddit returned status {response.status_code})")
except Exception as e:
    print("Could not fetch AI deals:", e)

# ---------------------------------------------------------
# TARGET 2: Philippine Scholarships (via BeautifulSoup)
# ---------------------------------------------------------
# Example: Scraping a generic scholarship board or news page
# (You can replace this URL with CHED, DOST, or your specific university portal)
scholarship_url = "https://www.scholarships.ph/" 
try:
    response = requests.get(scholarship_url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # This finds standard hyperlink tags. You will need to inspect the 
    # specific website's HTML to target the exact div or class.
    for article in soup.find_all('a', href=True):
        title = article.text.strip()
        link = urljoin(scholarship_url, article['href'])
        
        # Basic keyword filter
        if "2026" in title or "application" in title.lower():
            if link not in seen_scholarship_links:
                send_discord_alert(title, link, "PH Scholarship")
                save_seen(scholarship_seen_file, link)
except Exception as e:
    print("Could not fetch scholarships:", e)