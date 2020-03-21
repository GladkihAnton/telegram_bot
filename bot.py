# Настройки
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
import sqlite3
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


# Обработка команд
def createDB(user):
    with sqlite3.connect(":memory") as con:
        cur = con.cursor()
        q = """
        CREATE TABLE if not exists {table} (
          action1 TEXT,
          timeaction1 INTEGER,
          action2 TEXT,
          timeaction2 INTEGER,
          action3 TEXT,
          timeaction3 INTEGER,
          action4 TEXT,
          timeaction4 INTEGER,
          action5 TEXT,
          timeaction5 INTEGER,
          action6 TEXT,
          timeaction6 INTEGER,
          action7 TEXT,
          timeaction7 INTEGER,
          action8 TEXT,
          timeaction8 INTEGER,
          action9 TEXT,
          timeaction9 INTEGER,
          action10 TEXT,
          timeaction10 INTEGER)
        """
        cur.execute(q.format(table='db' + str(user)))
        con.commit()

def deleteDB(user):
    with sqlite3.connect(':memory') as db:
        cur = db.cursor()
        q = '''DROP TABLE IF EXISTS {table}'''
        cur.execute(q.format(table='db'+str(user)))
        db.commit()
def dostuff(text, user):
    with sqlite3.connect(":memory") as con:
        cur = con.cursor()
        cur.execute("INSERT INTO db438745245 VALUES (?, ?, ?, ?)", (text, text, text, text))
        con.commit()
        for row in cur.execute("SELECT * FROM stocks "):
            print(row)





def buttonCreateDB(update: Update, context: CallbackContext, user):
    createDB(user)

    print('yes')

def buttonDeleteDB(update: Update, context: CallbackContext, user):
    deleteDB(user)
    print('yes')


def buttonCheckDB(update: Update, context: CallbackContext, user):
    with sqlite3.connect(':memory') as db:
        cur = db.cursor()
        q = '''SELECT name FROM sqlite_master WHERE type="table"'''

        for item in cur.execute(q.format(table='db'+str(user))):
            print(item)


def startCommand(update: Update, context: CallbackContext):
    bot = context.bot
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='Проверить бд'),
                KeyboardButton(text='Создать бд'),
                KeyboardButton(text='Удалить бд')
            ],
        ],
        resize_keyboard=True,
    )
    text = 'Привет я бот-отчетник. Я буду запоминать все твои результаты за день и иногда присылать их тебе.' \
           'Так же буду напоминать тебе, чтобы ты не забывал докладывать о своих результатах за день.' \
           'Чтобы начать создай базу данных.  Для подробной информации напиши /help'
    bot.send_message(chat_id=update.message.chat_id, text=text, reply_markup=reply_markup)

def helpCommand(update: Update, context: CallbackContext):
    bot = context.bot
    bot.send_message(chat_id=update.message.chat_id, text="В разработке")

def message_handler(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "Создать бд":
        return buttonCreateDB(update, context, update.message.from_user.id)
    if text == "Удалить бд":
        return buttonDeleteDB(update, context, update.message.from_user.id)
    if text == 'Проверить бд':
        return buttonCheckDB(update, context, update.message.from_user.id)



# Хендлеры
def main():
    print('start')
    updater = Updater(token='1103722369:AAHEpIChRe2WepU3CNrkWrZGNajSJgF3QJ0',
                      base_url="https://telegg.ru/orig/bot", use_context=True)
    # Токен API к Telegram
    # with sqlite3.connect(":memory") as con:
    #     cur = con.cursor()
    #     cur.execute('DROP Table db438745245')
    #     con.commit()
    dispatcher = updater.dispatcher
    start_command_handler = CommandHandler('start', startCommand)
    help_command_handler = CommandHandler('help', helpCommand)
    # Добавляем хендлеры в диспетчер
    dispatcher.add_handler(start_command_handler)
    dispatcher.add_handler(help_command_handler)
    dispatcher.add_handler(MessageHandler(filters=Filters.text, callback=message_handler))
    # dispatcher.add_handler(text_message_handler)

    # Начинаем поиск обновлений
    updater.start_polling(clean=True)
    # Останавливаем бота, если были нажаты Ctrl + C
    print('processing')
    updater.idle()
    print('finish')


if __name__ == '__main__':
    main()
