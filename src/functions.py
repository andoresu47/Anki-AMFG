import codecs
import os
import urllib
from urllib.error import HTTPError
import requests
from src.folkets_lexikon_translate import FolketsLexikonScraper, LookupException
from googletrans import Translator
from google_speech import Speech
import src.download_google_images as dgi
import re
import traceback
import json
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from difflib import SequenceMatcher

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 ' \
             'Safari/537.36 '
headers = {'User-Agent': USER_AGENT}


def get_translation(words, example_sentences=True, json_dump_dir=None):
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
                raw_texts, orders = folkets_lexikon_scraper.get_query_data(word)
                translations = [extract_translation(raw_text, order) for raw_text, order in zip(raw_texts, orders)]
                types = [extract_type(raw_text) for raw_text in raw_texts]

                row_sections = [get_all_sections(row) for row in raw_texts]

                if example_sentences:
                    sentence_rows = [extract_sentences(get_section(sections, 'example'), order)
                                     for sections, order in zip(row_sections, orders)]
                    best_index = find_best_result(word, sentence_rows)

                    word_dict["translation"] = translations[best_index]
                    word_dict["type"] = types[best_index]

                    word_dict["sentences"] = {"source": sentence_rows[best_index][0],
                                              "translation": sentence_rows[best_index][1]}

                else:
                    word_translation = extract_translation(raw_texts[0], orders[0])
                    word_type = extract_type(raw_texts[0])

                    word_dict["translation"] = word_translation
                    word_dict["type"] = word_type

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

        if json_dump_dir is not None:
            file_path = os.path.join(json_dump_dir, 'data.json')
            if os.path.isfile(file_path):
                with codecs.open(file_path, 'r+', 'utf-8') as json_file:
                    print("Reading json file")
                    data_old = json.load(json_file)
                    json_file.seek(0)

                    values_old = [elem['word'] for elem in data_old['words']]

                    for elem in data["words"]:
                        if elem['word'] not in values_old:
                            data_old["words"].append(elem)

                    print("Dumping json file")
                    json.dump(data_old, json_file)
                    json_file.truncate()
            else:
                with codecs.open(file_path, 'w+', 'utf-8') as json_file:
                    print("Dumping json file")
                    json.dump(data, json_file)

        return data

    except Exception as e:
        traceback.print_exc()

    finally:
        folkets_lexikon_scraper.close_browser()


def extract_translation(raw_text, order):
    split_text = raw_text.split('\n')
    split_translation = split_text[0].split(',')

    if order[0] == '(Swedish)':
        return ",".join(split_translation[1:]).strip()
    else:
        return " ".join(split_translation[0].split(' ')[:-1]).strip()


def extract_type(raw_text):
    split_text = raw_text.split('\n')
    split_description = split_text[0].split(',')

    return split_description[0].split(' ')[-1].strip()


def extract_sentences(examples_raw, order):
    # If raw text is not None
    if examples_raw:
        try:
            # Matches what is in between parenthesis (english translation)
            # translations = re.findall('(?<=\()(.*)(?=\))', examples_raw)
            split_sentences = examples_raw.split('\n')
            try:
                translations = []
                for sentence in split_sentences:
                    # If there are multiple parenthesis, see if they are nested or they are 'orthogonal'
                    translation_test = re.findall('\((.*)\)', sentence)[0]
                    if '(' in translation_test and ')' in translation_test:
                        idx_open = [m.start() for m in re.finditer('\(', translation_test)]
                        idx_close = [m.start() for m in re.finditer('\)', translation_test)]
                        idx_close.reverse()

                        # If remaining parentheses are unbalanced, then the original pair is wrong
                        for i, j in zip(idx_open, idx_close):
                            if i > j:
                                translation_test = re.findall('\(.*?\)', sentence)[-1]
                                # Translation without enclosing parenthesis
                                n = len(translation_test)
                                translation_test = translation_test[1:n - 1]
                                break

                    translations.append(translation_test)

            except Exception as e:
                raise ValueError

            # If there are no translations for an example sentence, then we discard all
            if not translations:
                raise ValueError
            # Matches what is after Example and linebreak but not english translation
            # sentences = re.findall('(?:(?<=Example: )|(?<=\n))(.+)(?= \()', examples_raw)

            raw_sentences = examples_raw.replace('Example:', '').strip().split('\n')

            sentences = [re.sub('( ,| |,)$', '', sentence.replace('(' + translation + ')', ''))
                         for sentence, translation in zip(raw_sentences, translations)]

            # Filter sentences to only include those with translations
            # remove trailing whitespaces
            # and remove any text between parenthesis (in source language sentence)
            filtered_translations = []
            filtered_sentences = []
            for translation, sentence in zip(translations, sentences):
                if translation:
                    filtered_translations.append(translation.strip())
                    parenthesis_phrase = re.findall('\((.*)\)', sentence)
                    if parenthesis_phrase:
                        sentence = sentence.replace('(' + parenthesis_phrase[0] + ')', '')
                        sentence = sentence.replace('  ', ' ')
                    filtered_sentences.append(sentence.strip())

            if order[0] == '(Swedish)':
                return filtered_sentences, translations
            else:
                return translations, filtered_sentences

        except ValueError as e:
            print("No example sentences found.")
            return [], []
    else:
        print("No example sentences found.")
        return [], []


