# Modified from http://flask.pocoo.org/docs/0.11/tutorial/

# 1) Program queries art database, user selects picture // WORKS Can query Flickr and return results.
# 2) Program queries quote database, returns results, user selects quote // WORKS
# 2a) User can edit quote // WORKS
# 3) User triggers art/quote merger into new image// WORKS
# 4) User can edit/tweak result // TBA
# 5) User sends image to Twitter account:
#    a) User can Tweet text // WORKS
#    b) User can tweet image // WORKS

import os
import json, requests, sys, random
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from wtforms import RadioField, SubmitField,IntegerField,TextAreaField
from wtforms.validators import DataRequired
from flask_wtf import Form
import tweepy
import shutil
from PIL import Image, ImageDraw, ImageFont
import urllib.request

# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    # DATABASE=os.path.join(app.root_path, 'shakestweet.db'),
    # DATABASE=os.path.join(app.root_path, 'fnord'),
    DATABASE=os.path.join(app.root_path, 'globe.db'),
    DEBUG=True,
    SECRET_KEY='development key',
))
app.config.from_envvar('SHAKESTWEET_SETTINGS', silent=True)

class ImageTweakForm(Form):
    yfromtop     = IntegerField()
    color        = RadioField(choices=['White','Black','Red','Yellow'])
    verbiage = TextAreaField('To be or not to be')

class Flickr():
    def __init__(self, imagequery, imageResultList):
        #Sample Flickr search URL build from https://www.flickr.com/services/api/explore/flickr.photos.search
        # Adding "&license=7%2C8%2C9%2C10" restricts search to non-copyrighted images and United States Government works
        # TODO: This only works for a single-word search. Multiple words with spaces return an error.

        # Get user search terms from user input on shakestweet.html.
        searchImages = imagequery
        print(searchImages)
        flickr_api_key = open('static/secret/flickr_api_key.txt').read()
        flickerSearchURL = 'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key={}&license=7%2C8%2C9%2C10&tags={}&format=json&nojsoncallback=1'.format(flickr_api_key,searchImages)
        # fetchPhotoURL = 'https://farm%s.staticflickr.com/%s/%s_%s.jpg' % (farm, server, id, secret)

        #Search flickr for pictures
        flickrResponse = urllib.request.urlopen(flickerSearchURL)
        #get json back
        flickrResponseJSONString = flickrResponse.read().decode('UTF-8')
        flickrResponseJson = json.loads(flickrResponseJSONString)
        #Get first json object ('photos') which contains another json object ('photo') which is a json array

        # "total" tells you how many images the search found. The loop below selects all of them, capping it at 50.
        # TODO Break up the list; if more than 10 results, display 11-20 on a "See next 10 results" page
        jsonphotototal = int(flickrResponseJson['photos']['total'])
        if jsonphotototal > 50:
            jsonphotototal = 50
        for imageResult in range(0, jsonphotototal):
            jsonforphoto = flickrResponseJson['photos']['photo'][imageResult]
            #deal with this in the following way. vvvvvvv

            #Extract the secret, server, id and farm; which you need to construct another URL to request a specific photo
            #https://farm{farm-id}.staticflickr.com/{server-id}/{id}_{secret}.jpg
            secret = jsonforphoto['secret']
            id = jsonforphoto['id']
            server = jsonforphoto['server']
            farm = jsonforphoto['farm']

            print(jsonforphoto)  #Just checking we get the JSON we expect
            #TODO add error handing

            # fetchPhotoURL = 'https://farm%s.staticflickr.com/%s/%s_%s_m.jpg' % (farm, server, id, secret)
            # removing "_m" from above URL should return larger photos instead of thumbnails - although you can create URLs for both if you need them...
            fetchPhotoURL = 'https://farm%s.staticflickr.com/%s/%s_%s.jpg' % (farm, server, id, secret)
            print(fetchPhotoURL)   #Again, just checking

            #Reference: http://stackoverflow.com/questions/13137817/how-to-download-image-using-requests

            imageResultFileName = 'imageResult' + str(imageResult)
            imageResultList.append(imageResultFileName)
            imageResultFileNameStatic = 'static/images/imageResult' + str(imageResult) + '.jpg'
            #Read the response and save it as a .jpg. Use shutil to copy the stream of bytes into a file
            #What does 'with' mean? http://preshing.com/20110920/the-python-with-statement-by-example/
            resp = requests.get(fetchPhotoURL, stream=True)
            with open(imageResultFileNameStatic, 'wb') as out_file:
                shutil.copyfileobj(resp.raw, out_file)
            del resp



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

