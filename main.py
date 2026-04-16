import os
from dotenv import load_dotenv
import feedparser
import requests
from bs4 import BeautifulSoup
from google import genai

load_dotenv()

# ================== CONFIG ==================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_PERSON_URN = os.getenv("LINKEDIN_PERSON_URN")

if not GEMINI_API_KEY or not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_PERSON_URN:
    print("❌ ERROR: Missing API keys or LinkedIn tokens in .env file!")
    exit()

client = genai.Client(api_key=GEMINI_API_KEY)

RSS_FEEDS = [
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://huggingface.co/blog/feed.xml",
    "https://machinelearningmastery.com/feed/",
    "https://towardsdatascience.com/feed",
    "https://www.artificialintelligence-news.com/feed/",
    "https://www.unite.ai/feed/",
    "https://synthedia.substack.com/feed",
    "https://blog.google/technology/ai/rss/",
    "https://openai.com/news/rss.xml",
    "https://aws.amazon.com/blogs/machine-learning/feed/"
]

# ============================================

def get_top_news(limit=3):
    history = load_history()
    all_news = []
    
    for url in RSS_FEEDS:
        try:
            response = requests.get(url, timeout=10)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:10]:
                title = getattr(entry, 'title', '')
                link = getattr(entry, 'link', '')
                
                if link in history:
                    continue
                
                summary = getattr(entry, 'summary', getattr(entry, 'description', ''))[:400]
                soup = BeautifulSoup(summary, 'html.parser')
                clean_summary = soup.get_text()
                
                if title and link:
                    all_news.append({'title': title, 'summary': clean_summary, 'link': link})
        except Exception as e:
            continue
            
    unique_news = {item['title']: item for item in all_news}.values()
    return list(unique_news)[:limit]

import time # Add this to the very top of your file with the other imports!

def generate_roundup_post(news_list):
    news_text = ""
    for item in news_list:
        news_text += f"Title: {item['title']}\nSummary: {item['summary']}\nLink: {item['link']}\n\n"

    prompt = f"""You are a highly respected AI Automation Engineer on LinkedIn. Write a highly engaging, professional daily news roundup.
Choose the TOP 3 most impactful stories from this list:
{news_text}

STRICT FORMATTING RULES:
1. HOOK: One punchy, engaging sentence about the state of AI today.
2. THE UPDATES: For each story, use exactly this layout:
   [Emoji] Headline (Write a catchy headline, DO NOT use markdown bold)
   ↳ The News: 1 sentence summary.
   ↳ The Impact: 1 sentence explaining why this matters to developers or businesses.
   ↳ Link: [Insert the exact URL here]
3. SPACING: Leave a full empty line between each story so it is easy to read.
4. NO ROBOT SPEAK: Do not use labels like "Technical Why" or "In conclusion". Sound human, sharp, and authoritative.
5. HASHTAGS: End with 3-5 relevant hashtags (e.g., #AIAutomation #TechNews #Agents).

Output ONLY the final LinkedIn post."""
    
    # --- NEW RETRY LOGIC ---
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e) or "429" in str(e):
                print(f"⚠️ Gemini API is busy (Attempt {attempt + 1}/{max_retries}). Waiting 30 seconds...")
                time.sleep(30) # Wait 30 seconds before trying again
            else:
                print(f"❌ Unhandled AI generation error: {e}")
                return None
                
    print("❌ Failed to generate content after multiple retries. Skipping today's post.")
    return None

def load_history():
    if not os.path.exists("history.txt"):
        return []
    with open("history.txt", "r") as f:
        return [line.strip() for line in f.readlines()]

def save_history(links):
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

if __name__ == "__main__":
    print("🚀 Bot started! Fetching fresh AI news...")
    
    # Fetch a pool of news
    news_pool = get_top_news(limit=15)
    
    if news_pool:
        # Take the top 3 items that survived the history filter
        top_3_news = news_pool[:3]
        
        # Generate the post using only these 3 specific items
        post_content = generate_roundup_post(top_3_news)
        
        if post_content:
            # Execute LinkedIn post
            post_to_linkedin(post_content)
            
            # CRITICAL: Save these exact links to history.txt immediately
            # This prevents the "Groundhog Day" loop
            links_to_save = [item['link'] for item in top_3_news]
            save_history(links_to_save)
            
            print(f"✅ Success! Post published and {len(links_to_save)} links moved to history.")
        else:
            print("❌ Failed to generate post content.")
    else:
        print("💤 No new news found. All current articles have already been posted.")
