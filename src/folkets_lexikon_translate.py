"""Class for scraping dictionary data from queries made to Folkets-Lexikon
"""

from selenium import webdriver
import os
import time

FOLKETS_LEXIKON_LOOKUP = 'http://folkets-lexikon.csc.kth.se/folkets/folkets.en.html#lookup&'


class LookupException(Exception):
    """Class for managing data retrieval exceptions.

    """

    pass


class FolketsLexikonScraper:
    def __init__(self):
        dirname = os.path.dirname(__file__)
        # Headless browser
        options = webdriver.FirefoxOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')
        self.browser = webdriver.Firefox(executable_path=os.path.join(dirname, '../dependencies/geckodriver'),
                                         options=options)
        self.browser.set_page_load_timeout(30)

    def get_query_data(self, query):
        """
        Method to get dictionary data of a queried word from folkets-lexikon. At the moment,
        only the topmost result is considered.

        Args:
            query: word to query for from folkets-lexikon.
        """

        # Open link
        url = FOLKETS_LEXIKON_LOOKUP + query
        self.browser.get(url)
        time.sleep(1)

        try:
            # Check if word exists in dictionary
            state = self.browser.find_element_by_xpath("""//*[@id="folketsHuvud"]/div/table/tbody/tr[
            1]/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td/div""").text.lower()

            print("Getting data for '{0}'".format(query))

            if "There is no translation of" in state.lower() or "not in the dictionary" in state.lower():
                raise LookupException("Object not in the dictionary.")

            expand = self.browser.find_element_by_xpath("""//*[@id="folketsHuvud"]/div/table/tbody/tr[
            1]/td/table/tbody/tr[2]/td/table/tbody/tr[2]/td/div/div/table/tbody/tr[2]/td/table/tbody/tr/td[
            2]/table/tbody/tr[1]/td/table/tbody/tr/td[1]/div/img""")

            # Click on expand button for more information
            expand.click()
            time.sleep(0.5)

            lookup = self.browser.find_element_by_xpath("""//*[@id="folketsHuvud"]/div/table/tbody/tr[
            1]/td/table/tbody/tr[2]/td/table/tbody/tr[2]/td/div/div/table/tbody/tr[2]/td/table/tbody/tr/td[
            2]/table/tbody/tr[1]/td/table/tbody/tr/td[2]/table/tbody""")

            res = lookup.text
            # print(res[:10] + "...")

            # Get whether english or swedish text come first
            translation_row = lookup.find_element_by_class_name('gwt-HTML')
            flags = translation_row.find_elements_by_tag_name('img')
            flags_text = [f.get_attribute('alt') for f in flags]

            return res, flags_text

        except Exception as e:
            raise LookupException("Could not get data\n\t" + str(e))

    def close_browser(self):
        """Method to close the current webdriver session and all open Firefox windows spawned by this class.
        """

        self.browser.quit()
