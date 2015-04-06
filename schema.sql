-- Planned database schema?
-- PostgreSQL specific

DROP TABLE IF EXISTS series;
DROP TABLE IF EXISTS illustrators;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS author;
DROP TABLE IF EXISTS releases;
DROP TABLE IF EXISTS translators;


CREATE TABLE series (
    id          SERIAL PRIMARY KEY,
    description TEXT,
    type        TEXT,
    origin_loc  TEXT,
    demographic TEXT
);

CREATE TABLE tags (
    id          SERIAL PRIMARY KEY,
    series      INTEGER,
    weight      REAL DEFAULT 1,
    tag         TEXT NOT NULL,
    FOREIGN KEY(series) REFERENCES series(id),
    UNIQUE(series, tag)
);

CREATE TABLE genres (
    id          SERIAL PRIMARY KEY,
    series      INTEGER,
    genre       TEXT NOT NULL,
    FOREIGN KEY(series) REFERENCES series(id),
    UNIQUE(series, genre)
);

CREATE TABLE author (
    id          SERIAL PRIMARY KEY,
    series      INTEGER,
    author      TEXT NOT NULL,
    FOREIGN KEY(series) REFERENCES series(id),
    UNIQUE(series, author)
);

CREATE TABLE illustrators (
    id          SERIAL PRIMARY KEY,
    series      INTEGER,
    name        TEXT NOT NULL,
    FOREIGN KEY(series) REFERENCES series(id),
    UNIQUE(series, name)
);

CREATE TABLE translators (
    id          SERIAL PRIMARY KEY,
    group_name  TEXT NOT NULL,
    group_site  TEXT,
    UNIQUE(group_name)
);

CREATE TABLE releases (
    id          SERIAL PRIMARY KEY,
    series      INTEGER,
    volume      REAL NOT NULL,
    chapter     REAL NOT NULL,
    tlgroup     INTEGER,
    FOREIGN KEY(series)  REFERENCES series(id),
    FOREIGN KEY(tlgroup) REFERENCES translators(id)
);

