# 🚀 Autonomous LinkedIn AI News Agent

A cloud-native Python agent that curates trending AI news, synthesizes professional insights using Google Gemini 2.5 Flash, and publishes a "Daily AI Roundup" directly to LinkedIn.

## ✨ Key Features
* **100% Cloud-Based:** Runs on **GitHub Actions**—no local machine required.
* **Intelligent Memory:** Uses a `history.txt` system to ensure the same news is never posted twice.
* **Expert Analysis:** Powered by **Gemini 2.5 Flash** to provide deep-dive insights into *why* news matters, not just a summary.
* **Automated Scheduling:** Set to post every day at **10:00 AM IST** automatically.
* **Enterprise-Ready:** Built to handle API handshakes, secure secret management, and cross-platform publishing.

## 🛠️ Technical Stack
* **Language:** Python 3.10
* **LLM:** Google Gemini API (Generative AI)
* **Automation:** GitHub Actions (CI/CD)
* **Data Sources:** RSS Feeds (TechCrunch, OpenAI, Google AI Blog, etc.)
* **API:** LinkedIn UGC Post API

## 🚀 Setup & Deployment

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/Abhishekkumarroc/linkedin-ai-agent.git](https://github.com/Abhishekkumarroc/linkedin-ai-agent.git)
    ```

2.  **Configure GitHub Secrets:**
    Go to **Settings > Secrets and variables > Actions** and add:
    * `GEMINI_API_KEY`
    * `LINKEDIN_ACCESS_TOKEN`
    * `LINKEDIN_PERSON_URN`

3.  **Enable Permissions:**
    Under **Settings > Actions > General**, ensure **Workflow permissions** are set to **Read and write permissions**.

4.  **Activate:**
    The agent will run automatically on the cron schedule, or you can trigger it manually via the **Actions** tab.

## 📝 License
MIT License. Feel free to fork and build your own agent!
