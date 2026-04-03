import os
from datetime import datetime
from dotenv import load_dotenv
import feedparser
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json

def send_morning_syllabus():
    """Reads the learning vault and sends today's checklist to Telegram."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    # 1. Calculate the current Day of the challenge
    # Change this to the exact date you started Day 1!
    START_DATE = datetime(2026, 4, 3) 
    day_number = str((datetime.now() - START_DATE).days + 1)
    
    # 2. Load the Learning Vault
    try:
        with open("learning_vault.json", "r") as file:
            vault = json.load(file)
    except FileNotFoundError:
        print("❌ learning_vault.json not found!")
        return

    # 3. Get today's topics (or a default message if you run out of days)
    topics = vault.get(day_number, ["Review past concepts and build a custom project!"])
    
    # 4. Format the message for Telegram
    message = f"🤖 *Morning! Here is your Day {day_number} Syllabus:*\n\n"
    for topic in topics:
        message += f"☐ {topic}\n"
    
    message += "\n*Reply to this message as you complete them to add to tonight's log!*"

    # 5. Send it to your phone
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)
    print(f"✅ Sent Day {day_number} syllabus to Telegram.")

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

def generate_roundup_post(news_list):
    # 1. Format the news with Links so Gemini can use them
    news_text = ""
    for item in news_list:
        news_text += f"Title: {item['title']}\nSummary: {item['summary']}\nLink: {item['link']}\n\n"

    # 2. The Strict "Top Creator" Prompt
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

def generate_journey_post():
    """Reads the daily log and turns Telegram notes into a professional LinkedIn post."""
    try:
        # 1. Read your Telegram notes from the log file
        with open("daily_log.txt", "r") as f:
            user_notes = f.read().strip()
        
        if not user_notes:
            print("💤 daily_log.txt is empty. Nothing to post tonight.")
            return None

        # 2. Ask Gemini to format these notes professionally
        prompt = f"""
        You are an AI Automation Engineer. Turn the following rough notes into a professional 
        LinkedIn 'Day X/100' journey post. 
        
        Notes: {user_notes}

        STRICT FORMATTING:
        - Start with a punchy hook about the day's progress.
        - Use the '↳ The News' and '↳ The Impact' structure for 2-3 main achievements.
        - Keep the tone technical, professional, and bold.
        - DO NOT use markdown bold (no **stars**).
        - End with 5 relevant hashtags including #100DaysOfAI #DevOps.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"❌ Error generating journey post: {e}")
        return None

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
        print("🌅 Scheduled Morning Mode: Sending Syllabus & Fetching News...")
        
        # ---> SEND THE CHECKLIST TO YOUR PHONE <---
        send_morning_syllabus() 
        
        news = get_top_news(limit=15)
        if news:
            post = generate_roundup_post(news)
            post_to_linkedin(post)
            # Smart Saving
            posted_links = [item['link'] for item in news if item['title'] in post]
            if not posted_links:
                posted_links = [item['link'] for item in news[:3]]
            save_history(posted_links)
            
    # 14 UTC = 8:00 PM IST
    elif current_hour == 14:
        print("🌇 Scheduled Evening Mode: Generating Journey Post...")
        post = generate_journey_post()
        if post:
            post_to_linkedin(post)
            # THIS IS THE ERASER: It only runs once a day at 8 PM
            with open("daily_log.txt", "w") as f:
                f.write("") 
            print("🧹 daily_log.txt cleared for tomorrow.")
            
    # ALL OTHER HOURS (The Hourly Telegram Check)
    else:
        print("💤 Hourly check complete. Telegram updated. No LinkedIn post scheduled right now.")
