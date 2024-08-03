import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.redis import RedisStorage
from aiogram import html
from aiohttp import web
from datetime import datetime, timedelta
import pytz
import json
import hashlib
import re

from config import TOKEN
bot = Bot(token=TOKEN)

# Configure Redis storage
storage = RedisStorage.from_url("redis://default:kkGuru_nd11akv223mB@redis:6379/0")
redKeyZabb = "problemIdZabbRed"

# Initialize the dispatcher
dp = Dispatcher(storage=storage)

# Main keyboard buttons
mainKeyboardButt = [
        [KeyboardButton(text="All Problems"), KeyboardButton(text="My Problems")],
    ]
mainKeyboard = ReplyKeyboardMarkup(keyboard=mainKeyboardButt, resize_keyboard=True, one_time_keyboard=False, input_field_placeholder="Menu:")

# Initialize the router
router = Router()
dp.include_router(router)

# Function to format problem message
async def formatProblem(problemMess: str) -> str:
    pattern = r'Problem name: .+?\nHost: .+'
    match = re.search(pattern, problemMess)
    if match:
        result = match.group()
        return result
    else:
        result = problemMess
        return result

# Function to save problem information to Redis
async def save_problem(messInf: str, chat_id: str):
    pattern = r'Original problem ID:\s*(\d+)'
    match = re.search(pattern, messInf)

    if match:
        problem_id = match.group(1)
        key_problem = f"problem_{int(problem_id)}"

        if "Problem started at" in messInf:
            problemInf = await storage.redis.hget(redKeyZabb, key_problem)
            if not problemInf:
                problemInf = {
                    'message': messInf,
                    'chat_ids': [chat_id]
                }
            else:
                problemInf = json.loads(problemInf.decode('utf-8'))
                problemInf['chat_ids'].append(chat_id)

            await storage.redis.hset(redKeyZabb, key_problem, json.dumps(problemInf))
            print("Problem started")
        elif "Problem has been resolved at" in messInf:
            await storage.redis.hdel(redKeyZabb, key_problem)
            print("Problem has been resolved")
    else:
        saveMess = False
        return saveMess

# Function to get time difference between now and when the problem started
async def get_time_difference(messInf: str):
    pattern = r'Problem started at (\d{2}:\d{2}:\d{2}) on (\d{4}\.\d{2}\.\d{2})'
    match = re.search(pattern, messInf)

    if match:
        time_str = match.group(1)
        date_str = match.group(2)

        datetime_str = f"{date_str} {time_str}"

        timezone = pytz.timezone('Europe/Kiev')

        now = datetime.now(timezone)
        started_time = datetime.strptime(datetime_str, '%Y.%m.%d %H:%M:%S')
        started_time = timezone.localize(started_time)

        time_difference = now - started_time

        days = time_difference.days
        hours, remainder = divmod(time_difference.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        # Change the format here
        formatted_time_difference = f"{days}D:{hours}H:{minutes}M"
    else:
        formatted_time_difference = "indefinitely"

    return formatted_time_difference

# Function to convert time difference string to timedelta
async def get_time_delta(time_diff: str):
    if time_diff == "indefinitely":
        time_delta = timedelta.max
    else:
        days_str, hours_str, minutes_str = time_diff.split(':')
        days = int(days_str[:-1])  # Remove 'D' and convert to int
        hours = int(hours_str[:-1])  # Remove 'H' and convert to int
        minutes = int(minutes_str[:-1])  # Remove 'M' and convert to int
        time_delta = timedelta(days=days, hours=hours, minutes=minutes)

    return time_delta

# Function to sort and send message with problem details
async def sort_message_answer(problems: str, message: Message):
    problems.sort(key=lambda x: x[0], reverse=True)

    current_message = ""
    index = 1

    for _, problem_text in problems:
        indexed_problem_text = f"-[<b>{index}</b>]- {problem_text}"
        if len(current_message) + len(indexed_problem_text) > 4096:
            await message.answer(text=current_message, parse_mode='HTML')
            current_message = indexed_problem_text
        else:
            current_message += indexed_problem_text
        index += 1

    if current_message:
        await message.answer(text=current_message, parse_mode='HTML')
    else:
        current_message = "No active problems for this ID"
        await message.answer(text=current_message, parse_mode='HTML')

# Command handler for /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.reply(text='Hello!',
                         reply_markup=mainKeyboard)