def update_tweetable(verbiage, image, quotechosen, imagechosen, quotelocked, imagelocked):
    db = get_db()
    cur = db.execute("SELECT * FROM tweetable")
    tweetdata = cur.fetchall()
    print(tweetdata[0]['verbiage'])
    db.execute("UPDATE tweetable SET verbiage=?, image=?, quotechosen=?, imagechosen=?, quotelocked=?, imagelocked=? WHERE id = 0",[verbiage, image, quotechosen, imagechosen, quotelocked, imagelocked])
    db.commit()
    cur = db.execute("SELECT * FROM tweetable")
    tweetdata = cur.fetchall()
    print(tweetdata[0]['verbiage'])

def update_tweetable_text(verbiage):
    db = get_db()
    db.execute("UPDATE tweetable SET verbiage=? WHERE id = 0",[verbiage])
    db.commit()

def update_tweetable_image(image):
    db = get_db()
    db.execute("UPDATE tweetable SET image=? WHERE id = 0",[image])
    db.commit()

def update_tweetable_quotechosen(quotechosen):
    db = get_db()
    db.execute("UPDATE tweetable SET quotechosen=? WHERE id = 0",[quotechosen])
    db.commit()

def update_tweetable_imagechosen(imagechosen):
    db = get_db()
    db.execute("UPDATE tweetable SET imagechosen=? WHERE id = 0",[imagechosen])
    db.commit()

def update_tweetable_quotelocked(quotelocked):
    db = get_db()
    db.execute("UPDATE tweetable SET quotelocked=? WHERE id = 0",[quotelocked])
    db.commit()

def update_tweetable_imagelocked(imagelocked):
    db = get_db()
    db.execute("UPDATE tweetable SET imagelocked=? WHERE id = 0",[imagelocked])
    db.commit()


def get_tweetable_text():
    db = get_db()
    cur = db.execute("SELECT * FROM tweetable")
    rosencrantz = cur.fetchall()
    guildenstern =  rosencrantz[0]['verbiage']
    return guildenstern

def get_tweetable_image():
    db = get_db()
    cur = db.execute("SELECT * FROM tweetable")
    rosencrantz = cur.fetchall()
    guildenstern =  rosencrantz[0]['image']
    return guildenstern

def get_tweetable_quotechosen():
    db = get_db()
    cur = db.execute("SELECT * FROM tweetable")
    rosencrantz = cur.fetchall()
    guildenstern = rosencrantz[0]['quotechosen']
    return guildenstern

def get_tweetable_imagechosen():
    db = get_db()
    cur = db.execute("SELECT * FROM tweetable")
    rosencrantz = cur.fetchall()
    guildenstern =  rosencrantz[0]['imagechosen']
    return guildenstern

def get_tweetable_quotelocked():
    db = get_db()
    cur = db.execute("SELECT * FROM tweetable")
    rosencrantz = cur.fetchall()
    guildenstern =  rosencrantz[0]['quotelocked']
    return guildenstern

def get_tweetable_imagelocked():
    db = get_db()
    cur = db.execute("SELECT * FROM tweetable")
    rosencrantz = cur.fetchall()
    guildenstern =  rosencrantz[0]['imagelocked']
    return guildenstern


# This is the app starting point, and the zero-state if user cancels and starts over
@app.route('/',methods = ['POST', 'GET'])
def start_here():
    # Gathers current SQL database tweet data.
    verbiage=get_tweetable_text()
    image = get_tweetable_image()
    imagechosen = get_tweetable_imagechosen()
    quotechosen = get_tweetable_quotechosen()
    quotelocked = get_tweetable_quotelocked()
    imagelocked = get_tweetable_imagelocked()
    update_tweetable(verbiage, image, quotechosen, imagechosen, quotelocked, imagelocked)
    return render_template('shakestweet.html', verbiage=verbiage, image=image, imagechosen=imagechosen, quotechosen=quotechosen, quotelocked=quotelocked, imagelocked=imagelocked)


@app.route('/searchplays')
def search_for_quotes():
    # This code returns results for a search for a particular word:
    print(request.args)
    searchShakes = request.args.get('playquery')

    # Any previous choice of quote is cancelled
    update_tweetable_text(" ")
    update_tweetable_quotechosen(False)
    update_tweetable_quotelocked(False)

    # This if-else prevents an error if user goes to /search webpage (searching for "None"). /search?query=<foo> returns the expected result.
    if searchShakes == None:
        return "how did you get here?"
    else:
        db = get_db()
        cur = db.execute("SELECT * FROM shakespearetext WHERE text_entry LIKE '%" + searchShakes + "%'")
        shakeslines = cur.fetchall()
    return render_template('quotesearch.html', shakeslines=shakeslines, searchShakes=searchShakes)


