# ============================================================
# FinanceBot
# Python 3.13+
# aiogram 3.x
# ============================================================

import asyncio
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from xml.etree import ElementTree

import aiohttp

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


from database import (
    init_database,
    add_user,
    get_user_language,
    change_language,
    add_transaction,
    get_transactions,
    get_transactions_between,
    delete_all_transactions,
    delete_transactions_between,
    delete_transactions_by_type,
    delete_transactions_by_type_between,
)


# ============================================================
# TOKEN
# ============================================================

TOKEN = "8587092342:AAEEd7dh02GPb5pFDhEcu-2tVzoVRv8-Izg"


# ============================================================
# LINKS
# ============================================================

USER_AGREEMENT_URL = "https://example.com/user-agreement"
PUBLIC_OFFER_URL = "https://example.com/offer"

TELEGRAM_CHANNEL_URL = "https://t.me/your_channel"
WEBSITE_URL = "https://example.com"
SUPPORT_URL = "https://t.me/your_support"


# ============================================================
# BOT / DISPATCHER
# ============================================================

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ============================================================
# FSM
# ============================================================

class FinanceStates(StatesGroup):
    waiting_income = State()
    waiting_expense = State()
    waiting_currency = State()


# ============================================================
# TEXTS
# ============================================================

TEXTS = {
    "ru": {
        "start": (
            "👋 Добро пожаловать в FinanceBot! / Welcome to FinanceBot!\n\n"
            "FinanceBot помогает учитывать доходы/расходы, "
            "анализировать бюджет и отслеживать финансовую статистику / "
            "FinanceBot helps you track income/expenses, "
            "analyze your budget, and monitor your financial statistics.\n\n"
            "📄 Пользовательское соглашение / User Agreement\n"
            "🔗 Ссылка / Link\n\n"
            "📄 Оферта / Public Offer\n"
            "🔗 Ссылка / Link\n\n"
            "🌍 Пожалуйста, выберите язык / Please choose your language:\n\n"
            "Нажимая на кнопку выбора языка и продолжая использовать бота, "
            "вы подтверждаете, что ознакомились и соглашаетесь с "
            "Пользовательским соглашением и Публичной офертой. / "
            "By clicking the language selection button and continuing to use the bot, "
            "you confirm that you have read and agree to the User Agreement and Public Offer.\n\n"
        ),

        "menu": "Выберите нужное действие ниже:",

        "income": "💰 Доход",
        "expense": "💸 Расход",
        "statistics": "📊 Статистика",
        "rates": "💱 Курсы валют",
        "settings": "⚙️ Настройки",
        "info": "ℹ️ Больше информации",
        "legal": "📄 Соглашение и оферта",

        "income_prompt": (
            "💰 Введите доход одним сообщением.\n\n"
            "Например:\n"
            "• Зарплата 50000\n"
            "• Получил 2000 от друга\n"
            "• Продал телефон за 15000\n\n"
            "Можно указать валюту: ₽, $, €.\n"
            "Если валюту не указать, я спрошу её отдельно."
        ),

        "expense_prompt": (
            "💸 Введите расход одним сообщением.\n\n"
            "Например:\n"
            "• Купил хлеб за 120\n"
            "• Такси 380\n"
            "• Купил клаву за 5000\n"
            "• Кока кола 150\n\n"
            "Можно указать валюту: ₽, $, €.\n"
            "Если валюту не указать, я спрошу её отдельно."
        ),

        "currency_prompt": "💱 Выберите валюту:",

        "cancel": "❌ Отмена",

        "invalid": (
            "❌ Не удалось распознать финансовую операцию.\n\n"
            "Попробуйте написать, например:\n"
            "• Зарплата 50000\n"
            "• Получил 2000\n"
            "• Хлеб 120\n"
            "• Такси 380\n"
            "• Купил клаву за 5000"
        ),

        "invalid_amount": (
            "❌ Не удалось определить сумму.\n\n"
            "Напишите сумму, например: 5000, 120 ₽ или $25."
        ),

        "saved_income": "✅ Доход сохранён:\n\n{details}",
        "saved_expense": "✅ Расход сохранён:\n\n{details}",

        "category": "Категория",
        "amount": "Сумма",
        "currency": "Валюта",

        "statistics_title": "📊 Статистика",

        "no_data": "📊 За выбранный период операций нет.",

        "today": "Сегодня",
        "yesterday": "Вчера",
        "week": "Эта неделя",
        "month": "Этот месяц",
        "year": "Этот год",
        "all": "Архив / Всё время",

        "income_total": "💰 Доходы",
        "expense_total": "💸 Расходы",
        "balance": "💵 Баланс",
        "transactions": "🧾 Операций",

        "expenses_by_category": "🧾 Расходы по категориям:",

        "rates_title": "💱 Курсы валют",

        "rates_text": (
            "💱 Курсы валют\n\n"
            "Актуальные курсы относительно друг друга:\n\n"
            "🇺🇸 1 USD = ₽{usd:.2f}\n"
            "🇪🇺 1 EUR = ₽{eur:.2f}\n\n"
            "🇷🇺 1 RUB = ${rub_usd:.4f}\n"
            "🇷🇺 1 RUB = €{rub_eur:.4f}\n\n"
            "🇺🇸 1 USD = €{usd_eur:.4f}\n"
            "🇪🇺 1 EUR = ${eur_usd:.4f}\n\n"
            "Курсы обновляются автоматически."
        ),

        "settings_title": "⚙️ Настройки",
        "change_language": "🌍 Изменить язык",
        "delete_data": "🗑️ Удалить все данные",

        "info_text": (
            "ℹ️ Больше информации\n\n"
            "FinanceBot помогает вести учёт личных финансов.\n\n"
            "Здесь можно:\n"
            "• записывать доходы;\n"
            "• записывать расходы;\n"
            "• автоматически определять категории;\n"
            "• смотреть статистику за разные периоды;\n"
            "• отслеживать баланс;\n"
            "• просматривать актуальные курсы валют."
        ),

        "legal_text": (
            "📄 Документы\n\n"
            "Пользовательское соглашение и Публичная оферта "
            "регулируют условия использования FinanceBot."
        ),

        "delete_statistics": "🗑️ Удалить статистику",

        "delete_period": "Выберите период, за который хотите удалить статистику:",
        "delete_type": "Что удалить?",
        "delete_income": "💰 Только доходы",
        "delete_expenses": "💸 Только расходы",
        "delete_both": "🗑️ Доходы и расходы",

        "confirm_delete": (
            "⚠️ Вы действительно хотите удалить выбранные данные?\n\n"
            "Это действие нельзя отменить."
        ),

        "confirm_yes": "✅ Да, удалить",
        "confirm_no": "❌ Отмена",

        "deleted": "✅ Удалено операций: {count}",
        "nothing_deleted": "ℹ️ За выбранный период подходящих операций нет.",

        "back": "🔙 Назад",

        "language_changed": "✅ Язык изменён на русский.",

        "no_rates": "❌ Не удалось получить актуальные курсы валют.",

        "warning": (
            "⚠️ Обратите внимание: в этом месяце расходы составляют "
            "большую часть ваших доходов. Возможно, стоит пересмотреть бюджет."
        ),
    },

    "en": {
        "start": (
            "👋 Welcome to FinanceBot!\n\n"
            "FinanceBot helps you track income and expenses, "
            "analyze your budget, and monitor your financial statistics.\n\n"
            "📄 Пользовательское соглашение / User Agreement\n"
            "🔗 Ссылка / Link\n\n"
            "📄 Оферта / Public Offer\n"
            "🔗 Ссылка / Link\n\n"
            "🌍 Пожалуйста, выберите язык / Please choose your language:\n\n"
            "By clicking a language button and continuing to use the bot, "
            "you confirm that you have read and agree to the "
            "User Agreement and Public Offer."
        ),

        "menu": "Choose an action below:",

        "income": "💰 Income",
        "expense": "💸 Expense",
        "statistics": "📊 Statistics",
        "rates": "💱 Exchange Rates",
        "settings": "⚙️ Settings",
        "info": "ℹ️ More Information",
        "legal": "📄 Agreement & Offer",

        "income_prompt": (
            "💰 Enter your income in one message.\n\n"
            "Examples:\n"
            "• Salary 50000\n"
            "• Got 2000 from a friend\n"
            "• Sold a phone for 15000\n\n"
            "You can specify a currency: ₽, $, €.\n"
            "If you do not specify one, I will ask you separately."
        ),

        "expense_prompt": (
            "💸 Enter your expense in one message.\n\n"
            "Examples:\n"
            "• Bread 120\n"
            "• Taxi 380\n"
            "• Bought a keyboard for 5000\n"
            "• Coca Cola 150\n\n"
            "You can specify a currency: ₽, $, €.\n"
            "If you do not specify one, I will ask you separately."
        ),

        "currency_prompt": "💱 Choose a currency:",

        "cancel": "❌ Cancel",

        "invalid": (
            "❌ I could not recognize the financial transaction.\n\n"
            "Try something like:\n"
            "• Salary 50000\n"
            "• Got 2000\n"
            "• Bread 120\n"
            "• Taxi 380\n"
            "• Bought a keyboard for 5000"
        ),

        "invalid_amount": (
            "❌ I could not determine the amount.\n\n"
            "Enter an amount such as 5000, 120 ₽ or $25."
        ),

        "saved_income": "✅ Income saved:\n\n{details}",
        "saved_expense": "✅ Expense saved:\n\n{details}",

        "category": "Category",
        "amount": "Amount",
        "currency": "Currency",

        "statistics_title": "📊 Statistics",

        "no_data": "📊 There are no transactions for the selected period.",

        "today": "Today",
        "yesterday": "Yesterday",
        "week": "This Week",
        "month": "This Month",
        "year": "This Year",
        "all": "Archive / All Time",

        "income_total": "💰 Income",
        "expense_total": "💸 Expenses",
        "balance": "💵 Balance",
        "transactions": "🧾 Transactions",

        "expenses_by_category": "🧾 Expenses by category:",

        "rates_title": "💱 Exchange Rates",

        "rates_text": (
            "💱 Exchange Rates\n\n"
            "Current exchange rates:\n\n"
            "🇺🇸 1 USD = ₽{usd:.2f}\n"
            "🇪🇺 1 EUR = ₽{eur:.2f}\n\n"
            "🇷🇺 1 RUB = ${rub_usd:.4f}\n"
            "🇷🇺 1 RUB = €{rub_eur:.4f}\n\n"
            "🇺🇸 1 USD = €{usd_eur:.4f}\n"
            "🇪🇺 1 EUR = ${eur_usd:.4f}\n\n"
            "Rates are updated automatically."
        ),

        "settings_title": "⚙️ Settings",
        "change_language": "🌍 Change Language",
        "delete_data": "🗑️ Delete All Data",

        "info_text": (
            "ℹ️ More Information\n\n"
            "FinanceBot helps you manage your personal finances.\n\n"
            "You can:\n"
            "• record income;\n"
            "• record expenses;\n"
            "• automatically detect categories;\n"
            "• view statistics for different periods;\n"
            "• track your balance;\n"
            "• view current exchange rates."
        ),

        "legal_text": (
            "📄 Documents\n\n"
            "The User Agreement and Public Offer "
            "define the terms of using FinanceBot."
        ),

        "delete_statistics": "🗑️ Delete Statistics",

        "delete_period": "Choose the period for which you want to delete statistics:",
        "delete_type": "What do you want to delete?",
        "delete_income": "💰 Income only",
        "delete_expenses": "💸 Expenses only",
        "delete_both": "🗑️ Income and expenses",

        "confirm_delete": (
            "⚠️ Are you sure you want to delete the selected data?\n\n"
            "This action cannot be undone."
        ),

        "confirm_yes": "✅ Yes, delete",
        "confirm_no": "❌ Cancel",

        "deleted": "✅ Deleted transactions: {count}",
        "nothing_deleted": "ℹ️ There are no matching transactions for this period.",

        "back": "🔙 Back",

        "language_changed": "✅ Language changed to English.",

        "no_rates": "❌ Could not get current exchange rates.",

        "warning": (
            "⚠️ Your expenses make up a large part of your income this month. "
            "You may want to review your budget."
        ),
    },
}


