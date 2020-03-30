#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, time, timedelta
import sqlite3
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

CREATE, UPDATE, ADD, DELETE, DELETEDB = range(5)


def has_create_db(user):
    """checks that table with name "user" has created. The table name has type of name 'db' + user_id """
    with sqlite3.connect('users_database') as db:
        cur = db.cursor()
        all_tables = '''SELECT name FROM sqlite_master WHERE type="table"'''
        for row in cur.execute(all_tables):
            if user in row:
                return True
        return False


# Commands Handler

# /start
def start_command(update: Update, context: CallbackContext):
    """Runs if user wrote /start. Add three buttons."""
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


# /help
def help_command(update: Update, context: CallbackContext):
    """Runs if user wrtoe /help. The answer of function contains a useful commands"""
    bot = context.bot
    text = 'досутпные команды: \n' \
           '/deleteDB - удалить базу данных \n' \
           '/create - создать новую базу данных \n' \
           '/cancel - отмена предыдущего добавления \n' \
           '/add - добавить новые занятия \n' \
           '/delete - удалить занятия \n' \
           '/all - показать результаты за все время сотрудничества'

    bot.send_message(chat_id=update.message.chat_id, text=text)


# /cancel
def cancel(update: Update, context: CallbackContext):
    """Runs if user wrote /cancel. Cancels the last update of user's table."""
    if has_create_db('db' + str(update.message.from_user.id)):
        with sqlite3.connect('users_database') as db:
            cur = db.cursor()
            user = 'db' + str(update.message.from_user.id)
            select = """SELECT * FROM {table}"""
            refresh = "UPDATE {table} set time_week = {time_week}, time_month = {time_month}," \
                      " all_time={all_time}, last_update={last_update}" \
                      "  WHERE action_l = '{active}'"
            upd = {}
            for item in cur.execute(select.format(table=user)):
                upd[str(item[0])] = []
                last_update = int(item[5])
                upd[str(item[0])].append(int(item[2]) - last_update)  # [0] = time_week
                upd[str(item[0])].append(int(item[3]) - last_update)  # [1] = time_month
                upd[str(item[0])].append(int(item[4]) - last_update)  # [2] = all_time
                upd[str(item[0])].append(0)  # [3] last_update
            for active in upd.keys():
                cur.execute(refresh.format(table=user, active=str(active).lower(), time_week=upd[active][0],
                                           time_month=upd[active][1], all_time=upd[active][2], last_update=0))
            db.commit()

        update.message.reply_text(text='Вы удалили последнее обновление!')
    else:
        update.message.reply_text(text='База данных не создана.')


# /all
def check_all_db(update: Update, context: CallbackContext):
    """Runs if user wrote /all. The answer of function contains a records of user's activity at all the time."""
    user = 'db' + str(update.message.from_user.id)
    if has_create_db(user):
        text = ''
        with sqlite3.connect("users_database") as db:
            cur = db.cursor()
            for row in cur.execute("SELECT * FROM " + user):
                text += 'Занятие: ' + row[0] + ';'
                text += ' Кол-во часов за неделю: ' + str(row[5]) + '\n'
        update.message.reply_text(text=text)
    else:
        update.message.reply_text(text='К сожалению база данных еще не создана.')


# Conversations Handler

# /create
def command_create_db(update: Update, context: CallbackContext):
    """Runs if user wrote /create. If user's table hasn't created run "create_db" function."""
    user = 'db' + str(update.message.from_user.id)
    if not has_create_db(user):
        text = 'Отлично, вы хотите создать новую базу данных!' \
               ' Теперь вам нужно ввести свои занятия, которыми вы хотите заниматься.' \
               ' Введите их через пробел или через запятую.\n' \
               'П.С. Слова, разделенные пробелом, будут считаться за различные занятия, поэтому постарайтесь ввести' \
               ' занятие в одно слово, например, вместо "Английский язык" напишите "Английский."'
        update.message.reply_text(text=text)
        return CREATE
    else:
        update.message.reply_text(text='Подождите, вы же уже создали базу данных,'
                                       ' удалите ее, если хотите начать сначала.')
        return ConversationHandler.END


