# !/usr/bin/env python
#
# An application that allows you to entry time in the Redmine through a bot
# in Telegram
"""An application that allows you to entry time in the Redmine through a bot."""

import logging

from sqlalchemy import create_engine
from telegram import Bot, Update
from telegram.ext import Updater

from tracktime.bot import create_help_handler, create_setting_handler, \
    create_tracktime_handler
from tracktime.models import initialize_tables


def __error(bot: Bot, update: Update, error):
    """Log Errors caused by Updates."""
    logger = logging.getLogger(__name__)
    logger.warning('Update "%s" caused error "%s"', update, error)


def run(config: dict):
    """Run the application."""
    updater = Updater(config['token'], workers=1, request_kwargs={
        'proxy_url': config['proxy_url'],
        'urllib3_proxy_kwargs': {
            'username': config['proxy_username'],
            'password': config['proxy_password'],
        },
    })

    engine = create_engine(config['dsn_db'], echo=True)
    initialize_tables(engine)

    setting_handler = create_setting_handler(engine=engine,
                                             start_command_name='start',
                                             redmine_url=config['redmine_url'])
    tracktime_handler = create_tracktime_handler(engine=engine,
                                                 job_queue=updater.job_queue,
                                                 redmine_url=config[
                                                     'redmine_url'],
                                                 start_command_name='track',
                                                 cancel_command_name='cancel')
    help_handler = create_help_handler(command_name='help')

    dp = updater.dispatcher
    dp.add_handler(setting_handler)
    dp.add_handler(tracktime_handler)
    dp.add_handler(help_handler)
    dp.add_error_handler(__error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    config = {
        'token': 'TOKEN',
        'proxy_url': 'socks5://proxy',
        'proxy_username': 'proxy_username',
        'proxy_password': 'proxy_password',
        'redmine_url': 'https://host_redmine',
        'dsn_db': 'sqlite:///sqlite.db',
    }
    run(config)
