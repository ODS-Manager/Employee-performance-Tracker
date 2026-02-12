FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Add build arguments
ARG DATABASE_URL=sqlite:///./app.db
ARG SECRET_KEY=dev-secret-key-for-production
ARG CORS_ORIGINS=http://localhost:3000,https://ods-frontend-302004244593.asia-south1.run.app

# Copy requirements
COPY Backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY Backend/ .

# Set environment variables for Cloud Run
ENV DATABASE_URL=${DATABASE_URL}
ENV SECRET_KEY=${SECRET_KEY}
ENV CORS_ORIGINS=${CORS_ORIGINS}

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8080

# Run the application with port from environment
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
