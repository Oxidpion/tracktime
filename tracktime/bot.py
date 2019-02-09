"""This module contains the functions for creating handlers for a Telegram."""
import logging
from datetime import date, datetime, timedelta

from telegram.ext import CallbackQueryHandler, CommandHandler, \
    ConversationHandler, Filters, MessageHandler, run_async

from tracktime.handlers import all_user_ids, find_or_create_user, get_actual_issues, \
    save_time_entry, save_user_key, sync_user_with_redmine
from tracktime.messages import delete_message, edit_save_time_entry, \
    edit_set_comment_time_entry, edit_set_hours_time_entry, \
    edit_set_issue_time_entry, reply_cancel_time_entry, reply_help, \
    reply_invalid_redmine_key, reply_save_redmine_settings, \
    reply_set_hours_time_entry, reply_set_redmine_key, \
    reply_set_spent_on_time_entry, reply_start_redmine_settings, \
    reply_start_time_entry, reply_welcome
from tracktime.redmine import RedmineWrapper


def create_setting_handler(engine, job_queue, start_command_name, redmine_url):
    """Create a handler to configure the settings for the user.

    :param sqlalchemy.engine.Engine engine: Engine database
    :param telegram.ext.JobQueue job_queue:
    :param str start_command_name: Start command name in the chat
    :param str redmine_url: Url redmine resources
    :return: Handler of Telegram

    """
    SET_KEY = 1

    redmine = RedmineWrapper(redmine_url)

    @run_async
    def start(bot, update):
        user_id = update.message.from_user.id
        find_or_create_user(user_id, engine=engine)

        reply_start_redmine_settings(update.message)
        reply_set_redmine_key(update.message)
        return SET_KEY

    @run_async
    def set_key(bot, update):
        user_id = update.message.from_user.id
        redmine_key = update.message.text

        if not save_user_key(user_id, redmine_key, redmine, engine=engine):
            reply_invalid_redmine_key(update.message)
            return ConversationHandler.END

        __sync_user(user_id, job_queue=job_queue, redmine=redmine, engine=engine)
        reply_save_redmine_settings(update.message)
        reply_welcome(update.message)
        return ConversationHandler.END

    return ConversationHandler(
        entry_points=[CommandHandler(start_command_name, start)],
        states={SET_KEY: [MessageHandler(Filters.text, set_key)]},
        fallbacks=[])


