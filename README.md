# 📚 Hardcover AI Librarian

[![Build and Push Docker Image](https://github.com/Dukko/hardcover-recommendation-app/actions/workflows/docker-build.yml/badge.svg)](https://github.com/Dukko/hardcover-recommendation-app/actions/workflows/docker-build.yml)

**Your personal literary curator, powered by Artificial Intelligence and your actual reading history.**

Hardcover AI Librarian is a self-hosted web app that connects to your [Hardcover.app](https://hardcover.app) account, analyzes your reading patterns (ratings, genres, moods), and uses advanced Large Language Models (LLMs) to recommend books you will actually love.

It's a lightweight **FastAPI + HTMX** app (no Node/JS build step, no client framework) with a Catppuccin Mocha theme and a live progress stream while it works.

![App Screenshot](https://github.com/Dukko/hardcover-recommendation-app/blob/main/screenshot-1.jpg?raw=true)
![App Screenshot](https://github.com/Dukko/hardcover-recommendation-app/blob/main/screenshot-2.jpg?raw=true)

## ✨ Features

* **Deep Library Analysis:** Fetches your "Read" books from Hardcover to understand your taste profile.
* **Hybrid Intelligence:** Combines your strict filters (genre, page count, publication year, min rating — all slider-based) with AI reasoning (mood, vibe, writing style).
* **Skew Toward:** Search your Hardcover library and pin up to 3 books to nudge recommendations toward a similar vibe, backed by live autocomplete against Hardcover's catalog.
* **Multi-Provider Support:** Choose your brain! Supports **Google Gemini** (free tier available), **OpenAI**, and **Anthropic**, with the model dropdown populated live from each provider's API.
* **Real-Time Verification:** Every recommendation is cross-referenced against Hardcover's database to ensure the book exists and has valid metadata.
* **Live Progress:** A Server-Sent Events stream shows each step (fetching your library, thinking, verifying) instead of a single blocking spinner — useful if your library runs into the hundreds of books.
* **Privacy First:** Your API keys and data never leave your container. Keys are used strictly for API calls; browser-entered keys live only in a signed session cookie, never on disk.

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

A [GitHub Actions workflow](.github/workflows/docker-build.yml) rebuilds and publishes `dukkokun/hardcover-ai-librarian:latest` on every push to `main`, so the easiest path is to just pull it:

```bash
docker run -d \
  -p 8501:8501 \
  -e HARDCOVER_TOKEN="your_hardcover_token_here" \
  -e GEMINI_KEY="your_google_api_key_here" \
  --name hardcover-librarian \
  dukkokun/hardcover-ai-librarian:latest
```

...or use Compose for a persistent setup — copy [`docker-compose-prod.yml`](./docker-compose-prod.yml), fill in your keys, and run:

```bash
docker compose -f docker-compose-prod.yml up -d
```

Open your browser to: http://localhost:8501

Prefer to build from source instead of pulling the published image? `docker build -t hardcover-ai-librarian:latest .` from the repo root, then swap that tag into the command/compose file above.

Note: The app automatically handles the `Bearer ` prefix for Hardcover, so you can paste the raw token or the full string.

---

## 🧑‍💻 Local Development (without Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8501
```

Run the test suite with:

```bash
pytest
```

---

## ⚙️ Environment Variables

- `HARDCOVER_TOKEN` — Required. Your personal API token from Hardcover.app.
- `GEMINI_KEY` — Optional. Google AI Studio API Key.
- `OPENAI_KEY` — Optional. OpenAI API Key.
- `ANTHROPIC_KEY` — Optional. Anthropic Claude API Key.
- `SESSION_SECRET` — Optional. Signs the session cookie used to remember keys you enter in the browser (as opposed to the env vars above). Set this to a fixed random string if you want browser-entered keys to survive a container restart; otherwise a new one is generated each boot and browser-entered keys are simply forgotten.

Any of the four key variables can also be left unset and entered directly in the browser's Settings panel instead — they're editable there regardless of how they were originally provided.

---

## ❓ Troubleshooting

**"Could not fetch models"**

Ensure your API Key is valid and has access to the relevant models. Check the Docker logs for detailed debug output: `docker logs hardcover-librarian`.

**"Bearer token invalid"**

The app tries to auto-correct this, but ensure your `HARDCOVER_TOKEN` looks like a long string of random characters. It usually starts with `eyJ...`.

**"Container crashes immediately"**

Make sure you're on the current image: `docker pull dukkokun/hardcover-ai-librarian:latest` (or `docker compose -f docker-compose-prod.yml pull && docker compose -f docker-compose-prod.yml up -d`).

**Skew search / autocomplete shows nothing**

It needs both a saved Hardcover token and at least 2 characters typed before it queries Hardcover's catalog. If keys were just changed, click **Save Keys** first.

---

## 🤝 Contributing
Pull requests are welcome! If you find a bug or want to add a new AI provider, feel free to open an issue.
