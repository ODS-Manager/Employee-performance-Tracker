FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables for Cloud Run
ENV DATABASE_URL=sqlite:///./app.db
ENV SECRET_KEY=dev-secret-key-for-production
ENV CORS_ORIGINS=*

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8080

# Run the application with port from environment
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
