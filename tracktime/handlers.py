"""This module contains the main application logic."""

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, sessionmaker

from tracktime.models import Issue, TimeEntry, User


def find_or_create_user(user_id, engine=None):
    """Find or create user if not exists.

    :param int user_id:
    :param sqlalchemy.engine.Engine engine:
    :rtype: User
    """
    session = _create_session(engine=engine)
    user = session.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        user = User(user_id)
        session.add(user)
        session.commit()

    session.close()
    return user


def save_user_key(user_id, redmine_key, redmine=None, engine=None):
    """Save the authorization key to the user if key valid.

    :param int user_id:
    :param string redmine_key:
    :param tracktime.redmine.RedmineWrapper redmine:
    :param sqlalchemy.engine.Engine engine:
    :rtype: bool
    """
    session = _create_session(engine=engine)
    user = session.query(User).filter(User.id == user_id).one()

    valid_authkey = redmine.check_authkey(redmine_key)
    if valid_authkey:
        user.authkey = redmine_key
        session.add(user)
        session.commit()

    session.close()
    return valid_authkey


def all_user_ids(engine):
    """Return all save user id.

    :param sqlalchemy.engine.Engine engine:
    :return:
    """
    return [r[0] for r in engine.execute(select([User.id])).fetchall()]


def sync_user_with_redmine(user_id, spent_on=None, redmine=None, engine=None):
    """Copy all time entry from Redmine to db for user.

    :param int user_id:
    :param tracktime.redmine.RedmineWrapper redmine:
    :param sqlalchemy.engine.Engine engine:
    """
    session = _create_session(engine=engine)

    user = session.query(User).filter(User.id == user_id).one()
    issues_ids = [r[0] for r in session.execute(select([Issue.id])).fetchall()]
    time_entries = session.query(TimeEntry).filter(TimeEntry.user_id == user_id).all()

    for r_time_entry in redmine.get_all_time_entry(user, spent_on=spent_on):
        if r_time_entry.issue_id not in issues_ids:
            r_issue = redmine.get_issue(user, r_time_entry.issue_id)
            issues_ids.append(r_time_entry.issue_id)
            session.add(r_issue)

        time_entry = __get_time_entry(time_entries, r_time_entry.id)
        if time_entry is None:
            time_entry = r_time_entry
            time_entries.append(time_entry)
        else:
            time_entry.hours = r_time_entry.hours
            time_entry.comments = r_time_entry.comments
            time_entry.spent_on = r_time_entry.spent_on
        session.add(time_entry)

    session.commit()
    session.close()


def __get_time_entry(time_entries, time_entry_id):
    for time_entry in time_entries:
        if time_entry_id == time_entry.id:
            return time_entry
    return None


def get_actual_issues(user_id, engine=None):
    """Get actual issues.

    :param int user_id:
    :param sqlalchemy.engine.Engine engine:
    :rtype: list
    """
    s = select([TimeEntry.issue_id,
                func.max(TimeEntry.id).label('max_te'),
                func.count().label('count_te')])
    s = s.where(TimeEntry.user_id == user_id)
    s = s.group_by(TimeEntry.issue_id)
    s = s.order_by(desc('max_te'), desc('count_te'))
    s = s.limit(10)

    issue_ids = [row[0] for row in engine.execute(s)]

    session = _create_session(engine=engine)
    issues = session.query(Issue).filter(Issue.id.in_(issue_ids)).all()
    session.close()

    return issues


def save_time_entry(state, redmine=None, engine=None):
    """Save time entry to Redmine and db.

    :param dict state:
    :param tracktime.redmine.RedmineWrapper redmine:
    :param sqlalchemy.engine.Engine engine:
    :rtype: bool
    """
    session = _create_session(engine=engine)
    user = session.query(User).filter(User.id == state['user_id']).one()
    time_entry = TimeEntry(
        user=user,
        issue_id=state['issue_id'],
        spent_on=state['spent_on'],
        hours=state['hours'],
        comments=state['comments'])

    time_entry.id = redmine.save_time_entry(time_entry)
    if time_entry.id is None:
        session.close()
        return False

    session.add(time_entry)
    session.commit()
    session.close()
    return True


def _create_session(engine) -> Session:
    Session_ = sessionmaker()
    Session_.configure(bind=engine)
    return Session_()
