"""Script for downloading word data from various sources.

"""
import sys
import codecs
import src.functions as fn
import os

if __name__ == '__main__':
    # Set output directory
    dirname = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

    # Test data
    # words = ['egentligen', 'en motspelare', 'annorlunda', 'en lagkamrat', 'ett stycke', 'handlar om']
    with codecs.open(sys.argv[1], 'r', 'utf-8') as f:
        words = f.read().split('\r\n')

    # Get translation and sample sentence(s)
    scraped_data = fn.get_translation(words, True, dirname)
    print(scraped_data)

    for word_dict in scraped_data['words']:
        word = word_dict['word']
        # Create word directory for storing downloaded and generated data
        word_file = word.replace(' ', '_')
        word_dir = os.path.join(dirname, word_file)
        try:
            os.mkdir(word_dir)
            print("Directory ", word_dir, " Created ")
        except FileExistsError:
            print("Directory ", word_dir, " already exists")

        # Download the word's top-most search result from google images
        fn.download_google_search_image(query_string=word, thumbnail=True, directory=word_dir)

        # Generate audio file of word in native language
        fn.generate_mp3_file(word, os.path.join(word_dir, '{0}.mp3'.format(word_file)))
        # Generate audio file of example sentences if any
        sentences = word_dict['sentences']['source']
        for i in range(len(sentences)):
            fn.generate_mp3_file(sentences[i], os.path.join(word_dir, '{0}_sentence_{1}.mp3'.format(word_file, i + 1)))