# after /create
def create_db(update: Update, context: CallbackContext):
    """Handles the user's message. Writes in user's table the activities which user wrote. This function also starts
        2 jobs which remind you about your activities."""
    user = 'db' + str(update.message.from_user.id)
    answer = update.message.text
    pattern = r'\b[\w\.]+\b'
    words = re.findall(pattern, answer)
    create = " CREATE TABLE if not exists {table}" \
             " (action TEXT, action_l TEXT, time_week INTEGER, time_month INTEGER, all_time INTEGER, last_update INTEGER)"
    insert = "INSERT INTO {table} VALUES (?, ?, ?, ?, ?, ?)"
    with sqlite3.connect("users_database") as con:
        cur = con.cursor()
        cur.execute(create.format(table=user))
        for i in range(len(words)):
            cur.execute(insert.format(table=user), (words[i], str(words[i]).lower(), 0, 0, 0, 0))
        con.commit()
    text = 'Ура, вы создали свою базу данных! Вы положили начало нашего длительного сотрудничества!' \
           ' Будем развиваться вместе! Успехов вам в ваших занятиях!'
    update.message.reply_text(text=text)

    # Create job which will remember user for updating
    every_day_jobs = context.job_queue.run_repeating(callback=refresher, interval=timedelta(hours=24),
                                                     first=time(hour=1),
                                                     context=update.message.chat_id)
    new_job = context.job_queue.run_repeating(callback=reminder, interval=timedelta(minutes=30),
                                              first=time(hour=18),
                                              context=update.message.chat_id)
    context.chat_data[user + 'repeat'] = new_job
    context.chat_data[user + 'refresh'] = every_day_jobs
    return ConversationHandler.END


# function of job1
def refresher(context: CallbackContext):
    with sqlite3.connect('users_database') as db:
        cur = db.cursor()
        user = 'db' + str(context.job.context)
        refresh_last_update = "UPDATE {table} set last_update = 0"
        cur.execute(refresh_last_update.format(table=user))
        if datetime.now().day == 1:
            refresh_time_month = "UPDATE {table} set time_month = 0"
            cur.execute(refresh_time_month.format(table=user))
        if datetime.now().isoweekday() == 1:
            refresh_time_week = "UPDATE {table} set time_week = 0"
            cur.execute(refresh_time_week.format(table=user))
        db.commit()

<<<<<<< HEAD
def command_delete_db(update: Update, context: CallbackContext):
    user = 'db' + str(update.message.from_user.id)
    with sqlite3.connect(":memory") as db:
        cur = db.cursor()
        cur.execute('''DROP TABLE {table}'''.format(table=user))
        db.commit()
        update.message.reply_text(text='Вы удалили свою базу данных.')
=======
# function of job2
def reminder(context: CallbackContext):
    text = 'Пришло время заполнить результаты, пожалуйста, сделайте это.'
    context.bot.send_message(chat_id=context.job.context, text=text)
>>>>>>> pythonanywhere


# /add
def command_add(update: Update, context: CallbackContext):
    """Runs if user wrote /add. If user's table has created run "add_to_db" function."""
    user = 'db' + str(update.message.from_user.id)
    if has_create_db(user):
        text = 'Вы решили дополнить свои занятия, отлично! Отправте мне список увлечений через запятую или пробел.'
        update.message.reply_text(text=text)
        return ADD
    else:
        update.message.reply_text(text='База данных не создана')


# after /add
def add_to_db(update: Update, context: CallbackContext):
    """Handles the user's message. Writes in user's table new activities which user wrote"""
    answer = update.message.text
    user = 'db' + str(update.message.from_user.id)
    pattern = r'\b[\w\.]+\b'
    words = re.findall(pattern, answer)
    with sqlite3.connect('users_database') as db:
        cur = db.cursor()
        insert = "INSERT INTO {table} VALUES (?, ?, ?, ?, ?, ?)"
        if len(words) == 1:
            text = 'Вы добавили новое занятие: '
        else:
            text = 'Вы добавили новые занятия: '
        for i in range(len(words)):
            cur.execute(insert.format(table=user), (words[i], str(words[i]).lower(), 0, 0, 0, 0))
            text += words[i] + '; '
        db.commit()
        update.message.reply_text(text=text)
    return ConversationHandler.END


