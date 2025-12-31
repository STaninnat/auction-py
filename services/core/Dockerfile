FROM python:3.14.2-slim

WORKDIR /app

# Prevent Python from writing to .pyc files and print logs immediately.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]