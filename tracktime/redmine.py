"""This module contain the wrapper for the redminelib library."""

from redminelib import Redmine
from redminelib.exceptions import AuthError


class RedmineWrapper:
    """Wrapper for working with the :class:`redminelib.Redmine`."""

    def __init__(self, redmine_url):
        """Initialize wrapper.

        :param str redmine_url: The redmine url
        """
        self.url = redmine_url

    def check_authkey(self, authkey):
        """Check authorization key.

        :param string authkey: Authorization key to check
        :return: True if authorization key is correct
        """
        redmine = Redmine(url=self.url, key=authkey)
        try:
            redmine.auth()
            return True
        except AuthError:
            return False

    def save_time_entry(self, time_entry):
        """Save time entry in Redmine.

        :param tracktime.models.TimeEntry time_entry:
            The object whose data need to save

        :return: ``True`` if save time entry into Redmine is successful
        """
        redmine = Redmine(url=self.url, key=time_entry.user.authkey)
        try:
            redmine.time_entry.create(
                issue_id=time_entry.issue_id,
                hours=time_entry.hours,
                spent_on=time_entry.spent_on,
                comments=time_entry.comments)
            return True
        except AuthError:
            return False