def create_tracktime_handler(engine, job_queue, redmine_url, start_command_name,
                             cancel_command_name):
    """Create a handler to build and save a time entry.

    :param sqlalchemy.engine.Engine engine:  Engine database
    :param telegram.ext.JobQueue job_queue:
    :param str redmine_url: Url redmine resources
    :param str start_command_name: Start command name in chat
    :param str cancel_command_name: Cancel command name in chat
    :return: Handler in Telegram

    """
    SPENT_ON, ISSUE, COMMENTS, HOURS = range(10, 14)

    redmine = RedmineWrapper(redmine_url)

    @run_async
    def start(bot, update, user_data):
        reply_start_time_entry(update.message)

        user_id = int(update.message.from_user.id)
        message = reply_set_spent_on_time_entry(update.message, {})

        __sync_user_on_today(user_id, job_queue, redmine, engine)

        user_data['message_id'] = message.message_id
        user_data['user_id'] = user_id
        return SPENT_ON

    @run_async
    def spent_on(bot, update, user_data):
        spent_date = datetime.strptime(update.callback_query.data, '%Y-%m-%d')
        user_data['spent_on'] = spent_date.date()
        user_data['issues'] = {}

        issues = get_actual_issues(update.effective_user.id, engine=engine)
        for issue in issues:
            user_data['issues'][issue.id] = issue.name

        message = update.callback_query.message
        edit_set_issue_time_entry(message, user_data, issues)
        return ISSUE

    @run_async
    def issue(bot, update, user_data):
        issue_id = int(update.callback_query.data)

        user_data['issue_id'] = issue_id
        user_data['issue_name'] = user_data['issues'][issue_id]
        del user_data['issues']

        edit_set_comment_time_entry(update.callback_query.message, user_data)
        return COMMENTS

    @run_async
    def comments(bot, update, user_data):
        user_data['comments'] = update.message.text

        delete_message(update.message.chat, user_data['message_id'])
        message = reply_set_hours_time_entry(update.message, user_data)

        user_data['message_id'] = message.message_id
        return HOURS

    @run_async
    def add_hours(bot, update, user_data):
        hours = user_data.get('hours', 0)
        hours += float(update.callback_query.data)
        user_data['hours'] = hours

        message = update.callback_query.message
        edit_set_hours_time_entry(message, user_data, has_done_button=True)
        return HOURS

    @run_async
    def reset_hours(bot, update, user_data):
        del (user_data['hours'])

        message = update.callback_query.message
        edit_set_hours_time_entry(message, user_data, has_done_button=False)
        return HOURS

    @run_async
    def done(bot, update, user_data):
        if not save_time_entry(user_data, redmine, engine=engine):
            return ConversationHandler.END

        edit_save_time_entry(update.callback_query.message, user_data)
        user_data.clear()
        return ConversationHandler.END

    @run_async
    def cancel(bot, update, user_data):
        delete_message(update.message.chat, user_data['message_id'])
        reply_cancel_time_entry(update.message)
        user_data.clear()
        return ConversationHandler.END

    return ConversationHandler(
        entry_points=[CommandHandler(start_command_name, start, pass_user_data=True)],
        states={
            SPENT_ON: [
                CallbackQueryHandler(spent_on, pattern=r"^\d{4}-\d{2}-\d{2}$", pass_user_data=True)
            ],
            ISSUE: [CallbackQueryHandler(issue, pattern=r"^\d+$", pass_user_data=True)],
            COMMENTS: [MessageHandler(Filters.text, comments, pass_user_data=True)],
            HOURS: [
                CallbackQueryHandler(add_hours, pattern=r"^[\d.]+$", pass_user_data=True),
                CallbackQueryHandler(reset_hours, pattern=r"^Reset$", pass_user_data=True)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(done, pattern=r"^Done$", pass_user_data=True),
            CommandHandler(cancel_command_name, cancel, pass_user_data=True)
        ],
    )


def create_help_handler(command_name):
    """Create a handler to show the help message.

    :param str command_name: Command name in chat
    :return: Handler of Telegram

    """
    def help(bot, update):
        reply_help(update.message)

    return CommandHandler(command_name, help)


def __sync_user(user_id, time_offset=0, job_queue=None, redmine=None, engine=None):
    """Create a job to synchronize the user in Redmine with the database.

    :param int user_id:
    :param int time_offset:
    :param telegram.ext.JobQueue job_queue:
    :param tracktime.redmine.RedmineWrapper redmine:
    :param sqlalchemy.engine.Engine engine:

    """
    logger = logging.getLogger(__name__)

    @run_async
    def sync_time_entries(bot, job):
        logger.info('Start sync time entries for user {}'.format(user_id))
        sync_user_with_redmine(user_id, redmine=redmine, engine=engine)
        logger.info('Finish sync {}'.format(user_id))

    job_name = 'sync_user_{}'.format(user_id)
    if len(job_queue.get_jobs_by_name(job_name)) == 0:
        job_queue.run_once(sync_time_entries, time_offset, name=job_name)


def sync_daily_users(job_queue=None, redmine_url=None, engine=None):
    """Create daily jobs to synchronize saved users in the database with Redmine.

    :param telegram.ext.JobQueue job_queue:
    :param str redmine_url:
    :param sqlalchemy.engine.Engine engine:

    """
    redmine = RedmineWrapper(redmine_url)

    @run_async
    def sync_all_time_entries(bot, job):
        time_offset = timedelta()
        for user_id in all_user_ids(engine):
            __sync_user(user_id, time_offset, job_queue, redmine, engine)
            time_offset += timedelta(minutes=1)

    job_queue.run_once(sync_all_time_entries, 0)
    job_queue.run_daily(sync_all_time_entries, 0)


def __sync_user_on_today(user_id, job_queue=None, redmine=None, engine=None):
    """Create a job to partial synchronize the user for today in the database with Redmine.

    :param int user_id:
    :param telegram.ext.JobQueue job_queue:
    :param tracktime.redmine.RedmineWrapper redmine:
    :param sqlalchemy.engine.Engine engine:

    """
    logger = logging.getLogger(__name__)

    @run_async
    def sync_all_time_entries(bot, job):
        logger.info('Start sync time entries on today for user {}'.format(user_id))
        sync_user_with_redmine(user_id, date.today(), redmine, engine)
        logger.info('Finish sync on today {}'.format(user_id))

    job_name = 'sync_user_today_{}'.format(user_id)

    if len(job_queue.get_jobs_by_name(job_name)) == 0:
        job_queue.run_once(sync_all_time_entries, 0, name=job_name)
