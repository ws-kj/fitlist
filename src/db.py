#!/usr/bin/env python3
import os, sqlite3, string, collections


root = os.path.dirname(os.path.realpath(__file__))

def dict_gen(curs):
    # From Python Essential Reference by David Beazley
    field_names = [d[0].lower() for d in curs.description]
    while True:
        rows = curs.fetchmany()
        if not rows: return
        for row in rows:
            yield dict(zip(field_names, row))

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db():
    return sqlite3.connect(root + "/fitlist.db")

def commit(db, q, *args):
    c = db.cursor()
    c.execute(q, args);
    r = c.lastrowid
    db.commit()
    return r

# code by Niles Rogoff. Thanks man!
def _make_valid_ident(i):
	if i[0] not in (string.ascii_letters + "_"):
		i = "sql_" + i[0]
	return "".join([c if c in (string.ascii_letters + string.digits + "_") else "_" for c in i])

def _try_symbolize_names_for_sql(l):
	l = {_make_valid_ident(k): v for k, v in l.items()}
	cls = collections.namedtuple("t", l.keys())
	old_getitem = cls.__getitem__
	cls.__getitem__ = lambda self, k: l[k] if isinstance(k, str) else old_getitem(self, k)
	return cls(**l)


def nquery(q, *args, symbolize_names =  True):
    db = get_db()
    c = db.cursor()
    c.execute(q, args) # no splat!
    return [(_try_symbolize_names_for_sql if symbolize_names else lambda i: i)({c.description[i][0]: v for i, v in enumerate(row)}) for row in c.fetchall()]
# ---------------------------------

#TODO bad!!!!!! use niles!
def query(q, *args):
    db = get_db()
    c = db.cursor()
    rows = [r for r in dict_gen(c.execute(q, args))]
    db.commit()
    db.close()
    return rows

def execute(q, *args):
    db = get_db()
    c = db.cursor()
    c.execute(q, args)
    db.commit()
    db.close()

def init():
    db = get_db()
    db.row_factory = dict_factory
    c = db.cursor()

    #create users table
    c.execute("""
    create table if not exists users (
        user_id integer primary key autoincrement,
        username varchar(24) not null,
        password varchar(120) not null,
        email text,
        picture text,
        join_date timestamp default current_timestamp,
        bio varchar(512),
        likes int default 0,
        dislikes int default 0
    )
    """)

    #create workouts table
    c.execute("""
    create table if not exists workouts (
        workout_id integer primary key autoincrement,
        user_id integer,
        title varchar(128) not null,
        created_date timestamp default current_timestamp,
        content text not null,
        spreadsheet text,
        frequency int,
        tags text,
        stars int default 0,
        likes int default 0,
        dislikes int default 0,
        foreign key(user_id) references users(user_id)
    )
    """)

    #create review table
    c.execute("""
    create table if not exists reviews (
        review_id integer primary key autoincrement,
        workout_id integer,
        user_id integer,
        title varchar(128) not null,
        created_date timestamp default current_timestamp,
        content text not null,
        stars int not null,
        likes int default 0,
        dislikes int default 0,
        foreign key(workout_id) references workouts(workout_id),
        foreign key(user_id) references users(user_id)
    )
    """)
    db.commit()
    db.close()

