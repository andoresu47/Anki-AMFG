from src.folkets_lexikon_translate import FolketsLexikonScraper, LookupException
from googletrans import Translator


def get_translation(words):
    """ Function to scrape folkets-lexikon dictionary data for a given word translation.
    If unsuccessful, gets translation from google translate.
    """
    data = []
    folkets_lexikon_scraper = FolketsLexikonScraper()
    try:
        for word in words:
            try:
                d = folkets_lexikon_scraper.get_query_data(word)
                data.append(d)

            except LookupException as e:
                translator = Translator()
                translation = translator.translate(word, src='sv', dest='en')
                data.append([translation])

        return data

    except Exception as e:
        print(e)

    finally:
        folkets_lexikon_scraper.close_browser()
