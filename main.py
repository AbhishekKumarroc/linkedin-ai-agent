import os
from datetime import datetime
from dotenv import load_dotenv
import feedparser
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

load_dotenv()

# ================== CONFIG ==================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_PERSON_URN = os.getenv("LINKEDIN_PERSON_URN")

if not GEMINI_API_KEY or not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_PERSON_URN:
    print("❌ ERROR: Missing API keys or LinkedIn tokens in .env file!")
    exit()

genai.configure(api_key=GEMINI_API_KEY)
# Using gemini-1.5-flash as it is the current supported free tier model
model = genai.GenerativeModel('gemini-2.5-flash')

RSS_FEEDS = [
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://openai.com/index/feed/",
    "https://huggingface.co/blog/feed.xml",
    "https://blog.google/products/ai/feed/",
    "https://venturebeat.com/category/ai/feed/"
]

# ============================================

def get_top_news(limit=3):
    history = load_history()  # 1. Load the bot's memory
    all_news = []
    
    for url in RSS_FEEDS:
        try:
            response = requests.get(url, timeout=10)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:5]: # Look at top 5 just in case some are duplicates
                title = getattr(entry, 'title', '')
                link = getattr(entry, 'link', '') # 2. Grab the link!
                
                # 3. THE MAGIC CHECK: If we already posted this link, skip it entirely!
                if link in history:
                    continue
                
                summary = getattr(entry, 'summary', getattr(entry, 'description', ''))[:400]
                soup = BeautifulSoup(summary, 'html.parser')
                clean_summary = soup.get_text()
                
                if title and link:
                    # 4. Add the 'link' to the dictionary so save_history can use it later
                    all_news.append({'title': title, 'summary': clean_summary, 'link': link})
        except Exception as e:
            continue
            
    unique_news = {item['title']: item for item in all_news}.values()
    return list(unique_news)[:limit]

def generate_roundup_post(news_text):
    prompt = f"""Write a high-quality, professional LinkedIn "Daily AI Roundup" post based on these updates:
{news_text}

STRICT STYLING & CONTENT RULES:
1. HOOK: Start with a powerful one-sentence hook about the trajectory of AI innovation followed by a relevant emoji.
2. STRUCTURE: For EACH news item, write a dedicated 3-4 sentence paragraph.
3. FORMAT: Start each paragraph with a unique emoji. Use a BOLD-LIKE header by writing the first sentence in clear, punchy text.
4. INSIGHT: Explain the "Why" — why this matters for the future of tech.
5. NO MARKDOWN: DO NOT use **bold** or *italics*. Use only plain text.
6. SPACING: Ensure a full empty line between every paragraph.
7. CRITICAL RULE: DO NOT mention "100 Days of AI", "Day X", or any daily challenge. This is a pure industry news update.
8. HASHTAGS: Add exactly 5 relevant hashtags at the bottom (e.g., #AI #TechNews #GenerativeAI).

Output exactly the post content and nothing else."""
    
    response = model.generate_content(prompt)
    return response.text.strip()

def load_history():
    """Loads previously posted links to avoid duplicates."""
    if not os.path.exists("history.txt"):
        return []
    with open("history.txt", "r") as f:
        return [line.strip() for line in f.readlines()]

def save_history(links):
    """Saves new links to the history file."""
    with open("history.txt", "a") as f:
        for link in links:
            f.write(link + "\n")

def post_to_linkedin(post_text):
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    
    payload = {
        "author": LINKEDIN_PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": post_text},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 201:
        print("✅ Successfully auto-posted to LinkedIn!")
    else:
        print(f"❌ Failed to post. Status code: {response.status_code}")
        print(response.text)

# ================== MAIN ==================
if __name__ == "__main__":
    current_hour = datetime.now().hour # UTC time
    
    # 4:30 AM UTC = 10:00 AM IST
    if current_hour == 4:
        print("🌅 Morning Mode: Fetching AI News...")
        news = get_top_news(limit=3)
        if news:
            post = generate_roundup_post(news)
            post_to_linkedin(post)
            save_history([item['link'] for item in news])
            
    # 2:30 PM UTC = 8:00 PM IST
    elif current_hour == 14:
        print("🌇 Evening Mode: Generating Journey Post...")
        post = generate_journey_post() # Reads from daily_log.txt
        if post:
            post_to_linkedin(post)
            # Optional: Clear the log after posting so it's ready for tomorrow
            open("daily_log.txt", "w").close()
        post_to_linkedin(post_text)
        print("🎉 Done! Go check your LinkedIn profile.")
