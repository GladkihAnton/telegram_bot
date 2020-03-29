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


# CREATING DATABASE
def has_create_db(user):
    with sqlite3.connect(':memory') as db:
        cur = db.cursor()
        all_tables = '''SELECT name FROM sqlite_master WHERE type="table"'''
        for row in cur.execute(all_tables):
            if user in row:
                return True
        return False


def command_create_db(update: Update, context: CallbackContext):
    user = 'db' + str(update.message.from_user.id)
    if not has_create_db(user):
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
    create = " CREATE TABLE if not exists {table}" \
             " (action TEXT, time_week INTEGER, time_month INTEGER, all_time INTEGER, last_update INTEGER)"
    insert = "INSERT INTO {table} VALUES (?, ?, ?, ?, ?)"
    with sqlite3.connect(":memory") as con:
        cur = con.cursor()
        cur.execute(create.format(table=user))
        for i in range(len(words)):
            cur.execute(insert.format(table=user), (words[i], 0, 0, 0, 0))
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


# DELETING DATABASE

def command_delete_db(update: Update, context: CallbackContext):
    user = 'db' + str(update.message.from_user.id)
    with sqlite3.connect(":memory") as db:
        cur = db.cursor()
        cur.execute('''DROP TABLE {table}'''.format(table=user))
        db.commit()
        update.message.reply_text(text='Вы удалили свою базу данных.')


# CHECK DATABASE
def check_db(update: Update, context: CallbackContext, week):
    user = 'db' + str(update.message.from_user.id)
    if has_create_db(user):
        text = ''
        with sqlite3.connect(":memory") as db:
            cur = db.cursor()
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

def command_update_db(update: Update, context: CallbackContext):
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


def update_db(update: Update, context: CallbackContext):
    answer = str(update.message.text)

    user = 'db' + str(update.message.from_user.id)
    pattern = r'\b[\w\.]+\b'
    find = re.findall(pattern, answer)
    print(find)
    select = """SELECT * FROM {table} WHERE lower(ACTION) = '{active}'"""
    refresh = "UPDATE {table} set time_week = {time_week}, time_month = {time_month}," \
              " all_time={all_time}, last_update={last_update}" \
              "  WHERE lower(ACTION) = '{active}'"
    # refresh = "UPDATE {table} set time_week = 2 WHERE lower(ACTION) = '{active}'"
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
            with sqlite3.connect(':memory') as db:
                cur = db.cursor()
                for item in cur.execute(select.format(table=user, active=str(active).lower())):
                    time_week = int(item[1]) + int(hour)
                    time_month = int(item[2]) + int(hour)
                    all_time = int(item[3]) + int(hour)
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
            return UPDATE


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


def cancel(update: Update, context: CallbackContext):
    if has_create_db('db' + str(update.message.from_user.id)):
        with sqlite3.connect(':memory') as db:
            cur = db.cursor()
            user = 'db' + str(update.message.from_user.id)
            select = """SELECT * FROM {table}"""
            refresh = "UPDATE {table} set time_week = {time_week}, time_month = {time_month}," \
                      " all_time={all_time}, last_update={last_update}" \
                      "  WHERE lower(ACTION) = '{active}'"
            upd = {}
            for item in cur.execute(select.format(table=user)):
                print(item)
                upd[str(item[0])] = []
                last_update = int(item[4])
                upd[str(item[0])].append(int(item[1]) - last_update)  # [0] = time_week
                upd[str(item[0])].append(int(item[2]) - last_update)  # [1] = time_month
                upd[str(item[0])].append(int(item[3]) - last_update)  # [2] = all_time
                upd[str(item[0])].append(0)  # [4] last_update
            for active in upd.keys():
                cur.execute(refresh.format(table=user, active=str(active).lower(), time_week=upd[active][0],
                                           time_month=upd[active][1], all_time=upd[active][2], last_update=0))
            db.commit()

        update.message.reply_text(text='Вы удалили последнее обновление!')
    else:
        update.message.reply_text(text='База данных не создана.')


def command_add(update: Update, context: CallbackContext):
    user = 'db' + str(update.message.from_user.id)
    if has_create_db(user):
        return ADD
    else:
        update.message.reply_text(text='База данных не создана')


def add_to_db(update: Update, context: CallbackContext):
    answer = update.message.text
    user = 'db' + str(update.message.from_user.id)
    pattern = r'\b[\w\.]+\b'
    words = re.findall(pattern, answer)
    with sqlite3.connect(':memory') as db:
        cur = db.cursor()
        insert = "INSERT INTO {table} VALUES (?, ?, ?, ?, ?)"
        if len(words) == 1:
            text = 'Вы добавили новое занятие: '
        else:
            text = 'Вы добавили новые занятия: '
        for i in range(len(words)):
            cur.execute(insert.format(table=user), (words[i], 0, 0, 0, 0))
            text += words[i] + '; '
        db.commit()
        update.message.reply_text(text=text)
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


def reminder(context: CallbackContext):
    text = 'Пришло время заполнить результаты, пожалуйста, сделайте это.'
    context.bot.send_message(chat_id=context.job.context, text=text)


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
    # dispatcher.add_handler(MessageHandler(Filters.regex(''), button_check_week_db))
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