@app.route('/quotechosen')
def quote_chosen():
    lineID = request.args.get('quotechoice', '')
    flash('Quote chosen')
    db = get_db()
    cur = db.execute("SELECT * FROM shakespearetext WHERE line_id LIKE '%" + lineID + "%'")
    chosenShakesline = cur.fetchall()
    stringChosenShakesline =  chosenShakesline[0]['speaker'] + ': ' +  chosenShakesline[0]['text_entry'] + ' (from ' + chosenShakesline[0]['play_name'] + ')'
    update_tweetable_text(stringChosenShakesline)
    update_tweetable_quotechosen(True)
    verbiage = get_tweetable_text()
    image = get_tweetable_image()
    imagechosen = get_tweetable_imagechosen()
    quotechosen = get_tweetable_quotechosen()
    quotelocked = get_tweetable_quotelocked()
    imagelocked = get_tweetable_imagelocked()
    return render_template('shakestweet.html', verbiage=verbiage, image=image, imagechosen=imagechosen, quotechosen=quotechosen, quotelocked=quotelocked, imagelocked=imagelocked, lineID=lineID)

@app.route('/quotelocked')
def quote_locked():
    lockedquote = request.args.get('lockquote')
    flash('Quote locked')
    update_tweetable_text(lockedquote)
    update_tweetable_quotelocked(True)
    verbiage = get_tweetable_text()
    image = get_tweetable_image()
    imagechosen = get_tweetable_imagechosen()
    quotechosen = get_tweetable_quotechosen()
    quotelocked = get_tweetable_quotelocked()
    imagelocked = get_tweetable_imagelocked()
    return render_template('shakestweet.html', verbiage=verbiage, image=image, imagechosen=imagechosen, quotechosen=quotechosen, quotelocked=quotelocked, imagelocked=imagelocked)


@app.route('/searchimages')
def search_for_images():
    # This code returns results for a search for a particular word:
    print(request.args)
    searchImages = request.args.get('imagequery')

    # Any previous choice of image is cancelled
    update_tweetable_image("blank")
    update_tweetable_imagechosen(False)
    update_tweetable_imagelocked(False)

    # This if-else prevents an error if user goes to /search webpage (searching for "None"). /search?query=<foo> returns the expected result.
    if searchImages == None:
        return "how did you get here?"
    else:
        # imageList = imageResultList()
        imageList = []
        Flickr(searchImages,imageList)
        return render_template('imagesearch.html', searchImages = searchImages, imageList = imageList)

@app.route('/imagechosen')
def image_chosen():
    chosenImage = request.args.get('imagechoice', '')
    flash('Image chosen')
    update_tweetable_image(chosenImage)
    update_tweetable_imagechosen(True)
    verbiage = get_tweetable_text()
    image = get_tweetable_image()
    imagechosen = get_tweetable_imagechosen()
    quotechosen = get_tweetable_quotechosen()
    quotelocked = get_tweetable_quotelocked()
    imagelocked = get_tweetable_imagelocked()
    return render_template('shakestweet.html', verbiage=verbiage, image=image, imagechosen=imagechosen, quotechosen=quotechosen, quotelocked=quotelocked, imagelocked=imagelocked)

@app.route('/merge', methods=['GET', 'POST'])
def merge_image_and_text():
    flash('New image created')
    # TODO: Allow user to choose font size and color
    # TODO: Wrap text so it doesn't extend past right edge of image
    # TODO: Make default text larger and bolder

    # Default values
    verbiage = get_tweetable_text()
    yfromtop = 10
    colora = 255
    colorb = 255
    colorc = 255

    # TODO The program currently returns an error when I try to make changes to the merged image&text.
    # Changed values
    verbiage = request.form.get("verbiage", get_tweetable_text())
    yfromtop = request.form.get("yfromtop", "10")
    color = request.form.get("color", "White")
    if color == 'Yellow':
        colora = 255
        colorb = 255
        colorc = 0
    elif color == 'Black':
        colora = 0
        colorb = 0
        colorc = 0
    elif color == 'Red':
        colora = 255
        colorb = 0
        colorc = 0
    else:
        colora = 255
        colorb = 255
        colorc = 255

    image = get_tweetable_image()
    imageToMerge = 'static/images/' + image + '.jpg'

    # This code allows you to add text on top of an image. Modified from: https://pillow.readthedocs.io/en/3.3.x/reference/ImageDraw.html?highlight=text
    # get an image
    base = Image.open(imageToMerge).convert('RGBA')

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', base.size, (255, 255, 255, 0))

    # get a font
    # fnt = ImageFont.truetype('Pillow/Tests/fonts/FreeMono.ttf', 40)
    fnt = ImageFont.truetype('/Library/Fonts/Arial.ttf', 30)
    # fnt = ImageFont.load("arial.pil")
    # fnt = ImageFont.load_default()

    # get a drawing context
    d = ImageDraw.Draw(txt)

    # fetchPhotoURL = 'https://farm%s.staticflickr.com/%s/%s_%s.jpg' % (farm, server, id, secret)
    # draw text, half opacity
