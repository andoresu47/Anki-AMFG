import codecs
import json
import re
import sys

import src.functions as fn
import os
import genanki

word_model = genanki.Model(
    345175,
    'noun',
    fields=[
        {'name': 'Swedish'},
        {'name': 'Gender'},
        {'name': 'English'},
        {'name': 'Image'},
        {'name': 'Audio'}
    ],
    templates=[
        {
            'name': 'swe_eng_noun',
            'qfmt': '<span style="font-family: Liberation Sans; font-size: 40px;  ">{{Swedish}}</span>',
            'afmt': '<div class=swedish>{{FrontSide}}</div>'
                    '<hr id="answer">'
                    '<span style="font-family: Liberation Sans; font-size: 40px;  ">'
                    '{{English}}'
                    '<br>'
                    '<div class=pic>'
                    '{{Image}}'
                    '</div>'
                    '<div class=normal>'
                    '{{Audio}}'
                    '</div>'
                    '</span>',
        },
        {
            'name': 'eng_swe_noun',
            'qfmt': '<span style="font-family: Liberation Sans; font-size: 40px;  ">' 
                    '<div class=english>{{English}}</div>'
                    '<div class=swedish>{{type:Swedish}}</div>'
                    '<br>'
                    '<div class=pic>{{Image}}</div>'
                    '</span>',
            'afmt': '<span style="font-family: Liberation Sans; font-size: 40px;  ">'
                    '<div class=english>{{English}}</div>'
                    '<hr id="answer">'
                    '<div class=swedish>{{type:Swedish}}</div>'
                    '<br>'
                    '<div class=pic>{{Image}}</div>'
                    '<div class=normal>{{Audio}}</div>'
                    '</span>',
        },
        {
            'name': 'swe_eng_audio_noun',
            'qfmt': '<span style="font-family: Liberation Sans; font-size: 40px;  ">' 
                    '<div class=normal>Listen. {{Audio}}</div>'
                    '</span>',
            'afmt': '<span style="font-family: Liberation Sans; font-size: 40px;  ">' 
                    '<div class=normal>{{FrontSide}}</div>'
                    '<hr id="answer">'
                    '<div class=swedish>{{Swedish}}</div>'
                    '<br>'
                    '<div class=english>{{English}}</div>'
                    '<br>'
                    '<div class=pic>{{Image}}</div>'
                    '</span>',
        },
    ],
    css=""".card {
 font-family: arial;
 font-size: 20px;
 text-align: center;
 color: black;
 background-color: white;
}

.card1 { background-color: #ffffff; }
.card2 { background-color: #ffffff; }"""
)

sentence_model = genanki.Model(
    345671,
    'noun_sentence',
    fields=[
        {'name': 'Swedish'},
        {'name': 'Gender'},
        {'name': 'English'},
        {'name': 'Image'},
        {'name': 'Audio'},
        {'name': 'Sentence_sv'},
        {'name': 'Sentence_en'}
    ],
    templates=[
        {
            'name': 'swe_eng_sentence',
            'qfmt': '<span style="font-family: Liberation Sans; font-size: 40px;  ">' 
                    '<div class=swedish>{{Sentence_sv}}</div>'
                    '</span>',
            'afmt': '<span style="font-family: Liberation Sans; font-size: 40px;  ">'
                    '<div class=swedish>{{FrontSide}}</div>'
                    '<hr id="answer">'
                    '<div class=english>{{Sentence_en}}</div>'
                    '<br>'
                    '<div class=swe_eng>{{Swedish}} -- {{English}}</div>'
                    '<br>'
                    '<div class=pic>{{Image}}</div>'
                    '<div class=normal>{{Audio}}</div>'
                    '</span>',
        },
        {
            'name': 'swe_eng_audio_sentence',
            'qfmt': '<span style="font-family: Liberation Sans; font-size: 40px;  ">' 
                    '<div class=normal>Listen. {{Audio}}</div>'
                    '</span>',
            'afmt': '<span style="font-family: Liberation Sans; font-size: 40px;  ">' 
                    '<div class=swedish>{{FrontSide}}</div>'
                    '<hr id="answer">'
                    '<div class=swedish>{{Sentence_sv}}</div>'
                    '<br>'
                    '<div class=english>{{Sentence_en}}</div>'
                    '<br>'
                    '<div class=swe_eng>{{Swedish}} -- {{English}}</div>'
                    '<br>'
                    '<div class=pic>{{Image}}</div>'
                    '</span>',
        },
    ],
    css=""".card {
 font-family: arial;
 font-size: 20px;
 text-align: center;
 color: black;
 background-color: white;
}

.card1 { background-color: #ffffff; }
.card2 { background-color: #ffffff; }"""
)


