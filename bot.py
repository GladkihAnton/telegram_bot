# Настройки
import re
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext, \
    ConversationHandler, RegexHandler, Job
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
from datetime import datetime, time, timedelta
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
        all_tables = '''SELECT name FROM sqlite_master WHERE type="table"'''
        for row in cur.execute(all_tables):
            if user in row:
                access = False
        if access:
            text = 'Отлично, вы хотите создать новую базу данных!' \
                   ' Теперь вам нужно ввести до 10 своих активностей за которыми ' \
                   'я буду следить, а вы должны будете заполнять их по вечерам.\n' \
                   'П.С. Слова разделенные пробелом будут считаться за различные занятия, поэтому постарайтесь ввести' \
                   ' занятие в одно слово, например, вместо "Английский язык" напиши "Английский."'
            update.message.reply_text(text=text)
            return CREATE
        else:
            update.message.reply_text(text='Подождите, вы же уже создали базу данных,'
                                           ' удалите ее если хотите начать сначала.')
            return ConversationHandler.END


def create_db(update: Update, context: CallbackContext):
    user = 'db' + str(update.message.from_user.id)
    answer = update.message.text
    pattern = r'\b[\w\.]+\b'
    words = re.findall(pattern, answer)
    create = " CREATE TABLE if not exists {table} (action TEXT, timeWeek INTEGER, timeMonth INTEGER, allTime INTEGER)"
    insert = "INSERT INTO {table} VALUES (?, ?, ?, ?)"
    with sqlite3.connect(":memory") as con:
        cur = con.cursor()
        cur.execute(create.format(table=user))
        for i in range(len(words)):
            cur.execute(insert.format(table=user), (words[i], 0, 0, 0))
        con.commit()
    text = 'Ура, вы создали свою базу данных! Вы положили начало нашего длительного сотрудничества!' \
           ' Будем развиваться вместе! Успехов вам в ваших занятиях!'
    update.message.reply_text(text=text)
    return ConversationHandler.END


# DELETING DATABASE

def button_delete_db(update: Update, context: CallbackContext):
    user = 'db' + str(update.message.from_user.id)
    access = False
    with sqlite3.connect(':memory') as db:
        cur = db.cursor()
        all_tables = '''SELECT name FROM sqlite_master WHERE type="table"'''
        for row in cur.execute(all_tables):
            if user in row:
                access = True
        if access:
            cur.execute('''DROP TABLE {table}'''.format(table=user))
            update.message.reply_text(text='Вы удалили свою базу данных.')
        else:
            update.message.reply_text(text='Создайте базу данных, чтобы ее удалить.')
        db.commit()


# CHECK DATABASE
def check_db(update: Update, context: CallbackContext, week):
    user = 'db' + str(update.message.from_user.id)
    access = False
    with sqlite3.connect(':memory') as db:
        cur = db.cursor()
        text = ''
        all_tables = '''SELECT name FROM sqlite_master WHERE type="table"'''
        for row in cur.execute(all_tables):
            if user in row:
                access = True
        if access:
            for row in cur.execute("SELECT * FROM " + user):
                text += 'Ваша активность: ' + row[0] + ';'
                if week:
                    text += ' Кол-во часов за неделю: ' + str(row[1]) + '\n'
                else:
                    text += ' Кол-во часов за месяц: ' + str(row[2]) + '\n'
            update.message.reply_text(text=text)
        else:
            update.message.reply_text(text='К сожалению база данных еще не создана.')


def button_check_week_db(update: Update, context: CallbackContext):
    check_db(update, context, True)


def button_check_month_db(update: Update, context: CallbackContext):
    check_db(update, context, False)


# Update database

def button_update_db(update: Update, context: CallbackContext):
    user = 'db' + str(update.message.from_user.id)
    access = False
    with sqlite3.connect(':memory') as db:
        cur = db.cursor()
        all_tables = '''SELECT name FROM sqlite_master WHERE type="table"'''
        for row in cur.execute(all_tables):
            if user in row:
                access = True
        if access:
            text = 'Ура! Вы зашели добавить информации о прошедшем дне, я очень этому рад!' \
                   ' Пожалуйста, расскажите об этом в таком виде: "Занятие время занятия".' \
                   ' Отправляйте по одному сообщению для каждого занятия. Когда закончите напишите "стоп"'
            update.message.reply_text(text=text)
            return UPDATE
        else:
            text = 'База данных еще не создана.'
            update.message.reply_text(text=text)
            return ConversationHandler.END


