# 🚀 LinkedIn Autonomous AI Agent

An autonomous Python agent that curates trending AI news, writes a professional summary using Google Gemini, and automatically publishes a "Daily AI Roundup" to LinkedIn using the official LinkedIn API.

## ✨ Features
* **Automated Curation:** Fetches the latest news from top AI RSS feeds (TechCrunch, OpenAI, HuggingFace, etc.).
* **AI Processing:** Uses Google's Gemini 1.5 Flash model to synthesize the news into a punchy, engaging, and professional LinkedIn post.
* **Direct Publishing:** Posts directly to a LinkedIn profile via the LinkedIn REST API—no human intervention required.
* **Secure:** Designed to run locally or on a server via cron jobs/Task Scheduler with all credentials securely managed.

## 🛠️ Setup & Installation

**1. Clone the repository:**
`git clone https://github.com/Abhishekkumarroc/linkedin-ai-agent.git`
`cd linkedin-ai-agent`

**2. Install dependencies:**
`pip install google-generativeai requests feedparser beautifulsoup4 python-dotenv urllib3`

**3. Configure credentials:**
* Rename `.env.example` to `.env`
* Add your Gemini API Key.
* Add your LinkedIn Access Token and Person URN.

**4. Run the Agent:**
`python main.py`

## 💡 Use Case
Built to maintain a consistent, high-quality, thought-leadership presence on LinkedIn while focusing entirely on building and engineering.
