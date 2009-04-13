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

        def sanitize_text(self, text):
                ''' to remove the \n, \r and other white spaces in the text'''
                text=str(text)
                text=text.replace('\r','')
                text=text.replace('\n','')
                text.strip()
                return text


        def extract_bill_title(self, bill_soup):
                '''Extracts the Title of the bill from the soup'''
                title = bill_soup('h4')[1].dd.string
                sanitized_title = self.sanitize_text(title)
                return sanitized_title

        def extract_bill_versions(self, bill_soup):
                '''Extracts the versions of the Bill'''
                #the versions of the bills are all stored as - 
                # http://mlis.state.md.us/YYYYrs/bills
                #doing a findAll on links with '/bills/ we get a taglist
                a_taglist= bill_soup.findAll(href=re.compile('/bills/'))
                #the first a href tag is generally the Final bill version's tag 
                #which also appears at the last incase the bill is passed
                bill_versions=list()
                tag = a_taglist[0]
                bill_version=dict()
                bill_version['name']=tag.string
                bill_version['url']=tag.attrs[0][1]
                bill_versions.append(bill_version)
                del bill_version
                for tag in a_taglist[1:]:
                        bill_version=dict()
                        bill_version=dict()
                        bill_version['name']=tag.string
                        bill_version['url']=tag.attrs[0][1]
                        #handling duplicacy in the a_taglist
                        if bill_version['url'] == bill_versions[0]['url']:
                                bill_versions[0]['name'] = bill_versions[0]['name']+' : '+bill_version['name']
                        else:
                                bill_versions.append(bill_version)
                        print bill_version['name'], bill_version['url']
                        del bill_version

  
                logger.debug("Found Bill Versions:%d", len(bill_versions))
                return bill_versions


        def get_bill_info(self, bill_soup, bill_id, chamber , year):
                '''Extracts all the requested info for a given bill.  
                Calls the parent's methods to enter the results into CSV files.
                '''
                #calculating the session taking 2009 as the 426th regual session
                #MD has one session per year

                session = 426 + (int(year)-2009)
                bill_title =  self.extract_bill_title(bill_soup)
                print bill_title
                #MD has one session per year; 2009 is the 426th session
                self.add_bill(chamber, session, bill_id, bill_title)
                
                
                # get all versions of the bill.
                # TODO: add  ammendments
                
                # MD bills can have multiple versions, generally there is a 
                # first reading, a third reading and ammendments
                # Get them all, and loop over
                # the results, adding each one.

                bill_versions = self.extract_bill_versions(bill_soup)
                base_url='http://mlis.state.md.us'
                for version in bill_versions:
                        version_name = version['name']
                        version_url = urlparse.urljoin(base_url, version['url'])
                        self.add_bill_version(chamber, session, bill_id, version_name, version_url)

                # grab primary and cosponsors 
                # MD doesnt specify any particular name to the sponsor, Hence, making
                # an assumption that the first person on the liit is the primary sponsor
                # Everyone else listed will be added as a 'cosponsor'.

                '''
                sponsors = self.extract_bill_sponsors(bill_soup)
                primary_sponsor = sponsors[0]
                cosponsors = sponsors[1:]
                self.add_sponsorship(chamber, session, bill_id, 'primary', primary_sponsor)
                for leg in cosponsors:
                        self.add_sponsorship(chamber, session, bill_id, 'cosponsor', leg)

                # Add Actions performed on the bill.
                bill_actions = self.extract_bill_actions(bill_soup, chamber)
                for action in bill_actions:
                        action_chamber = action['action_chamber']
                        action_date = action['action_date']
                        action_text = action['action_text']
                        self.add_action(chamber, session, bill_id, action_chamber, action_text, action_date)

                '''

        def scrape_bills(self, chamber, year):
                ''' Scrapes the bills for the given year and chamber 
                The Maryland State stores the bills in the format- 
                http://mlis.state.md.us/1996rs/billfile/HB0001.htm
                so you will loop through the bills numbers 0001 to a number where you get 'page doesnt exist' repeatedly
                ''' 
                # Maryland's data is organised year-wise, they have one session in a year
                # THe upper house is called the senate and the lower house is called the House
                available_chambers = {'lower':'House', 'upper':'Senate'}
                chamber = available_chambers[chamber]
                
                if str(year) < '1996' :
                        raise NoDataForYear(year)
                if chamber is 'House':
                        short_code = 'HB'
                else:
                        short_code = 'SB'
                
                bill_number = 1
                end_of_bills = 0
                while (end_of_bills != 1):
                        bill_number_str = str(bill_number)
                        bill_number_str = '0'*(4-len(bill_number_str)) + bill_number_str
                        url = 'http://mlis.state.md.us/%srs/billfile/%s%s.htm'%(year, short_code, bill_number_str)
                        print url
                        logger.debug("Getting bill data from: %s", url)
                        data = urllib.urlopen(url).read()
                        soup = BeautifulSoup(data)
                        title_tag = soup.html.head.title
                        if title_tag.string.strip() == 'The page cannot be found':
                                end_of_bills = 1
                                break
                        logger.debug("Title of hte page: %s", title_tag.string)
                        bill_number = bill_number + 500
                        self.get_bill_info(soup, short_code+bill_number_str, chamber, year)


if __name__ == '__main__':
  MDLegislationScraper().run()