# /delete
def command_delete(update: Update, context: CallbackContext):
    """Runs if user wrote /delete. If user's table has created run "delete_from_db" function."""
    user = 'db' + str(update.message.from_user.id)
    if has_create_db(user):
        update.message.reply_text(text='Перечислите занятия через пробел или запятую, которые хотите удалить.')
        return DELETE
    else:
        update.message.reply_text(text='База данных не создана.')


# after /delete
def delete_from_db(update: Update, context: CallbackContext):
    """Handles the user's message. Deletes from user's table activities which user wrote"""
    answer = update.message.text
    user = 'db' + str(update.message.from_user.id)
    pattern = r'\b[\w\.]+\b'
    words = re.findall(pattern, answer)
    with sqlite3.connect('users_database') as db:
        cur = db.cursor()
        delete = "DELETE FROM {table} WHERE action_l = '{active}'"
        for i in range(len(words)):
            cur.execute(delete.format(table=user, active=str(words[i]).lower()))
        db.commit()
    return ConversationHandler.END


# /deleteDB
def question(update: Update, context: CallbackContext):
    """Runs if user wrote /deleteDB. Starts the conversation about deleting user's table."""
    user = 'db' + str(update.message.from_user.id)
    if has_create_db(user):
        update.message.reply_text(text='Вы уверены? /yes или /no')
        return DELETEDB
    else:
        update.message.reply_text(text='Создайте базу данных, чтобы ее удалить.')
        return ConversationHandler.END


# after /deleteDB
def yes_or_no(update: Update, context: CallbackContext):
    """If user wrote /yes this function starts "command_delete_db" """
    answer = update.message.text
    if str(answer).lower() == '/yes':
        command_delete_db(update, context)
        return ConversationHandler.END
    else:
        return ConversationHandler.END


# after /yes after /deleteDB
def command_delete_db(update: Update, context: CallbackContext):
    """Delete user's table"""
    user = 'db' + str(update.message.from_user.id)
    with sqlite3.connect("users_database") as db:
            cur = db.cursor()
            cur.execute('''DROP TABLE {table}'''.format(table=user))
            db.commit()
            update.message.reply_text(text='Вы удалили свою базу данных.')


# stop conversation
def stop(update: Update, context: CallbackContext):
    return ConversationHandler.END


# Buttons

# first button
def command_update_db(update: Update, context: CallbackContext):
    """Runs if user wrote /update. If user's table has created run "update_db" function."""
    user = 'db' + str(update.message.from_user.id)
    if has_create_db(user):
        text = 'Ура! Вы зашели добавить информации о прошедшем дне, я очень этому рад!' \
               ' Пожалуйста, расскажите об этом в таком виде: "Занятие время занятия".' \
               ' Отправляйте по одному сообщению для каждого занятия. Когда закончите напишите "стоп"'
        update.message.reply_text(text=text)
        return UPDATE
    else:
        text = 'База данных еще не создана.'
        update.message.reply_text(text=text)
        return ConversationHandler.END


# after first button
def update_db(update: Update, context: CallbackContext):
    """Handles the user's message. Updates user's table new records which user wrote"""
    answer = str(update.message.text)

    user = 'db' + str(update.message.from_user.id)
    pattern = r'\b[\w\.]+\b'
<<<<<<< HEAD
    find = re.findall(pattern, answer)
    print(find)
    select = """SELECT * FROM {table} WHERE lower(ACTION) = '{active}'"""
    refresh = "UPDATE {table} set time_week = {time_week}, time_month = {time_month}," \
              " all_time={all_time}, last_update={last_update}" \
              "  WHERE lower(ACTION) = '{active}'"
    # refresh = "UPDATE {table} set time_week = 2 WHERE lower(ACTION) = '{active}'"
=======
    select = """SELECT * FROM {table} WHERE action_l = '{active}'"""
    refresh = "UPDATE {table} set time_week = {time_week}, time_month = {time_month}," \
              " all_time={all_time}, last_update={last_update}" \
              "  WHERE action_l = '{active}'"
