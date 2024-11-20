import requests
import json
import uuid
import datetime
import asyncio
from telegram import Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, PreCheckoutQueryHandler
import tracemalloc
import os
tracemalloc.start()

# Токен вашего бота, полученный через BotFather
BOT_TOKEN = 'BOT_TOKKEN'

# URL для API
VPN_API_URL = 'http://{IP_ADDRESS}/{pannel_address}'
LOGIN_URL = f'{VPN_API_URL}/login'
ADD_CLIENT_URL = f'{VPN_API_URL}/panel/api/inbounds/addClient'

PROVIDER_TOKEN = "Provider_token"
SHOP_ID = "Sjhop_ID"
TRIAL_STATUS_FILE = 'trial_status.json'


# Авторизационные данные
LOGIN_DATA = {
    'username': 'admin',
    'password': 'admin'
}

def main_menu_keyboard():
    keyboard = [[InlineKeyboardButton("⬅️ Назад в главное меню", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

def load_trial_status():
    if os.path.exists(TRIAL_STATUS_FILE):
        with open(TRIAL_STATUS_FILE, 'r') as file:
            return json.load(file)
    return {}
def save_trial_status(trial_status):
    with open(TRIAL_STATUS_FILE, 'w') as file:
        json.dump(trial_status, file)

# Загрузка статуса пробного доступа при запуске бота
trial_status = load_trial_status()
# Логин в VPN API
def login_vpn():
    session = requests.Session()
    login_response = session.post(LOGIN_URL, json=LOGIN_DATA)
    if login_response.status_code == 200:
        print("Успешный логин. Куки сохранены.")
        return session
    else:
        print(f'Ошибка логина: {login_response.status_code}')
        return None

# Добавление VPN клиента
def add_vpn_client(session, tg_id, duration_days):    
    epoch = datetime.datetime.utcfromtimestamp(0)
    x_time = int((datetime.datetime.now() - epoch).total_seconds() * 1000.0) + duration_days * 86400000
    client_id = str(uuid.uuid1())

    data = {
        "id": 1,
        "settings": "{\"clients\":[{\"id\":\"" + client_id + "\","
                    "\"alterId\":90,\"email\":\"" + str(tg_id) + "\","
                    "\"limitIp\":3,\"totalGB\":0,\"expiryTime\":" + str(x_time) + ","
                    "\"enable\":true,\"tgId\":\"" + str(tg_id) + "\",\"subId\":\"\"}]}"
    }

    headers = {"Accept": "application/json"}
    response = session.post(ADD_CLIENT_URL, headers=headers, json=data)

    if response.status_code == 200:
        return client_id, tg_id
    else:
        return f'Ошибка API: {response.status_code}'
    

subscription_durations = {
    '1_month': 30,
    '3_month': 90,
    '6_month': 180,
    '12_month': 365
}
# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Попробовать 3 дня 🎁", callback_data='try_3_days')],
        [InlineKeyboardButton("Тарифы и покупка 💼", callback_data='tariffs'),
         InlineKeyboardButton("Личный кабинет 🛡", callback_data='account')],
        [InlineKeyboardButton("Инструкции 📚", callback_data='instructions'),
         InlineKeyboardButton("О сервере 🌐", callback_data='about_server')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text('Выберите опцию:', reply_markup=reply_markup)
    else:
        # Используем effective_chat, если update.message отсутствует
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Выберите опцию:', reply_markup=reply_markup)

# Обработка нажатия кнопки "Тарифы и покупка"
async def handle_tariffs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Подтверждение нажатия кнопки

    # Кнопки для выбора плана
    tariffs_keyboard = [
        [InlineKeyboardButton("1 месяц", callback_data='1_month'),
         InlineKeyboardButton("3 месяца", callback_data='3_month')],
        [InlineKeyboardButton("6 месяцев", callback_data='6_month'),
         InlineKeyboardButton("12 месяцев", callback_data='12_month')],
         [InlineKeyboardButton("Вернуться в главное меню", callback_data='main_menu')]
    ]
    
    reply_markup = InlineKeyboardMarkup(tariffs_keyboard)
    await query.edit_message_text(text="Выберите план подписки:", reply_markup=reply_markup)

# Обработка выбора плана
async def choose_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Подтверждение нажатия кнопки
    text = query.data

    if text in ['1_month', '3_month', '6_month', '12_month']:
        await query.edit_message_text(text=f'Вы выбрали план на {text}. Переходим к оплате...')

        amounts = {"1_month": 100, "3_month": 250, "6_month": 450, "12_month": 800}
        amount = amounts.get(text)
        try:
            # Отправка инвойса
            await context.bot.send_invoice(
                chat_id=query.message.chat.id,
                title=f'Подписка на {text}',
                description=f'Оплата за {text} подписку.',
                payload=text,  # Данные, которые будут отправлены обратно
                provider_token='Providen_ROKEN',  
                currency='RUB',
                prices=[{
                    'label': 'Подписка',
                    'amount': amount * 100  # Сумма в копейках
                }],
                start_parameter='test',
                is_flexible=False,
            )
        except Exception as e:
            await query.edit_message_text(
                        f'Ошибка при отправке инвойса: {str(e)}',
                        reply_markup=main_menu_keyboard()
                    )
    else:
        await query.edit_message_text(
                        "Веринтесь в главное меню и выберите, что вас интересует",
                        reply_markup=main_menu_keyboard()
                    )
# Обработка PreCheckoutQuery
async def pre_checkout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

# Обработка успешного платежа
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment_info = update.message.successful_payment  # Получаем информацию о платеже
    provider_payment_charge_id = payment_info.provider_payment_charge_id
    plan_type = payment_info.invoice_payload
    duration_days = subscription_durations.get(plan_type, 0)
    tg_id = update.message.from_user.id
    session = login_vpn()
    if session:
        api_url_list = 'http://{IP_ADDRESS}/{pannel_address}/panel/api/inbounds/list'
        header = {"Accept": "application/json"}
        user_id = tg_id
        api_list_response  = session.get(api_url_list, headers=header)
        api_list = api_list_response.json()
        user_found = False
        expiry_time_value = None 
        user_uuid = None
        for obj in api_list["obj"]:
            for client in obj["clientStats"]:
                if client["email"] == str(user_id):
                    # Если пользователь найден, добавляем значение к expiryTime
                    expiry_time_value = client["expiryTime"] + duration_days * 86400000  
                    
                    user_found = True
                    break  # Прекращаем поиск после нахожде
            if user_found:
                settings_data = json.loads(obj["settings"])
                for client in settings_data["clients"]:
                    if client["email"] == str(user_id):
                        user_uuid = client["id"]  # Извлекаем UUID
                        data_update = {
                                "id": 1,
                                "settings":
                                "{\"clients\":"
                                "[{\"id\":\"" + str(user_uuid) + "\","
                                "\"alterId\":90,\"email\":\"" + str(tg_id) + "\","
                                "\"limitIp\":3,\"totalGB\":0,"
                                "\"expiryTime\":" + str(expiry_time_value) + ",\"enable\":true,\"tgId\":\"" + str(tg_id) + "\",\"subId\":\"\"}]}"
                                }
                        update_url = f'http://{IP_ADDRESS}/{pannel_address}/panel/api/inbounds/updateClient/{user_uuid}'
                        response_user = session.post(update_url, headers=header, json=data_update)
                        await context.bot.send_message(chat_id=tg_id, text=f'Оплата успешна! Оплаченое время добавлено')
                        break
                break
        

        else:
            client_id, tg_id = add_vpn_client(session, tg_id, duration_days)        
            url_vpn = f'vless://{client_id}@IP_ADDRESS}:{PORT}?type=tcp&security=reality&pbk=F7b-XmxQBisfsNOhgTZ7JuiXi6KY8mPZDSi-aqVkpXE&fp=random&sni=google.com&sid=de057a28&spx=%2F#VLESS-{tg_id}'        
            message_text = (
        "Оплата успешна! Вот ваши настройки VPN:\n\n"
        "<b>Для копирования нажмите на текст ниже и следйте инструкциям дял своего устройства:</b>\n\n"
        f"<code>{url_vpn}</code>"
    )

        await context.bot.send_message(
            chat_id=tg_id,
            text=message_text,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
    else:
        await query.edit_message_text(
                        "Ошибка авторизации на VPN сервере.",
                        reply_markup=main_menu_keyboard()
                    )
    
    await start(update, context)
async def show_account_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tg_id = query.from_user.id
    session = login_vpn()

    if session:
        api_url_list = f'{VPN_API_URL}/panel/api/inbounds/list'
        header = {"Accept": "application/json"}
        api_list_response = session.get(api_url_list, headers=header)
        api_list = api_list_response.json()
        
        user_found = False
        user_uuid = None
        expiry_time = None

        # Поиск данных пользователя
        for obj in api_list["obj"]:
            for client in obj["clientStats"]:
                if client["email"] == str(tg_id):
                    expiry_time = client["expiryTime"]
                    user_found = True
                    break

            if user_found:
                settings_data = json.loads(obj["settings"])
                for client in settings_data["clients"]:
                    if client["email"] == str(tg_id):
                        user_uuid = client["id"]
                        break
                break

        # Проверка и вывод данных пользователя
        if user_found and user_uuid:
            # Подсчет оставшегося времени в днях
            remaining_time_ms = expiry_time - int((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)
            remaining_days = max(0, remaining_time_ms // (1000 * 60 * 60 * 24))
            message_text = (
                "<b>Ваш ID для поддержки:</b>\n"
                f"<code>{user_uuid}</code>\n"
                "<b>Оставшееся время подписки: </b>"
                f"<code>{remaining_days}</code> дней"
            )

            # Создание клавиатуры с кнопкой "Вернуться в главное меню"
            reply_markup = InlineKeyboardMarkup([[
                InlineKeyboardButton("Вернуться в главное меню", callback_data='main_menu')
            ]])

            await context.bot.send_message(
                chat_id=tg_id,
                text=message_text,
                parse_mode="HTML",
                reply_markup=reply_markup  # Добавляем клавиатуру здесь
            )
            
            
        else:
            await query.edit_message_text(
            "Пользователь не найден. Обратитесь в поддержку.",
            reply_markup=main_menu_keyboard()
        )
            
    else:
        await query.edit_message_text(
            "Ошибка авторизации на сервере VPN.",
            reply_markup=main_menu_keyboard()
        )
def check_existing_user(session, tg_id):
    api_url_list = f'{VPN_API_URL}/panel/api/inbounds/list'
    header = {"Accept": "application/json"}
    api_list_response = session.get(api_url_list, headers=header)
    
    if api_list_response.status_code != 200:
        return None, None

    api_list = api_list_response.json()
    
    # Перебираем все объекты для поиска нужного пользователя
    for obj in api_list["obj"]:
        found_email = False
        expiry_time = None

        # Сначала проверяем clientStats для нахождения пользователя по email
        for client in obj["clientStats"]:
            if client["email"] == str(tg_id):
                expiry_time = client["expiryTime"]
                found_email = True
                break  # Прекращаем поиск в clientStats после нахождения email
        
        # Если нашли нужный email, ищем UUID в settings
        if found_email:
            settings_data = json.loads(obj["settings"])
            for client in settings_data["clients"]:
                if client["email"] == str(tg_id):
                    user_uuid = client["id"]  # Получаем правильный UUID
                    return user_uuid, expiry_time  # Возвращаем найденные UUID и expiryTime

    # Если пользователь не найден
    return None, None

async def handle_try_3_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tg_id = str(query.from_user.id)  # Конвертируем в строку для использования в JSON

    # Проверка, использовал ли пользователь пробный период
    if trial_status.get(tg_id, False):
        await query.edit_message_text(
            "Вы уже использовали пробный период. Выберите тариф для подписки.",
            reply_markup=main_menu_keyboard()
        )
    else:
        # Логинимся и проверяем, существует ли уже пользователь
        session = login_vpn()
        if session:
            user_uuid, expiry_time = check_existing_user(session, tg_id)
            if user_uuid:
                additional_time = 3 * 86400000  # 3 дня в миллисекундах
                new_expiry_time = expiry_time + additional_time
                data_update = {
                                "id": 1,
                                "settings":
                                "{\"clients\":"
                                "[{\"id\":\"" + str(user_uuid) + "\","
                                "\"alterId\":90,\"email\":\"" + str(tg_id) + "\","
                                "\"limitIp\":3,\"totalGB\":0,"
                                "\"expiryTime\":" + str(new_expiry_time) + ",\"enable\":true,\"tgId\":\"" + str(tg_id) + "\",\"subId\":\"\"}]}"
                                }

                update_url = f'{VPN_API_URL}/panel/api/inbounds/updateClient/{user_uuid}'
                response_user = session.post(update_url, headers={"Accept": "application/json"}, json=data_update)
                if response_user.status_code == 200:
                    trial_status[tg_id] = True  # Обновляем статус триального периода
                    save_trial_status(trial_status)
                    await query.edit_message_text(
                        "Пробный период активирован. Вам добавлено 3 дня подписки.",
                        reply_markup=main_menu_keyboard()
                    )
                else:
                    await query.edit_message_text(
                        "Ошибка при обновлении данных пользователя.",
                        reply_markup=main_menu_keyboard()
                    )
            else:
                # Если пользователь не существует, создаем нового клиента на 3 дня
                client_id, tg_id = add_vpn_client(session, tg_id, 3)
                if client_id:
                    trial_status[tg_id] = True
                    save_trial_status(trial_status) 
                    url_vpn = f'vless://{client_id}@IP_ADDRESS}:{PORT}?type=tcp&security=reality&pbk=F7b-XmxQBisfsNOhgTZ7JuiXi6KY8mPZDSi-aqVkpXE&fp=random&sni=google.com&sid=de057a28&spx=%2F#VLESS-{tg_id}'        
                    message_text = (
                        "Пробный период активирован! Вот ваши настройки VPN:\n\n"
                        "<b>Для копирования нажмите на текст ниже и следуйте инструкциям для вашего устройства:</b>\n\n"
                        f"<code>{url_vpn}</code>"
                    )

                    await context.bot.send_message(
                        chat_id=query.from_user.id,
                        text=message_text,
                        parse_mode="HTML",
                        reply_markup=main_menu_keyboard()
                    )
                else:
                    await query.edit_message_text(
                        "Ошибка создания нового пользователя.",
                        reply_markup=main_menu_keyboard()
                    )
        else:
            await query.edit_message_text(
                        "Ошибка авторизации на VPN сервере.",
                        reply_markup=main_menu_keyboard()
                    )

application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(handle_try_3_days, pattern='try_3_days'))
application.add_handler(CallbackQueryHandler(handle_tariffs, pattern='tariffs'))
application.add_handler(CallbackQueryHandler(show_account_info, pattern='account'))
application.add_handler(CallbackQueryHandler(start, pattern='main_menu'))
application.add_handler(CallbackQueryHandler(choose_plan))
application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
application.add_handler(PreCheckoutQueryHandler(pre_checkout_callback))
application.run_polling()