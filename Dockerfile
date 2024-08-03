# Using the base Python image
FROM python:3.9-slim

# Installing curl and dependencies
RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*
   
# Installing Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copying the project code into the image
COPY . /app
WORKDIR /app

# Command to run the bot
CMD ["python", "bot.py"]