# ============================================================
# CATEGORY NAMES
# ============================================================

EXPENSE_CATEGORIES = {
    "food": {
        "ru": "🍔 Продукты",
        "en": "🍔 Food",
    },
    "transport": {
        "ru": "🚕 Транспорт",
        "en": "🚕 Transportation",
    },
    "home": {
        "ru": "🏠 Дом",
        "en": "🏠 Home",
    },
    "clothing": {
        "ru": "👕 Одежда и покупки",
        "en": "👕 Clothing & Shopping",
    },
    "technology": {
        "ru": "💻 Техника",
        "en": "💻 Technology",
    },
    "entertainment": {
        "ru": "🎮 Развлечения",
        "en": "🎮 Entertainment",
    },
    "health": {
        "ru": "💊 Здоровье",
        "en": "💊 Health",
    },
    "education": {
        "ru": "📚 Образование",
        "en": "📚 Education",
    },
    "services": {
        "ru": "📱 Услуги и подписки",
        "en": "📱 Services & Subscriptions",
    },
    "other_expense": {
        "ru": "💰 Другое",
        "en": "💰 Other",
    },
}


INCOME_CATEGORIES = {
    "salary": {
        "ru": "💼 Зарплата",
        "en": "💼 Salary",
    },
    "gift": {
        "ru": "🎁 Подарок",
        "en": "🎁 Gift",
    },
    "sale": {
        "ru": "🛍️ Продажа",
        "en": "🛍️ Sale",
    },
    "side_job": {
        "ru": "💻 Подработка",
        "en": "💻 Side job",
    },
    "other_income": {
        "ru": "💰 Другое",
        "en": "💰 Other",
    },
}


# ============================================================
# SMART CATEGORY DETECTION
# ============================================================