def generate_deck(scraped_data, data_dir):
    deck = genanki.Deck(123456, 'SFI_words')
    package = genanki.Package(deck)

    media_files = []
    for word_dict in scraped_data['words']:
        word = word_dict['word']
        gender = word_dict['gender']
        translation = word_dict['translation']
        sentences_source = word_dict['sentences']['source']
        sentences_translated = word_dict['sentences']['translation']

        if sentences_source:
            sentence_source = sentences_source[0]
            sentence_translated = sentences_translated[0]
        else:
            sentence_source = ''
            sentence_translated = ''

        # Get word directory where files are stored
        word_file = word.replace(' ', '_')
        word_dir = os.path.join(data_dir, word_file)

        # Media files in current word directory
        word_files = [os.path.join(data_dir, word_file, f) for f in os.listdir(word_dir) if
                      os.path.isfile(os.path.join(word_dir, f))]

        media_files = media_files + word_files

        word_notes = genanki.Note(word_model,
                                  [word,
                                   gender,
                                   translation,
                                   '<img src="{0}.jpg">'.format(word_file),
                                   '[sound:{0}.mp3]'.format(word_file)
                                   ]
                                  )

        deck.add_note(word_notes)

        if sentences_source:
            score, start_idx, end_idx, _ = fn.get_score_and_substring(word, sentence_source.lower())
            # If word does appear in sentence, then it gets bold-faced
            if score > 0.5:
                # Identify full words within best word match indices
                spaces = [m.start() for m in re.finditer(' ', sentence_source)]
                start_idx = fn.get_start_idx(spaces, start_idx)
                end_idx = fn.get_end_idx(spaces, end_idx - 1, len(sentence_source)) + 1

                sentence_start = sentence_source[:start_idx]
                sentence_word = sentence_source[start_idx:end_idx]
                sentence_end = sentence_source[end_idx:]
                sentence_source = '{0}<b>{1}</b>{2}'.format(sentence_start, sentence_word, sentence_end)

            sentence_notes = genanki.Note(sentence_model,
                                          ['<b>{0}</b>'.format(word),
                                           gender,
                                           translation,
                                           '<img src="{0}.jpg">'.format(word_file),
                                           '[sound:{0}_sentence_1.mp3]'.format(word_file),
                                           sentence_source,
                                           sentence_translated
                                           ]
                                          )
            deck.add_note(sentence_notes)

    package.media_files = media_files
    package.write_to_file('SFI_words.apkg')


if __name__ == '__main__':
    # Set multimedia directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

    # Words from which to create cards
    # words = ['egentligen', 'en motspelare', 'annorlunda', 'en lagkamrat', 'ett stycke', 'handlar om']
    with codecs.open(sys.argv[1], 'r', 'utf-8') as f:
        words = f.read().split('\r\n')

    # Get translation and sample sentence(s)
    file_path = os.path.join(data_dir, 'data.json')
    if os.path.isfile(file_path):
        with codecs.open(file_path, 'r', 'utf-8') as json_file:
            try:
                scraped_data = json.load(json_file)

            except Exception as e:
                print(e)
                scraped_data = fn.get_translation(words, data_dir)
    else:
        scraped_data = fn.get_translation(words, True, data_dir)

    generate_deck(scraped_data, data_dir)