def get_all_sections(raw_text):
    sections = re.findall('\n[a-zA-Z]+:', raw_text)
    indices = [raw_text.index(x) for x in sections]
    intervals = [-1] + indices + [len(raw_text)]

    sections = [raw_text[intervals[i - 1] + 1:intervals[i]] for i in range(1, len(intervals))]
    sections[0] = 'Main: ' + sections[0]

    return sections


def get_section(sections, query):
    for elem in sections:
        if query.lower() + ':' in elem.lower():
            return elem
    return None


def find_best_result(word, sentence_rows):
    best_index = 0
    best_score = 0
    for i in range(len(sentence_rows)):
        swedish_sentences = sentence_rows[i][0]
        if swedish_sentences:
            sentence = swedish_sentences[0]
            score = fuzz.partial_ratio(word, sentence.lower())
            if score > best_score:
                best_index = i
                best_score = score

    return best_index


def get_score_and_substring(string1, string2):
    """Modified version of fuzzy wuzzy's get_raw_score to return not only the score
    but the starting and ending indices of the matched substring.
    """

    sm = SequenceMatcher(None, string1, string2)
    matching_blocks = sm.get_matching_blocks()

    best_score = 0
    start = 0
    end = 0
    substr = ''
    for block in matching_blocks:
        string2_starting_index = 0
        if (block[1] - block[0] > 0):
            string2_starting_index = block[1] - block[0]
        string2_ending_index = string2_starting_index + len(string1)
        string2_substr = string2[string2_starting_index:string2_ending_index]

        sm2 = SequenceMatcher(None, string1, string2_substr)
        similarity_ratio = sm2.ratio()
        if similarity_ratio > best_score:
            best_score = similarity_ratio
            start = string2_starting_index
            end = string2_ending_index
            substr = string2_substr

    return best_score, start, end, substr


def get_start_idx(spaces, query):
    """ Function to get the starting index of a word intersected by a query index in a string.

    Args:
        spaces: list of indices of spaces in a sentence
        query: index to compute intersection.
    """

    l = len(spaces)
    if query < spaces[0]:
        return 0
    if spaces[l - 1] < query:
        return spaces[l - 1] + 1
    for i in range(1, l):
        if spaces[i - 1] < query < spaces[i]:
            return spaces[i - 1] + 1


def get_end_idx(spaces, query, string_length):
    """ Function to get the ending index of a word intersected by a query index in a string.

    Args:
        spaces: list of indices of spaces in a sentence
        query: index to compute intersection.
    """

    l = len(spaces)
    if query <= spaces[0]:
        return spaces[0] - 1
    if spaces[l - 1] < query:
        return string_length - 1
    for i in range(1, l):
        if spaces[i - 1] < query <= spaces[i]:
            return spaces[i] - 1


def generate_mp3_file(text, file_path, language='sv'):
    speech = Speech(text, language)
    speech.save(file_path)


def download_google_search_image(query_string, thumbnail, directory):
    urls = dgi.get_image_urls(query_string)
    dgi.save_top_result(query_string, urls, thumbnail, directory)


def download_pixabay(query_string, thumbnail, directory):
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    api_key = os.getenv("PIXABAY_API_KEY")
    query_string = query_string.replace(' ', '+')

    target_url = 'https://pixabay.com/api/?key={0}&q={1}&lang=sv'.format(api_key, query_string)
    json_data = requests.get(target_url).json()

    if json_data['hits']:
        for result in json_data['hits']:
            if thumbnail:
                image_url = result['previewURL']
            else:
                image_url = result['webformatURL']

            try:
                request = urllib.request.Request(image_url, None, headers)
                response = urllib.request.urlopen(request)
            except HTTPError:
                continue
            break

        query_string = query_string.replace('+', '_')
        path = os.path.join(directory, query_string + '.jpg')

        f = open(path, 'wb')
        f.write(response.read())
        f.close()

        return True

    else:
        return False


if __name__ == '__main__':
    dirname = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    word = 'attityd'
    get_translation([word])

    # word_file = word.replace(' ', '_')
    # word_dir = os.path.join(dirname, word_file)
    #
    # download_pixabay(query_string=word, thumbnail=False, directory=word_dir)