def normalize_text(text):
    text = str(text).lower().strip()

    replacements = {
        "ё": "е",
        "й": "и",
        "ъ": "",
        "ь": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = text.replace("coca-cola", "coca cola")
    text = text.replace("coca_cola", "coca cola")
    text = text.replace("coca-cola", "coca cola")
    text = text.replace("choco-pie", "choco pie")
    text = text.replace("choco_pie", "choco pie")
    text = text.replace("key-board", "keyboard")

    text = re.sub(r"[^a-zа-я0-9]+", " ", text)

    return " ".join(text.split())


def similar(a, b):
    return SequenceMatcher(
        None,
        normalize_text(a),
        normalize_text(b),
        autojunk=False,
    ).ratio()


CATEGORY_LEXICON = {

    "food": [
        # Russian
        "арбуз",
        "арбус",
        "арбузик",
        "дыня",
        "яблоко",
        "яблоки",
        "банан",
        "бананы",
        "апельсин",
        "апельсины",
        "мандарин",
        "мандарины",
        "виноград",
        "клубника",
        "ягоды",
        "лимон",
        "хлеб",
        "булка",
        "батон",
        "лаваш",
        "молоко",
        "кефир",
        "йогурт",
        "сыр",
        "творог",
        "масло",
        "яйца",
        "яйцо",
        "мясо",
        "курица",
        "курятина",
        "свинина",
        "говядина",
        "колбаса",
        "сосиска",
        "сосиски",
        "рыба",
        "икра",
        "рис",
        "гречка",
        "макароны",
        "паста",
        "картошка",
        "картофель",
        "овощи",
        "овощ",
        "помидор",
        "огурец",
        "морковь",
        "лук",
        "салат",
        "суп",
        "борщ",
        "пицца",
        "бургер",
        "гамбургер",
        "шаурма",
        "сэндвич",
        "бутерброд",
        "чипсы",
        "сухарики",
        "печенье",
        "шоколад",
        "конфеты",
        "конфета",
        "торт",
        "мороженое",
        "десерт",
        "еда",
        "продукты",
        "продукт",
        "чокопай",
        "чоко пай",
        "chocopie",
        "choco pie",
        "кола",
        "кока кола",
        "cocacola",
        "coca cola",
        "кока кола",
        "кока-кола",
        "coke",
        "пепси",
        "pepsi",
        "спрайт",
        "sprite",
        "фанта",
        "fanta",
        "напиток",
        "напитки",
        "сок",
        "вода",
        "чай",
        "кофе",
        "энергетик",
        "энергетик",

        # English
        "water",
        "milk",
        "bread",
        "cheese",
        "egg",
        "eggs",
        "meat",
        "chicken",
        "beef",
        "pork",
        "fish",
        "rice",
        "pasta",
        "potato",
        "potatoes",
        "vegetable",
        "vegetables",
        "fruit",
        "apple",
        "banana",
        "orange",
        "grape",
        "melon",
        "watermelon",
        "pizza",
        "burger",
        "hamburger",
        "sandwich",
        "chips",
        "cookie",
        "cookies",
        "chocolate",
        "candy",
        "cake",
        "ice cream",
        "food",
        "groceries",
        "cocacola",
        "coca cola",
        "coke",
        "pepsi",
        "sprite",
        "fanta",
        "juice",
        "tea",
        "coffee",
        "drink",
        "drinks",
        "chocopie",
        "choco pie",
    ],

    "transport": [
        "такси",
        "taxi",
        "автобус",
        "bus",
        "метро",
        "subway",
        "трамвай",
        "tram",
        "троллейбус",
        "trolleybus",
        "поезд",
        "train",
        "электричка",
        "самолет",
        "самолет",
        "plane",
        "flight",
        "билет",
        "ticket",
        "бензин",
        "fuel",
        "gas",
        "заправка",
        "parking",
        "парковка",
        "uber",
        "bolt",
        "каршеринг",
        "carsharing",
        "машина",
        "автомобиль",
        "car",
        "auto",
        "транспорт",
        "transport",
    ],

    "home": [
        "дом",
        "квартира",
        "жилье",
        "аренда",
        "rent",
        "ипотека",
        "mortgage",
        "коммуналка",
        "коммунальные",
        "свет",
        "электричество",
        "electricity",
        "вода дома",
        "отопление",
        "heating",
        "ремонт",
        "repair",
        "мебель",
        "furniture",
        "диван",
        "sofa",
        "couch",
        "кровать",
        "bed",
        "шкаф",
        "wardrobe",
        "стол",
        "table",
        "стул",
        "chair",
        "лампа",
        "lamp",
        "холодильник",
        "fridge",
        "refrigerator",
        "стиральная машина",
        "washing machine",
        "пылесос",
        "vacuum",
        "посуда",
        "dishes",
        "кастрюля",
        "сковорода",
        "полотенце",
        "towel",
        "уборка",
        "cleaning",
        "быт",
        "home",
    ],

    "clothing": [
        "одежда",
        "clothes",
        "clothing",
        "футболка",
        "tshirt",
        "t shirt",
        "рубашка",
        "shirt",
        "кофта",
        "свитер",
        "sweater",
        "худи",
        "hoodie",
        "толстовка",
        "куртка",
        "jacket",
        "пальто",
        "coat",
        "брюки",
        "pants",
        "джинсы",
        "jeans",
        "шорты",
        "shorts",
        "юбка",
        "skirt",
        "платье",
        "dress",
        "носки",
        "socks",
        "обувь",
        "shoes",
        "кроссовки",
        "sneakers",
        "ботинки",
        "boots",
        "сапоги",
        "сумка",
        "bag",
        "рюкзак",
        "backpack",
        "кошелек",
        "wallet",
        "аксессуар",
        "accessory",
        "часы",
        "watch",
        "кольцо",
        "ring",
        "покупки",
        "shopping",
    ],

    "entertainment": [
        "игра",
        "игры",
        "game",
        "games",
        "кино",
        "movie",
        "film",
        "театр",
        "theatre",
        "theater",
        "концерт",
        "concert",
        "музыка",
        "music",
        "подписка на музыку",
        "клуб",
        "club",
        "бар",
        "bar",
        "вечеринка",
        "party",
        "развлечения",
        "entertainment",
        "парк",
        "park",
        "аттракцион",
        "attraction",
        "путешествие",
        "travel",
        "туризм",
        "tourism",
    ],

    "health": [
        "врач",
        "doctor",
        "больница",
        "hospital",
        "клиника",
        "clinic",
        "аптека",
        "pharmacy",
        "лекарство",
        "лекарства",
        "medicine",
        "таблетки",
        "таблетка",
        "pills",
        "pill",
        "анализы",
        "анализ",
        "стоматолог",
        "dentist",
        "зуб",
        "teeth",
        "лечение",
        "treatment",
        "здоровье",
        "health",
        "витамины",
        "vitamins",
    ],

    "education": [
        "школа",
        "school",
        "университет",
        "university",
        "колледж",
        "college",
        "урок",
        "lesson",
        "курсы",
        "course",
        "репетитор",
        "tutor",
        "учеба",
        "education",
        "образование",
        "экзамен",
        "exam",
        "егэ",
        "огэ",
        "книга",
        "book",
        "учебник",
        "textbook",
        "тетрадь",
        "notebook",
        "ручка",
        "pen",
        "карандаш",
        "pencil",
        "канцелярия",
        "stationery",
    ],

    "services": [
        "интернет",
        "internet",
        "мобильная связь",
        "связь",
        "mobile",
        "сим карта",
        "sim",
        "подписка",
        "subscription",
        "netflix",
        "spotify",
        "youtube premium",
        "telegram premium",
        "icloud",
        "google one",
        "облако",
        "cloud",
        "сервис",
        "service",
        "мобильный интернет",
        "internet plan",
        "mobile plan",
        "phone bill",
        "счет за телефон",
    ],

    "technology": [
        "техника",
        "tech",
        "technology",
        "компьютер",
        "computer",
        "pc",
        "ноутбук",
        "laptop",
        "макбук",
        "macbook",
        "монитор",
        "monitor",
        "экран",
        "screen",
        "телефон",
        "phone",
        "smartphone",
        "смартфон",
        "айфон",
        "iphone",
        "андроид",
        "android",
        "планшет",
        "tablet",
        "айпад",
        "ipad",
        "клавиатура",
        "клава",
        "keyboard",
        "keybord",
        "keyboad",
        "keybaord",
        "клаву",
        "мышь",
        "мышка",
        "mouse",
        "наушники",
        "headphones",
        "гарнитура",
        "headset",
        "колонки",
        "speaker",
        "speakers",
        "микрофон",
        "microphone",
        "mic",
        "камера",
        "camera",
        "вебкамера",
        "webcam",
        "зарядка",
        "charger",
        "зарядник",
        "кабель",
        "cable",
        "провод",
        "пауэрбанк",
        "powerbank",
        "power bank",
        "флешка",
        "flash drive",
        "usb",
        "ssd",
        "hdd",
        "процессор",
        "cpu",
        "видеокарта",
        "gpu",
        "принтер",
        "printer",
        "роутер",
        "router",
        "модем",
        "modem",
    ],
}


# ============================================================
# INCOME KEYWORDS
# ============================================================

INCOME_KEYWORDS = {
    "salary": [
        "зарплата",
        "зарплату",
        "зарплатa",
        "salary",
        "paycheck",
        "wage",
        "wages",
        "оклад",
    ],
    "gift": [
        "подарок",
        "подарили",
        "подарил",
        "подарила",
        "gift",
        "birthday money",
    ],
    "sale": [
        "продал",
        "продала",
        "продажа",
        "продал вещь",
        "sale",
        "sold",
    ],
    "side_job": [
        "подработка",
        "подработал",
        "подработала",
        "side job",
        "freelance",
        "подработки",
    ],
}


# ============================================================
# CURRENCY
# ============================================================

def detect_currency(text):
    normalized = normalize_text(text)

    if "€" in text:
        return "EUR"

    if "$" in text:
        return "USD"

    if "₽" in text:
        return "RUB"

    currency_words = {
        "RUB": [
            "руб",
            "рубль",
            "рубля",
            "рублеи",
            "рубли",
            "рублей",
            "ruble",
            "rub",
        ],
        "USD": [
            "доллар",
            "доллара",
            "доллары",
            "долларов",
            "бакс",
            "баксы",
            "usd",
            "dollar",
            "dollars",
        ],
        "EUR": [
            "евро",
            "eur",
            "euro",
            "euros",
        ],
    }

    for currency, words in currency_words.items():
        for word in words:
            if word in normalized:
                return currency

    tokens = normalized.split()

    best_currency = None
    best_score = 0

    for token in tokens:
        if len(token) < 3:
            continue

        for currency, words in currency_words.items():
            for word in words:
                score = SequenceMatcher(
                    None,
                    token,
                    word,
                    autojunk=False,
                ).ratio()

                if len(word) >= 5:
                    threshold = 0.70
                else:
                    threshold = 0.82

                if score >= threshold and score > best_score:
                    best_score = score
                    best_currency = currency

    return best_currency


# ============================================================
# AMOUNT
# ============================================================

def extract_amount(text):
    cleaned = str(text)

    patterns = [
        r"(?<!\d)(\d{1,3}(?:[ \u00a0]\d{3})+(?:[.,]\d{1,2})?)(?!\d)",
        r"(?<!\d)(\d+(?:[.,]\d{1,2})?)(?!\d)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, cleaned)

        if matches:
            value = matches[-1]
            value = value.replace(" ", "").replace("\u00a0", "")
            value = value.replace(",", ".")

            try:
                amount = float(value)

                if amount > 0:
                    return amount
            except ValueError:
                pass

    return None


# ============================================================
# REMOVE AMOUNT / CURRENCY FROM COMMENT
# ============================================================

def clean_comment(text):
    result = str(text)

    result = re.sub(
        r"(?<!\d)\d{1,3}(?:[ \u00a0]\d{3})+(?:[.,]\d{1,2})?(?!\d)",
        " ",
        result,
    )

    result = re.sub(
        r"(?<!\d)\d+(?:[.,]\d{1,2})?(?!\d)",
        " ",
        result,
    )

    result = re.sub(
        r"(₽|\$|€)",
        " ",
        result,
    )

    result = re.sub(
        r"\b(руб(?:лей|ли|ля|ль)?|usd|eur|доллар(?:ов|а|ы)?|евро|"
        r"dollars?|euros?|rubles?)\b",
        " ",
        result,
        flags=re.IGNORECASE,
    )

    result = re.sub(
        r"\s+",
        " ",
        result,
    ).strip()

    return result


# ============================================================
# WORD SIMILARITY
# ============================================================

def word_similarity_score(word, keyword):
    word = normalize_text(word)
    keyword = normalize_text(keyword)

    if not word or not keyword:
        return 0.0

    if word == keyword:
        return 1.0

    if keyword in word or word in keyword:
        return 0.96

    return SequenceMatcher(
        None,
        word,
        keyword,
        autojunk=False,
    ).ratio()


# ============================================================
# SMART CATEGORY
# ============================================================

def smart_category(text, transaction_type):
    if transaction_type != "expense":
        normalized = normalize_text(text)

        best_category = "other_income"
        best_score = 0.0

        for category, keywords in INCOME_KEYWORDS.items():
            for keyword in keywords:
                keyword_normalized = normalize_text(keyword)

                if keyword_normalized in normalized:
                    return category

                for word in normalized.split():
                    if len(word) < 4:
                        continue

                    score = word_similarity_score(
                        word,
                        keyword_normalized,
                    )

                    threshold = (
                        0.70
                        if len(keyword_normalized) >= 7
                        else 0.78
                    )

                    if score >= threshold and score > best_score:
                        best_score = score
                        best_category = category

        return best_category

    normalized = normalize_text(text)

    # Longer phrases get priority.
    exact_matches = []

    for category, keywords in CATEGORY_LEXICON.items():
        for keyword in keywords:
            keyword_normalized = normalize_text(keyword)

            if not keyword_normalized:
                continue

            if keyword_normalized in normalized:
                exact_matches.append(
                    (
                        len(keyword_normalized),
                        category,
                    )
                )

    if exact_matches:
        exact_matches.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return exact_matches[0][1]

    # Special context rules.
    if (
        "вода дома" in normalized
        or "домашняя вода" in normalized
        or "water bill" in normalized
    ):
        return "home"

    if (
        "подписка" in normalized
        or "subscription" in normalized
    ):
        return "services"

    # Fuzzy matching.
    words = normalized.split()

    best_category = "other_expense"
    best_score = 0.0

    for category, keywords in CATEGORY_LEXICON.items():

        for keyword in keywords:
            keyword_normalized = normalize_text(keyword)

            # For multi-word phrases compare the complete phrase.
            if " " in keyword_normalized:
                score = SequenceMatcher(
                    None,
                    normalized,
                    keyword_normalized,
                    autojunk=False,
                ).ratio()

                if len(keyword_normalized) >= 10:
                    threshold = 0.67
                else:
                    threshold = 0.74

                if score >= threshold and score > best_score:
                    best_score = score
                    best_category = category

            for word in words:

                if len(word) < 4:
                    continue

                score = word_similarity_score(
                    word,
                    keyword_normalized,
                )

                if len(keyword_normalized) >= 8:
                    threshold = 0.67
                elif len(keyword_normalized) >= 6:
                    threshold = 0.72
                elif len(keyword_normalized) >= 5:
                    threshold = 0.77
                else:
                    threshold = 0.84

                if (
                    score >= threshold
                    and score > best_score
                ):
                    best_score = score
                    best_category = category

    return best_category


# ============================================================
# FINANCIAL CONTEXT
# ============================================================

def has_financial_context(text, transaction_type):
    normalized = normalize_text(text)

    if extract_amount(text) is not None:
        return True

    if transaction_type == "income":
        keywords = [
            "зарплата",
            "зарплату",
            "salary",
            "income",
            "получил",
            "получила",
            "получил деньги",
            "got",
            "earned",
            "заработал",
            "заработала",
            "подарок",
            "gift",
            "продал",
            "продала",
            "sale",
            "sold",
            "подработка",
            "side job",
        ]
    else:
        keywords = [
            "купил",
            "купила",
            "потратил",
            "потратила",
            "покупка",
            "расход",
            "expense",
            "bought",
            "spent",
            "buy",
            "такси",
            "taxi",
            "хлеб",
            "bread",
            "арбуз",
            "watermelon",
            "клаву",
            "клавиатура",
            "keyboard",
            "cocacola",
            "coca cola",
            "кола",
            "pepsi",
            "пепси",
        ]

    for keyword in keywords:
        if normalize_text(keyword) in normalized:
            return True

    return False


# ============================================================
# LANGUAGE
# ============================================================

async def current_language(
    telegram_id,
    state: FSMContext,
):
    data = await state.get_data()

    language = data.get("language")

    if language in ("ru", "en"):
        return language

    language = get_user_language(telegram_id)

    if language not in ("ru", "en"):
        language = "ru"

    await state.update_data(
        language=language
    )

    return language


# ============================================================
# KEYBOARDS
# ============================================================

def language_keyboard():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🇷🇺 Русский",
        callback_data="language_ru",
    )

    builder.button(
        text="🇺🇸 English (US)",
        callback_data="language_en",
    )

    builder.adjust(2)

    return builder.as_markup()


def main_menu(language):
    builder = InlineKeyboardBuilder()

    builder.button(
        text=TEXTS[language]["income"],
        callback_data="income",
    )

    builder.button(
        text=TEXTS[language]["expense"],
        callback_data="expense",
    )

    builder.button(
        text=TEXTS[language]["statistics"],
        callback_data="statistics",
    )

    builder.button(
        text=TEXTS[language]["rates"],
        callback_data="rates",
    )

    builder.button(
        text=TEXTS[language]["settings"],
        callback_data="settings",
    )

    builder.button(
        text=TEXTS[language]["info"],
        callback_data="info",
    )

    builder.button(
        text=TEXTS[language]["legal"],
        callback_data="legal",
    )

    builder.adjust(2, 2, 2, 1)

    return builder.as_markup()


def cancel_keyboard(language):
    builder = InlineKeyboardBuilder()

    builder.button(
        text=TEXTS[language]["cancel"],
        callback_data="cancel",
    )

    return builder.as_markup()


def currency_keyboard(language):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="₽",
        callback_data="currency_RUB",
    )

    builder.button(
        text="$",
        callback_data="currency_USD",
    )

    builder.button(
        text="€",
        callback_data="currency_EUR",
    )

    builder.button(
        text=TEXTS[language]["cancel"],
        callback_data="cancel",
    )

    builder.adjust(3, 1)

    return builder.as_markup()