>>>>>>> pythonanywhere
    if answer.lower() == 'стоп' or answer.lower() == '/stop':
        # context.chat_data[user + 'repeat'].schedule_removal()
        # hours = datetime.now().time().hour
        # first = datetime.now() + timedelta(days=1, hours=18) - timedelta(hours=hours)
        # new_job = context.job_queue.run_repeating(callback=reminder, interval=timedelta(seconds=25),
        #                                           first=first,
        #                                           context=update.message.chat_id)
        # context.chat_data[user + 'repeat'] = new_job
        update.message.reply_text(text='Спасибо!')
        return ConversationHandler.END
    else:
        try:
            find = re.findall(pattern, answer)
            print(find)
            active, hour = find[0], find[1]
            with sqlite3.connect('users_database') as db:
                cur = db.cursor()
                for item in cur.execute(select.format(table=user, active=str(active).lower())):
                    time_week = int(item[2]) + int(hour)
                    time_month = int(item[3]) + int(hour)
                    all_time = int(item[4]) + int(hour)
                    last_update = int(hour)
                    print(time_week, time_month, all_time, last_update)
                cur.execute(refresh.format(table=user, active=str(active).lower(), time_week=time_week,
                                           time_month=time_month, all_time=all_time, last_update=last_update))
                # cur.execute(refresh.format(table=user, active=str(active).lower()))
                # db.commit()
            update.message.reply_text(text='/stop')
            return UPDATE
        except IndexError:
            update.message.reply_text(text='Вы ввели не в верном формате. Правильный формат: '
                                           'Английский 10, например.')
            return UPDATE

        except ValueError:
            update.message.reply_text(text='Вы ввели не в верном формате. Правильный формат: '
                                           'Английский 10, например. П.С. ошибка в часах')
            return UPDATE

        except UnboundLocalError:
            with sqlite3.connect('users_database') as db:
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
            return UPDATE


<<<<<<< HEAD
# START MENU
def check(update: Update, context: CallbackContext):
    user = 'db' + str(update.message.from_user.id)
    with sqlite3.connect(":memory") as db:
        cur = db.cursor()
        for row in cur.execute("SELECT * FROM " + user):
            print(row)
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


# HELP

def help_command(update: Update, context: CallbackContext):
    bot = context.bot
    text = 'досутпные команды: \n' \
           '/deleteDB - удалить базу данных \n' \
           '/create - создать новую базу данных \n' \
           '/cancel - отмена предыдущего добавления \n' \
           '/add - добавить новые занятия \n' \
           '/delete - удалить занятия'

    bot.send_message(chat_id=update.message.chat_id, text=text)


# TEXT HANDLER

def message_handler(update: Update, context: CallbackContext):
    update.message.reply_text(text='Бот не умеет отвечать на сообщения. Для просмотра комманд введите /help')
    user = 'db' + str(update.message.from_user.id)
    if has_create_db(user):
        text = ''
        with sqlite3.connect(":memory") as db:
            cur = db.cursor()
            for row in cur.execute("SELECT * FROM " + user + " where lower(action) = '{a}'".format(a=str(update.message.text).lower())):
                print(row)
                print(type(row[1]))
                print(type(row[2]))
                print(type(row[3]))
                print(type(row[4]))
                if row[0] == str(update.message.text):
                    print('yes')
    print(update.message.text)


# END OF CONVERSATION
=======
# second button
def button_check_week_db(update: Update, context: CallbackContext):
    """Runs if user click on the button which name is "Недельные результаты".
        The function calls function "check_db" with argument True, which send the user's records at the last week."""
    check_db(update, context, True)
>>>>>>> pythonanywhere


# third button
def button_check_month_db(update: Update, context: CallbackContext):
    """Runs if user click on the button which name is "Недельные результаты".
         The function calls function "check_db" with argument True, which send the user's records at the last month."""
    check_db(update, context, False)


# function for second and third buttons
def check_db(update: Update, context: CallbackContext, week):
    user = 'db' + str(update.message.from_user.id)
    if has_create_db(user):
        text = ''
        with sqlite3.connect("users_database") as db:
            cur = db.cursor()
            for row in cur.execute("SELECT * FROM " + user):
                text += 'Занятие: ' + row[0] + ';'
                if week:
                    text += ' Кол-во часов за неделю: ' + str(row[2]) + '\n'
                else:
                    text += ' Кол-во часов за месяц: ' + str(row[3]) + '\n'
        update.message.reply_text(text=text)
