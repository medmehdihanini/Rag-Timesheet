FROM python:3.9-slim

WORKDIR /app

# Install dependencies first (for better Docker caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Download models at build time (optional, can be commented out if you prefer to download at runtime)
RUN python download_models.py

# Expose the port the app will run on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
