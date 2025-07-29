FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.7.1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements-minimal.txt ./

# Install Python dependencies (use minimal for now to avoid conflicts)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-minimal.txt

# Copy application
COPY . .

# Create data and logs directories
RUN mkdir -p /app/data /app/logs

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]