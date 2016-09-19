# Modified from http://flask.pocoo.org/docs/0.11/tutorial/

# ORDER OF BATTLE:
# Program queries art database, user selects picture // WORKS, not yet merged into main program
# Program queries quote database, returns results, user selects quote // WORKS, now needs to send data to tweeting section
# User triggers art/quote merger into new image// WORKS, not yet merged into main program
# User accepts merged image, or makes tweaks until result is satisfactory // TBA
# User sends image to Twitter account: // WORKS, not yet merged into main program

import os
import json, requests, sys, random
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from wtforms import RadioField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import Form
import tweepy

# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    # DATABASE=os.path.join(app.root_path, 'shakestweet.db'),
    DATABASE=os.path.join(app.root_path, 'fnord'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin', #for Twitter, s/b os.path.join(app.root_path, '/static/secret/twitter_usrname'),
    PASSWORD='default'#for Twitter, s/b os.path.join(app.root_path, '/static/secret/twitter_pwd'),
))
app.config.from_envvar('SHAKESTWEET_SETTINGS', silent=True)
twitter_consumer_key = open('static/secret/twitter_consumer_key.txt').read()
twitter_consumer_secret = open('static/secret/twitter_consumer_secret.txt').read()
twitter_access_token = open('static/secret/twitter_access_token.txt').read()
twitter_access_token_secret = open('static/secret/twitter_access_token_secret.txt').read()

auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_consumer_secret)
auth.set_access_token(twitter_access_token, twitter_access_token_secret)

api = tweepy.API(auth)


class SimpleForm(Form):
    example = RadioField('Quotes', choices=[('value','description'),('value_two','whatever')])
    submit = SubmitField('Choose selected quote')

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
def show_entries():
    db = get_db()
    cur = db.execute('select title, text from entries order by id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)


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

# TODO Below this line is incomplete stuff
@app.route('/start',methods = ['POST', 'GET'])
def main_navigation():
    # TODO get the buttons working http://stackoverflow.com/questions/19794695/flask-python-buttons
    return render_template('shakestweet.html', data="hello!!")
    # if 'quotechosen' in request.form['submit']:
    #     return render_template('shakestweet.html', data="hello!!")
    # elif 'newquotesearch' in request.form['submit']:
    #     return render_template('shakestweet.html', data="hey there!!")
    # else:
    #     return render_template('shakestweet.html', data="hello!!")
#  if request.form.validate_on_submit():
#     if 'quotechosen' in request.form:
#         return render_template('shakestweet.html', data="You have chosen a quote!")
#     elif 'newquotesearch' in request.form:
#         return render_template('shakestweet.html', data="hello!!")
#
#     if request.method == 'POST':
#         if request.form['submit'] == 'Choose selected quote':
#             return render_template('shakestweet.html', data="You have chosen a quote!")
#         elif request.form['submit'] == 'New search':
#             return render_template('shakestweet.html', data="hello!!")
#     #     else:
#     #         pass  # unknown
#     elif request.method == 'GET':
#         return render_template('shakestweet.html', data="hellofdsuhfdsuhfsdufsd!!")


@app.route('/searchplays')
def search_for_quotes():
    # This code returns results for a search for a particular word:
    print(request.args)
    searchShakes = request.args.get('playquery')
    # This if-else prevents an error if user goes to /search webpage (searching for "None"). /search?query=<foo> returns the expected result.
    if searchShakes == None:
        return "how did you get here?"
    elif searchShakes == 'banana':
            return "Yes, we have no bananas"
    else:
        db = get_db()
        cur = db.execute("SELECT * FROM shakespearetext WHERE text_entry LIKE '%" + searchShakes + "%'")
        shakeslines = cur.fetchall()

        radiofieldChoices = []
        rfChoices = []
        # for line in shakeslines:
        #     radiofieldValue = ['line_id']
        #     # radiofieldQuote = ['speaker'] + ': ' + ['text_entry'] + '(from ' + ['play_name'] + ')'
        #     radiofieldQuote = 'FORSOOTH'
        #     radiofieldChoices.append([radiofieldValue, radiofieldQuote])
        # # rfChoices = RadioField('Label', choices=[radiofieldChoices])
        # rfChoices = SimpleForm('Quotes', choices=[(radiofieldChoices)])
        # if rfChoices.validate_on_submit():
        #     return render_template('quotesearch.html', shakeslines=shakeslines, searchShakes=searchShakes, quotechosen=False, radiofieldChoices=radiofieldChoices, rfChoices=rfChoices)
        # else:
        #     return render_template('quotesearch.html', shakeslines=shakeslines, searchShakes=searchShakes, quotechosen=False, radiofieldChoices=radiofieldChoices, rfChoices=rfChoices)
        return render_template('quotesearch.html', shakeslines=shakeslines, searchShakes=searchShakes, quotechosen=False, radiofieldChoices=radiofieldChoices, rfChoices=rfChoices)


@app.route('/quotechosen')
def quote_chosen():
    lineID = request.args.get('quotechoice', '')
    flash('You chose line #' + lineID)
    db = get_db()
    cur = db.execute("SELECT * FROM shakespearetext WHERE line_id LIKE '%" + lineID + "%'")
    chosenShakesline = cur.fetchall()
    return render_template('shakestweet.html', data="You have chosen a quote!", quotechosen=True, lineID=lineID, chosenShakesline = chosenShakesline)

@app.route('/newsearch')
def new_search_for_quotes():
    return render_template('shakestweet.html', data="You have cancelled your text search!!", quotechosen=False)

@app.route('/tweet')
def tweet():
    chosenShakesline = request.args.get('chosenShakesline')
    api = tweepy.API(auth)
    # The line below does the actual Tweeting.
    # api.update_status('Tomorrow and tomorrow and tomorrow...')
    api.update_status(chosenShakesline)

    public_tweets = api.home_timeline()
    for tweet in public_tweets:
        print(tweet.text)



# TODO Add the system for getting photos from Flickr

if __name__ == '__main__':
    app.run()
