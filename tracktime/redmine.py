"""This module contain the wrapper for the redminelib library."""

from redminelib import Redmine
from redminelib.exceptions import AuthError

from tracktime.models import Issue, TimeEntry


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

        :param tracktime.models.TimeEntry time_entry: The object whose data need to save
        :return: ID time entry if save time entry into Redmine is successful
        """
        redmine = Redmine(url=self.url, key=time_entry.user.authkey)
        try:
            redmine_time_entry = redmine.time_entry.create(
                issue_id=time_entry.issue_id,
                hours=time_entry.hours,
                spent_on=time_entry.spent_on,
                comments=time_entry.comments)
            return redmine_time_entry.id
        except AuthError:
            return None

    def get_all_time_entry(self, user, spent_on=None):
        """Get all time entry from redmine for user.

        :param tracktime.models.User user:
        :param spent_on:
        :rtype: list

        """
        redmine = Redmine(url=self.url, key=user.authkey)
        try:
            time_entries = list()
            r_user_id = redmine.auth().id
            r_time_entries = redmine.time_entry.filter(user_id=r_user_id, spent_on=spent_on)
            for r_time_entry in r_time_entries:
                if 'issue' in dir(r_time_entry):
                    time_entry = TimeEntry(
                        id=r_time_entry.id,
                        user=user,
                        issue_id=r_time_entry.issue.id,
                        spent_on=r_time_entry.spent_on,
                        hours=r_time_entry.hours,
                        comments=r_time_entry.comments)
                    time_entries.append(time_entry)
            return time_entries
        except AuthError:
            return list()

    def get_issue(self, user, issue_id):
        """Get issue from from by id.

        :param tracktime.models.User user:
        :param int issue_id:
        :rtype: tracktime.models.Issue

        """
        redmine = Redmine(url=self.url, key=user.authkey)
        try:
            r_issue = redmine.issue.get(issue_id)
            return Issue(r_issue.id, r_issue.subject)
        except AuthError:
            return None
