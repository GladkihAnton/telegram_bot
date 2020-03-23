# Настройки
import re
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext, \
    ConversationHandler, RegexHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
import sqlite3
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

CREATE, UPDATE = range(2)


# CREATING DATABASE

def button_create_db(update: Update, context: CallbackContext):
    access = True
    user = 'db' + str(update.message.from_user.id)
    with sqlite3.connect(':memory') as db:
        cur = db.cursor()
        q = '''SELECT name FROM sqlite_master WHERE type="table"'''
        for row in cur.execute(q):
            if user in row:
                access = False
        if access:
            text = 'Отлично, ты хочешь создать новую базу данных!' \
                   ' Теперь тебе нужно ввести до 10 своих активностей за которыми ' \
                   'я буду следить, а ты должен(а) будешь заполнять их по вечерам.\n' \
                   'П.С. Слова разделенные пробелом будут считаться за различные занятия, поэтому постарайся ввести' \
                   ' занятие в одно слово, например, вместо "Английский язык" напиши "Английский."'
            update.message.reply_text(text=text)
            return CREATE
        else:
            update.message.reply_text(text='Подожди, ты же уже создал(а) базу данных,'
                                           ' удали ее если хочешь начать сначала.')
            return ConversationHandler.END


def create_db(update: Update, context: CallbackContext):
    user = 'db' + str(update.message.from_user.id)
    answer = update.message.text
    pattern = r'\b[\w\.]+\b'
    words = re.findall(pattern, answer)
    values = []  # [activity, 0, activity1, 0 ....]
    tempForCreat = []  # variable for creat dinamic table and insert values
    tempForInsert = []
    create = " CREATE TABLE if not exists {table} ("
    insert = "INSERT INTO {table} VALUES ("
    for i in range(len(words)):
        values.append(words[i])
        values.append(0)
        tempForCreat.append('action' + str(i) + ' TEXT, timeAction' + str(i) + ' INTEGER')
        tempForInsert.append('?')
    temp1ForCreat = ', '.join(tempForCreat)  # the processing of variable
    temp1ForInsert = ', '.join(2 * tempForInsert)
    create += temp1ForCreat + ')'  # finish process
    insert += temp1ForInsert + ')'
    with sqlite3.connect(":memory") as con:
        cur = con.cursor()
        cur.execute(create.format(table=user))
        cur.execute(insert.format(table=user), tuple(values))
        con.commit()
    text = 'Ура, ты создал(а) свою базу данных! Ты положил(а) начало нашего длительного сотрудничества!' \
           ' Будем развиваться вместе! Успехов тебе в твоих занятиях!'
    update.message.reply_text(text=text)
    return ConversationHandler.END


# DELETING DATABASE

def button_delete_db(update: Update, context: CallbackContext):
    user = 'db' + str(update.message.from_user.id)
    access = False
    with sqlite3.connect(':memory') as db:
        cur = db.cursor()
        q = '''SELECT name FROM sqlite_master WHERE type="table"'''
        for row in cur.execute(q):
            if user in row:
                access = True
        if access:
            cur.execute('''DROP TABLE {table}'''.format(table=user))
            update.message.reply_text(text='Ты удалил(а) свою базу данных.')
        else:
            update.message.reply_text(text='Создай базу данных, чтобы ее удалить.')
        db.commit()


# CHECK DATABASE

def button_check_db(update: Update, context: CallbackContext):
    user = 'db' + str(update.message.from_user.id)
    access = False
    i = 0
    with sqlite3.connect(':memory') as db:
        cur = db.cursor()
        text = ''
        q = '''SELECT name FROM sqlite_master WHERE type="table"'''
        for row in cur.execute(q):
            if user in row:
                access = True
        if access:
            for row in cur.execute("SELECT * FROM " + user):
                for item in row:
                    i += 1
                    if i%2 == 1:
                        text += 'Твоя активность: ' + item + ';'
                    else:
                        text += ' Кол-во часов: ' + str(item) + '\n'
            update.message.reply_text(text=text)
        else:
            update.message.reply_text(text='К сожалению база данных еще не создана.')


# Update database


def button_update_db(update: Update, context: CallbackContext):
    pass


def update_db(update: Update, context: CallbackContext):
    pass


# START MENU

def start_command(update: Update, context: CallbackContext):
    keyboard = [
        [
            KeyboardButton(text='Создать базу данных'),
            KeyboardButton(text='Проверить базы данных'),
            KeyboardButton(text='Удалить базу данных'),
            KeyboardButton(text='Добавить результаты')
        ]
    ]
    text = 'Привет я бот-отчетник. Я буду запоминать все твои результаты за день и иногда присылать их тебе.' \
           'Так же буду напоминать тебе, чтобы ты не забывал докладывать о своих результатах за день.' \
           'Чтобы начать создай базу данных.  Для подробной информации напиши /help'
    update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))


# HELP

def help_command(update: Update, context: CallbackContext):
    bot = context.bot
    bot.send_message(chat_id=update.message.chat_id, text="В разработке")


# TEXT HANDLER

def message_handler(update: Update, context: CallbackContext):
    text = update.message.text
    print(text)


# END OF CONVERSATION

def cancel(update: Update, context: CallbackContext):
    return ConversationHandler.END


# MAIN MENU
def main():
    print('start')
    updater = Updater(token='1103722369:AAHEpIChRe2WepU3CNrkWrZGNajSJgF3QJ0',
                      base_url="https://telegg.ru/orig/bot", use_context=True)
    dispatcher = updater.dispatcher

    # Handlers of command
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('help', help_command))

    # Handlers of conversation
    dispatcher.add_handler(ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('Создать базу данных'), button_create_db)],
        states={
            CREATE: [MessageHandler(Filters.text, create_db)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    ))

    # Handlers of regex
    dispatcher.add_handler(MessageHandler(Filters.regex('Проверить базы данных'), button_check_db))
    dispatcher.add_handler(MessageHandler(Filters.regex('Удалить базу данных'), button_delete_db))

    # Handlers of textMessage
    dispatcher.add_handler(MessageHandler(filters=Filters.text, callback=message_handler))


    # Начинаем поиск обновлений
    updater.start_polling(clean=True)
    # Останавливаем бота, если были нажаты Ctrl + C
    print('processing')
    updater.idle()
    print('finish')


if __name__ == '__main__':
    main()
