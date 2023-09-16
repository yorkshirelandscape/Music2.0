from lyricsgenius import Genius
from cobe.brain import Brain
from decouple import config
import sys
import re
import json
import os

# Parse arguments, Pt 1
arg_cnt = len(sys.argv)
search_term = sys.argv[1]

# Instantiate Genius and define search parameters
genius = Genius(config('GENIUS_TOKEN'))
genius.remove_section_headers = True
genius.skip_non_songs = True

exc_terms = [ "acoustic", "remix", "mix$", "live$", "live at", 
              "live in", "demo$", "version", "DVD", "edit$",
              "booklet", "album", "live from", "extended" ]

# Grab existing song titles to add to exclusion list
if os.path.isfile( 'lyrics.json' ):
    with open( 'lyrics.json', 'r' ) as file:
        artists = json.load( file )
    titles = []
    found_artist = next( ( artist for artist in artists if artist[ "artist" ] == search_term ), None )
    if found_artist:
        for s in found_artist[ "songs" ]:
            titles.append( s["title"] )
        for s in titles:
            exc_terms.append( s )

genius.excluded_terms = exc_terms

# Parse argument, Pt 2
if arg_cnt == 2: 
    artist = genius.search_artist( search_term )
elif arg_cnt >= 3:
    search_max = int( sys.argv[2] )
    artist = genius.search_artist( search_term, max_songs = search_max )
else: 
    sys.exit('Arguments: search_artist [max_songs]')

# Uncomment to save full output to disk.
# artist.save_lyrics( overwrite = True )

# Remove ads and insert missing periods at the end of each line
songs = []
for s in artist.songs:
    songs.append( 
        {   'title': s.title,
            'lyrics': 
                re.sub( r'(^.*Get tickets as low as.*$|^.*You might also like.*$|[0-9]*Embed$)', '',
                    re.sub( r'^.*$', '',
                        s.lyrics.replace( '\n\n', '\n' )
                            .replace( '\n', '.\n' )
                            .replace( '..', '.' ),
                        1,
                        re.MULTILINE
                    ),
                    0,
                    re.MULTILINE
                )
        }
    )

artist_dict = { 'artist': artist.name, 'songs': songs }

# Save lyrics by artist to JSON file
if not os.path.isfile( 'lyrics.json' ):
    with open( 'lyrics.json', 'w' ) as file:
        file.write( '[]' )

with open( 'lyrics.json', 'r+' ) as file:
        artists = json.load( file )
        existing_artist = next( ( artist for artist in artists if artist[ "artist" ] == search_term ), None )
        if existing_artist:
            for s in artist_dict[ 'songs' ]:
                existing_artist[ 'songs' ].append( s )
        else:
            artists.append( artist_dict )
        file.seek( 0 )
        json.dump( artists, file, indent = 4 )


# Get just the lyrics
output = ''
for s in songs:
    output += s.get('lyrics')
# print( output )

# Write them to a temporary file
with open( 'buffer.txt', 'a+' ) as f:
    f.write( output )
    f.seek( 0 )
    # buffer = f.read()
    # print( buffer )

# Call cobe from the command line to learn from the temp file, then delete it
os.system( 'poetry run cobe -b brain.brn learn buffer.txt' )
os.remove( 'buffer.txt' )

# Open or create the brain and reply to a test question.
brain = Brain( 'brain.brn' )
reply = brain.reply( 'What''s black?' )
print( reply )
