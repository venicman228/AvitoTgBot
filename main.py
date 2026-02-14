### V1.0.3 ###

import asyncio
import time
import validators
import logging
import random
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from usersDb import sql_requests

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

### BOT SETTINGS
bot = Bot(token="923435933:AAHiS5BYwxT4DxgWUF3l3NTu8yAu316T9T4")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

### LOGGING SETTINGS
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пул потоков для запуска Selenium (синхронные операции)
thread_pool = ThreadPoolExecutor(max_workers=10)

# DB FOR USERS PARSERS
users_parsers: Dict[int, List[asyncio.Task, asyncio.Task, asyncio.Task]] = {}
users_parsers = defaultdict(list)
print(users_parsers)

# DB FOR DRIVERS
user_drivers: Dict[int, webdriver.Firefox] = {}

### ADMIN USER_ID
admin = 735962679

### STATE MACHINE
class States(StatesGroup):
    send_url = State()
    replace_url = State()
    parser = State()
    stop_parser = State()
    link_number = State()

### MAIN KEYBOARD
def main_keyboard():
    buttons = [
        [types.KeyboardButton(text="Начать поиск объявлений")],
        [types.KeyboardButton(text="Заменить ссылки для поиска объявлений")],
        [types.KeyboardButton(text="Активные ссылки для поиска объявлений")],
        [types.KeyboardButton(text="Отмена")]
    ]

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите команду"
    )
    return keyboard

### NUMBER KEYBOARD
def number_keyboard():
    buttons = [
        [types.KeyboardButton(text="1")],
        [types.KeyboardButton(text="2")],
        [types.KeyboardButton(text="3")],
        [types.KeyboardButton(text="Отмена")]
    ]

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Введите номер ссылки",
    )
    return keyboard

### START
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    ## ADD USER IN SQL TABLE
    sql_requests.add_user_in_db(message.chat.id)

    await message.answer(
        "С пощью этого бота ты сможешь отслеживать новые объявления на авито",
        reply_markup=main_keyboard()
    )

### РАССЫЛКА
@dp.message(Command("bot_start"))
async def bot_start(message: types.Message, state: FSMContext):
    state.clear()
    if message.chat.id == admin:
        logger.info("Админ запустил рассылку") # debug

        users_id = sql_requests.all_users_id()
        logger.info(f"users: {users_id}") # debug

        for user_id in users_id:
            try:
                await bot.send_message(
                    chat_id=user_id[0],
                    text=
                        "Бот запущен!\n"
                        "Для начала работы пропишите <b>/start</b>",
                    parse_mode="html",
                    reply_markup=main_keyboard()
                )
                logger.info(f"Сообщение отправлено {user_id[0]}")
            except Exception as e:
                logger.error(f"Ошибка у {user_id[0]}\n{e}")


## НАЧАЛЬНАЯ ФУНКЦИЯ ДЛЯ __ОТПРАВКИ__ ССЫЛКИ ПОИСКА
@dp.message(F.text.lower() == "активные ссылки для поиска объявлений")
async def send_active_link(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Отправьте номер ссылки, которую хотите увидеть\n"
        "<b>Доступно 3 ссылки</b>",
        parse_mode="html",
        reply_markup=number_keyboard()
    )
    await state.update_data(send_url=1)
    await state.set_state(States.link_number) # Переходим в состояние link_number

## НАЧАЛЬНАЯ ФУНКЦИЯ ДЛЯ __ЗАМЕНЫ__ ССЫЛКИ ПОИСКА
@dp.message(F.text.lower() == "заменить ссылки для поиска объявлений")
async def replace_link(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Отправьте номер ссылки, которую хотите заменить\n"
        "<b>Доступно 3 ссылки</b>",
        parse_mode="html",
        reply_markup=number_keyboard()
    )
    await state.update_data(replace_url=1)
    await state.set_state(States.link_number) # Переходим в состояние link_number

