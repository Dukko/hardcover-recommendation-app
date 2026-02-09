# 📚 Hardcover AI Librarian

**Your personal literary curator, powered by Artificial Intelligence and your actual reading history.**

Hardcover AI Librarian is a local web application that connects to your [Hardcover.app](https://hardcover.app) account, analyzes your reading patterns (ratings, genres, moods), and uses advanced Large Language Models (LLMs) to recommend books you will actually love.

![App Screenshot](https://raw.githubusercontent.com/dukkokun/hardcover-recommendation-app/main/screenshot-1.png)
![App Screenshot](https://raw.githubusercontent.com/dukkokun/hardcover-recommendation-app/main/screenshot-2.png)

## ✨ Features

* **Deep Library Analysis:** Fetches your "Read" books from Hardcover to understand your taste profile.
* **Hybrid Intelligence:** Combines your strict filters (Genre, Page Count, Year) with AI reasoning (Mood, Vibe, Writing Style).
* **Multi-Provider Support:** Choose your brain! Supports **Google Gemini** (Free tier available), **OpenAI (GPT-4o)**, and **Anthropic (Claude 3.5)**.
* **Real-Time Verification:** Every recommendation is cross-referenced against Hardcover's database to ensure the book exists and has valid metadata.
* **Privacy First:** Your API keys and data never leave your container. Keys are used strictly for API calls and are not stored permanently.

---

## 🔑 Prerequisites

Before running the app, you need API keys.

1.  **Hardcover API Token (Required):**
    * Go to [Hardcover Settings > API](https://hardcover.app/account/api).
    * Copy your API Token.
2.  **AI Provider Key (At least one required):**
    * **Gemini:** Get a free key at [Google AI Studio](https://aistudio.google.com/).
    * **OpenAI:** Get a key at [platform.openai.com](https://platform.openai.com/).
    * **Anthropic:** Get a key at [console.anthropic.com](https://console.anthropic.com/).

---

## 🚀 Quick Start (Docker)

Create a docker-compose.yml file for a persistent setup: [Compose file](https://github.com/Dukko/hardcover-recommendation-app/blob/main/docker-compose-prod.yml)

Edit the variables with your keys.

Run it:
```docker-compose up -d
```


### Option 2: The One-Liner
Run this command in your terminal. Replace `YOUR_TOKEN` with your actual keys. You can omit the AI keys you aren't using.

```bash
docker run -d \
  -p 8501:8501 \
  -e HARDCOVER_TOKEN="your_hardcover_token_here" \
  -e GEMINI_KEY="your_google_api_key_here" \
  --name hardcover-librarian \
  dukkokun/hardcover-ai-librarian:latest
```
Open your browser to: http://localhost:8501
Note: The app automatically handles the Bearer  prefix for Hardcover, so you can paste the raw token or the full string.

---
## ⚙️ Environment Variables

The container uses a custom entrypoint script to map standard environment variables into Streamlit's secrets system.

- HARDCOVER_TOKEN	Required. Your personal API token from Hardcover.app.

- GEMINI_KEY	Optional. Google AI Studio API Key.

- OPENAI_KEY	Optional. OpenAI API Key.

- ANTHROPIC_KEY	Optional. Anthropic Claude API Key.

---

## ❓ Troubleshooting

"Could not fetch models"

Ensure your API Key is valid and has access to the relevant models (e.g., gemini-1.5-flash).

Check the Docker logs for detailed debug output: docker logs hardcover-librarian.

"Bearer token invalid"

The app tries to auto-correct this, but ensure your HARDCOVER_TOKEN looks like a long string of random characters. It usually starts with eyJ....

"Container crashes immediately"

Ensure you are using the latest image: docker pull dukkokun/hardcover-ai-librarian:latest.

Verify you aren't mounting a directory over the .streamlit folder if you are using environment variables.

--- 

## 🤝 Contributing
Pull requests are welcome! If you find a bug or want to add a new AI provider, feel free to open an issue.
