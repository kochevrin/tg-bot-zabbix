#!/bin/bash

# This script is part of the tg-bot application and is used to send messages to a Telegram bot or directly to Telegram if the bot API fails.

# Token of your Telegram bot
token='YOUR-BOT-TOKEN-IS-HERE'

# Parameters for sending the message
chat="$1"
subj="$2"
message="$3"

# URL of your docker server with the running tg-bot
web_url="http://your-bot-ip-address:8989/zabbmess"


# Prepare the message text
text_j="${subj}\n${message}"
text_bot=$(printf "%s\n%s" "$text_j" | tr -d '\r' | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
text_zab=$(printf "%s\n%s" "$text_j" | tr -d '\r' | sed 's/"/\\"/g')
output="chat_id&${chat}@text&${text_bot}"

# Attempt to send the message to the bot API via the webhook (bot API)
response=$(curl -s --header 'Content-Type: application/json' \
    --request 'POST' \
    --data "{\"data\":\"${output}\"}" \
    --max-time 5 "${web_url}")

status=$?


# Output the response for debugging
echo "Response from bot API: $response"

# Check if the message was successfully sent to the bot API
if [[ $status -eq 0 ]]; then
  echo "Message sent successfully to bot API"
else
  echo "Bot API failed, sending message via Telegram API"
  /usr/bin/curl -s --header 'Content-Type: application/json' --request 'POST' --data "{\"chat_id\":\"${chat}\",\"text\":\"${text_zab}\n\n---TG_api_Send---\"}" "https://api.telegram.org/bot${token}/sendMessage"
fi