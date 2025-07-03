import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, filters, ContextTypes

# Загрузка переменных окружения из .env (если файл присутствует)
load_dotenv()

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Константы состояний для ConversationHandler
NAME, PHONE, TIME, ADDRESS, FORMAT_STATE, COMMENT, CONFIRM, CHOOSE_FIELD, NEW_VALUE = range(9)

# Вспомогательная функция для формирования сводки заявки из user_data
def compose_summary(user_data: dict, prefix: str = "Проверьте, пожалуйста, ваши данные:\n") -> str:
    name = user_data.get('name')
    phone = user_data.get('phone')
    time = user_data.get('time')
    address = user_data.get('address')
    format_label = user_data.get('format_label')
    format_price = user_data.get('format_price')
    comment = user_data.get('comment') or ''
    # Если комментария нет, указываем "нет"
    comment_display = comment if comment and comment.strip() else "нет"
    summary_text = (
        f"{prefix}"
        f"Имя: {name}\n"
        f"Телефон: {phone}\n"
        f"Удобное время: {time}\n"
        f"Адрес: {address}\n"
        f"Формат: {format_label} — {format_price}\n"
        f"Комментарий: {comment_display}"
    )
    return summary_text

# Команда /start — приветствие и главное меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    intro_text = (
        "Добро пожаловать в XENON PRIVE.\n"
        "Это цифровой сервис для индивидуальных ксеноновых ингаляций."
    )
    # Кнопки основного меню (InlineKeyboard)
    keyboard = [
        [InlineKeyboardButton(" О XENON PRIVE", callback_data="about")],
        [InlineKeyboardButton(" Что даёт ингаляция", callback_data="benefits")],
        [InlineKeyboardButton(" Выбрать формат", callback_data="choose_format")],
        [InlineKeyboardButton(" Записаться", callback_data="signup")],
        [InlineKeyboardButton(" Канал", url="https://t.me/xenox40")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(intro_text, reply_markup=reply_markup)

# Обработчик пункта меню "О XENON PRIVE"
async def about_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    about_text = (
        "XENON PRIVE — премиальный сервис индивидуальных ксеноновых ингаляций (40% ксенона / 60% кислорода). "
        "Каждая сессия направлена на глубокую релаксацию, снятие стресса и улучшение эмоционального состояния. "
        "Ингаляции проводятся квалифицированным специалистом в комфортной обстановке. "
        "Совмещая современные технологии и персональный подход, XENON PRIVE помогает вам обрести внутреннее спокойствие и равновесие."
    )
    # Отправляем отдельным сообщением, чтобы меню осталось доступно
    await query.message.reply_text(about_text)

# Обработчик пункта меню "Что даёт ингаляция"
async def benefits_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    benefits_text = (
        "Что дают ксеноновые ингаляции:\n"
        "• Глубокое расслабление и снижение уровня стресса.\n"
        "• Снятие тревожности, улучшение настроения и эмоционального состояния.\n"
        "• Обезболивающее действие, снижение мышечного напряжения.\n"
        "• Улучшение качества сна и общее восстановление организма.\n"
        "• Комфортная и безопасная неинвазивная процедура."
    )
    await query.message.reply_text(benefits_text)

# Обработчик пункта меню "Выбрать формат"
async def choose_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    # Кнопки с вариантами форматов (количество сессий и цена)
    formats = [
        ("1 сессия — 40 000 ₽", "format_1"),
        ("3 сессии — 100 000 ₽", "format_3"),
        ("5 сессий — 150 000 ₽", "format_5"),
        ("8 сессий — 180 000 ₽", "format_8"),
        ("10 сессий — 200 000 ₽", "format_10")
    ]
    keyboard = [[InlineKeyboardButton(text, callback_data=data)] for text, data in formats]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Выберите формат программы:", reply_markup=reply_markup)

# Обработчик выбора формата из главного меню (сохраняет выбор)
async def format_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data  # например, "format_3"
    sessions_number = data.split('_')[1]  # извлекаем число сессий
    mapping = {
        "1": ("1 сессия", "40 000 ₽"),
        "3": ("3 сессии", "100 000 ₽"),
        "5": ("5 сессий", "150 000 ₽"),
        "8": ("8 сессий", "180 000 ₽"),
        "10": ("10 сессий", "200 000 ₽")
    }
    label, price = mapping.get(sessions_number, (f"{sessions_number} сессий", ""))
    # Сохраняем выбор в user_data
    context.user_data['format_label'] = label
    context.user_data['format_price'] = price
    # Обновляем сообщение с вариантами, отмечая выбор, и уведомляем пользователя
    await query.edit_message_text(f"Выбран формат: {label} — {price}")
    await query.message.reply_text("Формат сохранён. Теперь вы можете записаться на сессию через меню 📝 Записаться.")

# Стартовая точка диалога записи (нажатие "Записаться")
async def start_signup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    # Спрашиваем имя
    await query.message.reply_text("Как Вас зовут?")
    return NAME

# Шаг 1: получаем имя пользователя
async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    context.user_data['name'] = name
    # Спрашиваем телефон. Предлагаем кнопку для отправки контакта
    contact_button = KeyboardButton("📱 Отправить номер телефона", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Укажите, пожалуйста, Ваш номер телефона.", reply_markup=reply_markup)
    return PHONE

# Шаг 2: получаем телефон (текстом или контактом)
async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.contact:
        # Пользователь отправил контакт через кнопку
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()
    context.user_data['phone'] = phone
    # Спрашиваем удобное время
    await update.message.reply_text(
        "Когда Вам удобно пройти сессию? Укажите дату и время.",
        reply_markup=ReplyKeyboardRemove()
    )
    return TIME

# Шаг 3: получаем удобное время
async def time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    preferred_time = update.message.text.strip()
    context.user_data['time'] = preferred_time
    # Спрашиваем адрес или район
    await update.message.reply_text("Укажите адрес или район, где будет проходить сессия.")
    return ADDRESS

# Шаг 4: получаем адрес
async def address_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = update.message.text.strip()
    context.user_data['address'] = address
    # Если формат уже был выбран ранее через меню, пропускаем вопрос о формате
    if 'format_label' in context.user_data and 'format_price' in context.user_data:
        # Переходим сразу к вопросу о комментарии
        await update.message.reply_text(
            "Если у Вас есть дополнительные комментарии или вопросы, вы можете написать их ниже.\n"
            "Если комментариев нет, отправьте /skip."
        )
        return COMMENT
    else:
        # Спрашиваем формат сессий, показываем клавиатуру с вариантами
        formats = [
            ("1 сессия — 40 000 ₽", "format_1"),
            ("3 сессии — 100 000 ₽", "format_3"),
            ("5 сессий — 150 000 ₽", "format_5"),
            ("8 сессий — 180 000 ₽", "format_8"),
            ("10 сессий — 200 000 ₽", "format_10")
        ]
        keyboard = [[InlineKeyboardButton(text, callback_data=data)] for text, data in formats]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите формат программы:", reply_markup=reply_markup)
        return FORMAT_STATE

# Шаг 5: обработчик выбора формата в процессе диалога
async def format_handler_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data  # например, "format_5"
    sessions_number = data.split('_')[1]
    mapping = {
        "1": ("1 сессия", "40 000 ₽"),
        "3": ("3 сессии", "100 000 ₽"),
        "5": ("5 сессий", "150 000 ₽"),
        "8": ("8 сессий", "180 000 ₽"),
        "10": ("10 сессий", "200 000 ₽")
    }
    label, price = mapping.get(sessions_number, (f"{sessions_number} сессий", ""))
    context.user_data['format_label'] = label
    context.user_data['format_price'] = price
    # Обновляем сообщение с вариантами формата, указывая выбранный вариант
    await query.edit_message_text(f"Выбран формат: {label} — {price}")
    if context.user_data.get('editing_field') == 'format':
        # Если выбор формата произошёл в режиме редактирования данных
        context.user_data['editing_field'] = None  # сбрасываем флаг редактирования
        # Формируем обновлённую сводку и возвращаемся к этапу подтверждения
        summary_text = compose_summary(context.user_data, prefix="Обновленные данные:\n")
        keyboard = [
            [InlineKeyboardButton("✅ Отправить заявку", callback_data="confirm_send")],
            [InlineKeyboardButton("✏️ Изменить данные", callback_data="edit_data")]
        ]
        await query.message.reply_text(summary_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return CONFIRM
    else:
        # Переходим к вопросу о комментарии
        await query.message.reply_text(
            "Если у Вас есть дополнительные комментарии или вопросы, вы можете написать их ниже.\n"
            "Если комментариев нет, отправьте команду /skip."
        )
        return COMMENT

# Шаг 6: получаем комментарий (либо команда /skip для пропуска)
async def comment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    # Если пользователь написал "нет" или аналогичное - считаем, что комментария нет
    if text.lower() in ["нет", "не", "no", "none"]:
        context.user_data['comment'] = ""
    else:
        context.user_data['comment'] = text
    # Формируем сводку введённых данных и предлагаем подтвердить или отредактировать
    summary_text = compose_summary(context.user_data)
    keyboard = [
        [InlineKeyboardButton("✅ Отправить заявку", callback_data="confirm_send")],
        [InlineKeyboardButton("✏️ Изменить данные", callback_data="edit_data")]
    ]
    await update.message.reply_text(summary_text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM

# Обработчик команды /skip (пропустить комментарий)
async def skip_comment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Пользователь выбрал пропустить комментарий
    context.user_data['comment'] = ""
    summary_text = compose_summary(context.user_data)
    keyboard = [
        [InlineKeyboardButton("✅ Отправить заявку", callback_data="confirm_send")],
        [InlineKeyboardButton("✏️ Изменить данные", callback_data="edit_data")]
    ]
    await update.message.reply_text(summary_text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM

# Шаг 7: подтверждение заявки (пользователь нажал "Отправить заявку")
async def confirm_send_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    # Собираем данные заявки
    name = context.user_data.get('name')
    phone = context.user_data.get('phone')
    time = context.user_data.get('time')
    address = context.user_data.get('address')
    format_label = context.user_data.get('format_label')
    format_price = context.user_data.get('format_price')
    comment = context.user_data.get('comment') or "(нет)"
    # Информация о пользователе (Telegram)
    user = query.from_user
    username = user.username
    user_id = user.id
    user_info = f"@{username} (ID: {user_id})" if username else f"ID: {user_id}"
    # Формируем текст для администратора (в указанный чат)
    admin_message = (
        "🔔 Новая заявка XENON PRIVE 🔔\n"
        f"Имя: {name}\n"
        f"Телефон: {phone}\n"
        f"Удобное время: {time}\n"
        f"Адрес: {address}\n"
        f"Формат: {format_label} — {format_price}\n"
        f"Комментарий: {comment}\n"
        f"Пользователь Telegram: {user_info}"
    )
    # Отправляем заявку в админский чат
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    if admin_chat_id:
        try:
            admin_chat_id_int = int(admin_chat_id)
        except ValueError:
            admin_chat_id_int = admin_chat_id  # на случай, если chat_id не числовой
        try:
            await context.bot.send_message(chat_id=admin_chat_id_int, text=admin_message)
        except Exception as e:
            logging.error(f"Failed to send admin message: {e}")
    # Сообщаем пользователю об успешной отправке
    await query.message.reply_text("Спасибо! Ваша заявка принята. Мы свяжемся с вами в ближайшее время.", reply_markup=ReplyKeyboardRemove())
    # Очищаем сохранённые данные и завершаем диалог
    context.user_data.clear()
    return ConversationHandler.END

# Обработчик нажатия "Изменить данные" на этапе подтверждения
async def edit_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    # Убираем кнопки подтверждения/редактирования в сообщении со сводкой
    await query.edit_message_reply_markup(reply_markup=None)
    # Отправляем новое сообщение с выбором поля для редактирования
    keyboard = [
        [InlineKeyboardButton("Имя", callback_data="edit_name"), InlineKeyboardButton("Телефон", callback_data="edit_phone")],
        [InlineKeyboardButton("Время", callback_data="edit_time"), InlineKeyboardButton("Адрес", callback_data="edit_address")],
        [InlineKeyboardButton("Формат", callback_data="edit_format"), InlineKeyboardButton("Комментарий", callback_data="edit_comment")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_confirm")]
    ]
    await query.message.reply_text("Что вы хотите изменить?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_FIELD

# Обработчик выбора поля для редактирования
async def choose_field_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data  # например, "edit_phone" или "back_to_confirm"
    if data == "back_to_confirm":
        # Вернуться к подтверждению без изменений
        summary_text = compose_summary(context.user_data)
        keyboard = [
            [InlineKeyboardButton("✅ Отправить заявку", callback_data="confirm_send")],
            [InlineKeyboardButton("✏️ Изменить данные", callback_data="edit_data")]
        ]
        await query.message.reply_text(summary_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return CONFIRM
    # Иначе, выбрано конкретное поле для редактирования
    field = data.split('_')[1]  # получаем часть после "edit_"
    context.user_data['editing_field'] = field
    if field == "format":
        # Редактирование формата: снова показываем варианты форматов
        formats = [
            ("1 сессия — 40", "format_1"),
            ("3 сессии — 100", "format_3"),
            ("5 сессий — 150", "format_5"),
            ("8 сессий — 180", "format_8"),
            ("10 сессий — 200", "format_10")
        ]
        keyboard = [[InlineKeyboardButton(text, callback_data=data)] for text, data in formats]
        await query.message.reply_text("Выберите новый формат:", reply_markup=InlineKeyboardMarkup(keyboard))
        return FORMAT_STATE
    else:
        # Редактирование текстового поля: запрашиваем новое значение
        if field == "name":
            prompt = "Введите новое имя:"
        elif field == "phone":
            prompt = "Введите новый номер телефона:"
        elif field == "time":
            prompt = "Укажите новое удобное время:"
        elif field == "address":
            prompt = "Укажите новый адрес или район:"
        elif field == "comment":
            prompt = "Введите новый комментарий (или оставьте пустым):"
        else:
            prompt = "Введите новое значение:"
        await query.message.reply_text(prompt)
        return NEW_VALUE

# Обработчик ввода нового значения поля при редактировании
async def new_value_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_text = update.message.text.strip()
    field = context.user_data.get('editing_field')
    if field:
        # Обновляем соответствующее поле в сохранённых данных
        if field == "name":
            context.user_data['name'] = new_text
        elif field == "phone":
            context.user_data['phone'] = new_text
        elif field == "time":
            context.user_data['time'] = new_text
        elif field == "address":
            context.user_data['address'] = new_text
        elif field == "comment":
            context.user_data['comment'] = new_text
        context.user_data['editing_field'] = None
    # Отправляем обновлённую сводку данных для подтверждения
    summary_text = compose_summary(context.user_data, prefix="Обновленные данные:\n")
    keyboard = [
        [InlineKeyboardButton("✅ Отправить заявку", callback_data="confirm_send")],
        [InlineKeyboardButton("✏️ Изменить данные", callback_data="edit_data")]
    ]
    await update.message.reply_text(summary_text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM

# Обработчик команды /cancel для отмены диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        await update.message.reply_text(
            "Вы отменили запись. Если потребуется, вы можете начать заново командой /start.",
            reply_markup=ReplyKeyboardRemove()
        )
    context.user_data.clear()
    return ConversationHandler.END

# Обработчик /cancel вне диалога (общий)
async def cancel_command_global(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Активной записи нет.", reply_markup=ReplyKeyboardRemove())

# Главная функция запуска бота
def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        logging.error("BOT_TOKEN не задан. Поместите токен вашего бота в переменную окружения BOT_TOKEN.")
        return
    # Создаем приложение бота
    application = Application.builder().token(token).build()

    # Регистрируем обработчики команд и событий
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel_command_global))
    application.add_handler(CallbackQueryHandler(about_info, pattern="^about$"))
    application.add_handler(CallbackQueryHandler(benefits_info, pattern="^benefits$"))
    application.add_handler(CallbackQueryHandler(choose_format, pattern="^choose_format$"))
    # Глобальный обработчик выбора формата (работает вне режима диалога)
    # block=False позволяет обработчику диалога перехватывать эти же callback, когда он активен
    application.add_handler(CallbackQueryHandler(format_selection, pattern="^format_(1|3|5|8|10)$", block=False))

    # Определяем диалог (ConversationHandler) для процесса записи
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_signup, pattern="^signup$")],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            PHONE: [
                MessageHandler(filters.CONTACT, phone_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler)
            ],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_handler)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, address_handler)],
            FORMAT_STATE: [CallbackQueryHandler(format_handler_conv, pattern="^format_")],
            COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, comment_handler)
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm_send_handler, pattern="^confirm_send$"),
                CallbackQueryHandler(edit_data_handler, pattern="^edit_data$")
            ],
            CHOOSE_FIELD: [CallbackQueryHandler(choose_field_handler, pattern="^(edit_|back_to_confirm)")],
            NEW_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_value_handler)]
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("skip", skip_comment_handler)],
        allow_reentry=True
    )
    application.add_handler(conv_handler)

    # Запуск бота (долгополлинг)
    logging.info("Bot is starting polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