# Callback query handler for adding to list
@router.callback_query(F.data == "add_to_list")
async def handle_add_to_list(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    message_text = callback_query.message.text

    saveMess = True

    await save_problem(message_text, str(chat_id))

    if saveMess == False:
        await callback_query.answer("Invalid problem content!")
    else:
        await callback_query.answer("Problem status updated!")
    await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text=message_text, reply_markup=None)

# Callback query handler for other buttons
@router.callback_query()
async def handle_other_buttons(callback_query: types.CallbackQuery):
    callback_data = callback_query.data
    await callback_query.answer("ERROR!")

# Message handler for "My Problems"
@dp.message(F.text == "My Problems")
async def get_problem(message: Message):
    chat_id = message.from_user.id

    problemZabbix = await storage.redis.hgetall(redKeyZabb)
    if not problemZabbix:
        await message.answer("No active problems found")
        return

    problems = []

    for key, value in problemZabbix.items():
        key_str = key.decode('utf-8')
        problemInf = json.loads(value.decode('utf-8'))
        probID = key_str.split('_')

        if str(chat_id) in problemInf.get('chat_ids', []):
            value_str = problemInf.get('message', '').replace('\\n', '\n')
            time_diff = await get_time_difference(value_str)
            formatted_value_str = await formatProblem(value_str)

            time_delta = await get_time_delta(time_diff)

            problem_text = f"PID <b>{probID[1]}</b> | <b>{time_diff}</b>\n{formatted_value_str}\n\n\n"
            problems.append((time_delta, problem_text))

    await sort_message_answer(problems, message)

# Message handler for "All Problems"
@dp.message(F.text == "All Problems")
async def get_all_problem(message: Message):
    problemZabbix = await storage.redis.hgetall(redKeyZabb)
    if not problemZabbix:
        await message.answer("No active problems found")
        return

    problems = []

    for key, value in problemZabbix.items():
        key_str = key.decode('utf-8')
        problemInf = json.loads(value.decode('utf-8'))
        probID = key_str.split('_')
        value_str = problemInf.get('message', '').replace('\\n', '\n')
        time_diff = await get_time_difference(value_str)
        formatted_value_str = await formatProblem(value_str)

        time_delta = await get_time_delta(time_diff)

        problem_text = f"PID <b>{probID[1]}</b> | <b>{time_diff}</b>\n{formatted_value_str}\n\n\n"
        problems.append((time_delta, problem_text))

    await sort_message_answer(problems, message)

# Webhook routes for handling incoming messages from Zabbix
routes = web.RouteTableDef()

@routes.get('/health')
async def health_check(request):
    return web.json_response({'status': 'healthy'})

@routes.post('/zabbmess')
async def handle_zabbmess(request):
    data = await request.json()
    print(data)

    text = data['data']
    textSp = text.split('@')

    textID = textSp[0]
    textDT = textSp[1]

    chat_id = textID.split('&')[1]
    messInf = textDT.split('&')[1]
    messInf = messInf.replace('#', '\n')
    messInf = messInf.replace('\\n', '\n')

    await save_problem(messInf, str(chat_id))

    await bot.send_message(chat_id, text=messInf, parse_mode='HTML')
    return web.json_response(status=200, text='Message sent!\n')

# Default route for handling basic requests
@routes.get('/')
async def handle_webhook(request):
    if request.method == 'GET':
        return web.Response(text='START!')
    return web.Response(text='Unknown command')

# Function to initialize the web server
async def init_server():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8989)
    await site.start()

# Main function to start the bot and web server
async def main():
    await init_server()
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')