### ВЫБОР ССЫЛКИ И ОПРЕДЕЛЕНИЕ ТЕКУЩЕЙ ФУНКЦИИ (** СОСТОЯНИЕ LINK_NUMBER **)
@dp.message(F.text, States.link_number)
async def capture_link_number(message: types.Message, state: FSMContext):
    url_number = message.text
    if (url_number in "123"):

        data = await state.get_data()
        await state.update_data(link_number=url_number)

        if data.get("send_url") == 1: # Переходим в состояние send_url
            await send_url(message.chat.id, url_number, state)

        elif data.get("replace_url") == 1: # Переходим в состояние replace_url
            await message.answer(
                f"<b>ВЫБРАНА ССЫЛКА №{message.text}</b>\n\n"
                "Отправьте <b>ссылку</b> в формате <b>https://www.avito.ru//адресс</b>\n"
                "или завершите действие командой <b>\"Отмена\"</b>\n\n"
                f"Ваша текущая ссылка №{message.text}\n"
                f"{sql_requests.get_active_link(url_number, message.chat.id)}",
                parse_mode="html",
                reply_markup=main_keyboard()
            )
            await state.set_state(States.replace_url)

        elif data.get("parser") == 1: # Переходим в состояние parser
            await parser(url_number, message.chat.id, state)
        
        elif data.get("stop_parser") == 1: # Переходим в состояние stop_parser
            await stop_parser(url_number, message.chat.id, state)
            

    elif message.text.lower() == "отмена":
        await message.answer(
            "Ссылка не выбрана!",
            reply_markup=main_keyboard()
        )
        await state.clear()
    else:
        await message.answer(
            "Номер ссылки введен некоректно! <b>Доступно 3 ссылки</b>\n"
            "Повторите попытку или завершите действие командой\n"
            "<b>\"Отмена</b>\"",
            parse_mode="html",
            reply_markup=number_keyboard()
        )
        return

## КОНЕЧНАЯ ФУНКЦИЯ __ОТПРАВКИ__ ССЫЛКИ ПОЛЬЗОВАТЕЛЮ (**СОСТОЯНИЕ SEND_URL**)
async def send_url(user_id, url_number, state: FSMContext):
    await state.set_state(States.send_url)
    link = sql_requests.get_active_link(url_number, user_id)

    if link:
        await bot.send_message(
            user_id,
            f"<b>Текущая ссылка №{url_number}</b>\n{link}",
            parse_mode="html",
            reply_markup=main_keyboard()
        )
    else:
        await bot.send_message(
            user_id,
            "У вас не установлена активная ссылка для поиска",
            reply_markup=main_keyboard()
        )

    await state.update_data(send_url=0)
    await state.clear()

## КОНЕЧНАЯ ФУНКЦИЯ __ЗАМЕНЫ__ ССЫЛКИ ПОИСКА (**СОСТОЯНИЕ REPLACE_URL**)
@dp.message(F.text, States.replace_url)
async def replace_url(message: types.Message, state: FSMContext):
    data = await state.get_data()
    url_number = data.get("link_number")

    # Реализуем выход из текущего состояния сообщением "отмена"
    if message.text.lower() == "отмена":
        await message.answer("Ссылка не изменена", reply_markup=main_keyboard())
        await state.update_data(replace_url=0)
        await state.clear()
    else:
        # Проверяем валидность ссылки
        if validators.url(message.text):
            ## CONNECT TO SQL AND CHANGE "SEARCH_LINK"
            sql_requests.replace_active_link(url_number, message.text, message.chat.id)
            await message.answer(
                f"Ваша новая ссылка №{url_number} для поиска объявлений\n{message.text}",
                reply_markup=main_keyboard()
            )
            await state.update_data(replace_url=0)
            await state.clear()
        else:
            await message.answer(
                "Введена <b>некорректная ссылка</b>, попробуйте еще раз\n"
                "или завершите дейсвтие сообщением <b>\"Отмена\"</b>",
                parse_mode="html",
            )
            return

### START PARSER
##PAGE PARSER
def products_parser(url, user_id):

        try:

            

            ## TAKE USER_AGENT
            user = UserAgent().random # Также можно использовать юзер агенты из файла user_agent_pc.txt, но они почему-то не работают
            while user.split()[1][1:] != ("Windows" or "Linux"): # Исключаем мобильных юзеров
                user = UserAgent().random

            #logger.info(f"Пользователем {user_id} используется следующий юзер агент:\n{user}") # debug

            ## FIREFOX CONFIG
            options = Options()
            #options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-dev-shm-usage")
            options.set_preference("general.useragent.override", f"{user}")
            driver = webdriver.Firefox(options=options)
            driver.get(url)
            user_drivers[user_id] = driver # Сохраняем драйвер для возможности закрытия
            WebDriverWait(driver, 10)

            ## PARSER
            source_data = driver.page_source
            soup = BeautifulSoup(source_data, "html.parser")

            products = soup.find_all("div", {"class": "iva-item-content-fRmzq"})
            products_info = {}  # Создаем словарь вида "ссылка: [название, цена]"

            for product in products[:5]:
                link = f"avito.ru{product.find("a", {"class": "iva-item-sliderLink-kra4e"}).get("href")}"
                title = product.find("h2").text
                price = product.find("div", {"class": "price-priceContent-I4I3p"}).find("span").text
                products_info[link] = [title, price]

            return products_info

        except Exception as e:
            logger.error(f"Ошибка в парсере пользователя {user_id}: {e}") # debug
        finally:
            try: driver.quit()
            except: pass

