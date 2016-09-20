import sqlite3, requests, json

def main():
    # JSON to SQLite3 converter modified from here: https://gist.github.com/atsuya046/7957165#file-jsontosqlite-py
    # This downloads the JSON data containing Shakespeare texts from my website
    url = 'http://christopherbahn.com/programming/will_play_text_python.json'
    response = requests.get(url)
    response.raise_for_status()
    # Load JSON data into a Python variable.
    bill = json.loads(response.text, strict=False)

    print(bill[1200]["text_entry"])

    line_id = bill[0]["line_id"]
    play_name = bill[0]["play_name"]
    speech_number = bill[0]["speech_number"]
    line_number = bill[0]["line_number"]
    speaker = bill[0]["speaker"]
    text_entry = bill[0]["text_entry"]
    data = [line_id, play_name, speech_number, line_number, speaker, text_entry]

#    if not hasattr(g, 'sqlite_db'):
#     db = sqlite3.connect('fnord') # This was the working db up to 9/30
    db = sqlite3.connect('globe.db')  # This is the working db as of 9/30
#    rv.row_factory = sqlite3.Row

    db.execute('drop table if exists shakespearetext')
    db.execute('create table shakespearetext(line_id integer primary key, play_name text not null, speech_number text not null, line_number text not null, speaker text not null, text_entry text not null)')
    for stratford in range(1, 111396):
        line_id = bill[stratford]["line_id"]
        play_name = bill[stratford]["play_name"]
        speech_number = bill[stratford]["speech_number"]
        line_number = bill[stratford]["line_number"]
        speaker = bill[stratford]["speaker"]
        text_entry = bill[stratford]["text_entry"]
        data = [line_id, play_name, speech_number, line_number, speaker, text_entry]
        db.execute('insert into shakespearetext (line_id, play_name, speech_number, line_number, speaker, text_entry) values (?, ?, ?, ?, ?, ?)', data)
        db.commit()
        print(str(bill[stratford]["line_id"]) + ": " + bill[stratford]["text_entry"])

    db.execute('drop table if exists tweetable')
    db.execute('create table tweetable(id integer primary key, verbiage text not null, image text not null, quotechosen boolean, imagechosen boolean, quotelocked boolean, imagelocked boolean)')
    id = 0
    verbiage = "The rest is silence."
    image = "blank"
    quotechosen = False
    imagechosen = False
    quotelocked = False
    imagelocked = False
    data = [id, verbiage, image, quotechosen, imagechosen, quotelocked, imagelocked]
    db.execute('insert into tweetable (id, verbiage, image, quotechosen, imagechosen, quotelocked, imagelocked) values (?, ?, ?, ?, ?, ?, ?)', data)
    db.commit()
    print(image)

main()
