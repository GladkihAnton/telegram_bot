# Настройки
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
import sqlite3
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


# Обработка команд
def createdb(user):
    with sqlite3.connect(":memory") as con:
        cur = con.cursor()
        q = """
        CREATE TABLE {table} (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          date DATE,
          old_counter TEXT,
          new_counter TEXT,
          odds TEXT,
          tarrif TEXT,
          summa TEXT)
        """
        cur.execute(q.format(table='db' + str(user)))
        con.commit()


def dostuff(text, user):
    with sqlite3.connect(":memory") as con:
        cur = con.cursor()
        cur.execute("INSERT INTO db438745245 VALUES (?, ?, ?, ?)", (text, text, text, text))
        con.commit()
        for row in cur.execute("SELECT * FROM stocks "):
            print(row)


def startCommand(update: Update, context: CallbackContext):
    job = context.bot

    job.send_message(chat_id=update.message.chat_id, text='Привет Дианка! Давай общаться!')
    # update.message.reply_text(text='ypa')
    print('lol)')

def button(update: Update, context: CallbackContext):
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='Попробуй еще!'),
            ],
        ],
        resize_keyboard=True,
    )
    update.message.reply_text(
        text='Дианочка, ты очень хорошая девушка!',
        reply_markup=reply_markup
    )
def button1(update: Update, context: CallbackContext):
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='Продолжаем!'),
            ],
        ],
        resize_keyboard=True,
    )
    update.message.reply_text(
        text='Я очень рад, что вы с Антошкой вместе!',
        reply_markup=reply_markup
    )

def button2(update: Update, context: CallbackContext):
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='Конец :('),
            ],
        ],
        resize_keyboard=True,
    )
    update.message.reply_text(
        text='И Антошка тоже рад! Только тсс... не говори ему, что я тебе рассказал',
        reply_markup=reply_markup
    )
def button3(update: Update, context: CallbackContext):
    update.message.reply_text(
        text='Спасибо тебе за развлечение! Хорошего и продуктивного дня тебе!',
        reply_markup=ReplyKeyboardRemove()
    )
def message_handler(update: Update, context: CallbackContext):
    text = update.message.text
    if text=='Нажми на меня!':
        return button(update=update, context=context)
    if text=='Попробуй еще!':
        return button1(update=update, context=context)
    if text=='Продолжаем!':
        return button2(update=update, context=context)
    if text=='Конец :(':
        return button3(update=update, context=context)

    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='Нажми на меня!'),
            ],
        ],
        resize_keyboard=True,
    )

    update.message.reply_text(
        text='Я пока что глупый бот и не умею общаться с людьми, но у меня есть крутые кнопочки, попробуй!!!',
        reply_markup=reply_markup,
    )


# def textMessage(bot, update):
#     response = ''
#     test = update.message.text
#     user = update.message.from_user.id
#     bot.send_message(chat_id=update.message.chat_id, text=response)
#     # createdb(user)
#     # dostuff(test, user)
#     print(test)


# Хендлеры
def main():
    print('start')
    updater = Updater(token='1103722369:AAHEpIChRe2WepU3CNrkWrZGNajSJgF3QJ0',
                      base_url="https://telegg.ru/orig/bot", use_context=True)  # Токен API к Telegram
    dispatcher = updater.dispatcher
    start_command_handler = CommandHandler('start', startCommand)
    # text_message_handler = MessageHandler(Filters.text, textMessage)
    # Добавляем хендлеры в диспетчер
    dispatcher.add_handler(start_command_handler)
    dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))
    # dispatcher.add_handler(text_message_handler)

    # Начинаем поиск обновлений
    updater.start_polling(clean=True)
    # Останавливаем бота, если были нажаты Ctrl + C
    print('processing')
    updater.idle()
    print('finish')


if __name__ == '__main__':
    main()
