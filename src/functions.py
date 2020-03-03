from src.folkets_lexikon_translate import FolketsLexikonScraper, LookupException
from googletrans import Translator
from google_speech import Speech
import src.download_google_images as dgi
import re
import traceback


def get_translation(words, example_sentences=True):
    """ Function to scrape folkets-lexikon dictionary data for a given word translation.
    If unsuccessful, gets translation from google translate.
    """
    data = {"words": []}
    folkets_lexikon_scraper = FolketsLexikonScraper()
    try:
        for elem in words:
            # Get word and gender if noun
            split_word = elem.split(' ')
            gender = ''
            if split_word[0] == 'en' or split_word[0] == 'ett':
                gender = split_word[0]
                word = ' '.join(split_word[1:])
            else:
                word = elem

            word_dict = {"word": word, "gender": gender}

            try:
                raw_text = folkets_lexikon_scraper.get_query_data(word)
                word_translation = extract_translation(raw_text)
                word_type = extract_type(raw_text)

                word_dict["translation"] = word_translation
                word_dict["type"] = word_type

                if example_sentences:
                    sentences, sentence_translations = extract_sentences(raw_text)
                    word_dict["sentences"] = {"source": sentences, "translation": sentence_translations}

            except LookupException as e:
                print(e)
                print("Getting translation from Google Translate")
                translator = Translator()
                translation = translator.translate(word, src='sv', dest='en')
                word_dict["translation"] = translation.text

                if example_sentences:
                    word_dict["sentences"] = {"source": [], "translation": []}

            finally:
                data["words"].append(word_dict)

        return data

    except Exception as e:
        traceback.print_exc()

    finally:
        folkets_lexikon_scraper.close_browser()


def extract_translation(raw_text):
    split_text = raw_text.split('\n')
    return ",".join(split_text[0].split(',')[1:]).strip()


def extract_type(raw_text):
    split_text = raw_text.split('\n')
    split_description = split_text[0].split(',')

    return split_description[0].split(' ')[-1].strip()


def extract_sentences(raw_text):
    try:
        idx = raw_text.index('Example:')
        examples_raw = raw_text[idx:]

        # Matches what is in between parenthesis (english translation)
        translations = re.findall('(?<=\()(.*)(?=\))', examples_raw)
        # Matches what is after Example and linebreak but not english translation
        sentences = re.findall('(?:(?<=Example: )|(?<=\n))(.+)(?= \()', examples_raw)

        # Remove any trailing whitespaces
        translations = [item.strip() for item in translations]
        sentences = [item.strip() for item in sentences]

        return sentences, translations

    except ValueError as e:
        print("No example sentences found.")
        return [], []


def generate_mp3_file(text, file_path, language='sv'):
    speech = Speech(text, language)
    speech.save(file_path)


def download_google_search_image(query_string, thumbnail, directory):
    urls = dgi.get_image_urls(query_string)
    dgi.save_top_result(query_string, urls, thumbnail, directory)
