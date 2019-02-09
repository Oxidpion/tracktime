"""The module provides the message formatting and building."""

from datetime import date, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

FINISH_ENTRY_TIME = 'Сейчас я знаю:\n' \
                    '{}\n' \
                    'Осталось подтвердить изменения или изменить комментарий.' \
                    ' А также можешь отказатся от помощи, щелкнув на /cancel'


def reply_welcome(message):
    """Reply greeting on the message.

    :param telegram.Message message: A message to which you must respond
    :rtype: telegram.Message Response message
    """
    return message.reply_text('Для помощи обратитесь к команде /help, чтобы затрекать время '
                              'выберите команду /track')


def reply_help(message):
    """Reply with command help on the message.

    :param telegram.Message  message: A message to which you must respond
    :rtype: telegram.Message Response message
    """
    return message.reply_text(
        'Команда /start позволит зарегестрироватся или сменить ключ от '
        'редмайна, а с помощью команды /track можно затрекать время, выполнив '
        'пошаговые инструкции')


def reply_start_redmine_settings(message):
    """Reply greeting on the message to customize user settings.

    :param telegram.Message  message: A message to which you must respond
    :rtype: telegram.Message Response message
    """
    return message.reply_text('Привет! Чтобы можно было воспользоватся ботом нужно его настроить')


def reply_set_redmine_key(message):
    """The response message to configure the authorization key Redmine.

    :param telegram.Message  message: A message to which you must respond
    :rtype: telegram.Message Response message
    """
    return message.reply_text(
        'Пожалуйста введите ключ от redmine, который можно получить в профиле')


def reply_invalid_redmine_key(message):
    """Error message on authorization key Redmine.

    :param telegram.Message  message: A message to which you must respond
    :rtype: telegram.Message Response message
    """
    return message.reply_text('Меня не обмануть, введи правильный ключ. Для повторного ввода '
                              'используй команду /start')


def reply_save_redmine_settings(message):
    """The response message with successful saving of settings.

    :param telegram.Message  message: A message to which you must respond
    :rtype: telegram.Message Response message
    """
    return message.reply_text('Настройки подключения к redmine успешно сохранены')


def reply_start_time_entry(message):
    """Reply greeting on the message to set to the time entry.

    :param telegram.Message  message: A message to which you must respond
    :rtype: telegram.Message Response message
    """
    return message.reply_text('Бот выручит тебя, только укажи куда мне затрекать время')


def reply_set_spent_on_time_entry(message, status):
    """The response message to set spent on the time entry.

    :param telegram.Message  message: A message to which you must respond
    :param dict status: Data dictionary which contains time entry information
    :rtype: telegram.Message Response message
    """
    text = 'Сейчас я знаю:\n' \
           '{}\n' \
           'Теперь нужно указать смещение на какой день нужно затрекать ' \
           'время. Но ты можешь отказатся от помощи, щелкнув на /cancel'
    text = text.format(_print_status_entry_time(status))
    reply_markup = _create_last_7_day_keyboard()
    return message.reply_text(text, reply_markup=reply_markup)


def _print_status_entry_time(status):
    message = list()
    if 'issue_name' in status:
        message.append('Задача - {}'.format(status['issue_name']))
    if 'spent_on' in status:
        message.append('Дата - {}'.format(_russian_date(status['spent_on'])))
    if 'hours' in status:
        message.append('Часов - {}'.format(status['hours']))
    if 'comments' in status:
        message.append('Комментарий - {}'.format(status['comments']))

    if len(message) == 0:
        message.append('Ничего')

    return '\n'.join(message).join(['\n', '\n'])


def _create_last_7_day_keyboard():
    buttons = [
        InlineKeyboardButton(_russian_date(d), callback_data=str(d))
        for d in _date_from_today(range(0, -8, -1))
    ]
    return InlineKeyboardMarkup(_build_menu(buttons, n_cols=2))


def edit_set_issue_time_entry(message, status, issues):
    """
    Edit the current message on response with setting task of the time entry.

    :param telegram.Message message: A message to which you need to edit
    :param dict status: Data dictionary which contains time entry information
    :param list issues:
    :rtype: telegram.Message message: Response message
    """
    text = 'Сейчас я знаю:\n' \
           '{}\n' \
           'Теперь нужно указать в какую задачу нужно затрекать время. ' \
           'Но ты можешь отказатся от помощи, щелкнув на /cancel'
    text = text.format(_print_status_entry_time(status))
    reply_markup = _create_issue_keyboard(issues)
    return message.bot.edit_message_text(
        text, chat_id=message.chat.id, message_id=message.message_id, reply_markup=reply_markup)


def _create_issue_keyboard(issues):
    issues.reverse()
    buttons = [InlineKeyboardButton(issue.name, callback_data=issue.id) for issue in issues]
    return InlineKeyboardMarkup(_build_menu(buttons, n_cols=1))


