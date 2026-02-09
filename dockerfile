# Use a lightweight Python base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependency file first (for better caching)
COPY requirements.txt .

# Install dependencies
# We add --no-cache-dir to keep the image small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY app.py .
COPY .streamlit .streamlit

#  Setup Entrypoint 
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Expose Streamlit's default port
EXPOSE 8501

# Add a healthcheck (Good practice for production)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Use the entrypoint script to initialize secrets, then run the app
ENTRYPOINT ["./entrypoint.sh"]
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]