#    d.text((10, 10), "Hello", font=fnt, fill=(255, 255, 255, 128))
    # draw text, full opacity
    colora = int(colora)
    colorb = int(colorb)
    colorc = int(colorc)
    yfromtop=int(yfromtop)
    d.text((10, yfromtop),verbiage,font=fnt, fill=(colora,colorb,colorc, 255))
    # d.text((10, 10),verbiage,font=fnt, fill=(255,255,255,255))

    out = Image.alpha_composite(base, txt)
    # out.show()
    out.save('static/images/merged.jpg')

    # TODO update database to include separate field for merged image, so you don't have to overwrite original
    # update_tweetable_image('merged')
    mergedimage = 'merged'
    verbiage = get_tweetable_text()
    image = get_tweetable_image()
    imagechosen = get_tweetable_imagechosen()
    quotechosen = get_tweetable_quotechosen()
    quotelocked = get_tweetable_quotelocked()
    imagelocked = get_tweetable_imagelocked()
    return render_template('merge.html', verbiage=verbiage, image=image, imagechosen=imagechosen, quotechosen=quotechosen, quotelocked=quotelocked, imagelocked=imagelocked,mergedimage=mergedimage, yfromtop=yfromtop)

@app.route('/tweak', methods=['POST'])
def tweak():
    #TODO This section, governing image tweaks, does not work yet
    # form = ImageTweakForm(request.POST)
    # if request.method == 'POST':
    # Changed values
    # verbiage = request.form.get("verbiage", get_tweetable_text())
    # yfromtop = request.form.get("yfromtop", "10")
    # color = request.form.get("color", "White")
    # if color == 'Yellow':
    #     colora = 255
    #     colorb = 255
    #     colorc = 0
    # elif color == 'Black':
    #     colora = 0
    #     colorb = 0
    #     colorc = 0
    # elif color == 'Red':
    #     colora = 255
    #     colorb = 0
    #     colorc = 0
    # else:
    #     colora = 255
    #     colorb = 255
    #     colorc = 255
    return redirect(url_for('merge'))


@app.route('/mergelock')
def mergelock():
    # update_tweetable_image('merged')
    mergedimage = 'merged'
    update_tweetable_imagelocked(True)
    verbiage = get_tweetable_text()
    image = get_tweetable_image()
    imagechosen = get_tweetable_imagechosen()
    quotechosen = get_tweetable_quotechosen()
    quotelocked = get_tweetable_quotelocked()
    imagelocked = get_tweetable_imagelocked()
    return render_template('shakestweet.html', verbiage=verbiage, image=image, imagechosen=imagechosen, quotechosen=quotechosen, quotelocked=quotelocked, imagelocked=imagelocked, mergedimage=mergedimage)




@app.route('/cancel')
def cancel():
    # Updates SQL database to clear the current tweet data.
    verbiage = " "
    image = "blank"
    imagechosen = False
    quotechosen = False
    quotelocked = False
    imagelocked = False
    update_tweetable(verbiage, image, quotechosen, imagechosen, quotelocked, imagelocked)
    flash('Thou hast canceled! Try again.')
    return redirect(url_for('start_here'))


@app.route('/tweet', methods=['POST'])
def tweet():
    twitter_consumer_key = open('static/secret/twitter_consumer_key.txt').read()
    twitter_consumer_secret = open('static/secret/twitter_consumer_secret.txt').read()
    twitter_access_token = open('static/secret/twitter_access_token.txt').read()
    twitter_access_token_secret = open('static/secret/twitter_access_token_secret.txt').read()
    auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_consumer_secret)
    auth.set_access_token(twitter_access_token, twitter_access_token_secret)
    api = tweepy.API(auth)

    mergedimage = 'merged'
    verbiage = get_tweetable_text()
    image = get_tweetable_image()

    # TODO Truncate if verbiage is longer than 140 characters
    tweetThisText = verbiage
    tweetThisImage = 'static/images/merged.jpg'
    # The line below does the actual Tweeting.
    # api.update_status(tweetThisText) # for text-only tweets
    api.update_with_media(tweetThisImage,tweetThisText)
    flash('Tweet posted!')

    # reset everything to zero and start again
    verbiage = " "
    image = "blank"
    imagechosen = False
    quotechosen = False
    quotelocked = False
    imagelocked = False
    update_tweetable(verbiage, image, quotechosen, imagechosen, quotelocked, imagelocked)
    return redirect(url_for('start_here'))




if __name__ == '__main__':
    app.run()