def edit_set_comment_time_entry(message, status):
    """Edit message.

    Edit the current message on response with setting comments of the time
    entry.

    :param telegram.Message message: A message to which you need to edit
    :param dict status: Data dictionary which contains time entry information
    :rtype: telegram.Message message: Edited message
    """
    text = 'Сейчас я знаю:\n' \
           '{}\n' \
           'Теперь нужно написать комментарий или ты можешь отказатся от ' \
           'помощи, щелкнув на /cancel'
    text = text.format(_print_status_entry_time(status))
    return message.bot.edit_message_text(
        text, chat_id=message.chat.id, message_id=message.message_id)


def delete_message(chat, message_id):
    """
    Delete message from chat by message_id.

    :param telegram.Chat chat: Chat, in which you want to delete  the message
    :param int message_id: The message id
    """
    chat.bot.delete_message(chat_id=chat.id, message_id=message_id)


def reply_set_hours_time_entry(message, status):
    """The response message to set hours of time entry.

    :param telegram.Message message: A message to which you must respond
    :param dict status: Data dictionary which contains time entry information
    :rtype: telegram.Message message: Response message
    """
    text = 'Сейчас я знаю:\n' \
           '{}\n' \
           'Теперь нужно добавить время, сколько хочется затрекать время. ' \
           'Но ты можешь отказатся от помощи, щелкнув на /cancel'
    text = text.format(_print_status_entry_time(status))
    reply_markup = _create_hours_keyboard(has_done_button=False)
    return message.reply_text(text, reply_markup=reply_markup)


def _create_hours_keyboard(has_done_button=False):
    hours = ['0.1', '0.5', '1', '2', '4', '8']

    buttons = [InlineKeyboardButton(h, callback_data=h) for h in hours]
    buttons.append(InlineKeyboardButton('Сброс', callback_data='Reset'))

    if has_done_button:
        footer_buttons = [InlineKeyboardButton('Готово', callback_data='Done')]
        buttons = _build_menu(buttons, n_cols=4, footer_buttons=footer_buttons)
    else:
        buttons = _build_menu(buttons, n_cols=4)

    return InlineKeyboardMarkup(buttons)


def edit_set_hours_time_entry(message, status, has_done_button=False):
    """
    Edit the current message on response with setting hours of the time entry.

    :param telegram.Message message: A message to which you need to edit
    :param dict status: Data dictionary which contains time entry information
    :param bool has_done_button: When the `` True`` in the edited message in
        the keyboard will be added to the bottom of the button labeled "Done"

    :rtype: telegram.Message message: Edited message
    """
    text = 'Сейчас я знаю:\n' \
           '{}\n' \
           'Теперь нужно добавить время, сколько хочется затрекать время. ' \
           'Но ты можешь отказатся от помощи, щелкнув на /cancel'
    text = text.format(_print_status_entry_time(status))
    reply_markup = _create_hours_keyboard(has_done_button=has_done_button)
    return message.bot.edit_message_text(
        text, chat_id=message.chat.id, message_id=message.message_id, reply_markup=reply_markup)


def edit_save_time_entry(message, status):
    """Edit the current message on response with saving time entry.

    :param telegram.Message message: A message to which you need to edit
    :param dict status: Data dictionary which contains time entry information
    :rtype: telegram.Message message: Edited message
    """
    text = 'Бот выручит прямо сейчас:\n{}'
    text = text.format(_print_status_entry_time(status))
    return message.bot.edit_message_text(
        text, chat_id=message.chat.id, message_id=message.message_id)


def reply_cancel_time_entry(message):
    """Cancel reply message to set the time entry.

    :param telegram.Message message: A message to which you must respond
    :rtype: telegram.Message message: Response message
    """
    return message.reply_text('Бот пытался помочь, но не смог. Попробуй в следующий раз')


def _build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def _date_from_today(range_):
    """Generate dates by offset range in days the current day.

    :param range range_:
    :rtype: list
    """
    return [date.today() + timedelta(days=delta) for delta in range_]


def _russian_date(date_):
    """Humanize a date in Russian.

    :param date date_:
    :rtype: str
    """
    if date_ == date.today():
        return 'Сегодня'
    if date_ == date.today() - date.resolution:
        return 'Вчера'
    if date_ == date.today() + date.resolution:
        return 'Завтра'
    return '{} {} ({})'.format(date_.day, _russian_month(date_), _russian_weekday(date_))


def _russian_weekday(date_):
    """Humanize a weekday in Russian.

    :param date date_:
    :rtype: str
    """
    return ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'][date_.weekday()]


def _russian_month(date_):
    """Humanize a month in Russian.

    :param date date_:
    :rtype: str
    """
    months = [
        'Янв', 'Фев', 'Март', 'Апр', 'Май', 'Июнь', 'Июль', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'
    ]
    return months[date_.month - 1]
