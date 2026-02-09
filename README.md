# Hardcover AI Librarian

This shitty vibecoded app pulls your Hardcover library, runs it through Gemini, and ** I think ** it gives you recommendations?

### Requirements

- Your Hardcover API
- A Gemini API


## 🚀 How to Run

### Option 1: Quick Start (Enter keys in browser)
Just run the image. You will be asked for your keys in the sidebar.
```
docker run -p 8501:8501 dukkokun/hardcover-ai
```

### Option 2: Pass Keys via Command Line (No typing)

```
docker run -p 8501:8501 \
  -e STREAMLIT_SECRETS_CONNECTIONS_HARDCOVER_TOKEN="YOUR_TOKEN including Bearer" \
  -e STREAMLIT_SECRETS_CONNECTIONS_GEMINI_KEY="YOUR_KEY" \
  dukkokun/hardcover-ai
```

### Option 3: Use a Config File
Mount your local .streamlit folder containing secrets.toml.

```
docker run -p 8501:8501 -v $(pwd)/.streamlit:/app/.streamlit dukkokun/hardcover-ai
```
