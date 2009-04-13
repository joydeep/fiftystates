#!/usr/bin/env python

import logging
import re
import urllib
import urlparse
from BeautifulSoup import BeautifulSoup

# Toggle this to the logging verbosity you want.
verbosity = logging.INFO

logger = logging.getLogger("MDScraper")
logger.setLevel(verbosity)
console_handler = logging.StreamHandler()
# Set up log formatters, and add them to the handlers.
console_formatter = logging.Formatter("%(message)s")
console_handler.setFormatter(console_formatter)
# Add the handlers to the logger.
logger.addHandler(console_handler)


# ugly hack
import sys
sys.path.append('./scripts/')
from pyutils.legislation import LegislationScraper, NoDataForYear

class MDLegislationScraper(LegislationScraper):
        state = 'md'
        def scrape_bills(self, chamber, year):
                ''' Scrapes the bills for the given year and chamber 
                The Maryland State stores the bills in the format- 
                http://mlis.state.md.us/1996rs/billfile/HB0001.htm
                so you will loop through the bills numbers 0001 to a number where you get 'page doesnt exist' repeatedly
                ''' 
                # Maryland's data is organised year-wise
                # THe upper house is called the senate and the lower house is called the House
                available_chambers = {'lower':'House', 'upper':'Senate'}
                chamber = available_chambers[chamber]
                
                if str(year) < '1996' :
                        raise NoDataForYear(year)
                
                if chamber is 'lower':
                        short_code = 'HB'
                else:
                        short_code = 'SB'
                
                bill_number = 1
                end_of_bills = 0
                while (end_of_bills != 1):
                        bill_number_str = str(bill_number)
                        bill_number_str = '0'*(4-len(bill_number_str)) + bill_number_str
                        url = 'http://mlis.state.md.us/%srs/billfile/%s%s.htm'%(year, short_code, bill_number_str)
                        # print url
                        logger.debug("Getting bill data from: %s", url)
                        data = urllib.urlopen(url).read()
                        soup = BeautifulSoup(data)
                        title_tag = soup.html.head.title
                        if title_tag.string.strip() == 'The page cannot be found':
                                end_of_bills = 1
                        print title_tag.string , end_of_bills
                        bill_number = bill_number + 500

if __name__ == '__main__':
  MDLegislationScraper().run()
