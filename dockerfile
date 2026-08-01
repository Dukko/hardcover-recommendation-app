# Use a lightweight Python base image
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the dependency file first (for better caching)
COPY requirements.txt .

# Install dependencies
# We add --no-cache-dir to keep the image small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY app app
COPY templates templates
COPY static static

# Expose the app port
EXPOSE 8501

# Add a healthcheck (Good practice for production)
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8501"]
