import src.functions as fn
import os
import genanki

basic_model = genanki.Model(
    345678,
    'Basic',
    fields=[
        {'name': 'Swedish'},
        {'name': 'English'},
        {'name': 'Image'},
        {'name': 'Audio'}
        #        {'name': 'Sentence_sv'},
        #        {'name': 'Sentence_en'}
    ],
    templates=[
        {
            'name': 'Word',
            'qfmt': '<div class=swedish>'
                    '{{Swedish}}'
                    '</div>',
            'afmt': '<div class=swedish>'
                    '{{FrontSide}}'
                    '</div>'
                    '<hr id="answer">'
                    '{{English}}'
                    '<br>'
                    '<div class=pic>'
                    '{{Image}}'
                    '</div>'
                    '<div class=normal>'
                    '{{Audio}}'
                    '</div>',
        },
    ],
)


def generate_deck(scraped_data, data_dir):
    deck = genanki.Deck(123456, 'SFI_words')
    package = genanki.Package(deck)

    media_files = []
    for word_dict in scraped_data['words']:
        word = word_dict['word']
        translation = word_dict['translation']
        # sentences_source = word_dict['sentences']['source']
        # sentences_translated = word_dict['sentences']['translation']

        # if not sentences_source:
        #     sentence_source = sentences_source[0]
        #     sentence_translated = sentences_translated[0]
        # else:
        #     sentence_source = ''
        #     sentence_translated = ''

        # Get word directory where files are stored
        word_file = word.replace(' ', '_')
        word_dir = os.path.join(data_dir, word_file)

        # Media files in current word directory
        word_files = [os.path.join(data_dir, word_file, f) for f in os.listdir(word_dir) if os.path.isfile(os.path.join(word_dir, f))]

        media_files = media_files + word_files

        note = genanki.Note(basic_model,
                            [word,
                             translation,
                             '<img src="{0}.jpg">'.format(word_file),
                             '[sound:{0}.mp3]'.format(word_file)
                             ]
                            )
        deck.add_note(note)

    package.media_files = media_files
    package.write_to_file('SFI_words.apkg')


if __name__ == '__main__':
    # Set multimedia directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

    # Words from which to create cards
    words = ['egentligen', 'motspelare', 'annorlunda', 'lagkamrat']

    # Get translation and sample sentence(s)
    scraped_data = fn.get_translation(words)

    generate_deck(scraped_data, data_dir)
