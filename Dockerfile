FROM python:3.13-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

# Set container environment variable
ENV CONTAINER_ENV=true

# Expose port 7860
EXPOSE 7860

# Health check uses the same Python runtime as the app.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health', timeout=3)"

# Run application
CMD ["python", "main.py"]
