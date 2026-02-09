#!/bin/bash

# Create the directory if it doesn't exist
mkdir -p .streamlit

# Write the secrets to the file
echo "[connections]" > .streamlit/secrets.toml
echo "hardcover_token = \"$HARDCOVER_TOKEN\"" >> .streamlit/secrets.toml
echo "gemini_key = \"$GEMINI_KEY\"" >> .streamlit/secrets.toml
echo "openai_key = \"$OPENAI_KEY\"" >> .streamlit/secrets.toml
echo "anthropic_key = \"$ANTHROPIC_KEY\"" >> .streamlit/secrets.toml

# Run the command passed to docker (streamlit run ...)
exec "$@"