def update_db(update: Update, context: CallbackContext):
    answer = str(update.message.text)
    user = 'db' + str(update.message.from_user.id)
    pattern = r'\b[\w\.]+\b'
    select = """SELECT * FROM {table} WHERE ACTION = '{active}'"""
    refresh = "UPDATE {table} set timeWeek = {time_week}, timeMonth = {time_month}, allTime={all_time}" \
              "  WHERE ACTION = '{active}'"
    if answer.lower() == 'стоп':
        return ConversationHandler.END
    else:
        try:
            find = re.findall(pattern, answer)
            active, hour = find[0], find[1]
            with sqlite3.connect(':memory') as db:
                cur = db.cursor()
                for item in cur.execute(select.format(table=user, active=active)):
                    time_week= int(item[1]) + int(hour)
                    time_month = int(item[2]) + int(hour)
                    all_time = int(item[3]) + int(hour)
                cur.execute(refresh.format(table=user, active=active, time_week=time_week,
                                           time_month=time_month, all_time=all_time))
                db.commit()
            return UPDATE
        except IndexError:
            update.message.reply_text(text='Вы ввели не в верном формате. Правильный формат: '
                                           'Английский 10, например.')
        except ValueError:
            update.message.reply_text(text='Вы ввели не в верном формате. Правильный формат: '
                                           'Английский 10, например. П.С. ошибка в часах')
        except UnboundLocalError:
            with sqlite3.connect(':memory') as db:
                db.cursor()
                text = 'Вы ошиблись в названии занятия. Ваши занятия: '
                comma = False
                for row in cur.execute("SELECT * FROM {table}".format(table=user)):
                    if comma:
                        text += ', '
                    text += row[0]
                    comma = True
                text += '.'
            update.message.reply_text(text=text)


# START MENU

def start_command(update: Update, context: CallbackContext):
    keyboard = [
        [
            KeyboardButton(text='Добавить результаты'),
            KeyboardButton(text='Недельные результаты'),
            KeyboardButton(text='Результаты за месяц'),
        ],
    ]
    text = 'Привет я бот-отчетник. Я буду запоминать все ваши результаты за день и иногда присылать их вам.' \
           'Так же буду напоминать вам, чтобы вы не забывали докладывать о своих результатах за день.' \
           'Чтобы начать создай базу данных /create.  Для подробной информации напиши /help'
    update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    # context.job_queue.run_repeating(callback=reminder, interval=timedelta(seconds=5),
    #                                 first=datetime.now()-timedelta(hours=3),
    #                                 context=update.message.chat_id)


# HELP

def help_command(update: Update, context: CallbackContext):
    bot = context.bot
    bot.send_message(chat_id=update.message.chat_id, text="В разработке")


# TEXT HANDLER

def message_handler(update: Update, context: CallbackContext):
    text = update.message.text
    context.job_queue.stop()
    print(text)
    print()
    if (datetime.now() - timedelta(hours=3)).isoweekday() == 1:
        print('yes')


# END OF CONVERSATION
def yes_or_no(update: Update, context: CallbackContext):
    pass


def cancel(update: Update, context: CallbackContext):
    return ConversationHandler.END


def reminder(context: CallbackContext):
    context.bot.send_message(chat_id=context.job.context, text='ypa')
    print('ypa')
    print(datetime.now())


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
        entry_points=[CommandHandler('create', button_create_db),
                      MessageHandler(Filters.regex('Добавить результаты'), button_update_db)],
        states={
            CREATE: [MessageHandler(Filters.text, create_db)],
            UPDATE: [MessageHandler(Filters.text, update_db)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    ))

    # Handlers of regex
    dispatcher.add_handler(MessageHandler(Filters.regex('Недельные результаты'), button_check_week_db))
    dispatcher.add_handler(MessageHandler(Filters.regex('Результаты за месяц'), button_check_month_db))
    dispatcher.add_handler(CommandHandler('delete', button_delete_db))

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
