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
    # --- The "Fastest" Breaking News ---
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    
    # --- Deep Tech & Open Source (Gemma/Llama news lives here) ---
    "https://huggingface.co/blog/feed.xml",
    "https://machinelearningmastery.com/feed/",
    "https://towardsdatascience.com/feed",
    
    # --- AI Industry Specific ---
    "https://www.artificialintelligence-news.com/feed/",
    "https://www.unite.ai/feed/",
    "https://synthedia.substack.com/feed",
    
    # --- Big Tech Official (Straight from the source) ---
    "https://blog.google/technology/ai/rss/",
    "https://openai.com/news/rss.xml",
    "https://aws.amazon.com/blogs/machine-learning/feed/"
]

# ============================================

def get_top_news(limit=3):
    history = load_history()  # 1. Load the bot's memory
    all_news = []
    
    for url in RSS_FEEDS:
        try:
            response = requests.get(url, timeout=10)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:10]: # Look at top 5 just in case some are duplicates
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
    prompt = f"""You are an expert AI Automation Engineer. From the list below, pick ONLY the TOP 3 stories that are most relevant to:
1. AI Agents & Autonomy (e.g., Google's new ADK or Agentic workflows)
2. Open-source model breakthroughs (e.g., Gemma 4)
3. Cloud Infrastructure for AI (e.g., GKE or NVIDIA updates)

News Stories:
{news_text}

STRICT RULES:
- Post exactly 3 stories.
- Use a professional, punchy hook.
- DO NOT mention 'Day 1' or '100 Days Challenge' in this morning post.
- For each story, explain the "Technical Why" it matters to developers.
- Use emojis for headers, but NO bold or italics.
"""
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
    print(f"🕒 Bot woke up! Current Server Hour (UTC): {current_hour}")
    
    # 4 UTC = 9:30 AM to 10:30 AM IST
    if current_hour == 4:
        print("🌅 Scheduled Morning Mode: Fetching AI News...")
        news = get_top_news(limit=15)
        if news:
        post = generate_roundup_post(news)
        post_to_linkedin(post)
        
        # Smart Saving: Only save links that Gemini actually included in the post
        posted_links = [item['link'] for item in news if item['title'] in post]
        
        # If the title matching is tricky, just save the top 3 we sent:
        if not posted_links:
            posted_links = [item['link'] for item in news[:3]]
            
        save_history(posted_links)
            
    # 14 UTC = 7:30 PM to 8:30 PM IST
    elif current_hour == 14:
        print("🌇 Scheduled Evening Mode: Generating Journey Post...")
        post = generate_journey_post()
        if post:
            post_to_linkedin(post)
            open("daily_log.txt", "w").close() 
            
    # MANUAL OVERRIDE (For when you click the button yourself)
    else:
        print("🚀 Manual Override Triggered: Forcing Morning News Post...")
        news = get_top_news(limit=15)
        if news:
        post = generate_roundup_post(news)
        post_to_linkedin(post)
        
        # Smart Saving: Only save links that Gemini actually included in the post
        posted_links = [item['link'] for item in news if item['title'] in post]
        
        # If the title matching is tricky, just save the top 3 we sent:
        if not posted_links:
            posted_links = [item['link'] for item in news[:3]]
            
        save_history(posted_links)
        else:
            print("💤 No new news found in RSS feeds.")