def statistics_period_keyboard(language):
    builder = InlineKeyboardBuilder()

    if language == "ru":
        buttons = [
            ("📅 Сегодня", "stats_period_today"),
            ("📅 Вчера", "stats_period_yesterday"),
            ("📆 Эта неделя", "stats_period_week"),
            ("🗓 Этот месяц", "stats_period_month"),
            ("📅 Этот год", "stats_period_year"),
            ("🗃 Архив / Всё время", "stats_period_all"),
        ]
    else:
        buttons = [
            ("📅 Today", "stats_period_today"),
            ("📅 Yesterday", "stats_period_yesterday"),
            ("📆 This Week", "stats_period_week"),
            ("🗓 This Month", "stats_period_month"),
            ("📅 This Year", "stats_period_year"),
            ("🗃 Archive / All Time", "stats_period_all"),
        ]

    for text, callback_data in buttons:
        builder.button(
            text=text,
            callback_data=callback_data,
        )

    builder.button(
        text=TEXTS[language]["delete_statistics"],
        callback_data="delete_statistics",
    )

    builder.button(
        text=TEXTS[language]["back"],
        callback_data="back_main",
    )

    builder.adjust(2)

    return builder.as_markup()


def statistics_keyboard(language):
    builder = InlineKeyboardBuilder()

    builder.button(
        text=TEXTS[language]["back"],
        callback_data="statistics",
    )

    builder.button(
        text=TEXTS[language]["delete_statistics"],
        callback_data="delete_statistics",
    )

    builder.button(
        text=TEXTS[language]["back"],
        callback_data="back_main",
    )

    builder.adjust(1)

    return builder.as_markup()


