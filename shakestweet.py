# Modified from http://flask.pocoo.org/docs/0.11/tutorial/

# ORDER OF BATTLE:
# Program queries art database, returns results
# Program queries quote database, returns results
# User selects art
# User selects quote
# User triggers art/quote merger into new image
# User accepts merged image, or makes tweaks until result is satisfactory
# User sends image to Twitter account: Usr/pwd DrMehendriSolon, MONSTER

# -*- coding: utf-8 -*-
"""
    Flaskr
    ~~~~~~
    A microblog example application written as Flask tutorial with
    Flask and sqlite3.
    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import os
import json, requests, sys, random
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash


# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'shakestweet.db'),
#    DATABASE=os.path.join(app.root_path, 'fnord'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin', #for Twitter, s/b os.path.join(app.root_path, '/static/secret/twitter_usrname'),
    PASSWORD='default'#for Twitter, s/b os.path.join(app.root_path, '/static/secret/twitter_pwd'),
))
app.config.from_envvar('SHAKESTWEET_SETTINGS', silent=True)


# def convert_json_to_sqlite():
#     # JSON to SQLite3 converter modified from here: https://gist.github.com/atsuya046/7957165#file-jsontosqlite-py
#     # This downloads the JSON data containing Shakespeare texts from my website
#     url = 'http://christopherbahn.com/programming/will_play_text_python.json'
#     response = requests.get(url)
#     response.raise_for_status()
#     # Load JSON data into a Python variable.
#     bill = json.loads(response.text, strict=False)
#
#     line_id = bill[0]["line_id"]
#     play_name = bill[0]["play_name"]
#     speech_number = bill[0]["speech_number"]
#     line_number = bill[0]["line_number"]
#     speaker = bill[0]["speaker"]
#     text_entry = bill[0]["text_entry"]
#     data = [line_id, play_name, speech_number, line_number, speaker, text_entry]
#
#     if not session.get('logged_in'):
#         abort(401)
#     db = get_db()
#     db.execute('insert into shakespearetext (line_id, play_name, speech_number, line_number, speaker, text_entry) values (?, ?, ?, ?, ?, ?)', data)
#     db.commit()


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

# TODO This is the default page. It's where the main part of your program goes.
@app.route('/')
def show_shakestweet():
   return render_template('shakestweet.html', data="hello there!!!!")
# def show_entries():
#     db = get_db()
#     cur = db.execute('select title, text from entries order by id desc')
#     entries = cur.fetchall()
#     return render_template('show_entries.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (title, text) values (?, ?)',
               [request.form['title'], request.form['text']])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

# TODO Reconfigure this to login to Twitter.
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

# TODO Below this line is incomplete stuff I'm not sure I will keep
@app.route('/start')
def show_template():
	return render_template('shakestweet.html', data="hello!!")


@app.route('/searchplays')
def search_for_quotes():
    # TODO search for appropriate quote and do stuff with it
    print(request.args)
    searchShakes = request.args.get('query')
    # This if-else prevents an error if user goes to /search webpage (searching for "None"). /search?query=<foo> returns the expected result.
    if searchShakes == None:
        return "how did you get here?"
    else:
        newLine = 'Search results for %s:' % (searchShakes)
        print('Search results AGAIN for %s:' % (searchShakes))
        searchResultList = []
        searchResultList.append(newLine)
        for line in query_db("SELECT * FROM shakespearetext WHERE text_entry LIKE '%" + searchShakes + "%'"):
            searchResultList.append(newLine)
            #print
            #user['username'], 'has the id', user['user_id']
            return newLine + newLine

        # This SHOULD print entire list of search results
        #searchResultList = list(getSearchResultList(searchShakes, bill))
        # return (list(getSearchResultList(searchShakes,bill)))


def getSearchResultList(searchShakes, bill):
    # This code returns results for a search for a particular word:
    print('Search results for %s:' % (searchShakes))
    newLine = 'Search results for %s:' % (searchShakes)
    searchResultList = []
    searchResultList.append(newLine)
    for line in bill:
        if line['text_entry'].__contains__(searchShakes):
            print(line['speaker'], ':', line['text_entry'], '(from ', line['play_name'], ')')
            newLine = line['speaker'] + ": " + line['text_entry'] + " (from " + line['play_name'] + ")"
            searchResultList.append(newLine)
    return render_template('show_entries.html', entries=entries)
