# Use an official Python runtime as a parent image

FROM python:3.12-slim

# Set environment variables for production-like logging
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Install build dependencies and clean up
RUN apt-get update \
    && apt-get install -y gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first, then install dependencies (for cache efficiency)
COPY container/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY container/ /app/

# Default command to run your scraper
CMD ["python", "main.py"]
