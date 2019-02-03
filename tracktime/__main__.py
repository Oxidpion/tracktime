# !/usr/bin/env python
#
# An application that allows you to entry time in the Redmine through a bot
# in Telegram
"""An application that allows you to entry time in the Redmine through a bot.

The application must be configured through the environment.

Environment:
    TELEGRAM_TOKEN : The telegram token.
    REDMINE_URL : Redmine URI that should track time entry.
    DSN_DB: Optional. Default `sqlite:///sqlite.db`. Database data source name.
    PROXY_URL: Optional. URI proxy through which the bot will work.
    PROXY_USERNAME: Optional. Proxy username.
    PROXY_PASSWORD: Optional. Proxy password.
"""

import logging
import os

from sqlalchemy import create_engine
from telegram import Bot, Update
from telegram.ext import Updater

from tracktime.bot import create_help_handler, create_setting_handler, create_tracktime_handler
from tracktime.models import initialize_tables


def __error(bot: Bot, update: Update, error):
    """Log Errors caused by Updates."""
    logger = logging.getLogger(__name__)
    logger.warning('Update "%s" caused error "%s"', update, error)


def run(config: dict):
    """Run the application.

    :param config: Configuration dictionary.

    Key `proxy` is optional. If key `proxy` is not exists then bot create
    a standard connection. Example:

        config = {
            'token': 'TELEGRAM_TOKEN',
            'redmine_url': 'REDMINE_URL',
            'dsn_db': 'DSN_DB',
            'proxy': {  # Optional
                'url': 'PROXY_URL',
                'username': 'PROXY_USERNAME',
                'password': 'PROXY_PASSWORD'
            }
        }

    """
    request_kwargs = {}
    if 'proxy' in config:
        request_kwargs = {
            'proxy_url': config['proxy']['url'],
            'urllib3_proxy_kwargs': {
                'username': config['proxy']['username'],
                'password': config['proxy']['password'],
            }
        }

    updater = Updater(config['token'], workers=1, request_kwargs=request_kwargs)

    engine = create_engine(config['dsn_db'], echo=True)
    initialize_tables(engine)

    setting_handler = create_setting_handler(engine=engine,
                                             start_command_name='start',
                                             redmine_url=config['redmine_url'])
    tracktime_handler = create_tracktime_handler(engine=engine,
                                                 job_queue=updater.job_queue,
                                                 redmine_url=config['redmine_url'],
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


def __get_env_config():
    config = {
        'token': os.environ['TELEGRAM_TOKEN'],
        'redmine_url': os.environ['REDMINE_URL'],
        'dsn_db': os.getenv('DSN_DB', 'sqlite:///sqlite.db')
    }

    config_proxy = {}
    if 'PROXY_URL' in os.environ:
        config_proxy['url'] = os.getenv('PROXY_URL')

    if 'PROXY_USERNAME' in os.environ:
        config_proxy['username'] = os.getenv('PROXY_USERNAME')

    if 'PROXY_PASSWORD' in os.environ:
        config_proxy['password'] = os.getenv('PROXY_PASSWORD')

    if len(config_proxy) == 3:
        config['proxy'] = config_proxy

    return config


if __name__ == '__main__':
    config = __get_env_config()
    run(config)
