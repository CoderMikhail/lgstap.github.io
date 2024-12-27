from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3


# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Проверяем, существует ли столбец first_launch
    c.execute("PRAGMA table_info(users)")
    columns = c.fetchall()
    column_names = [column[1] for column in columns]

    if 'first_launch' not in column_names:
        # Добавляем столбец first_launch
        c.execute("ALTER TABLE users ADD COLUMN first_launch BOOLEAN DEFAULT 1")

    conn.commit()
    conn.close()


# Добавление лида и начисление баланса
def add_lead(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET leads = leads + 1, balance = balance + 0.4 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Добавляем пользователя в базу данных, если его еще нет
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id, username, balance, leads, first_launch) VALUES (?, ?, 0, 0, 1)",
              (user_id, username))
    conn.commit()

    # Проверяем, первый ли это запуск
    c.execute("SELECT first_launch FROM users WHERE id = ?", (user_id,))
    first_launch = c.fetchone()[0]
    conn.close()

    if first_launch:
        # Показываем меню со спонсорами
        keyboard = [[InlineKeyboardButton("Панель управления",
                                          web_app={'url': 'https://codermikhail.github.io/legendwebapp.github.io/'})]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Добро пожаловать!', reply_markup=reply_markup)

        # Устанавливаем first_launch в False
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("UPDATE users SET first_launch = 0 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
    else:
        # Показываем главное меню
        keyboard = [
            [InlineKeyboardButton("Профиль", callback_data='profile')],
            [InlineKeyboardButton("О нас", callback_data='about')],
            [InlineKeyboardButton("Чат", callback_data='chat')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Главное меню:', reply_markup=reply_markup)


# Обработка нажатия кнопок в главном меню
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'profile':
        user_id = query.from_user.id
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT balance, leads FROM users WHERE id = ?", (user_id,))
        result = c.fetchone()
        conn.close()

        if result:
            balance, leads = result
            profile_text = f"""💻 Профиль
┠ Ваша ссылка: https://t.me/lgndtmwabot?start=ref{user_id}
┠ Всего {leads} лидов
┠ На сумму {balance}$
🏦 Для вывода нужно 5.0$, у вас {balance}$
┗💼 Не хватает {max(0, 5.0 - balance)}$ для вывода."""
            await query.edit_message_text(profile_text)
    elif query.data == 'about':
        await query.edit_message_text("Информация о нас.")
    elif query.data == 'chat':
        await query.edit_message_text("Перейдите в чат: [ссылка на чат].")


def main() -> None:
    # Инициализация базы данных
    init_db()

    # Создаем приложение с помощью ApplicationBuilder
    application = ApplicationBuilder().token("7614493417:AAEMcK6cM7SXR3RD9GyEt-YPAzN5_piBTJ8").build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Запускаем бота
    application.run_polling()


if __name__ == '__main__':
    main()