def settings_keyboard(language):
    builder = InlineKeyboardBuilder()

    builder.button(
        text=TEXTS[language]["change_language"],
        callback_data="change_language",
    )

    builder.button(
        text=TEXTS[language]["delete_data"],
        callback_data="delete_all_data",
    )

    builder.button(
        text=TEXTS[language]["back"],
        callback_data="back_main",
    )

    builder.adjust(1)

    return builder.as_markup()


def info_keyboard(language):
    builder = InlineKeyboardBuilder()

    if language == "ru":
        builder.button(
            text="📢 Telegram-канал",
            url=TELEGRAM_CHANNEL_URL,
        )

        builder.button(
            text="🌐 Сайт",
            url=WEBSITE_URL,
        )

        builder.button(
            text="🆘 Поддержка",
            url=SUPPORT_URL,
        )
    else:
        builder.button(
            text="📢 Telegram Channel",
            url=TELEGRAM_CHANNEL_URL,
        )

        builder.button(
            text="🌐 Website",
            url=WEBSITE_URL,
        )

        builder.button(
            text="🆘 Support",
            url=SUPPORT_URL,
        )

    builder.button(
        text=TEXTS[language]["back"],
        callback_data="back_main",
    )

    builder.adjust(1)

    return builder.as_markup()


def legal_keyboard(language):
    builder = InlineKeyboardBuilder()

    if language == "ru":
        builder.button(
            text="📄 Пользовательское соглашение",
            url=USER_AGREEMENT_URL,
        )

        builder.button(
            text="📄 Публичная оферта",
            url=PUBLIC_OFFER_URL,
        )
    else:
        builder.button(
            text="📄 User Agreement",
            url=USER_AGREEMENT_URL,
        )

        builder.button(
            text="📄 Public Offer",
            url=PUBLIC_OFFER_URL,
        )

    builder.button(
        text=TEXTS[language]["back"],
        callback_data="back_main",
    )

    builder.adjust(1)

    return builder.as_markup()


# ============================================================
# PERIODS
# ============================================================

def get_period_dates(period):
    now = datetime.now()

    if period == "today":
        start = datetime(
            now.year,
            now.month,
            now.day,
        )

        end = start + timedelta(days=1)

    elif period == "yesterday":
        end = datetime(
            now.year,
            now.month,
            now.day,
        )

        start = end - timedelta(days=1)

    elif period == "week":
        start = datetime(
            now.year,
            now.month,
            now.day,
        )

        start -= timedelta(
            days=start.weekday()
        )

        end = start + timedelta(days=7)

    elif period == "month":
        start = datetime(
            now.year,
            now.month,
            1,
        )

        if now.month == 12:
            end = datetime(
                now.year + 1,
                1,
                1,
            )
        else:
            end = datetime(
                now.year,
                now.month + 1,
                1,
            )

    elif period == "year":
        start = datetime(
            now.year,
            1,
            1,
        )

        end = datetime(
            now.year + 1,
            1,
            1,
        )

    else:
        return None, None

    return (
        start.isoformat(),
        end.isoformat(),
    )


def get_statistics_transactions(
    telegram_id,
    period,
):
    if period == "all":
        return get_transactions(
            telegram_id
        )

    start_date, end_date = get_period_dates(
        period
    )

    return get_transactions_between(
        telegram_id,
        start_date,
        end_date,
    )


# ============================================================
# EXCHANGE RATES
# CBR XML
# ============================================================

