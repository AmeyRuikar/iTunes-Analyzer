import xml.etree.ElementTree as ET
import sqlite3

# run mdfind on a terminal and get the path to iTUNES file (.xml)   
import subprocess

conn = sqlite3.connect('trackdb.sqlite')
cur = conn.cursor()

# Make some fresh tables using executescript()
cur.executescript('''
DROP TABLE IF EXISTS Artist;
DROP TABLE IF EXISTS Album;
DROP TABLE IF EXISTS Genre;
DROP TABLE IF EXISTS Track;

CREATE TABLE Artist (
    id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name    TEXT UNIQUE
);


CREATE TABLE Genre (
    id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name    TEXT UNIQUE
);

CREATE TABLE Album (
    id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    artist_id  INTEGER,
    title   TEXT UNIQUE
);

CREATE TABLE Track (
    id  INTEGER NOT NULL PRIMARY KEY 
        AUTOINCREMENT UNIQUE,
    title TEXT  UNIQUE,
    album_id  INTEGER,
    genre_id  INTEGER,
    len INTEGER, rating INTEGER, count INTEGER
);
''')


#start a new process and run mdfind command
p = subprocess.Popen(["mdfind","iTunes Music Library.xml"],  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
filePath, err = p.communicate()
if(err == ''):
    fname = filePath.split('\n')[0]

if ( len(fname) < 1 ) : fname = 'iTunes Music Library.xml'

def lookup(d, key):
    found = False
    for child in d:
        if found : return child.text
        if child.tag == 'key' and child.text == key :
            found = True
    return None

stuff = ET.parse(fname)
all = stuff.findall('dict/dict/dict')
print 'Dict count:', len(all)
cnt = 0;

for entry in all:
    if ( lookup(entry, 'Track ID') is None ) : continue

    name = lookup(entry, 'Name')
    artist = lookup(entry, 'Artist')
    album = lookup(entry, 'Album')
    count = lookup(entry, 'Play Count')
    rating = lookup(entry, 'Rating')
    length = lookup(entry, 'Total Time')
    genre = lookup(entry, 'Genre')

    if name is None or artist is None: 
        continue
    
    if album is None:
        album = 0;
        
    if rating is None:
        rating = 0;
    
    if genre is None:
        genre = 0;

    cnt = cnt + 1
    print cnt, "->"
    print name,  count, rating, length, genre

    cur.execute('''INSERT OR IGNORE INTO Artist (name) 
        VALUES ( ? )''', ( artist, ) )
    cur.execute('SELECT id FROM Artist WHERE name = ? ', (artist, ))
    artist_id = cur.fetchone()[0]

    cur.execute('''INSERT OR IGNORE INTO Album (title, artist_id) 
        VALUES ( ?, ? )''', ( album, artist_id ) )
    cur.execute('SELECT id FROM Album WHERE title = ? ', (album, ))
    album_id = cur.fetchone()[0]
    
    cur.execute('''INSERT OR IGNORE INTO Genre (name) 
        VALUES ( ? )''', ( genre, ) )
    cur.execute('SELECT id FROM Genre WHERE name = ? ', (genre, ))
    genre_id = cur.fetchone()[0]

    cur.execute('''INSERT OR REPLACE INTO Track
        (title, album_id, genre_id, len, rating, count) 
        VALUES ( ?, ?, ?, ?, ?, ? )''', 
        ( name, album_id, genre_id, length, rating, count ) )

    conn.commit()
    
    
    
print "\n\nAnalysis\n\n"

# out of loop analysis    
cur.execute('''select title from Track 
                where count =  (select MAX(count) from Track);''');
    
mostPlayed = cur.fetchone()[0]
    
print "\n Most played song ever -> ", mostPlayed


cur.execute('''select title from Track 
                where count =  (select MIN(count) from Track);''');
    
leastPlayed = cur.fetchone()[0]
    
print "\n least played song ever -> ", leastPlayed
# lets try and use this fact

#favorite artist

cur.execute('''select name from artist ,
                (select artist_id, MAX(col) from 
                (select artist_id, count(*) as col from album
                group by artist_id)) 
                where id = artist_id;
            ''');

favouriteArtist = cur.fetchone()[0]
print "\n Fav Artist: ", favouriteArtist
    
    
    
#favourite genre

cur.execute('''select name from 
                Genre,(select genre_id, MAX(CNT) from
                (  
                select genre_id, count(*) AS CNT from track
                group by genre_id)) 
                where genre_id = id and name <> 0;
            ''');

if cur.fetchone() != None:
    favouriteGenre = cur.fetchone()[0]
    print "\n Fav Genre: ", favouriteGenre
    
