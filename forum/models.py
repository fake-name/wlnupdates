from datetime import datetime

from flask_security import UserMixin
from flask_security import RoleMixin
from sqlalchemy import event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.orderinglist import ordering_list

from app import db


class Base(db.Model):

    """A base class that automatically creates the table name and
    primary key.
    """

    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


class TimestampMixin(object):
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow)

    def readable_date(self, date, format='%H:%M on %-d %B'):
        """Format the given date using the given format."""
        return date.strftime(format)


# Authentication
# ~~~~~~~~~~~~~~
class UserRoleAssoc(db.Model):

    """Associates a user with a role."""

    __tablename__ = 'user_role_assoc'
    user_id = db.Column(db.ForeignKey('users.id'), primary_key=True)
    role_id = db.Column(db.ForeignKey('forum_roles.id'), primary_key=True)



class Role(Base, RoleMixin):
    __tablename__ = 'forum_roles'
    """
    A specific role. `RoleMixin` provides the following methods:

        `__eq__(self, other)`
            Returns ``True`` if the `name` attributes are the same. If
            `other` is a string, returns `self.name == other`.

        `__ne__(self, other)`
    """

    name = db.Column(db.String)
    description = db.Column(db.String)

    def __repr__(self):
        return '<Role(%s, %s)>' % (self.id, self.name)


# Forum
# ~~~~~
class Board(Base):
    __tablename__ = 'forum_boards'
    #: The human-readable name, e.g. "Python 3"
    name = db.Column(db.String)

    #: The URL-encoded name, e.g. "python-3"
    slug = db.Column(db.String, unique=True)

    #: A short description of what the board contains.
    description = db.Column(db.Text)

    #: The threads associated with this board.
    threads = db.relationship('Thread', cascade='all,delete', backref='board', order_by='desc(Thread.updated)', lazy='dynamic')

    def __unicode__(self):
        return self.name


class Thread(Base, TimestampMixin):
    __tablename__ = 'forum_threads'
    name = db.Column(db.String(80))

    #: The original author of the thread.
    author_id = db.Column(db.ForeignKey('users.id'), index=True)
    author = db.relationship('Users', backref='threads')

    #: The parent board.
    board_id = db.Column(db.ForeignKey('forum_boards.id'), index=True)

    #: An ordered collection of posts
    posts = db.relationship('Post', backref='threads',
                            cascade='all,delete',
                            order_by='Post.id',
                            collection_class=ordering_list('index'))

    #: Length of the threads
    length = db.Column(db.Integer, default=0)

    def __unicode__(self):
        return self.name


class Post(Base, TimestampMixin):
    __tablename__ = 'forum_posts'
    #: Used to order the post within its :class:`Thread`
    index = db.Column(db.Integer, default=0, index=True)

    #: The post content. The site views expect Markdown by default, but
    #: you can store anything here.
    content = db.Column(db.Text)

    #: The original author of the post.
    author_id = db.Column(db.ForeignKey('users.id'), index=True)
    author = db.relationship('Users', backref='posts')

    #: The parent thread.
    thread_id = db.Column(db.ForeignKey('forum_threads.id'), index=True)


    def __repr__(self):
        return '<Post(%s)>' % self.id


def thread_posts_append(thread, post, initiator):
    """Update some thread values when `Thread.posts.append` is called."""
    thread.length += 1
    thread.updated = datetime.utcnow()

event.listen(Thread.posts, 'append', thread_posts_append)