<<<<<<< HEAD
    return ConversationHandler.END


def command_delete(update: Update, context: CallbackContext):
    user = 'db' + str(update.message.from_user.id)
    if has_create_db(user):
        update.message.reply_text(text='Перечислите занятия, которые хотите удалить.')
        return DELETE
    else:
        update.message.reply_text(text='База данных не создана.')


def delete_from_db(update: Update, context: CallbackContext):
    answer = update.message.text
    user = 'db' + str(update.message.from_user.id)
    pattern = r'\b[\w\.]+\b'
    words = re.findall(pattern, answer)
    with sqlite3.connect(':memory') as db:
        cur = db.cursor()
        delete = "DELETE FROM {table} WHERE lower(ACTION) = '{active}'"
        for i in range(len(words)):
            cur.execute(delete.format(table=user, active=str(words[i]).lower()))
        db.commit()
    return ConversationHandler.END


def question(update: Update, context: CallbackContext):
    user = 'db' + str(update.message.from_user.id)
    if has_create_db(user):
        update.message.reply_text(text='Вы уверены? /yes или /no')
        return DELETEDB
    else:
        update.message.reply_text(text='Создайте базу данных, чтобы ее удалить.')
        return ConversationHandler.END


def yes_or_no(update: Update, context: CallbackContext):
    answer = update.message.text
    if str(answer).lower() == '/yes':
        command_delete_db(update, context)
        return ConversationHandler.END
    else:
        return ConversationHandler.END


def stop(update: Update, context: CallbackContext):
    return ConversationHandler.END


def refresher(context: CallbackContext):
    if datetime.now().day == 1:
        with sqlite3.connect(':memory') as db:
            cur = db.cursor()
            user = 'db' + str(context.job.context)
            refresh = "UPDATE {table} set time_month = 0"
            cur.execute(refresh.format(table=user))
            db.commit()
    if datetime.now().isoweekday() == 1:
        with sqlite3.connect(':memory') as db:
            cur = db.cursor()
            user = 'db' + str(context.job.context)
            refresh = "UPDATE {table} set time_week = 0"
            cur.execute(refresh.format(table=user))
            db.commit()
=======
    else:
        update.message.reply_text(text='К сожалению база данных еще не создана.')
>>>>>>> pythonanywhere


# Text handler
def message_handler(update: Update, context: CallbackContext):
    update.message.reply_text(text='Бот не умеет отвечать на сообщения. Для просмотра комманд введите /help')


# MAIN MENU
def main():
    print('start')
    token = input()
    updater = Updater(token=token
                      , base_url="https://telegg.ru/orig/bot", use_context=True)
    dispatcher = updater.dispatcher

    # Handlers of command
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('cancel', cancel))
    dispatcher.add_handler(CommandHandler('all', all))

    # Handlers of conversation
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler('create', command_create_db),
                      CommandHandler('add', command_add),
                      CommandHandler('delete', command_delete),
                      CommandHandler('deleteDB', question),
                      MessageHandler(Filters.regex('Добавить результаты'), command_update_db)],
        states={
            CREATE: [MessageHandler(Filters.text, create_db)],
            UPDATE: [MessageHandler(Filters.text, update_db)],
            ADD: [MessageHandler(Filters.text, add_to_db)],
            DELETE: [MessageHandler(Filters.text, delete_from_db)],
            DELETEDB: [MessageHandler(Filters.text, yes_or_no)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    ))

    # Handlers of regex
    dispatcher.add_handler(MessageHandler(Filters.regex('Недельные результаты'), button_check_week_db))
    dispatcher.add_handler(MessageHandler(Filters.regex('Результаты за месяц'), button_check_month_db))
    # dispatcher.add_handler(MessageHandler(Filters.regex('check'), check))

    # Handlers of textMessage
    dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))

    updater.start_polling(clean=True)
    print('processing')
    updater.idle()
    print('finish')


if __name__ == '__main__':
    main()
