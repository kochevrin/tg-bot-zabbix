# Telegram Bot for zabbix server with Docker

This project includes a Telegram bot that uses Redis for storage and is managed with Docker Compose. The bot interacts with Zabbix to track and manage problems and provides health check and problem reporting functionalities.

## Configuration

❗ **Change the variable `TOKEN` in the `.config.py`** file. 

💡 **Note that the `.config.py` file should be in the same directory as `tg-bot-docker-compose.yml`.**

## Running the Bot

❗ Change the variable "TOKEN" in the `.config.py`.

💡 Note that the `.config.py` file should be in the same directory as `tg-bot-docker-compose.yml`.

## Deploy Telegram Bot using Docker Compose: `docker compose -f tg-bot-docker-compose.yml up -d`

## Bot Code

The bot is implemented using the `aiogram` library and includes the following features:

- **Health Check**: Provides a simple endpoint to check if the bot service is healthy.
- **Problem Management**: Stores and retrieves problem information from Redis.
- **Commands**:
  - `/start`: Greets users and displays a main menu.
  - "My Problems": Retrieves and displays problems assigned to the user.
  - "All Problems": Retrieves and displays all active problems.

### Key Functions

- `formatProblem`: Formats problem messages to extract relevant information.
- `save_problem`: Saves problem information to Redis or removes it if resolved.
- `get_time_difference`: Calculates the time difference between the problem start time and now.
- `get_time_delta`: Converts time difference string into a `timedelta` object.
- `sort_message_answer`: Sorts problems and sends a message with details.

## Web Server

The bot also runs a web server to handle incoming Zabbix messages and perform health checks. The server includes the following routes:

- `/health`: Returns a JSON response indicating the service status.
- `/zabbmess`: Receives messages from Zabbix and sends notifications to the appropriate chat.
- `/`: A default route for basic requests.

## Docker Setup

The project uses Docker Compose to manage the bot and Redis container. The setup includes:

### Services

- **redis**:
  - Image: `redis:latest`
  - Container Name: `redis-server-container`
  - Volumes: `redis-data:/data`
  - Healthcheck: Checks Redis server availability.

- **telegram_bot**:
  - Build: Context and Dockerfile specified
  - Container Name: `telegram-bot-container`
  - Depends on: Redis service
  - Ports: `8989:8989`
  - Volumes: `bot-data:/app/data`
  - Healthcheck: Checks the bot's health endpoint.

### Networks

- **tgNetwork**: Custom network for inter-service communication.

### Volumes

- **redis-data**: Persistent storage for Redis data.
- **bot-data**: Persistent storage for bot data.


## Zabbix Alerts with telegram.sh
The project includes a telegram.sh script, usually located in /usr/lib/zabbix/alertscripts/telegram.sh, designed to send alerts from Zabbix to the Telegram bot. This script handles the following:

- Token: Uses the bot token for authentication.
- Parameters: Takes the chat ID, subject, and message content as inputs.
- Webhook URL: Sends the message to the specified webhook URL if the bot API is reachable.
- Fallback: If the webhook API fails, the script sends the message directly via the Telegram API.
- To use the telegram.sh script:

## To use the telegram.sh script:

- Ensure the script is executable:
- `chmod +x telegram.sh`
- Update the token variable in the script with your Telegram bot token.


# Author
Konstantin Kochervrin