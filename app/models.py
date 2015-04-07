from app import db

class Series(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text())
    type        = db.Column(db.Text())
    origin_loc  = db.Column(db.Text())
    demographic = db.Column(db.Text())

class Tags(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    series      = db.Column(db.Integer, db.ForeignKey('series.id'))
    weight      = db.Column(db.Float, default=1)
    tag         = db.Column(db.Text(), nullable=False)
    u_1         = db.UniqueConstraint('series', 'tag')

class Genres(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    series      = db.Column(db.Integer, db.ForeignKey('series.id'))
    genre       = db.Column(db.Text(), nullable=False)

    u_1         = db.UniqueConstraint('series', 'genre')

class Author(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    series      = db.Column(db.Integer, db.ForeignKey('series.id'))
    author      = db.Column(db.Text(), nullable=False)

    u_1         = db.UniqueConstraint('series', 'author')

class Illustrators(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    series      = db.Column(db.Integer, db.ForeignKey('series.id'))
    name        = db.Column(db.Text(), nullable=False)

    u_1         = db.UniqueConstraint('series', 'name')

class Translators(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    group_name  = db.Column(db.Text(), nullable=False)
    group_site  = db.Column(db.Text())
    u_1         = db.UniqueConstraint('group_name')

class Releases(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    series      = db.Column(db.Integer, db.ForeignKey('series.id'))
    volume      = db.Column(db.Float(), nullable=False)
    chapter     = db.Column(db.Float(), nullable=False)
    tlgroup     = db.Column(db.Integer, db.ForeignKey('translators.id'))


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)  # python 3

    def __repr__(self):
        return '<User %r>' % (self.nickname)

# DROP TABLE author;
# DROP TABLE genres;
# DROP TABLE illustrators;
# DROP TABLE migrate_version;
# DROP TABLE releases;
# DROP TABLE series;
# DROP TABLE tags;
# DROP TABLE translators;