async def get_exchange_rates():
    url = "https://www.cbr.ru/scripts/XML_daily.asp"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:

                if response.status != 200:
                    return None

                xml_data = await response.text()

        root = ElementTree.fromstring(
            xml_data
        )

        usd = None
        eur = None

        for item in root.findall("Valute"):

            char_code = item.findtext(
                "CharCode"
            )

            value_text = item.findtext(
                "Value"
            )

            nominal_text = item.findtext(
                "Nominal"
            )

            if not value_text:
                continue

            value = float(
                value_text.replace(",", ".")
            )

            nominal = float(
                nominal_text
                if nominal_text
                else "1"
            )

            rate = value / nominal

            if char_code == "USD":
                usd = rate

            elif char_code == "EUR":
                eur = rate

        if not usd or not eur:
            return None

        return {
            "USD": usd,
            "EUR": eur,
        }

    except Exception:
        return None


# ============================================================
# CURRENCY CONVERSION
# ============================================================

def amount_to_rub(
    amount,
    currency,
    rates,
):
    if currency == "RUB":
        return amount

    if currency == "USD":
        return amount * rates["USD"]

    if currency == "EUR":
        return amount * rates["EUR"]

    return amount


def rub_to_all(
    rub_amount,
    rates,
):
    return {
        "RUB": rub_amount,
        "USD": rub_amount / rates["USD"],
        "EUR": rub_amount / rates["EUR"],
    }


def format_money(values):
    return (
        f"₽ {values['RUB']:,.2f}\n"
        f"$ {values['USD']:,.2f}\n"
        f"€ {values['EUR']:,.2f}"
    )


# ============================================================
# STATISTICS
# ============================================================

def calculate_statistics(
    transactions,
    rates,
    language,
    period,
):
    income_rub = 0.0
    expense_rub = 0.0

    for transaction in transactions:

        amount = transaction[1]
        currency = transaction[2]
        transaction_type = transaction[3]

        rub_amount = amount_to_rub(
            amount,
            currency,
            rates,
        )

        if transaction_type == "income":
            income_rub += rub_amount

        elif transaction_type == "expense":
            expense_rub += rub_amount

    balance_rub = income_rub - expense_rub

    income_values = rub_to_all(
        income_rub,
        rates,
    )

    expense_values = rub_to_all(
        expense_rub,
        rates,
    )

    balance_values = rub_to_all(
        balance_rub,
        rates,
    )

    period_names = {
        "ru": {
            "today": "Сегодня",
            "yesterday": "Вчера",
            "week": "Эта неделя",
            "month": "Этот месяц",
            "year": "Этот год",
            "all": "Архив / Всё время",
        },
        "en": {
            "today": "Today",
            "yesterday": "Yesterday",
            "week": "This Week",
            "month": "This Month",
            "year": "This Year",
            "all": "Archive / All Time",
        },
    }

    period_name = period_names[
        language
    ].get(
        period,
        period,
    )

    if language == "ru":

        text = (
            f"📊 Статистика — {period_name}\n\n"
            f"💰 Доходы:\n"
            f"   ₽ {income_values['RUB']:,.2f}\n"
            f"   $ {income_values['USD']:,.2f}\n"
            f"   € {income_values['EUR']:,.2f}\n\n"
            f"💸 Расходы:\n"
            f"   ₽ {expense_values['RUB']:,.2f}\n"
            f"   $ {expense_values['USD']:,.2f}\n"
            f"   € {expense_values['EUR']:,.2f}\n\n"
            f"💵 Баланс:\n"
            f"   ₽ {balance_values['RUB']:,.2f}\n"
            f"   $ {balance_values['USD']:,.2f}\n"
            f"   € {balance_values['EUR']:,.2f}\n\n"
            f"🧾 Операций: {len(transactions)}"
        )

    else:

        text = (
            f"📊 Statistics — {period_name}\n\n"
            f"💰 Income:\n"
            f"   ₽ {income_values['RUB']:,.2f}\n"
            f"   $ {income_values['USD']:,.2f}\n"
            f"   € {income_values['EUR']:,.2f}\n\n"
            f"💸 Expenses:\n"
            f"   ₽ {expense_values['RUB']:,.2f}\n"
            f"   $ {expense_values['USD']:,.2f}\n"
            f"   € {expense_values['EUR']:,.2f}\n\n"
            f"💵 Balance:\n"
            f"   ₽ {balance_values['RUB']:,.2f}\n"
            f"   $ {balance_values['USD']:,.2f}\n"
            f"   € {balance_values['EUR']:,.2f}\n\n"
            f"🧾 Transactions: {len(transactions)}"
        )

    return text


# ============================================================
# CATEGORY STATISTICS
# ============================================================

def get_expense_categories_statistics(
    transactions,
    rates,
):
    result = {}

    for transaction in transactions:

        amount = transaction[1]
        currency = transaction[2]
        transaction_type = transaction[3]
        category = transaction[4]

        if transaction_type != "expense":
            continue

        if category not in result:
            result[category] = {
                "RUB": 0.0,
                "USD": 0.0,
                "EUR": 0.0,
            }

        rub_amount = amount_to_rub(
            amount,
            currency,
            rates,
        )

        result[category]["RUB"] += rub_amount

        result[category]["USD"] += (
            rub_amount / rates["USD"]
        )

        result[category]["EUR"] += (
            rub_amount / rates["EUR"]
        )

    return result


def format_category_statistics(
    transactions,
    rates,
    language,
):
    categories = get_expense_categories_statistics(
        transactions,
        rates,
    )

    if not categories:

        if language == "ru":
            return "📊 Расходов за выбранный период нет."

        return "📊 There are no expenses for the selected period."

    lines = []

    if language == "ru":
        lines.append(
            "🧾 Расходы по категориям:\n"
        )
    else:
        lines.append(
            "🧾 Expenses by category:\n"
        )

    category_order = [
        "food",
        "transport",
        "home",
        "clothing",
        "technology",
        "entertainment",
        "health",
        "education",
        "services",
        "other_expense",
    ]

    for category in category_order:

        if category not in categories:
            continue

        values = categories[category]

        name = EXPENSE_CATEGORIES.get(
            category,
            EXPENSE_CATEGORIES["other_expense"],
        )[language]

        lines.append(
            f"{name}\n"
            f"   ₽ {values['RUB']:,.2f}\n"
            f"   $ {values['USD']:,.2f}\n"
            f"   € {values['EUR']:,.2f}\n"
        )

    return "\n".join(lines)


# ============================================================
# START
# ============================================================