## ЗАПУСК ПОТОКА
async def run_selenium_in_thread(url, user_id):

    # Запускает Selenium в отдельном потоке
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool,
        products_parser,
        url,
        user_id
    )

async def parser_loop(user_id, url):

    last_sends_product = "NONE"

    while user_id in users_parsers:

        logger.info(f"Запуск парсера для пользователя {user_id} - {datetime.now().hour}:{datetime.now().minute}:{datetime.now().second}") # debug

        try:
            # Парсим объявления
            new_products = await run_selenium_in_thread(url, user_id)

            if new_products:
                # Отправляем только новые объявления
                if len(list(new_products.keys())) >= 1:
                    last_saves_product = new_products[list(new_products.keys())[0]][0]
                    for link in new_products:
                        if (new_products[link][0] != last_sends_product):
                            await bot.send_message(
                                user_id,
                                f"{new_products[link][0]}\n"
                                f"<b>Цена - {new_products[link][1]} рублей</b>\n"
                                f"<b>Ссылка</b>\n{link}",
                                parse_mode="html"
                            )
                        else:
                            break

                    # Обновляем переменную, в которой хранится последнее отправленное объялвение
                    last_sends_product = last_saves_product

            # Ожидание перед следующим запросом
            sec = random.randint(50, 70)
            await asyncio.sleep(sec)

        except Exception as e:
            logger.error(f"Ошибка в отправке объявлений пользователю {user_id}: {e}")
            await asyncio.sleep(sec)  # Ждем перед повторной попыткой

# НАЧАЛО ОТПРАВКИ ОБЪЯВЛЕНИЙ
@dp.message(F.text.lower() == "начать поиск объявлений")
async def start_parser(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Выберите номер ссылки для начала поиска объявлений",
        reply_markup=number_keyboard()
    )
    await state.update_data(parser=1)
    await state.set_state(States.link_number)


async def parser(link_number, user_id, state: FSMContext):
    await state.set_state(States.parser)

    # Проверяем запущен ли у пользователя парсер
    if user_id in users_parsers:
        if users_parsers[user_id][int(link_number)-1] != None:
            await bot.send_message(
                user_id,
                f"Поиск уже запущен!\nДля сброса используйте команду <b>/stop</b>",
                parse_mode="html",
                reply_markup=main_keyboard()
            )
            return
    else:
        for i in range(3): users_parsers[user_id].append(None)
    
    await bot.send_message(
        user_id,
        "Начинаю поиск объявлений для вас\n"
        "Для сброса поиска пропишите команду <b>/stop</b>",
        parse_mode="html",
        reply_markup=main_keyboard()
    )
    await state.clear()

    url = sql_requests.get_active_link(link_number, user_id)
    task = asyncio.create_task(parser_loop(user_id, url))
    users_parsers[user_id][int(link_number)-1] = task

'''
## CLOSE USER DRIVER
async def close_user_driver(user_id):

    if user_id in user_drivers:
        driver = user_drivers[user_id]
        await asyncio.get_event_loop().run_in_executor(
            thread_pool
        )

    if user_id in user_drivers:
        del user_drivers[user_id]
'''

### STOP PARSER
@dp.message(Command("stop"))
async def stop_parser(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(stop_parser=1)
    await message.answer(
        "Выберите номер ссылки для остановки поиска по ней",
        reply_markup=number_keyboard()
    )
    await state.set_state(States.link_number)

async def stop_parser(link_number, user_id, state: FSMContext):
    await state.set_state(stop_parser)
    if user_id in users_parsers:
        if users_parsers[user_id][int(link_number)-1] != None:
            task = users_parsers[user_id][int(link_number)-1]
            task.cancel()
            await bot.send_message(
                user_id,
                f"Поиск объявлений по ссылке №{link_number} остановлен",
                reply_markup=main_keyboard()
            )
            try:
                await task
            except asyncio.CancelledError:
                pass
        else:
            await bot.send_message(
                user_id,
                "Поиск по выбранной ссылке не был запущен!",
                reply_markup=main_keyboard()
            )
            await state.clear()

        users_parsers[user_id][int(link_number)-1] = None
        logger.info(f"Парсер №{link_number} остановлен для пользователя {user_id}") # debug
        await state.clear()

def cleanup():
    # Закрываем пул потоков
    thread_pool.shutdown(wait=True)

    logger.info("Очистка ресурсов завершена")

async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await cleanup()

if __name__ == "__main__":
    asyncio.run(main())