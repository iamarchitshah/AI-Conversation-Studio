FROM python:3.10-slim

WORKDIR /app

# Copy requirements.txt first for better layer caching
COPY outputs/backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY outputs/backend/ .

# Expose port 8000
EXPOSE 8000

# Start FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
