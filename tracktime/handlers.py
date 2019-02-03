"""This module contains the main application logic."""

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

    if redmine.check_authkey(redmine_key):
        session.close()
        return False

    user.authkey = redmine_key
    session.add(user)
    session.close()
    return True


def get_actual_issues(user_id, engine=None):
    """Get actual issues.

    :param int user_id:
    :param sqlalchemy.engine.Engine engine:
    :rtype: list
    """
    return [Issue(1, 'Task 1'), Issue(2, 'Task 2')]


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
        comments=state['comments']
    )
    if not redmine.save_time_entry(time_entry):
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
