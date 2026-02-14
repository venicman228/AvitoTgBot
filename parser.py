import asyncio
import time
import validators
import os
import logging
from typing import Dict
from usersDb import sql_requests

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage


driver = None
try:
    driver.quit()
except:
    pass