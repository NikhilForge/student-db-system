# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the app
COPY . .

# Create MySQL database directory (if needed)
RUN mkdir -p /var/lib/mysql

# Expose Flask port
EXPOSE 5000

# Start Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "app:app"]