@dp.message(Command("start"))
async def start_handler(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    await message.answer(
        TEXTS["ru"]["start"],
        reply_markup=language_keyboard(),
    )


# ============================================================
# LANGUAGE SELECTION
# ============================================================

@dp.callback_query(
    F.data == "language_ru"
)
async def select_russian(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    await state.clear()

    await state.update_data(
        language="ru"
    )

    add_user(
        callback.from_user.id,
        "ru",
    )

    await callback.message.edit_text(
        "🇷🇺 Язык выбран: Русский.\n\n"
        + TEXTS["ru"]["menu"],
        reply_markup=main_menu("ru"),
    )


@dp.callback_query(
    F.data == "language_en"
)
async def select_english(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    await state.clear()

    await state.update_data(
        language="en"
    )

    add_user(
        callback.from_user.id,
        "en",
    )

    await callback.message.edit_text(
        "🇺🇸 Language selected: English (US).\n\n"
        + TEXTS["en"]["menu"],
        reply_markup=main_menu("en"),
    )


# ============================================================
# CHANGE LANGUAGE
# ============================================================

@dp.callback_query(
    F.data == "change_language"
)
async def change_language_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    await callback.message.edit_text(
        TEXTS["ru"]["start"],
        reply_markup=language_keyboard(),
    )


# ============================================================
# MAIN MENU
# ============================================================

@dp.callback_query(
    F.data == "back_main"
)
async def back_main(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    await state.set_state(None)

    await callback.message.edit_text(
        TEXTS[language]["menu"],
        reply_markup=main_menu(language),
    )


# ============================================================
# CANCEL
# ============================================================

@dp.callback_query(
    F.data == "cancel"
)
async def cancel_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    await state.set_state(None)

    await callback.message.edit_text(
        TEXTS[language]["menu"],
        reply_markup=main_menu(language),
    )


# ============================================================
# INCOME
# ============================================================

@dp.callback_query(
    F.data == "income"
)
async def income_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    await state.set_state(
        FinanceStates.waiting_income
    )

    await callback.message.edit_text(
        TEXTS[language]["income_prompt"],
        reply_markup=cancel_keyboard(language),
    )


# ============================================================
# EXPENSE
# ============================================================

@dp.callback_query(
    F.data == "expense"
)
async def expense_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    await state.set_state(
        FinanceStates.waiting_expense
    )

    await callback.message.edit_text(
        TEXTS[language]["expense_prompt"],
        reply_markup=cancel_keyboard(language),
    )


# ============================================================
# PROCESS INCOME
# ============================================================

@dp.message(
    FinanceStates.waiting_income
)
async def process_income(
    message: Message,
    state: FSMContext,
):
    language = await current_language(
        message.from_user.id,
        state,
    )

    text = message.text or ""

    if normalize_text(text) in {
        "отмена",
        "cancel",
    }:
        await state.set_state(None)

        await message.answer(
            TEXTS[language]["menu"],
            reply_markup=main_menu(language),
        )

        return

    amount = extract_amount(text)

    if amount is None:
        await message.answer(
            TEXTS[language]["invalid_amount"],
            reply_markup=cancel_keyboard(language),
        )

        return

    if not has_financial_context(
        text,
        "income",
    ):
        await message.answer(
            TEXTS[language]["invalid"],
            reply_markup=cancel_keyboard(language),
        )

        return

    currency = detect_currency(text)

    category = smart_category(
        text,
        "income",
    )

    comment = clean_comment(text)

    await state.update_data(
        pending_amount=amount,
        pending_currency=currency,
        pending_type="income",
        pending_category=category,
        pending_comment=comment,
    )

    if currency is None:

        await state.set_state(
            FinanceStates.waiting_currency
        )

        await message.answer(
            TEXTS[language]["currency_prompt"],
            reply_markup=currency_keyboard(language),
        )

        return

    await save_transaction(
        message,
        state,
        language,
        amount,
        currency,
        "income",
        category,
        comment,
    )


# ============================================================
# PROCESS EXPENSE
# ============================================================

@dp.message(
    FinanceStates.waiting_expense
)
async def process_expense(
    message: Message,
    state: FSMContext,
):
    language = await current_language(
        message.from_user.id,
        state,
    )

    text = message.text or ""

    if normalize_text(text) in {
        "отмена",
        "cancel",
    }:
        await state.set_state(None)

        await message.answer(
            TEXTS[language]["menu"],
            reply_markup=main_menu(language),
        )

        return

    amount = extract_amount(text)

    if amount is None:
        await message.answer(
            TEXTS[language]["invalid_amount"],
            reply_markup=cancel_keyboard(language),
        )

        return

    if not has_financial_context(
        text,
        "expense",
    ):
        await message.answer(
            TEXTS[language]["invalid"],
            reply_markup=cancel_keyboard(language),
        )

        return

    currency = detect_currency(text)

    category = smart_category(
        text,
        "expense",
    )

    comment = clean_comment(text)

    await state.update_data(
        pending_amount=amount,
        pending_currency=currency,
        pending_type="expense",
        pending_category=category,
        pending_comment=comment,
    )

    if currency is None:

        await state.set_state(
            FinanceStates.waiting_currency
        )

        await message.answer(
            TEXTS[language]["currency_prompt"],
            reply_markup=currency_keyboard(language),
        )

        return

    await save_transaction(
        message,
        state,
        language,
        amount,
        currency,
        "expense",
        category,
        comment,
    )


# ============================================================
# CURRENCY SELECTION
# ============================================================

@dp.callback_query(
    F.data.startswith("currency_")
)
async def currency_selection(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    currency = callback.data.replace(
        "currency_",
        "",
    )

    data = await state.get_data()

    amount = data.get(
        "pending_amount"
    )

    transaction_type = data.get(
        "pending_type"
    )

    category = data.get(
        "pending_category"
    )

    comment = data.get(
        "pending_comment",
        "",
    )

    if amount is None or transaction_type is None:
        await state.set_state(None)

        await callback.message.edit_text(
            TEXTS[language]["menu"],
            reply_markup=main_menu(language),
        )

        return

    await save_transaction(
        callback.message,
        state,
        language,
        amount,
        currency,
        transaction_type,
        category,
        comment,
    )


# ============================================================
# SAVE TRANSACTION
# ============================================================

async def save_transaction(
    message,
    state,
    language,
    amount,
    currency,
    transaction_type,
    category,
    comment,
):
    add_transaction(
        message.chat.id,
        amount,
        currency,
        transaction_type,
        category,
        comment,
    )

    await state.clear()

    await state.update_data(
        language=language
    )

    if transaction_type == "income":

        category_name = INCOME_CATEGORIES.get(
            category,
            INCOME_CATEGORIES["other_income"],
        )[language]

        details = (
            f"{TEXTS[language]['amount']}: "
            f"{amount:,.2f}\n"
            f"{TEXTS[language]['currency']}: "
            f"{currency}\n"
            f"{TEXTS[language]['category']}: "
            f"{category_name}"
        )

        text = TEXTS[language][
            "saved_income"
        ].format(
            details=details
        )

    else:

        category_name = EXPENSE_CATEGORIES.get(
            category,
            EXPENSE_CATEGORIES["other_expense"],
        )[language]

        details = (
            f"{TEXTS[language]['amount']}: "
            f"{amount:,.2f}\n"
            f"{TEXTS[language]['currency']}: "
            f"{currency}\n"
            f"{TEXTS[language]['category']}: "
            f"{category_name}"
        )

        text = TEXTS[language][
            "saved_expense"
        ].format(
            details=details
        )

    await message.answer(
        text,
        reply_markup=main_menu(language),
    )


# ============================================================
# STATISTICS
# ============================================================

@dp.callback_query(
    F.data == "statistics"
)
async def statistics_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    if language == "ru":
        text = (
            "📊 Статистика\n\n"
            "Выберите период, за который хотите посмотреть "
            "доходы, расходы, баланс и расходы по категориям:"
        )
    else:
        text = (
            "📊 Statistics\n\n"
            "Choose a period to view your income, expenses, "
            "balance, and expenses by category:"
        )

    await callback.message.edit_text(
        text,
        reply_markup=statistics_period_keyboard(language),
    )


# ============================================================
# STATISTICS PERIOD
# ============================================================

@dp.callback_query(
    F.data.startswith("stats_period_")
)
async def statistics_period_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    period = callback.data.replace(
        "stats_period_",
        "",
    )

    transactions = get_statistics_transactions(
        callback.from_user.id,
        period,
    )

    rates = await get_exchange_rates()

    if rates is None:
        await callback.message.answer(
            TEXTS[language]["no_rates"]
        )
        return

    statistics_text = calculate_statistics(
        transactions,
        rates,
        language,
        period,
    )

    categories_text = format_category_statistics(
        transactions,
        rates,
        language,
    )

    full_text = (
        statistics_text
        + "\n\n"
        + categories_text
    )

    # Monthly spending warning.
    if period == "month":

        income_rub = 0.0
        expense_rub = 0.0

        for transaction in transactions:

            amount = transaction[1]
            currency = transaction[2]
            transaction_type = transaction[3]

            rub_amount = amount_to_rub(
                amount,
                currency,
                rates,
            )

            if transaction_type == "income":
                income_rub += rub_amount

            elif transaction_type == "expense":
                expense_rub += rub_amount

        if (
            income_rub > 0
            and expense_rub >= income_rub * 0.7
        ):
            full_text += (
                "\n\n"
                + TEXTS[language]["warning"]
            )

    await callback.message.edit_text(
        full_text,
        reply_markup=statistics_keyboard(language),
    )


# ============================================================
# EXCHANGE RATES
# ============================================================

@dp.callback_query(
    F.data == "rates"
)
async def rates_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    rates = await get_exchange_rates()

    if rates is None:
        await callback.message.edit_text(
            TEXTS[language]["no_rates"],
            reply_markup=main_menu(language),
        )

        return

    usd = rates["USD"]
    eur = rates["EUR"]

    rub_usd = 1 / usd
    rub_eur = 1 / eur
    usd_eur = usd / eur
    eur_usd = eur / usd

    text = TEXTS[language][
        "rates_text"
    ].format(
        usd=usd,
        eur=eur,
        rub_usd=rub_usd,
        rub_eur=rub_eur,
        usd_eur=usd_eur,
        eur_usd=eur_usd,
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text=TEXTS[language]["back"],
        callback_data="back_main",
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
    )


# ============================================================
# SETTINGS
# ============================================================

@dp.callback_query(
    F.data == "settings"
)
async def settings_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    await callback.message.edit_text(
        TEXTS[language]["settings_title"],
        reply_markup=settings_keyboard(language),
    )


# ============================================================
# INFO
# ============================================================

@dp.callback_query(
    F.data == "info"
)
async def info_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    await callback.message.edit_text(
        TEXTS[language]["info_text"],
        reply_markup=info_keyboard(language),
    )


# ============================================================
# LEGAL
# ============================================================

@dp.callback_query(
    F.data == "legal"
)
async def legal_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    await callback.message.edit_text(
        TEXTS[language]["legal_text"],
        reply_markup=legal_keyboard(language),
    )


# ============================================================
# DELETE ALL DATA
# ============================================================

@dp.callback_query(
    F.data == "delete_all_data"
)
async def delete_all_data_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text=TEXTS[language]["confirm_yes"],
        callback_data="confirm_delete_all",
    )

    builder.button(
        text=TEXTS[language]["confirm_no"],
        callback_data="settings",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        TEXTS[language]["confirm_delete"],
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(
    F.data == "confirm_delete_all"
)
async def confirm_delete_all(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    count = delete_all_transactions(
        callback.from_user.id
    )

    await callback.message.edit_text(
        TEXTS[language]["deleted"].format(
            count=count
        ),
        reply_markup=main_menu(language),
    )


# ============================================================
# DELETE STATISTICS
# ============================================================

def delete_period_keyboard(language):
    builder = InlineKeyboardBuilder()

    buttons_ru = [
        ("📅 Сегодня", "delete_period_today"),
        ("📅 Вчера", "delete_period_yesterday"),
        ("📆 Эта неделя", "delete_period_week"),
        ("🗓 Этот месяц", "delete_period_month"),
        ("📅 Этот год", "delete_period_year"),
        ("🗃 Архив / Всё время", "delete_period_all"),
    ]

    buttons_en = [
        ("📅 Today", "delete_period_today"),
        ("📅 Yesterday", "delete_period_yesterday"),
        ("📆 This Week", "delete_period_week"),
        ("🗓 This Month", "delete_period_month"),
        ("📅 This Year", "delete_period_year"),
        ("🗃 Archive / All Time", "delete_period_all"),
    ]

    buttons = (
        buttons_ru
        if language == "ru"
        else buttons_en
    )

    for text, data in buttons:
        builder.button(
            text=text,
            callback_data=data,
        )

    builder.button(
        text=TEXTS[language]["back"],
        callback_data="statistics",
    )

    builder.adjust(2)

    return builder.as_markup()


@dp.callback_query(
    F.data == "delete_statistics"
)
async def delete_statistics_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    await callback.message.edit_text(
        TEXTS[language]["delete_period"],
        reply_markup=delete_period_keyboard(language),
    )


@dp.callback_query(
    F.data.startswith("delete_period_")
)
async def delete_period_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    period = callback.data.replace(
        "delete_period_",
        "",
    )

    await state.update_data(
        delete_period=period
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text=TEXTS[language]["delete_income"],
        callback_data="delete_type_income",
    )

    builder.button(
        text=TEXTS[language]["delete_expenses"],
        callback_data="delete_type_expense",
    )

    builder.button(
        text=TEXTS[language]["delete_both"],
        callback_data="delete_type_both",
    )

    builder.button(
        text=TEXTS[language]["back"],
        callback_data="delete_statistics",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        TEXTS[language]["delete_type"],
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(
    F.data.startswith("delete_type_")
)
async def delete_type_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    delete_type = callback.data.replace(
        "delete_type_",
        "",
    )

    await state.update_data(
        delete_type=delete_type
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text=TEXTS[language]["confirm_yes"],
        callback_data="confirm_delete_yes",
    )

    builder.button(
        text=TEXTS[language]["confirm_no"],
        callback_data="statistics",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        TEXTS[language]["confirm_delete"],
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(
    F.data == "confirm_delete_yes"
)
async def confirm_delete_yes(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    language = await current_language(
        callback.from_user.id,
        state,
    )

    data = await state.get_data()

    period = data.get(
        "delete_period",
        "all",
    )

    delete_type = data.get(
        "delete_type",
        "both",
    )

    if period == "all":
        start_date = None
        end_date = None
    else:
        start_date, end_date = get_period_dates(
            period
        )

    if delete_type == "both":

        if period == "all":
            count = delete_all_transactions(
                callback.from_user.id
            )
        else:
            count = delete_transactions_between(
                callback.from_user.id,
                start_date,
                end_date,
            )

    else:

        transaction_type = (
            "income"
            if delete_type == "income"
            else "expense"
        )

        if period == "all":
            count = delete_transactions_by_type(
                callback.from_user.id,
                transaction_type,
            )
        else:
            count = delete_transactions_by_type_between(
                callback.from_user.id,
                transaction_type,
                start_date,
                end_date,
            )

    await state.clear()

    await state.update_data(
        language=language
    )

    if count == 0:

        await callback.message.edit_text(
            TEXTS[language]["nothing_deleted"],
            reply_markup=main_menu(language),
        )

    else:

        await callback.message.edit_text(
            TEXTS[language]["deleted"].format(
                count=count
            ),
            reply_markup=main_menu(language),
        )


# ============================================================
# TEXT FALLBACK
# ============================================================

@dp.message()
async def text_fallback(
    message: Message,
    state: FSMContext,
):
    language = await current_language(
        message.from_user.id,
        state,
    )

    text = message.text or ""

    if not text.strip():
        return

    if normalize_text(text) in {
        "отмена",
        "cancel",
    }:
        await state.set_state(None)

        await message.answer(
            TEXTS[language]["menu"],
            reply_markup=main_menu(language),
        )

        return

    await message.answer(
        TEXTS[language]["invalid"],
        reply_markup=main_menu(language),
    )


# ============================================================
# START BOT
# ============================================================

async def main():
    init_database()

    print("FinanceBot started.")

    await dp.start_polling(
        bot
    )


if __name__ == "__main__":
    asyncio.run(main())