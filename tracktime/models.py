"""This module contains the models described in the database tables."""

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """Represent the table user in a database."""

    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    authkey = Column(String(30))

    def __repr__(self):
        """Represent the user object."""
        return 'User#{} {}'.format(self.id, self.authkey)

    def __init__(self, id, authkey=''):
        """Initialize object.

        :param int id: ID user in telegram
        :param str authkey: Authorization key in Redmine
        """
        self.id = id
        self.authkey = authkey


class Issue(Base):
    """Represent the table issue in a database."""

    __tablename__ = 'issue'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)

    def __repr__(self):
        """Represent the issue object."""
        return 'Issue#{} {}'.format(self.id, self.name)

    def __init__(self, id, name):
        """Initialize object.

        :param int id: ID issue in redmine
        :param str name: Name issue in redmine
        """
        self.id = id
        self.name = name


class TimeEntry(Base):
    """Represent the table time_entry in a database."""

    __tablename__ = 'time_entry'
    id = Column(Integer, primary_key=True)
    spent_on = Column(Date)
    hours = Column(Float, nullable=False)
    comments = Column(Text)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User')

    issue_id = Column(Integer, ForeignKey('issue.id'))
    issue = relationship('Issue')

    def __repr__(self):
        """Represent the time entry object."""
        return 'TimeEntry#{} {}h {}'.format(self.id, self.hours, self.spent_on)

    def __init__(self, user=None, issue_id=None, spent_on=None, hours=None,
                 comments=None):
        """Initialize object.

        :param User user: The user who owns the time entry
        :param int issue_id: ID issue on which to track time entry
        :param datetime.date spent_on: The date on which to track time entry
        :param float hours: Number of hours to track time entry
        :param str comments: Description of time entry
        """
        self.user = user
        self.issue_id = issue_id
        self.spent_on = spent_on
        self.hours = hours
        self.comments = comments


def initialize_tables(engine):
    """Create tables which not exists in a database.

    :param sqlalchemy.engine.Engine engine:
    """
    for model in [User, Issue, TimeEntry]:
        if not engine.dialect.has_table(engine, model.__table__.name):
            model.__table__.create(bind=engine)
